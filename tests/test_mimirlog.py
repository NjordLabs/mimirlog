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
    current_span_id,
    get_logger,
    log_call,
    reset,
)
from mimirlog.otel import format_span, load_module
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


def test_span_id_without_otel() -> None:
    """Run this step."""
    assert current_span_id() is None
    assert load_module("opentelemetry.trace") is None
    assert load_module("missing", finder=lambda _name: None) is None
    assert format_span(object()) is None

    class Context:
        """Hold a test double."""

        is_valid = True
        span_id = 255

    class Span:
        """Hold a test double."""

        def get_span_context(self) -> Context:
            """Run this step."""
            return Context()

    assert format_span(Span()) == "00000000000000ff"

    class Invalid:
        """Hold a test double."""

        def get_span_context(self) -> object:
            """Run this step."""
            return object()

    assert format_span(Invalid()) is None

    class MissingId:
        """Hold a test double."""

        def get_span_context(self) -> object:
            """Run this step."""
            return type("Ctx", (), {"is_valid": True, "span_id": "nope"})()

    assert format_span(MissingId()) is None

    class FakeModule:
        """Hold a test double."""

        @staticmethod
        def get_current_span() -> Span:
            """Run this step."""
            return Span()

    loaded = load_module(
        "opentelemetry.trace",
        finder=lambda _name: object(),
        importer=lambda _name: FakeModule(),  # type: ignore[arg-type, return-value]
    )
    assert loaded is not None
    assert format_span(loaded.get_current_span()) == "00000000000000ff"


def test_current_span_id_reads_a_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run this step."""

    class Context:
        """Hold a test double."""

        is_valid = True
        span_id = 1

    class Span:
        """Hold a test double."""

        def get_span_context(self) -> Context:
            """Run this step."""
            return Context()

    class Module:
        """Hold a test double."""

        @staticmethod
        def get_current_span() -> Span:
            """Run this step."""
            return Span()

    monkeypatch.setattr("mimirlog.otel.load_module", lambda _name: Module())
    assert current_span_id() == "0000000000000001"
    monkeypatch.setattr("mimirlog.otel.load_module", lambda _name: object())
    assert current_span_id() is None
    monkeypatch.setattr(
        "mimirlog.otel.load_module",
        lambda _name: type("Module", (), {"get_current_span": 1})(),
    )
    assert current_span_id() is None


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
