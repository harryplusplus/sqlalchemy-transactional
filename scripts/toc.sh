#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "[1/1] markdown-toc-cli README.md"
uv run --group dev markdown-toc-cli README.md
