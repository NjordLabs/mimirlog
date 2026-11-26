"""Nested redaction and formatter output."""

from __future__ import annotations

import logging
from collections import UserDict

from mimirlog.redact import RedactionFilter, redact_mapping


def test_redact_walks_nested_mappings_and_lists() -> None:
    """Run this step."""
    cleaned = redact_mapping({
        "Api_Key": "k",
        "nested": {
            "access_token": "a",
            "authorization": "auth",
            "cookie": "c",
            "host": "example",
            "private_key": "p",
            "refresh_token": "r",
            "session": "s",
        },
        "items": [{"Password": "pw"}, "keep", [{"token": "t"}]],
        "count": 1,
        "flag": False,
        "pair": ("token", "left-alone"),
    })
    assert cleaned["Api_Key"] == "***"
    assert cleaned["nested"] == {
        "access_token": "***",
        "authorization": "***",
        "cookie": "***",
        "host": "example",
        "private_key": "***",
        "refresh_token": "***",
        "session": "***",
    }
    assert cleaned["items"] == [{"Password": "***"}, "keep", [{"token": "***"}]]
    assert cleaned["count"] == 1
    assert cleaned["flag"] is False
    assert cleaned["pair"] == ("token", "left-alone")


def test_redact_walks_tuples_mappings_and_cycles() -> None:
    """Run this step."""
    nested = UserDict({"client_secret": "c", "name": "ada"})
    cleaned = redact_mapping({
        "rows": ({"secret_key": "k"}, "keep"),
        "bag": nested,
    })
    assert cleaned["rows"] == ({"secret_key": "***"}, "keep")
    assert cleaned["bag"] == {"client_secret": "***", "name": "ada"}

    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic
    assert redact_mapping(cyclic)["self"] == "***"

    deep: dict[str, object] = {"leaf": "ok"}
    for _ in range(40):
        deep = {"child": deep}
    node: object = redact_mapping(deep)
    for _ in range(33):
        assert isinstance(node, dict)
        node = node["child"]
    assert node == "***"


def test_filter_redacts_mapping_args_and_keeps_strings() -> None:
    """Run this step."""
    mapped = logging.LogRecord(
        "app",
        logging.INFO,
        __file__,
        1,
        "user %(name)s",
        {"name": "ada", "token": "secret"},
        None,
    )
    assert RedactionFilter().filter(mapped) is True
    assert mapped.args == {"name": "ada", "token": "***"}

    positional = logging.LogRecord(
        "app",
        logging.INFO,
        __file__,
        1,
        "user %s %s",
        ({"session": "s"}, "plain"),
        None,
    )
    RedactionFilter().filter(positional)
    assert positional.args == ({"session": "***"}, "plain")

    bare = logging.LogRecord("app", logging.INFO, __file__, 1, "hi", (), None)
    bare.args = None
    RedactionFilter().filter(bare)
    assert bare.args is None
