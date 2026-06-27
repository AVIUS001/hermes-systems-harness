#!/usr/bin/env python3
"""Three-day/weekly local learning-loop updates for the Aerial Labs harness."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
HARNESS = VAULT / "harness"
GRAPH_PATH = HARNESS / "graph" / "graph.json"
UPDATES = HARNESS / "updates"
DAILY = UPDATES / "daily"
TRI_DAILY = UPDATES / "every_3_days"
WEEKLY = UPDATES / "weekly"
MEMORY = VAULT / "memory"
APPS_GENERATED = HARNESS / "config" / "macos_apps.generated.json"
APP_INTEGRATIONS = HARNESS / "config" / "app_integrations.json"
EXPORT_SCRIPT = HARNESS / "scripts" / "export_obsidian.py"

LEARNING_PROCESS_ID = "process-agentic-learning-loop"
OLLAMA_CANDIDATES = [
    "ollama",
    "/Applications/Ollama.app/Contents/Resources/ollama",
    "/usr/local/bin/ollama",
    "/opt/homebrew/bin/ollama",
]
GEMMA_MODEL_CANDIDATES = [
    "gemma4:latest",
    "gemma3:latest",
    "gemma2:latest",
    "gemma:latest",
]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_graph() -> dict:
    return load_json(GRAPH_PATH, {
        "version": "1.0.0",
        "meta": {
            "program": "Aerial Labs",
            "operator": "Aerial Industries Pte. Ltd. Singapore",
            "domain": "www.aerial-labs.ca",
            "last_ingest": None,
            "last_change": None,
        },
        "nodes": [],
        "edges": [],
    })


def upsert_node(graph: dict, node: dict) -> None:
    for i, existing in enumerate(graph["nodes"]):
        if existing["id"] == node["id"]:
            graph["nodes"][i] = {**existing, **node}
            return
    graph["nodes"].append(node)


def add_edge(graph: dict, fr: str, to: str, relation: str, rationale: str) -> None:
    key = (fr, to, relation)
    for edge in graph["edges"]:
        if (edge.get("from"), edge.get("to"), edge.get("relation")) == key:
            return
    graph["edges"].append({
        "from": fr,
        "to": to,
        "relation": relation,
        "rationale": rationale,
    })


def graph_stats(graph: dict) -> dict:
    by_type = Counter(n.get("type", "unknown") for n in graph.get("nodes", []))
    by_status = Counter(n.get("status", "unknown") for n in graph.get("nodes", []))
    attention = [
        n for n in graph.get("nodes", [])
        if n.get("status") in {"blocked", "review_required", "stale", "revision_needed"}
    ]
    return {
        "last_ingest": graph.get("meta", {}).get("last_ingest"),
        "nodes": len(graph.get("nodes", [])),
        "edges": len(graph.get("edges", [])),
        "by_type": dict(sorted(by_type.items())),
        "by_status": dict(sorted(by_status.items())),
        "attention": sorted(attention, key=lambda n: (n.get("status", ""), n.get("title", "")))[:25],
    }


def read_recent_memory(days: int) -> list[dict]:
    items: list[dict] = []
    today = date.today()
    for offset in range(days):
        day = today - timedelta(days=offset)
        path = MEMORY / f"{day.isoformat()}.md"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            items.append({
                "date": day.isoformat(),
                "path": str(path),
                "line_count": len(lines),
                "headlines": lines[:12],
            })
    return items


def recent_audits(days: int) -> list[dict]:
    cutoff = now_utc() - timedelta(days=days)
    audits = []
    for path in sorted((HARNESS / "audit").glob("*.json"), reverse=True):
        mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if mtime < cutoff:
            continue
        payload = load_json(path, {})
        audits.append({
            "path": str(path),
            "changed_node": payload.get("changed_node"),
            "impact_count": payload.get("impact_count"),
            "human_judgment_required": payload.get("human_judgment_required"),
        })
    return audits[:20]


def app_snapshot() -> dict:
    generated = load_json(APPS_GENERATED, {"apps": []})
    configured = load_json(APP_INTEGRATIONS, {"adapters": {}})
    apps = generated.get("apps", [])
    roles = Counter(app.get("role", "unknown") for app in apps)
    enabled = [
        {"name": app["name"], "role": app.get("role"), "integration": app.get("integration")}
        for app in apps
        if app.get("enabled_by_default")
    ][:30]
    return {
        "discovered_apps": len(apps),
        "roles": dict(sorted(roles.items())),
        "enabled_default_examples": enabled,
        "configured_adapters": sorted(configured.get("adapters", {}).keys()),
    }


def calendar_events(days: int) -> list[dict]:
    end_days = max(days, 1)
    script = f'''
set nowDate to current date
set endDate to nowDate + ({end_days} * days)
set output to ""
tell application "Calendar"
  repeat with cal in calendars
    try
      set eventList to (every event of cal whose start date is greater than or equal to nowDate and start date is less than or equal to endDate)
      repeat with ev in eventList
        set output to output & (name of ev as text) & " | " & (start date of ev as text) & " | " & (name of cal as text) & linefeed
      end repeat
    end try
  end repeat
end tell
return output
'''
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            check=False,
            text=True,
            capture_output=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return [{"error": "calendar_adapter_timeout_after_60s"}]
    except OSError as exc:
        return [{"error": f"calendar_adapter_failed: {exc}"}]
    if proc.returncode != 0:
        err = re.sub(r"\s+", " ", proc.stderr.strip())
        return [{"error": err or "calendar_permission_or_adapter_error"}]
    events = []
    for line in proc.stdout.splitlines():
        parts = [p.strip() for p in line.split("|", 2)]
        if len(parts) == 3:
            events.append({"title": parts[0], "start": parts[1], "calendar": parts[2]})
    return events[:50]


def find_ollama() -> str | None:
    found = shutil.which("ollama")
    if found:
        return found
    for candidate in OLLAMA_CANDIDATES:
        path = Path(candidate)
        if path.exists() and path.is_file():
            return str(path)
    return None


def ollama_models(binary: str) -> list[str]:
    proc = subprocess.run(
        [binary, "list"],
        check=False,
        text=True,
        capture_output=True,
        timeout=15,
    )
    if proc.returncode != 0:
        return []
    models = []
    for line in proc.stdout.splitlines()[1:]:
        parts = line.split()
        if parts:
            models.append(parts[0])
    return models


def choose_gemma_model(models: list[str]) -> str | None:
    lowered = {m.lower(): m for m in models}
    for candidate in GEMMA_MODEL_CANDIDATES:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    for model in models:
        if "gemma" in model.lower():
            return model
    return None


def llm_context(payload: dict) -> str:
    attention = [
        {
            "id": n.get("id"),
            "type": n.get("type"),
            "status": n.get("status"),
            "title": n.get("title"),
        }
        for n in payload["graph"]["attention"][:12]
    ]
    memory = [
        {
            "date": item["date"],
            "headlines": item["headlines"][:6],
        }
        for item in payload["memory"]
    ]
    compact = {
        "mode": payload["mode"],
        "generated_at": payload["generated_at"],
        "graph": {
            "last_ingest": payload["graph"]["last_ingest"],
            "nodes": payload["graph"]["nodes"],
            "edges": payload["graph"]["edges"],
            "attention": attention,
        },
        "memory": memory,
        "audits": payload["audits"][:8],
        "calendar": payload.get("calendar", [])[:12],
        "apps": {
            "discovered_apps": payload["apps"]["discovered_apps"],
            "configured_adapters": payload["apps"]["configured_adapters"],
        },
    }
    return json.dumps(compact, indent=2, ensure_ascii=False)


def clean_ollama_output(text: str) -> str:
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    text = text.replace("\x1b", "")
    text = re.sub(r"(?is)\bthinking\.\.\..*?\.\.\.done thinking\.\s*", "", text)
    marker = "### Aerial Labs Engineering Update Summary"
    if marker in text:
        text = text[text.index(marker):]
    text = text.encode("ascii", "ignore").decode("ascii")
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def gemma_summary(payload: dict) -> dict:
    binary = find_ollama()
    if not binary:
        return {"status": "unavailable", "reason": "ollama_binary_not_found", "text": ""}
    try:
        models = ollama_models(binary)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unavailable", "reason": f"ollama_list_failed: {exc}", "text": ""}
    model = choose_gemma_model(models)
    if not model:
        return {"status": "unavailable", "reason": "no_gemma_model_found", "binary": binary, "models": models, "text": ""}

    prompt = "\n".join([
        "You are the local offline Gemma model producing an Aerial Labs learning-loop update.",
        "Use only the JSON context below. Do not invent facts.",
        "Return final output only. Do not include hidden reasoning, analysis, scratchpad, or a thinking section.",
        "Use ASCII only. Do not use emoji. Keep lines readable and do not split words across lines.",
        "Use plain Markdown bullets, not JSON.",
        "Treat the graph attention list as the execution queue. Count blocked and review_required items exactly.",
        "Write a concise engineering update with these sections:",
        "1. What changed or matters",
        "2. Execution queue",
        "3. Risks or stale links",
        "4. Calendar constraints",
        "5. Memory to preserve",
        "",
        llm_context(payload),
    ])
    try:
        proc = subprocess.run(
            [binary, "run", "--hidethinking", "--nowordwrap", "--think=false", model, prompt],
            check=False,
            text=True,
            capture_output=True,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "failed", "reason": f"ollama_run_failed: {exc}", "binary": binary, "model": model, "text": ""}
    if proc.returncode != 0:
        return {
            "status": "failed",
            "reason": clean_ollama_output(proc.stderr) or "ollama_run_nonzero",
            "binary": binary,
            "model": model,
            "text": "",
        }
    return {"status": "used", "binary": binary, "model": model, "text": clean_ollama_output(proc.stdout)}


def markdown_list(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def render_update(mode: str, payload: dict) -> str:
    stats = payload["graph"]
    attention = [
        f"`{n.get('id')}` — {n.get('status')}: {n.get('title')}"
        for n in stats["attention"]
    ]
    memory_lines = []
    for item in payload["memory"]:
        memory_lines.append(f"{item['date']} ({item['line_count']} lines): {Path(item['path']).name}")
        for headline in item["headlines"][:5]:
            memory_lines.append(f"  - {headline}")

    audit_lines = [
        f"{Path(a['path']).name}: {a.get('changed_node')} ({a.get('impact_count')} impacts, human={a.get('human_judgment_required')})"
        for a in payload["audits"]
    ]
    calendar_lines = []
    for event in payload.get("calendar", []):
        if "error" in event:
            calendar_lines.append(event["error"])
        else:
            calendar_lines.append(f"{event['start']} — {event['title']} ({event['calendar']})")

    apps = payload["apps"]
    role_lines = [f"{role}: {count}" for role, count in apps["roles"].items()]
    llm = payload.get("llm", {"status": "disabled", "text": ""})
    mode_title = {
        "daily": "Daily",
        "tri_day": "Every Three Days",
        "weekly": "Weekly",
    }.get(mode, mode.title())
    llm_lines = [
        f"Status: {llm.get('status', 'unknown')}",
    ]
    if llm.get("model"):
        llm_lines.append(f"Model: {llm['model']}")
    if llm.get("reason"):
        llm_lines.append(f"Reason: {llm['reason']}")
    if llm.get("text"):
        llm_lines.extend(["", llm["text"]])

    return "\n".join([
        f"# Aerial Labs {mode_title} Learning Update — {payload['local_date']}",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Graph last ingest: {stats['last_ingest']}",
        f"- Graph size: {stats['nodes']} nodes / {stats['edges']} edges",
        "",
        "## Attention Queue",
        "",
        markdown_list(attention),
        "",
        "## Recent Memory",
        "",
        markdown_list(memory_lines),
        "",
        "## Impact Audits",
        "",
        markdown_list(audit_lines),
        "",
        "## Calendar Window",
        "",
        markdown_list(calendar_lines),
        "",
        "## Local App Surface",
        "",
        f"- Discovered apps: {apps['discovered_apps']}",
        f"- Configured adapters: {', '.join(apps['configured_adapters'])}",
        "",
        markdown_list(role_lines),
        "",
        "## Offline Gemma Synthesis",
        "",
        "\n".join(llm_lines),
        "",
        "## Learning Loop Actions",
        "",
        "- Keep graph as system of record before acting on loose files.",
        "- Treat `blocked`, `review_required`, `stale`, and `revision_needed` nodes as the next execution queue.",
        "- Register new CAD, analysis, test, and compliance outputs as graph artifacts linked to the requirement that created them.",
        "- Do not send messages, emails, or public updates from this loop without explicit human approval.",
        "",
    ])


def write_update(mode: str, include_calendar: bool, calendar_days: int, export: bool, use_llm: bool) -> Path:
    graph = load_graph()
    lookback_days = {"daily": 1, "tri_day": 3, "weekly": 7}[mode]
    payload = {
        "mode": mode,
        "generated_at": now_utc().isoformat(),
        "local_date": date.today().isoformat(),
        "graph": graph_stats(graph),
        "memory": read_recent_memory(lookback_days),
        "audits": recent_audits(lookback_days),
        "apps": app_snapshot(),
        "calendar": calendar_events(calendar_days) if include_calendar else [],
    }
    payload["llm"] = gemma_summary(payload) if use_llm else {"status": "disabled", "text": ""}

    if mode == "daily":
        out = DAILY / f"{payload['local_date']}.md"
        node_id = f"artifact-learning-update-daily-{payload['local_date']}"
        title = f"Daily learning update {payload['local_date']}"
    elif mode == "tri_day":
        out = TRI_DAILY / f"{payload['local_date']}.md"
        node_id = f"artifact-learning-update-3day-{payload['local_date']}"
        title = f"Every-three-days learning update {payload['local_date']}"
    else:
        iso = date.today().isocalendar()
        out = WEEKLY / f"{iso.year}-W{iso.week:02d}.md"
        node_id = f"artifact-learning-update-weekly-{iso.year}-W{iso.week:02d}"
        title = f"Weekly learning update {iso.year}-W{iso.week:02d}"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_update(mode, payload), encoding="utf-8")

    upsert_node(graph, {
        "id": LEARNING_PROCESS_ID,
        "type": "process",
        "title": "Agentic learning loop cadence",
        "status": "active",
        "owner": "harness",
        "source_path": str(APP_INTEGRATIONS),
        "source_kind": "local_update_architecture",
        "metadata": {
            "every_3_days": "graph, memory, audits, calendar, local app surface, offline Gemma synthesis",
            "weekly": "seven-day graph/memory/audit synthesis",
        },
    })
    upsert_node(graph, {
        "id": node_id,
        "type": "artifact",
        "title": title,
        "status": "active",
        "owner": "harness",
        "source_path": str(out),
        "source_kind": "learning_update",
        "metadata": {
            "mode": mode,
            "generated_at": payload["generated_at"],
            "calendar_included": include_calendar,
            "offline_llm_status": payload["llm"].get("status"),
            "offline_llm_model": payload["llm"].get("model"),
        },
    })
    add_edge(graph, node_id, LEARNING_PROCESS_ID, "derives_from", "Learning summaries are produced by the hard-coded three-day/weekly update cadence.")
    add_edge(graph, node_id, "platform-aviabox", "hosted_on", "Aviabox.ai is the target orchestrator for graph-derived learning-loop summaries.")
    graph["meta"]["last_change"] = payload["generated_at"]
    save_json(GRAPH_PATH, graph)

    if export and EXPORT_SCRIPT.exists():
        subprocess.run([sys.executable, str(EXPORT_SCRIPT)], check=False)

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Write Aerial Labs learning-loop update")
    parser.add_argument("--mode", choices=["daily", "tri_day", "weekly"], required=True)
    parser.add_argument("--calendar", action="store_true", help="Include local Calendar events. macOS may request permission.")
    parser.add_argument("--calendar-days", type=int, default=7)
    parser.add_argument("--llm", dest="llm", action="store_true", default=True, help="Use offline Gemma through Ollama when available.")
    parser.add_argument("--no-llm", dest="llm", action="store_false", help="Skip offline Gemma and use deterministic extraction only.")
    parser.add_argument("--no-export", action="store_true", help="Do not export graph markdown after updating graph.json")
    args = parser.parse_args()

    path = write_update(args.mode, args.calendar, args.calendar_days, export=not args.no_export, use_llm=args.llm)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
