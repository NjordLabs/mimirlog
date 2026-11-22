"""Protocols for an optional OpenTelemetry span."""

from __future__ import annotations

from typing import Protocol, cast, runtime_checkable


@runtime_checkable
class _Trace(Protocol):
    """Module that can return the active span."""

    def get_current_span(self) -> object:
        """Return the active span.

        Returns:
            The active span.
        """
        return None


@runtime_checkable
class _Span(Protocol):
    """Object that exposes a span context."""

    def get_span_context(self) -> object:
        """Return the span context.

        Returns:
            The span context.
        """
        return None


@runtime_checkable
class _SpanContext(Protocol):
    """Fields read from a span context."""

    is_valid: bool
    span_id: object


def read_span(module: object) -> object | None:
    """Return the current span object, or ``None``.

    Args:
        module: Imported trace module.

    Returns:
        The span, or ``None`` when the module cannot produce one.
    """
    getter = getattr(module, "get_current_span", None)
    if not callable(getter):
        return None
    return cast(object, getter())


def hex_span_id(context: object) -> str | None:
    """Format a span id when the context looks valid.

    Args:
        context: Object with ``is_valid`` and ``span_id``.

    Returns:
        A 16-digit hex span id, or ``None``.
    """
    if not hasattr(context, "is_valid") or not hasattr(context, "span_id"):
        return None
    if getattr(context, "is_valid", False) is not True:
        return None
    span_id = getattr(context, "span_id", None)
    if not isinstance(span_id, int):
        return None
    return format(span_id, "016x")
