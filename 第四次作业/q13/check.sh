#!/usr/bin/env bash
set -euo pipefail

echo "=== ruff format --check ==="
ruff format --check .

echo "=== ruff check ==="
ruff check .

echo "=== pytest ==="
pytest

echo "=== All checks passed ==="
