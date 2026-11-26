# Changelog

## Unreleased

## 0.2.1 - 2026-11-26

- Secret-named extras, including `password`, are redacted. Mapping values, tuples, and other mappings are walked, and a cycle stops at `***`.
- A decorator around a function that returns a coroutine logs the outcome after that coroutine finishes.
- The pymjolnir wheel is 0.1.2.

## 0.2.0 - 2026-11-22

- Nested redaction for a wider set of secret keys, including mapping arguments.
- JSON records keep JSON-safe extras and the current span id, without traceback text.
- `log_call` and `benchmark` keep callable metadata and await coroutine functions.
- `configure` replaces its handlers under a lock.

## 0.1.0 - 2026-11-22

- JSON formatter, redaction filter, and correlation ids.
- Named loggers through the pymjolnir multiton.
- `log_call` and `benchmark` decorators.
- Optional OpenTelemetry span id when that package is installed.
