"""JSON lines for the standard library logging module."""

from __future__ import annotations

import json
import logging
from typing import cast

from mimirlog.context import correlation_id
from mimirlog.otel import current_span_id

_RESERVED = frozenset(
    logging.LogRecord("n", logging.INFO, "", 0, "", (), None).__dict__,
) | {"asctime", "message"}


def _scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _extras(record: logging.LogRecord) -> dict[str, object]:
    extras: dict[str, object] = {}
    fields = cast("dict[str, object]", vars(record))
    for key, value in fields.items():
        if key in _RESERVED or not _scalar(value):
            continue
        extras[key] = value
    return extras


def _exception(record: logging.LogRecord) -> dict[str, object]:
    if not record.exc_info:
        return {}
    kind = record.exc_info[0]
    return {"exception": kind.__name__ if kind else ""}


def _span_field() -> dict[str, object]:
    span_id = current_span_id()
    if span_id is None:
        return {}
    return {"span_id": span_id}


def _dump(payload: dict[str, object]) -> str:
    try:
        return json.dumps(payload)
    except (TypeError, ValueError):
        return json.dumps(payload, default=str)


class JsonFormatter(logging.Formatter):
    """Format one record as a single JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize ``record`` without traceback text.

        JSON-safe extras are copied. ``span_id`` is set when a current
        span is available. Values ``json`` cannot encode fall back to
        ``str``.

        Args:
            record: Record already passed through filters.

        Returns:
            One JSON object, with no trailing newline.
        """
        message: object = record.msg if isinstance(record.msg, dict) else record.getMessage()
        payload: dict[str, object] = {
            "correlation_id": correlation_id(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
        }
        payload.update(_exception(record))
        payload.update(_span_field())
        for key, value in _extras(record).items():
            if key not in payload:
                payload[key] = value
        return _dump(payload)
