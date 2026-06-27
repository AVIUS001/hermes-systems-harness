#!/usr/bin/env bash
# Scan tracked/staged files for common leak patterns before pushing to GitHub.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

FAIL=0

echo "=== Checking gitignore coverage ==="
FORBIDDEN_PATHS=(
  "MEMORY.md"
  "USER.md"
  "TOOLS.md"
  "memory/"
  "harness/graph/graph.json"
  "graph/"
  "harness/config/email.env"
  "harness/config/sources.yaml"
  "harness/outbox/"
)

for path in "${FORBIDDEN_PATHS[@]}"; do
  if git check-ignore -q "$path" 2>/dev/null; then
    echo "  OK gitignored: $path"
  else
    echo "  FAIL not gitignored: $path"
    FAIL=1
  fi
done

if ! git check-ignore -q harness/graph/graph.sample.json 2>/dev/null; then
  echo "  OK tracked candidate: harness/graph/graph.sample.json"
else
  echo "  FAIL sample graph is gitignored (should be public)"
  FAIL=1
fi

echo ""
echo "=== Scanning files that would be committed ==="

if git rev-parse --verify HEAD >/dev/null 2>&1; then
  FILES=$(git ls-files)
else
  FILES=$(git ls-files --others --exclude-standard)
fi

if [[ -z "$FILES" ]]; then
  echo "  (no files to scan)"
fi

should_skip() {
  local file="$1"
  [[ "$file" == "harness/scripts/verify_public_safe.sh" ]] && return 0
  [[ "$file" == *.example ]] && return 0
  [[ "$file" == harness/config/email.env.example ]] && return 0
  return 1
}

while IFS= read -r file; do
  [[ -z "$file" || ! -f "$file" ]] && continue
  should_skip "$file" && continue

  if grep -qE '/Users/[a-zA-Z0-9_-]+' "$file" 2>/dev/null; then
    echo "  LEAK in $file: home directory path (/Users/...)"
    grep -nE '/Users/[a-zA-Z0-9_-]+' "$file" | head -2
    FAIL=1
  fi
  if grep -qE 'arinze@|eddy7@test\.com|Eddy7&' "$file" 2>/dev/null; then
    echo "  LEAK in $file: personal email or test credential"
    grep -nE 'arinze@|eddy7@test\.com|Eddy7&' "$file" | head -2
    FAIL=1
  fi
  if grep -qE 'HERMES_SMTP_PASSWORD=[^r]' "$file" 2>/dev/null; then
    if ! grep -q 'replace-with' "$file" 2>/dev/null; then
      echo "  LEAK in $file: SMTP password value"
      FAIL=1
    fi
  fi
done <<< "$FILES"

echo ""
if [[ "$FAIL" -eq 0 ]]; then
  echo "PASS: No obvious leaks detected."
  exit 0
else
  echo "FAIL: Fix leaks before pushing to GitHub."
  exit 1
fi
