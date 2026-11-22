"""Call logging and timing, without recording arguments."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from mimirlog.log import get_logger


def log_call(func: Callable[..., object]) -> Callable[..., object]:
    """Log the outcome of ``func`` without its arguments.

    Args:
        func: Callable to wrap.

    Returns:
        A wrapper with the same call signature.
    """
    logger = get_logger("mimirlog.call")

    def wrapper(*args: object, **kwargs: object) -> object:
        started = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.info({
                "duration_ms": round(duration_ms, 3),
                "function": func.__qualname__,
                "outcome": "exception",
                "exception": type(exc).__name__,
            })
            raise
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info({
            "duration_ms": round(duration_ms, 3),
            "function": func.__qualname__,
            "outcome": "success",
        })
        return result

    wrapper.__qualname__ = func.__qualname__
    return wrapper


def benchmark(
    logger: logging.Logger | None = None,
) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Return a decorator that logs how long the call took.

    Args:
        logger: Destination. ``None`` uses the ``mimirlog.benchmark`` logger.

    Returns:
        A decorator.
    """
    destination = logger if logger is not None else get_logger("mimirlog.benchmark")

    def decorate(func: Callable[..., object]) -> Callable[..., object]:
        def wrapper(*args: object, **kwargs: object) -> object:
            started = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - started) * 1000
                destination.info({
                    "duration_ms": round(duration_ms, 3),
                    "function": func.__qualname__,
                })

        wrapper.__qualname__ = func.__qualname__
        return wrapper

    return decorate
