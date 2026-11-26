"""Call and benchmark decorators."""

from __future__ import annotations

import asyncio
import io
import json
import logging

import pytest

from mimirlog import benchmark, configure, get_logger, log_call
from mimirlog.format import JsonFormatter


def test_log_call_records_success_and_exception() -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)

    @log_call
    def add(left: int, right: int) -> int:
        """Run this step."""
        return left + right

    @log_call
    def fail() -> None:
        """Run this step."""
        raise RuntimeError("nope")

    assert add.__name__ == "add"
    assert add(1, 2) == 3
    with pytest.raises(RuntimeError):
        fail()
    lines = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert lines[0]["message"]["outcome"] == "success"
    assert lines[1]["message"]["exception"] == "RuntimeError"


def test_log_call_waits_for_a_returned_coroutine() -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)

    @log_call
    def later() -> object:
        """Run this step."""

        async def inner() -> str:
            return "done"

        return inner()

    assert asyncio.run(later()) == "done"
    lines = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert lines[0]["message"]["outcome"] == "success"

    @log_call
    def broken() -> object:
        """Run this step."""

        async def inner() -> str:
            raise RuntimeError("late")

        return inner()

    with pytest.raises(RuntimeError):
        asyncio.run(broken())
    failed = [json.loads(line) for line in stream.getvalue().splitlines()][-1]
    assert failed["message"]["exception"] == "RuntimeError"


def test_benchmark_logs_duration() -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)

    @benchmark()
    def work() -> str:
        """Run this step."""
        return "ok"

    assert work.__name__ == "work"
    assert work() == "ok"

    @benchmark(get_logger("bench"))
    def boom() -> None:
        """Run this step."""
        raise RuntimeError("slow")

    with pytest.raises(RuntimeError):
        boom()
    lines = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert str(lines[0]["message"]["function"]).endswith("work")
    assert "duration_ms" in lines[0]["message"]
    assert str(lines[1]["message"]["function"]).endswith("boom")


def test_formatter_includes_exception_type() -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)
    logger = get_logger("app")
    try:
        raise ValueError("bad")
    except ValueError:
        logger.exception("failed")
    text = stream.getvalue()
    assert "Traceback" not in text
    payload = json.loads(text.strip())
    assert payload["exception"] == "ValueError"
    assert payload["message"] == "failed"
    record = logger.makeRecord(
        logger.name, logging.INFO, __file__, 1, "plain", (), (None, None, None)
    )
    rendered = json.loads(JsonFormatter().format(record))
    assert rendered["exception"] == ""
    assert "span_id" not in rendered
