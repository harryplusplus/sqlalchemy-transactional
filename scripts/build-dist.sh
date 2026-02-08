#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[1/2] uv build --clear"
uv build --clear

echo "[2/2] twine check dist/*"
uv run --group dev twine check dist/*
