#!/bin/sh
set -e
echo "=== Starting listener ==="
exec uv run python -m listener.main
