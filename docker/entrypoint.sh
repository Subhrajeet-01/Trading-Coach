#!/bin/bash
set -e

# Run the seeding and schema initialization script using the venv python
echo "🔧 Running DB initialization and seeding..."
/app/.venv/bin/python scripts/seed_db.py

# Launch the application using the venv uvicorn
# Render provides the PORT environment variable.
echo "🚀 Starting application on port ${PORT:-8000}..."
exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
