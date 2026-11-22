"""Drop secret-shaped mapping keys before a record is formatted."""

from __future__ import annotations

import logging

_SECRET_KEYS = frozenset({
    "authorization",
    "password",
    "secret",
    "token",
})


def redact_mapping(payload: dict[str, object]) -> dict[str, object]:
    """Return a copy of ``payload`` with secret keys replaced.

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
            cleaned[key] = value
    return cleaned


class RedactionFilter(logging.Filter):
    """Replace secret mapping keys on a log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact ``record.msg`` when it is a mapping.

        Args:
            record: Record about to be formatted.

        Returns:
            Always ``True``. The record is kept.
        """
        if isinstance(record.msg, dict):
            record.msg = redact_mapping(record.msg)
        return True
