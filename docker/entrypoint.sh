#!/bin/bash
set -e

echo "Starting application with Uvicorn..."
exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
