#!/usr/bin/env bash
# Initialize local-only files from public examples. Safe to run repeatedly.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

copy_if_missing() {
  local src="$1" dest="$2"
  if [[ ! -f "$dest" ]]; then
    cp "$src" "$dest"
    echo "Created $dest from example"
  fi
}

mkdir -p harness/local harness/graph harness/outbox harness/state harness/updates/overnight memory

copy_if_missing harness/config/sources.yaml.example harness/config/sources.yaml
copy_if_missing harness/platforms/registry.yaml.example harness/platforms/registry.yaml
copy_if_missing harness/config/email.env.example harness/config/email.env
copy_if_missing USER.example.md USER.md
copy_if_missing TOOLS.example.md TOOLS.md

if [[ ! -f harness/graph/graph.json ]]; then
  cp harness/graph/graph.sample.json harness/graph/graph.json
  echo "Created harness/graph/graph.json from sample"
fi

if [[ ! -f memory/.gitkeep ]]; then
  touch memory/.gitkeep
fi

echo ""
echo "Local init complete. Next steps:"
echo "  1. Edit harness/config/sources.yaml with your private ingest paths"
echo "  2. Edit harness/platforms/registry.yaml with your platform repo paths"
echo "  3. Edit USER.md and TOOLS.md (copied from *.example if missing)"
echo "  4. Optional: add harness/local/bootstrap_extension.py for program-specific Hermes seeds"
echo "  5. Run: python3 harness/scripts/bootstrap_hermes.py"
echo "  6. Run: ./harness/scripts/verify_public_safe.sh"
