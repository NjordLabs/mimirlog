"""Protocols for an optional OpenTelemetry span."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


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
    if not isinstance(module, _Trace):
        return None
    try:
        return module.get_current_span()
    except TypeError:
        return None


def hex_span_id(context: object) -> str | None:
    """Format a span id when the context looks valid.

    Args:
        context: Object with ``is_valid`` and ``span_id``.

    Returns:
        A 16-digit hex span id, or ``None``.
    """
    if not isinstance(context, _SpanContext):
        return None
    if context.is_valid is not True:
        return None
    if not isinstance(context.span_id, int):
        return None
    return format(context.span_id, "016x")
