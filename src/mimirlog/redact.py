"""Drop secret-shaped mapping keys before a record is formatted."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import cast

_LogArgs = tuple[object, ...] | Mapping[str, object] | None

_SECRET_KEYS = frozenset({
    "access_token",
    "api_key",
    "authorization",
    "cookie",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "session",
    "token",
})


def redact_mapping(payload: dict[str, object]) -> dict[str, object]:
    """Return a copy of ``payload`` with secret keys replaced.

    Nested mappings and lists are walked. Scalars and other containers
    are copied unchanged. Key matching is case-insensitive.

    Args:
        payload: Mapping that may contain credentials.

    Returns:
        A new mapping. Secret values are the string ``"***"``.
    """
    cleaned: dict[str, object] = {}
    for key, value in payload.items():
        if key.lower() in _SECRET_KEYS:
            cleaned[key] = "***"
        else:
            cleaned[key] = _redact_value(value)
    return cleaned


def _redact_value(value: object) -> object:
    if isinstance(value, dict):
        return redact_mapping(cast("dict[str, object]", value))
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    return value


def _redact_args(args: _LogArgs) -> _LogArgs:
    if isinstance(args, dict):
        return redact_mapping(cast("dict[str, object]", args))
    if isinstance(args, tuple):
        return tuple(_redact_value(item) for item in args)
    return args


class RedactionFilter(logging.Filter):
    """Replace secret mapping keys on a log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact mapping messages and mapping arguments.

        String arguments are left unchanged so free text is not scanned.

        Args:
            record: Record about to be formatted.

        Returns:
            Always ``True``. The record is kept.
        """
        if isinstance(record.msg, dict):
            record.msg = redact_mapping(record.msg)
        record.args = _redact_args(record.args)
        return True
