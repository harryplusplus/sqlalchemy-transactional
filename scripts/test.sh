#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

MIN_SQLALCHEMY_VERSION="${MIN_SQLALCHEMY_VERSION:-2.0.0}"
MIN_SQLALCHEMY_SPEC="sqlalchemy[asyncio]==${MIN_SQLALCHEMY_VERSION}"

echo "[1/2] pytest with project dependencies"
uv run --group dev pytest "$@"

echo "[2/2] pytest with minimum supported SQLAlchemy: ${MIN_SQLALCHEMY_SPEC}"
uv run --isolated --group dev --with "${MIN_SQLALCHEMY_SPEC}" pytest "$@"
