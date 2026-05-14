#!/bin/sh
set -e
echo "=== Sync: Google Sheets → SQLite ==="
uv run python -m listener.sync
echo "=== Starting listener ==="
exec uv run python -m listener.main
