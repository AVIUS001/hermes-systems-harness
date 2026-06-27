#!/usr/bin/env python3
"""Read-only overnight health check for Hermes/Aerial Labs graph operations."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
GRAPH_PATH = VAULT / "harness" / "graph" / "graph.json"
OUT_DIR = VAULT / "harness" / "updates" / "overnight"


TRACE_RELATIONS = {"derives_from", "satisfies", "implements", "compliance_maps_to", "verifies"}
REVIEW_STATUSES = {"review_required", "stale", "revision_needed", "blocked"}


def load_graph() -> dict:
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def path_exists(path_value: str) -> bool | None:
    if not path_value or path_value.startswith("http://") or path_value.startswith("https://"):
        return None
    return Path(path_value).exists()


def analyze(graph: dict) -> dict:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = [n["id"] for n in nodes]
    node_set = set(node_ids)
    duplicate_ids = sorted([nid for nid, count in Counter(node_ids).items() if count > 1])

    broken_edges = [
        e for e in edges
        if e.get("from") not in node_set or e.get("to") not in node_set
    ]

    outgoing: dict[str, list[dict]] = {}
    incoming: dict[str, list[dict]] = {}
    for e in edges:
        outgoing.setdefault(e.get("from", ""), []).append(e)
        incoming.setdefault(e.get("to", ""), []).append(e)

    traceability_gaps = []
    for n in nodes:
        if n.get("type") != "artifact":
            continue
        outs = outgoing.get(n["id"], [])
        if not any(e.get("relation") in TRACE_RELATIONS for e in outs):
            traceability_gaps.append({"id": n["id"], "title": n.get("title", n["id"])})

    review_queue = [
        {
            "id": n["id"],
            "type": n.get("type"),
            "title": n.get("title", n["id"]),
            "status": n.get("status"),
            "owner": n.get("owner", "systems_engineer"),
        }
        for n in nodes
        if n.get("status") in REVIEW_STATUSES
    ]

    missing_sources = []
    for n in nodes:
        source_path = n.get("source_path")
        exists = path_exists(source_path) if isinstance(source_path, str) else None
        if exists is False:
            missing_sources.append({"id": n["id"], "title": n.get("title", n["id"]), "source_path": source_path})

    by_type = Counter(n.get("type", "unknown") for n in nodes)
    by_status = Counter(n.get("status", "unknown") for n in nodes)
    agent_nodes = [n for n in nodes if n.get("type") == "agent"]
    service_nodes = [n for n in nodes if n.get("type") == "service"]

    risk_score = (
        len(broken_edges) * 5
        + len(duplicate_ids) * 5
        + len(traceability_gaps) * 2
        + len([n for n in review_queue if n["status"] == "blocked"]) * 3
        + len(missing_sources)
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "last_ingest": graph.get("meta", {}).get("last_ingest"),
        "last_change": graph.get("meta", {}).get("last_change"),
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "by_type": dict(sorted(by_type.items())),
            "by_status": dict(sorted(by_status.items())),
            "agents": len(agent_nodes),
            "services": len(service_nodes),
        },
        "risk_score": risk_score,
        "duplicate_ids": duplicate_ids,
        "broken_edges": broken_edges[:100],
        "traceability_gaps": traceability_gaps[:100],
        "missing_sources": missing_sources[:100],
        "review_queue": review_queue[:100],
        "recommended_morning_actions": recommended_actions(broken_edges, duplicate_ids, traceability_gaps, missing_sources, review_queue),
    }


def recommended_actions(
    broken_edges: list[dict],
    duplicate_ids: list[str],
    traceability_gaps: list[dict],
    missing_sources: list[dict],
    review_queue: list[dict],
) -> list[str]:
    actions: list[str] = []
    if broken_edges:
        actions.append("Repair broken graph edges before trusting impact analysis.")
    if duplicate_ids:
        actions.append("Deduplicate graph node IDs.")
    if traceability_gaps:
        actions.append("Add requirement/test/compliance links for artifact traceability gaps.")
    if missing_sources:
        actions.append("Verify missing local source paths or update platform/source registries.")
    blocked = [n for n in review_queue if n["status"] == "blocked"]
    if blocked:
        actions.append("Resolve blocked nodes with human judgment.")
    stale = [n for n in review_queue if n["status"] in {"stale", "revision_needed", "review_required"}]
    if stale:
        actions.append("Run targeted impact analysis or assign agent work packets for stale/review nodes.")
    if not actions:
        actions.append("No critical overnight action required.")
    return actions


def write_markdown(report: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    path = OUT_DIR / f"{date}.md"
    lines = [
        f"# Overnight Health - {date}",
        "",
        f"- Timestamp: `{report['timestamp']}`",
        f"- Last ingest: `{report.get('last_ingest')}`",
        f"- Last change: `{report.get('last_change')}`",
        f"- Risk score: `{report['risk_score']}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in report["counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Recommended Morning Actions", ""])
    for item in report["recommended_morning_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Review Queue", ""])
    for item in report["review_queue"][:30]:
        lines.append(f"- `{item['status']}` `{item['type']}` [[{item['id']}|{item['title']}]]")
    lines.extend(["", "## Traceability Gaps", ""])
    for item in report["traceability_gaps"][:30]:
        lines.append(f"- [[{item['id']}|{item['title']}]]")
    lines.extend(["", "## Missing Sources", ""])
    for item in report["missing_sources"][:30]:
        lines.append(f"- `{item['id']}`: `{item['source_path']}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only Hermes overnight health check")
    parser.add_argument("--write", action="store_true", help="Write markdown report to harness/updates/overnight")
    args = parser.parse_args()

    report = analyze(load_graph())
    if args.write:
        report["markdown_report"] = str(write_markdown(report))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
