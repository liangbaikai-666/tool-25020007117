#!/usr/bin/env bash
set -euo pipefail

curl -fsS http://127.0.0.1:8000/packages.json \
  | jq -s '[.[] | select(.status == "active" and .downloads >= 100)] | sort_by(-.downloads, .name)' \
  | jq -r '
      "# Active Packages (downloads ≥ 100)",
      "",
      "| Name | Version | Downloads |",
      "|------|---------|-----------|",
      (.[] | "| \(.name) | \(.version) | \(.downloads) |")
    ' > summary.md

cat summary.md
