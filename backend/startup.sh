#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PORT=${PORT:-8000}

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --app-dir "$SCRIPT_DIR" \
  --env-file "$SCRIPT_DIR/.env"
