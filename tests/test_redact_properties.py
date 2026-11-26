"""Property tests for redaction."""

from __future__ import annotations

import pytest

pytest.importorskip("hypothesis")
from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from mimirlog.redact import redact_mapping  # noqa: E402

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
