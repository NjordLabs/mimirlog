"""A sync wrapper that returns a coroutine."""

from __future__ import annotations

import asyncio
import io
import json

import pytest

from mimirlog import configure, log_call


def test_log_call_waits_for_a_returned_coroutine() -> None:
    """The outcome is logged after the returned coroutine finishes."""
    stream = io.StringIO()
    configure(stream=stream)

    @log_call
    def later() -> object:
        """Return a coroutine."""

        async def inner() -> str:
            """Finish later."""
            return "done"

        return inner()

    assert asyncio.run(later()) == "done"
    lines = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert lines[0]["message"]["outcome"] == "success"

    @log_call
    def broken() -> object:
        """Return a coroutine that fails."""

        async def inner() -> str:
            """Fail later."""
            raise RuntimeError("late")

        return inner()

    with pytest.raises(RuntimeError):
        asyncio.run(broken())
    failed = [json.loads(line) for line in stream.getvalue().splitlines()][-1]
    assert failed["message"]["exception"] == "RuntimeError"
