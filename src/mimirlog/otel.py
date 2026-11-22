"""Optional bridge to an OpenTelemetry span.

The OpenTelemetry packages are not a dependency. When they are absent,
``current_span_id`` returns ``None``.
"""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Callable
from types import ModuleType
from typing import cast


def current_span_id() -> str | None:
    """Return the current span id when OpenTelemetry is installed.

    Returns:
        A hex span id, or ``None`` when there is no current span.
    """
    module = load_module("opentelemetry.trace")
    if module is None:
        return None
    get_current = getattr(module, "get_current_span", None)
    if not callable(get_current):
        return None
    caller: Callable[[], object] = cast(Callable[[], object], get_current)
    return format_span(caller())  # pylint: disable=not-callable


def load_module(
    name: str,
    finder: Callable[[str], object | None] = importlib.util.find_spec,
    importer: Callable[[str], ModuleType] = importlib.import_module,
) -> ModuleType | None:
    """Import ``name`` when it is installed.

    Args:
        name: Module name.
        finder: Returns a spec, or ``None`` when the module is absent.
        importer: Imports a module that the finder accepted.

    Returns:
        The imported module, or ``None``.
    """
    try:
        spec = finder(name)
    except ModuleNotFoundError:
        return None
    if spec is None:
        return None
    return importer(name)


def format_span(span: object) -> str | None:
    """Read a hex span id from an object that looks like a span.

    Args:
        span: Object with ``get_span_context``.

    Returns:
        A 16-digit hex span id, or ``None`` when the span is invalid.
    """
    get_context = getattr(span, "get_span_context", None)
    if get_context is None:
        return None
    context = get_context()
    if not getattr(context, "is_valid", False):
        return None
    span_id = getattr(context, "span_id", None)
    if not isinstance(span_id, int):
        return None
    return format(span_id, "016x")
