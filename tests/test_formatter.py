"""Formatter extras and async decorators."""

from __future__ import annotations

import io
import json
import logging

import pytest

from mimirlog import configure, get_logger


def _configured(monkeypatch: pytest.MonkeyPatch) -> tuple[logging.Logger, io.StringIO]:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)

    def span() -> str:
        """Run this step."""
        return "span-1"

    monkeypatch.setattr("mimirlog.format.current_span_id", span)
    return get_logger("app"), stream


def test_formatter_keeps_safe_extras_and_span(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run this step."""
    logger, stream = _configured(monkeypatch)
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
    line = json.loads(stream.getvalue())
    assert line["span_id"] == "span-1"
    assert line["request_id"] == "r"
    assert line["count"] == 2
    assert line["correlation_id"] is None


def test_formatter_keeps_scalars_and_drops_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run this step."""
    logger, stream = _configured(monkeypatch)
    logger.info(
        "ready",
        extra={"blob": {"a": 1}, "flag": True, "missing": None, "ratio": 0.5},
    )
    line = json.loads(stream.getvalue())
    assert line["ratio"] == 0.5
    assert line["flag"] is True
    assert line["missing"] is None
    assert "blob" not in line
    assert "filename" not in line


def test_formatter_stringifies_a_mapping_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run this step."""
    logger, stream = _configured(monkeypatch)
    logger.info({"event": "ready", "tags": {"a"}})
    message = json.loads(stream.getvalue())["message"]
    assert message["event"] == "ready"
    assert "a" in message["tags"]


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
