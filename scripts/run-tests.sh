#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
export POSTGRES_PORT="${POSTGRES_PORT:-55432}"
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
export POSTGRES_DB="${POSTGRES_DB:-django_postgresql_estimated_count_test}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to run tests. Install Docker and retry." >&2
  exit 1
fi

docker compose up -d --wait postgres

uv run pytest "$@"
