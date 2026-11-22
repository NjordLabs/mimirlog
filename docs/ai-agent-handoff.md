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
sh scripts/check-ci-docker.sh
```

`check-ci-docker.sh` runs the same gates in `ghcr.io/pirlruc/ci-python`
(digest-pinned). That image has no `uv`, so the script installs this
package inside the container and leaves the checkout read-only. The
image is private.

## Known pitfalls

GitHub-hosted quality jobs pull a private image. The job stays red
until `GHCR_READ_TOKEN` on this repository can read it.

`radon` and `pip-audit` are not project dependencies, so
`scripts/check-ci-local.sh` does not invoke them.

## Suggested next work

PyPI publish (LOG-001-T2) stays open. The quality caller will test
3.13 and 3.14. The pymjolnir pin moves to the release wheel when
0.1.1 exists.

## Recent history

- fix(ci): run quality gates inside ci-python without uv
- chore(ci): skip secret jobs for dependabot pull requests
- feat(log): redact nested secrets and await decorated calls
- fix(quality): split span tests and hide untyped span lookups from mypy
- docs(readme): install the v0.1.0 release wheel

*Last updated: 2026-11-22.*
