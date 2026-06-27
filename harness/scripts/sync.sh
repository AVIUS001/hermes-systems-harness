#!/usr/bin/env bash
# Aerial Labs harness — sync sources → graph → Obsidian
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="${ROOT}/harness/.venv/bin/python"
[[ -x "$PY" ]] || PY=python3
exec "$PY" "${ROOT}/harness/scripts/sync.py" "$@"
