#!/usr/bin/env python3
"""One-command harness sync: ingest sources → graph.json → Obsidian export → optional symlink refresh."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lib.sources import obsidian_symlink, watch_paths  # noqa: E402

VAULT = Path(__file__).resolve().parents[2]
STATE_PATH = VAULT / "harness" / "state" / "sync-state.json"
PYTHON = VAULT / "harness" / ".venv" / "bin" / "python"


def _fingerprint(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return "missing"
    if p.is_file():
        st = p.stat()
        return f"f:{st.st_mtime_ns}:{st.st_size}"
    count = 0
    newest = 0
    for f in p.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            count += 1
            newest = max(newest, f.stat().st_mtime_ns)
    return f"d:{count}:{newest}"


def sources_changed() -> bool:
    paths = watch_paths()
    if not paths:
        return True
    state = {}
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    prev = state.get("fingerprints", {})
    current = {p: _fingerprint(p) for p in paths}
    return current != prev


def save_state(result: dict) -> None:
    paths = watch_paths()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "fingerprints": {p: _fingerprint(p) for p in paths},
        "result": result,
    }, indent=2) + "\n", encoding="utf-8")


def run(force: bool = False) -> dict:
    if not force and not sources_changed():
        return {"skipped": True, "reason": "sources unchanged"}

    py = str(PYTHON if PYTHON.exists() else Path(sys.executable))
    ingest = subprocess.run([py, str(SCRIPTS / "ingest.py")], capture_output=True, text=True)
    if ingest.returncode != 0:
        print(ingest.stderr or ingest.stdout, file=sys.stderr)
        sys.exit(ingest.returncode)
    ingest_result = json.loads(ingest.stdout)

    hermes = subprocess.run([py, str(SCRIPTS / "bootstrap_hermes.py")], capture_output=True, text=True)
    if hermes.returncode != 0:
        print(hermes.stderr or hermes.stdout, file=sys.stderr)
        sys.exit(hermes.returncode)
    hermes_result = json.loads(hermes.stdout)

    export = subprocess.run([py, str(SCRIPTS / "export_obsidian.py")], capture_output=True, text=True)
    if export.returncode != 0:
        print(export.stderr or export.stdout, file=sys.stderr)
        sys.exit(export.returncode)
    export_result = json.loads(export.stdout)

    symlink = obsidian_symlink()
    if symlink and symlink.parent.exists():
        symlink.unlink(missing_ok=True)
        symlink.symlink_to(VAULT / "graph")

    result = {
        "ingest": ingest_result,
        "hermes": hermes_result,
        "export": export_result,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
    save_state(result)
    return result


def main() -> int:
    force = "--force" in sys.argv
    result = run(force=force)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
