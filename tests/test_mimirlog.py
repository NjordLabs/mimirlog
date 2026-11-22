"""Behaviour of the structured logger."""

from __future__ import annotations

import io
import json

import pytest

from mimirlog import (
    bind,
    configure,
    correlation_id,
    get_logger,
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
