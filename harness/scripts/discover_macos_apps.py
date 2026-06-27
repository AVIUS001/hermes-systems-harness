#!/usr/bin/env python3
"""Discover installed macOS apps and classify local integration roles."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
OUT = VAULT / "harness" / "config" / "macos_apps.generated.json"

APP_ROOTS = [
    Path("/Applications"),
    Path("/System/Applications"),
    Path.home() / "Applications",
]

CLASSIFIERS = {
    "Calendar": ("schedule_context", "read_only_osask"),
    "Reminders": ("task_context", "read_only_osask_disabled"),
    "Mail": ("inbox_context", "read_only_osask_disabled"),
    "Notes": ("knowledge_capture", "read_only_osask_disabled"),
    "Shortcuts": ("local_automation", "local_execute"),
    "Obsidian": ("systems_graph_ui", "local_files"),
    "Codex": ("agent_execution", "workspace"),
    "Claude": ("agent_review", "manual"),
    "Ollama": ("local_llm", "local_service"),
    "ChatGPT Atlas": ("agent_browser", "manual"),
    "Google Chrome": ("browser", "manual"),
    "Microsoft Edge": ("browser", "manual"),
    "Opera GX": ("browser", "manual"),
    "Slack": ("messaging", "no_outbound_default"),
    "Discord": ("messaging", "no_outbound_default"),
    "Microsoft Teams": ("messaging", "no_outbound_default"),
    "WhatsApp": ("messaging", "no_outbound_default"),
    "Messages": ("messaging", "no_outbound_default"),
    "MATLAB_R2024a": ("analysis", "manual_artifact_links"),
    "Mathematica": ("analysis", "manual_artifact_links"),
    "SystemModeler": ("modeling", "manual_artifact_links"),
    "Autodesk Fusion": ("cad", "manual_artifact_links"),
    "Inventor Fusion": ("cad", "manual_artifact_links"),
    "Blender": ("cad_visualization", "manual_artifact_links"),
    "Numbers": ("spreadsheet", "manual_artifact_links"),
    "Pages": ("documents", "manual_artifact_links"),
    "Keynote": ("presentations", "manual_artifact_links"),
    "Docker": ("platform_runtime", "manual"),
}


def app_name(path: Path) -> str:
    return path.name.removesuffix(".app")


def classify(name: str) -> dict:
    role, integration = CLASSIFIERS.get(name, ("available_app", "manual"))
    return {
        "role": role,
        "integration": integration,
        "enabled_by_default": integration not in {
            "read_only_osask_disabled",
            "no_outbound_default",
        },
    }


def discover() -> list[dict]:
    apps: list[dict] = []
    seen: set[str] = set()
    for root in APP_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.app")):
            name = app_name(path)
            key = f"{name}:{path}"
            if key in seen:
                continue
            seen.add(key)
            item = {
                "name": name,
                "path": str(path),
                "root": str(root),
            }
            item.update(classify(name))
            apps.append(item)
    return apps


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover macOS apps for harness integration")
    parser.add_argument("--write", action="store_true", help=f"Write {OUT}")
    args = parser.parse_args()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "Local app discovery only. Messaging/outbound apps are disabled by default.",
        "apps": discover(),
    }
    text = json.dumps(payload, indent=2) + "\n"
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
        print(OUT)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
