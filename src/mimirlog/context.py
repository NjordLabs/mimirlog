"""Correlation ids carried on a context variable."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_correlation: ContextVar[str | None] = ContextVar("mimirlog_correlation", default=None)


def correlation_id() -> str | None:
    """Return the correlation id for the current context.

    Returns:
        The bound id, or ``None`` when nothing is bound.
    """
    return _correlation.get()


@contextmanager
def bind(value: str) -> Iterator[None]:
    """Bind ``value`` as the correlation id for the duration of the block.

    Args:
        value: Id copied onto every record emitted inside the block.

    Yields:
        None.
    """
    token = _correlation.set(value)
    try:
        yield
    finally:
        _correlation.reset(token)
