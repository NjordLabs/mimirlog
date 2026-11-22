#!/bin/sh
# Run scripts/check-ci-local.sh inside the published ci-python image.
# The image is private. Log in first: docker login ghcr.io
# Tag in the digest comment: ghcr.io/pirlruc/ci-python:3.3.0 (linux/amd64).
set -eu

ROOT="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"
IMAGE="${MIMIRLOG_CI_IMAGE:-ghcr.io/pirlruc/ci-python@sha256:894d5ae1d9bd55d68262f4ed65cd6f57d7186038d7e8e8668dba443ee0ebfbbd}"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker is required" >&2
    exit 1
fi
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
    echo "==> Pulling ${IMAGE}"
    docker pull "${IMAGE}"
fi

echo "==> Quality gates in ${IMAGE}"
docker run --rm \
    -v "${ROOT}:/work" \
    -w /work \
    -e HOME=/tmp \
    --user "$(id -u):$(id -g)" \
    "${IMAGE}" \
    sh scripts/check-ci-local.sh
