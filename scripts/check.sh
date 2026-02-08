#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

TARGETS=("$@")
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=(.)
fi

echo "[1/4] ruff check --fix ${TARGETS[*]}"
uv run --group dev ruff check --fix "${TARGETS[@]}"

echo "[2/4] ruff format ${TARGETS[*]}"
uv run --group dev ruff format "${TARGETS[@]}"

echo "[3/4] deptry"
uv run --group dev deptry . --known-first-party sqlalchemy_transactional

echo "[4/4] pyright"
uv run --group dev pyright
