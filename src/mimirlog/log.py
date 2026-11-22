"""Named loggers and one-time configuration."""

from __future__ import annotations

import logging
import sys
import threading
from typing import TextIO

from pymjolnir import Multiton

from mimirlog.format import JsonFormatter
from mimirlog.redact import RedactionFilter

_loggers: Multiton[logging.Logger] = Multiton(logging.getLogger)
_owned: set[int] = set()
_lock = threading.Lock()


def configure(level: int = logging.INFO, stream: TextIO | None = None) -> None:
    """Attach one JSON handler to the root logger.

    A second call replaces the handlers this function added. Handlers
    created by other libraries are left in place. Replacement is
    serialized so two callers cannot drop each other's handler.

    Args:
        level: Root level, as a ``logging`` constant.
        stream: Stream for the handler. ``None`` uses ``sys.stderr``.
    """
    with _lock:
        root = logging.getLogger()
        root.setLevel(level)
        for handler in list(root.handlers):
            if id(handler) in _owned:
                root.removeHandler(handler)
                _owned.discard(id(handler))
        target = sys.stderr if stream is None else stream
        handler = logging.StreamHandler(target)
        handler.setFormatter(JsonFormatter())
        handler.addFilter(RedactionFilter())
        _owned.add(id(handler))
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return the logger for ``name``, creating it once.

    Args:
        name: Logger name. An empty name is rejected.

    Returns:
        The standard-library logger for ``name``.
    """
    return _loggers.get(name)


def reset() -> None:
    """Drop the named-logger cache. The process loggers stay registered."""
    _loggers.reset()
