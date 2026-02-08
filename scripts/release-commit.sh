#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean. Commit or stash changes first."
  exit 1
fi

echo "[1/4] uv version --bump patch --frozen"
uv version --bump patch --frozen
VERSION="$(uv version --short)"

if git rev-parse --verify "v${VERSION}" >/dev/null 2>&1; then
  echo "Tag v${VERSION} already exists."
  exit 1
fi

echo "[2/4] git commit pyproject.toml"
git add pyproject.toml
git commit -m "chore: release v${VERSION}"

echo "[3/4] git tag v${VERSION}"
git tag "v${VERSION}"

echo "[4/4] done"
echo "Created commit: chore: release v${VERSION}"
echo "Created tag: v${VERSION}"
echo "Push is intentionally not executed."
