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

GitHub-hosted quality jobs pull a private `ci-lint` image. The job
stays red until `GHCR_READ_TOKEN` on this repository can read
`ghcr.io/pirlruc/ci-lint`.

## Suggested next work

Publish 0.1.0 after the quality job is green, then point nodeio at
the release instead of the git pin.

## Recent history

- feat(log): add JSON logging, redaction, and call decorators

*Last updated: 2026-11-22.*
