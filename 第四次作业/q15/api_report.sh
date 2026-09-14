#!/usr/bin/env bash
set -euo pipefail

curl -fsS http://127.0.0.1:8000/packages.json \
  | jq -r '.[] | select(.status == "active" and .downloads >= 100)' \
  | jq -s 'sort_by(-.downloads, .name)' \
  | jq -r '
      "# Active Packages Report",
      "",
      "| name | version | downloads |",
      "|------|---------|-----------|",
      (.[] | "| \(.name) | \(.version) | \(.downloads) |")
    ' > summary.md

cat summary.md
