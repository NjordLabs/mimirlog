"""Structured logging for Python services.

Named loggers are a multiton. Correlation ids travel on a context
variable. Redaction runs before a record is formatted.
"""

from mimirlog.context import bind, correlation_id
from mimirlog.decorators import benchmark, log_call
from mimirlog.log import configure, get_logger, reset
from mimirlog.otel import current_span_id

__all__ = [
    "benchmark",
    "bind",
    "configure",
    "correlation_id",
    "current_span_id",
    "get_logger",
    "log_call",
    "reset",
]
