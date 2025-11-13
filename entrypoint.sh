#!/usr/bin/env bash
set -euo pipefail

# Optional debug mode
if [ "${DEBUG:-false}" = "true" ]; then
  set -x
fi

# Ensure output directory exists and is writable
echo "Ensuring /app/etl/output exists and is writable..."
mkdir -p /app/etl/output
chown -R "$(id -u):$(id -g)" /app/etl/output || true

# Validate PORT environment variable
: "${PORT:=8000}"  # Default to 8000 if PORT is not set
if ! [[ "${PORT}" =~ ^[0-9]+$ ]]; then
  echo "Error: PORT must be a valid number." >&2
  exit 1
fi

# If any arguments are passed, run them (exec mode)
if [ "$#" -gt 0 ]; then
  echo "Executing custom command: $*"
  exec "$@"
else
  # No args: start uvicorn binding to $PORT
  echo "Starting uvicorn on port ${PORT}..."
  exec uvicorn services.api.main:app --host 0.0.0.0 --port "${PORT}"
fi
