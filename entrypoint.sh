#!/usr/bin/env bash
set -euo pipefail

# Ensure output directory exists and is writable
mkdir -p /app/etl/output
chown -R "$(id -u):$(id -g)" /app/etl/output || true

# If any arguments are passed, run them (exec mode)
if [ "$#" -gt 0 ]; then
  exec "$@"
else
  # No args: start uvicorn binding to $PORT (Render sets this)
  : "${PORT:=8000}"   # default to 8000 when PORT not set
  exec uvicorn services.api.main:app --host 0.0.0.0 --port "${PORT}"
fi
