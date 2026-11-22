"""Async decorator behaviour."""

from __future__ import annotations

import asyncio
import io
import json

import pytest

from mimirlog import benchmark, configure, get_logger, log_call


def test_log_call_awaits_coroutines() -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)

    @log_call
    async def add(left: int, right: int) -> int:
        """Run this step."""
        return left + right

    @log_call
    async def fail() -> None:
        """Run this step."""
        raise RuntimeError("nope")

    assert add.__name__ == "add"
    assert asyncio.run(add(1, 2)) == 3
    with pytest.raises(RuntimeError):
        asyncio.run(fail())
    lines = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert lines[0]["message"]["outcome"] == "success"
    assert lines[1]["message"]["exception"] == "RuntimeError"


def test_benchmark_awaits_coroutines() -> None:
    """Run this step."""
    stream = io.StringIO()
    configure(stream=stream)

    @benchmark()
    async def work() -> str:
        """Run this step."""
        return "ok"

    @benchmark(get_logger("bench"))
    async def boom() -> None:
        """Run this step."""
        raise RuntimeError("slow")

    assert work.__name__ == "work"
    assert asyncio.run(work()) == "ok"
    with pytest.raises(RuntimeError):
        asyncio.run(boom())
    lines = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert "duration_ms" in lines[0]["message"]
    assert "duration_ms" in lines[1]["message"]
