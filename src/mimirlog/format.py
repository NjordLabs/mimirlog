"""JSON lines for the standard library logging module."""

from __future__ import annotations

import json
import logging

from mimirlog.context import correlation_id


class JsonFormatter(logging.Formatter):
    """Format one record as a single JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize ``record`` without the traceback text of other records.

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
        if record.exc_info:
            kind = record.exc_info[0]
            payload["exception"] = kind.__name__ if kind else ""
        return json.dumps(payload, default=str)
