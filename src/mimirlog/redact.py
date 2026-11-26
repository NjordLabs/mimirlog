"""Drop secret-shaped mapping keys before a record is formatted."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import cast

_LogArgs = tuple[object, ...] | Mapping[str, object] | None

_SECRET_KEYS = frozenset({
    "access_token",
    "api_key",
    "authorization",
    "client_secret",
    "cookie",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "secret_key",
    "session",
    "token",
})

_MAX_DEPTH = 32


def is_secret_key(key: str) -> bool:
    """Return whether ``key`` names a credential.

    Matching is case-insensitive.

    Args:
        key: Mapping key or log-record attribute name.

    Returns:
        ``True`` when the name is in the secret list.
    """
    return key.lower() in _SECRET_KEYS


def redact_mapping(payload: Mapping[str, object]) -> dict[str, object]:
    """Return a copy of ``payload`` with secret keys replaced.

    Nested mappings, lists, and tuples are walked. A cycle or a value
    deeper than 32 levels becomes ``"***"``. Key matching is
    case-insensitive.

    Args:
        payload: Mapping that may contain credentials.

    Returns:
        A new mapping. Secret values are the string ``"***"``.
    """
    seen = {id(payload)}
    return _redact_mapping(cast("Mapping[object, object]", payload), 0, seen)


def _redact_mapping(
    payload: Mapping[object, object], depth: int, seen: set[int]
) -> dict[str, object]:
    cleaned: dict[str, object] = {}
    for key, value in payload.items():
        name = key if isinstance(key, str) else str(key)
        if is_secret_key(name):
            cleaned[name] = "***"
        else:
            cleaned[name] = _redact_value(value, depth + 1, seen)
    return cleaned


def _redact_value(value: object, depth: int, seen: set[int]) -> object:
    if depth > _MAX_DEPTH:
        return "***"
    if isinstance(value, Mapping):
        return _walk(value, seen, lambda: _redact_mapping(value, depth, seen))
    if isinstance(value, list):
        return _walk(value, seen, lambda: _copy_list(value, depth, seen))
    if isinstance(value, tuple):
        return _walk(value, seen, lambda: _copy_tuple(value, depth, seen))
    return value


def _copy_list(value: list[object], depth: int, seen: set[int]) -> list[object]:
    return [_redact_value(item, depth + 1, seen) for item in value]


def _copy_tuple(value: tuple[object, ...], depth: int, seen: set[int]) -> tuple[object, ...]:
    return tuple(_redact_value(item, depth + 1, seen) for item in value)


def _walk(value: object, seen: set[int], copy: Callable[[], object]) -> object:
    ident = id(value)
    if ident in seen:
        return "***"
    seen.add(ident)
    try:
        return copy()
    finally:
        seen.discard(ident)


def _redact_args(args: _LogArgs) -> _LogArgs:
    if isinstance(args, Mapping):
        return redact_mapping(args)
    if isinstance(args, tuple):
        return tuple(_redact_value(item, 0, set()) for item in args)
    return args


class RedactionFilter(logging.Filter):
    """Replace secret mapping keys on a log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact mapping messages and mapping arguments.

        String arguments are left unchanged so free text is not scanned.

        Args:
            record: Record about to be formatted.

        Returns:
            Always ``True``. The record is kept.
        """
        if isinstance(record.msg, dict):
            record.msg = redact_mapping(record.msg)
        record.args = _redact_args(record.args)
        _redact_attributes(record)
        return True


def _redact_attributes(record: logging.LogRecord) -> None:
    for key, value in list(vars(record).items()):
        if key in {"args", "msg"}:
            continue
        if is_secret_key(key):
            setattr(record, key, "***")
        elif isinstance(value, (Mapping, list, tuple)):
            setattr(record, key, _redact_value(value, 0, set()))
