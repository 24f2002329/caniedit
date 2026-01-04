#!/bin/bash
set -e

echo "Starting CanIEdit API"

cd /home/site/wwwroot

# Ensure pip exists
python -m pip install --upgrade pip

# Install dependencies
python -m pip install -r requirements.txt

# Start app (IMPORTANT: python -m uvicorn)
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
