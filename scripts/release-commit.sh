#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean. Commit or stash changes first."
  exit 1
fi

RELEASE_VERSION="${RELEASE_VERSION:-}"
if [[ -n "${RELEASE_VERSION}" ]]; then
  echo "[1/5] uv version ${RELEASE_VERSION} --frozen"
  uv version "${RELEASE_VERSION}" --frozen
else
  echo "[1/5] uv version --bump patch --frozen"
  uv version --bump patch --frozen
fi

VERSION="$(uv version --short)"

if git rev-parse --verify "v${VERSION}" >/dev/null 2>&1; then
  echo "Tag v${VERSION} already exists."
  exit 1
fi

echo "[2/5] uv lock"
uv lock

echo "[3/5] git commit pyproject.toml uv.lock"
git add pyproject.toml uv.lock
git commit -m "chore: release v${VERSION}"

echo "[4/5] git tag v${VERSION}"
git tag "v${VERSION}"

echo "[5/5] done"
echo "Created commit: chore: release v${VERSION}"
echo "Created tag: v${VERSION}"
echo "Push is intentionally not executed."
echo "Tip: set RELEASE_VERSION to publish a specific version (example: RELEASE_VERSION=1.0.0)."
