"""Optional bridge to an OpenTelemetry span.

The OpenTelemetry packages are not a dependency. When they are absent,
``current_span_id`` returns ``None``.
"""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Callable
from types import ModuleType

from mimirlog.spanproto import _Span, _Trace, hex_span_id, read_span


def current_span_id() -> str | None:
    """Return the current span id when OpenTelemetry is installed.

    Returns:
        A hex span id, or ``None`` when there is no current span.
    """
    module = load_module("opentelemetry.trace")
    if not isinstance(module, _Trace):
        return None
    return format_span(read_span(module))


def load_module(
    name: str,
    finder: Callable[[str], object | None] | None = None,
    importer: Callable[[str], ModuleType] | None = None,
) -> ModuleType | None:
    """Import ``name`` when it is installed.

    Args:
        name: Module name.
        finder: Returns a spec, or ``None`` when the module is absent.
        importer: Imports a module that the finder accepted.

    Returns:
        The imported module, or ``None``.
    """
    chosen_finder = importlib.util.find_spec if finder is None else finder
    chosen_importer = importlib.import_module if importer is None else importer
    try:
        spec = chosen_finder(name)
    except ModuleNotFoundError:
        return None
    if spec is None:
        return None
    return chosen_importer(name)


def format_span(span: object) -> str | None:
    """Read a hex span id from an object that looks like a span.

    Args:
        span: Object with ``get_span_context``.

    Returns:
        A 16-digit hex span id, or ``None`` when the span is invalid.
    """
    if not isinstance(span, _Span):
        return None
    return hex_span_id(span.get_span_context())
