"""Span id lookup when OpenTelemetry is absent."""

from __future__ import annotations

import pytest

from mimirlog import current_span_id
from mimirlog.otel import format_span, load_module
from mimirlog.spanproto import _Span, _Trace, hex_span_id


def test_span_id_without_otel() -> None:
    """Run this step."""
    assert current_span_id() is None
    assert load_module("opentelemetry.trace") is None
    assert load_module("missing", finder=lambda _name: None) is None
    assert format_span(object()) is None


def test_format_span_reads_a_valid_context() -> None:
    """Run this step."""

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


def test_format_span_rejects_an_invalid_context() -> None:
    """Run this step."""

    class Invalid:
        """Hold a test double."""

        def get_span_context(self) -> object:
            """Run this step."""
            return object()

    class MissingId:
        """Hold a test double."""

        def get_span_context(self) -> object:
            """Run this step."""
            return type("Ctx", (), {"is_valid": True, "span_id": "nope"})()

    assert format_span(Invalid()) is None
    assert format_span(MissingId()) is None

    class NotValid:
        """Hold a test double."""

        is_valid = False
        span_id = 1

    class MissingSpan:
        """Hold a test double."""

        is_valid = True

    assert hex_span_id(NotValid()) is None
    assert hex_span_id(MissingSpan()) is None
    assert _Trace.get_current_span(_Trace) is None
    assert _Span.get_span_context(_Span) is None


def test_load_module_uses_an_injected_importer() -> None:
    """Run this step."""

    class Context:
        """Hold a test double."""

        is_valid = True
        span_id = 255

    class Span:
        """Hold a test double."""

        def get_span_context(self) -> Context:
            """Run this step."""
            return Context()

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
