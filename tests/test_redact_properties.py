"""Property tests for redaction."""

from __future__ import annotations

import importlib.util

import pytest

if importlib.util.find_spec("hypothesis") is None:
    pytest.skip("hypothesis is not installed", allow_module_level=True)
from hypothesis import given
from hypothesis import strategies as st

from mimirlog.redact import redact_mapping

_KEYS = st.sampled_from(["password", "token", "note", "secret", "name"])


@given(st.dictionaries(_KEYS, st.text(max_size=20), max_size=5))
def test_secret_keys_are_replaced(payload: dict[str, str]) -> None:
    """Every secret-named key becomes *** and other keys stay."""
    cleaned = redact_mapping(payload)
    for key, value in payload.items():
        if key in {"password", "token", "secret"}:
            assert cleaned[key] == "***"
        else:
            assert cleaned[key] == value
