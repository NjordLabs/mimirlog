"""Behaviour of the structured logger."""

from __future__ import annotations

import asyncio
import io
import json
import logging

import pytest

from mimirlog import (
    benchmark,
    bind,
    configure,
    correlation_id,
    get_logger,
    log_call,
    reset,
)
from mimirlog.format import JsonFormatter
from mimirlog.redact import RedactionFilter, redact_mapping


def test_named_logger_is_cached() -> None:
    """Run this step."""
    reset()
    first = get_logger("app")
    second = get_logger("app")
    assert first is second


def test_empty_logger_name_is_rejected() -> None:
    """Run this step."""
    with pytest.raises(ValueError):
        get_logger("")


def test_configure_emits_json_and_replaces_its_handler() -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)
    configure(stream=stream)
    with bind("run-1"):
        get_logger("app").info({"password": "secret", "event": "ready"})
    payload = json.loads(stream.getvalue().strip().splitlines()[-1])
    assert payload["correlation_id"] == "run-1"
    assert payload["message"]["password"] == "***"
    assert payload["message"]["event"] == "ready"
    assert correlation_id() is None


def test_redact_leaves_other_keys() -> None:
    """Run this step."""
    cleaned = redact_mapping({"token": "abc", "host": "example"})
    assert cleaned == {"token": "***", "host": "example"}


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


def test_redact_walks_nested_mappings_and_lists() -> None:
    """Run this step."""
    cleaned = redact_mapping({
        "Api_Key": "k",
        "nested": {
            "access_token": "a",
            "authorization": "auth",
            "cookie": "c",
            "host": "example",
            "private_key": "p",
            "refresh_token": "r",
            "session": "s",
        },
        "items": [{"Password": "pw"}, "keep", [{"token": "t"}]],
        "count": 1,
        "flag": False,
        "pair": ("token", "left-alone"),
    })
    assert cleaned["Api_Key"] == "***"
    assert cleaned["nested"] == {
        "access_token": "***",
        "authorization": "***",
        "cookie": "***",
        "host": "example",
        "private_key": "***",
        "refresh_token": "***",
        "session": "***",
    }
    assert cleaned["items"] == [{"Password": "***"}, "keep", [{"token": "***"}]]
    assert cleaned["count"] == 1
    assert cleaned["flag"] is False
    assert cleaned["pair"] == ("token", "left-alone")


def test_filter_redacts_mapping_args_and_keeps_strings() -> None:
    """Run this step."""
    mapped = logging.LogRecord(
        "app",
        logging.INFO,
        __file__,
        1,
        "user %(name)s",
        {"name": "ada", "token": "secret"},
        None,
    )
    assert RedactionFilter().filter(mapped) is True
    assert mapped.args == {"name": "ada", "token": "***"}

    positional = logging.LogRecord(
        "app",
        logging.INFO,
        __file__,
        1,
        "user %s %s",
        ({"session": "s"}, "plain"),
        None,
    )
    RedactionFilter().filter(positional)
    assert positional.args == ({"session": "***"}, "plain")

    bare = logging.LogRecord("app", logging.INFO, __file__, 1, "hi", (), None)
    bare.args = None
    RedactionFilter().filter(bare)
    assert bare.args is None


def test_formatter_keeps_safe_extras_span_and_stringifies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)

    def span() -> str:
        """Run this step."""
        return "span-1"

    monkeypatch.setattr("mimirlog.format.current_span_id", span)
    logger = get_logger("app")
    logger.info(
        "ready",
        extra={
            "blob": {"a": 1},
            "count": 2,
            "correlation_id": "override",
            "flag": True,
            "missing": None,
            "ratio": 0.5,
            "request_id": "r",
        },
    )
    logger.info({"event": "ready", "tags": {"a"}})
    lines = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert lines[0]["span_id"] == "span-1"
    assert lines[0]["request_id"] == "r"
    assert lines[0]["count"] == 2
    assert lines[0]["correlation_id"] is None
    assert lines[0]["ratio"] == 0.5
    assert lines[0]["flag"] is True
    assert lines[0]["missing"] is None
    assert "blob" not in lines[0]
    assert "filename" not in lines[0]
    assert lines[1]["message"]["event"] == "ready"
    assert "a" in lines[1]["message"]["tags"]


def test_configure_defaults_to_stderr_and_keeps_foreign_handlers() -> None:
    """Run this step."""
    root = logging.getLogger()
    foreign = logging.NullHandler()
    root.addHandler(foreign)
    stream = io.StringIO()
    try:
        configure()
        configure(stream=stream)
        assert foreign in root.handlers
        get_logger("app").info("ready")
    finally:
        root.removeHandler(foreign)
    assert "ready" in stream.getvalue()


def test_decorators_await_coroutines() -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)

    @log_call
    async def add(left: int, right: int) -> int:
        """Run this step."""
        return left + right

    @log_call
    async def fail() -> None:
        """Run this step."""
        raise RuntimeError("nope")

    @benchmark()
    async def work() -> str:
        """Run this step."""
        return "ok"

    @benchmark(get_logger("bench"))
    async def boom() -> None:
        """Run this step."""
        raise RuntimeError("slow")

    assert add.__name__ == "add"
    assert asyncio.run(add(1, 2)) == 3
    with pytest.raises(RuntimeError):
        asyncio.run(fail())
    assert work.__name__ == "work"
    assert asyncio.run(work()) == "ok"
    with pytest.raises(RuntimeError):
        asyncio.run(boom())
    lines = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert lines[0]["message"]["outcome"] == "success"
    assert lines[1]["message"]["exception"] == "RuntimeError"
    assert "duration_ms" in lines[2]["message"]
    assert "duration_ms" in lines[3]["message"]
