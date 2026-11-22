# AI agent handoff

## Identity

`mimirlog` is structured logging. Python 3.13. Public repository
`NjordLabs/mimirlog`.

## Scope

JSON records, redaction, correlation ids, and call decorators. Named
loggers use pymjolnir's multiton, pinned in `pyproject.toml`.

## Commands

```bash
sh scripts/check-ci-local.sh
```

## Known pitfalls

`v0.1.0` is released. Quality on that pull request passed with
`GHCR_READ_TOKEN` able to pull the private lint image.

## Suggested next work

PyPI publish stays open. The GitHub Release is `v0.1.0`.

## Recent history

- feat(log): add JSON logging, redaction, and call decorators
- fix(quality): split span tests and hide untyped span lookups from mypy
- docs(readme): install from the v0.1.0 git tag

*Last updated: 2026-11-22.*
