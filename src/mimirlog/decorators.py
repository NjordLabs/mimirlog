"""Call logging and timing, without recording arguments."""

from __future__ import annotations

import functools
import inspect
import logging
import time
from collections.abc import Awaitable, Callable
from typing import NamedTuple, cast

from mimirlog.log import get_logger


class _Outcome(NamedTuple):
    success: dict[str, object]
    failure: Callable[[BaseException], dict[str, object]] | None


def _duration_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)


def _record(
    logger: logging.Logger, function: str, started: float, fields: dict[str, object]
) -> None:
    payload: dict[str, object] = {
        "duration_ms": _duration_ms(started),
        "function": function,
    }
    payload.update(fields)
    logger.info(payload)


def _finish(
    logger: logging.Logger,
    function: str,
    started: float,
    exc: BaseException | None,
    outcome: _Outcome,
) -> None:
    if exc is None or outcome.failure is None:
        _record(logger, function, started, outcome.success)
        return
    _record(logger, function, started, outcome.failure(exc))


def _protect(
    call: Callable[[], object],
    logger: logging.Logger,
    function: str,
    outcome: _Outcome,
) -> object:
    started = time.perf_counter()
    try:
        result = call()
    except Exception as exc:
        _finish(logger, function, started, exc, outcome)
        raise
    if inspect.iscoroutine(result):
        return _await_returned(result, logger, function, started, outcome)
    _finish(logger, function, started, None, outcome)
    return result


async def _await_returned(
    result: object,
    logger: logging.Logger,
    function: str,
    started: float,
    outcome: _Outcome,
) -> object:
    try:
        value = await cast(Awaitable[object], result)
    except Exception as exc:
        _finish(logger, function, started, exc, outcome)
        raise
    _finish(logger, function, started, None, outcome)
    return value


def _wrap(
    func: Callable[..., object], logger: logging.Logger, outcome: _Outcome
) -> Callable[..., object]:
    function = func.__qualname__

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: object, **kwargs: object) -> object:
            started = time.perf_counter()
            try:
                result = await cast(Awaitable[object], func(*args, **kwargs))
            except Exception as exc:
                _finish(logger, function, started, exc, outcome)
                raise
            _finish(logger, function, started, None, outcome)
            return result

        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args: object, **kwargs: object) -> object:
        return _protect(lambda: func(*args, **kwargs), logger, function, outcome)

    return wrapper


def log_call(func: Callable[..., object]) -> Callable[..., object]:
    """Log the outcome of ``func`` without its arguments.

    Coroutine functions are wrapped with an async wrapper that awaits
    them. The wrapper keeps the wrapped callable's metadata.

    Args:
        func: Callable to wrap.

    Returns:
        A wrapper with the same call signature.
    """
    logger = get_logger("mimirlog.call")

    def on_error(exc: BaseException) -> dict[str, object]:
        return {"exception": type(exc).__name__, "outcome": "exception"}

    return _wrap(func, logger, _Outcome({"outcome": "success"}, on_error))


def benchmark(
    logger: logging.Logger | None = None,
) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """Return a decorator that logs how long the call took.

    Coroutine functions are wrapped with an async wrapper that awaits
    them. The wrapper keeps the wrapped callable's metadata.

    Args:
        logger: Destination. ``None`` uses the ``mimirlog.benchmark`` logger.

    Returns:
        A decorator.
    """
    destination = logger if logger is not None else get_logger("mimirlog.benchmark")

    def decorate(func: Callable[..., object]) -> Callable[..., object]:
        return _wrap(func, destination, _Outcome({}, None))

    return decorate
