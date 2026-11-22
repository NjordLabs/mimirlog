"""Behaviour of the structured logger."""

from __future__ import annotations

import io
import json

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
from mimirlog.redact import redact_mapping


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

    assert work() == "ok"
    payload = json.loads(stream.getvalue().strip())
    assert str(payload["message"]["function"]).endswith("work")
    assert "duration_ms" in payload["message"]


def test_formatter_includes_exception_type() -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)
    logger = get_logger("app")
    try:
        raise ValueError("bad")
    except ValueError:
        logger.exception("failed")
    payload = json.loads(stream.getvalue().strip())
    assert payload["exception"] == "ValueError"
