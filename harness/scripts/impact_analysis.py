#!/usr/bin/env python3
"""
Change propagation engine for Aerial Labs systems graph.

Given a changed node, traverse dependencies and emit an action queue for agents
or the human systems engineer.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
GRAPH_PATH = VAULT / "harness" / "graph" / "graph.json"
AUDIT_DIR = VAULT / "harness" / "audit"

# Relations that propagate downstream impact
DOWNSTREAM = {
    "affects", "derives_from", "satisfies", "verifies",
    "implements", "compliance_maps_to", "blocks", "elevates_trl",
}

# What to do per node type when impacted
ACTIONS = {
    "requirement": ["re_review_requirement", "notify_owner"],
    "regulation": ["re_run_compliance_check", "flag_dependent_tests"],
    "test_procedure": ["reopen_test", "invalidate_evidence"],
    "artifact": ["mark_revision_needed", "rerun_linked_analysis"],
    "process": ["mark_icd_stale", "notify_quality"],
    "compliance_evidence": ["revalidate_against_regulation"],
    "budget": ["recompute_budget"],
    "interface": ["mark_icd_for_revision"],
    "platform": ["sync_registry", "notify_platform_owner"],
    "decision": ["surface_for_human_judgment"],
    "agent": ["refresh_agent_context", "verify_agent_permissions"],
    "service": ["check_service_health", "verify_service_boundary"],
}


def load_graph() -> dict:
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def build_indexes(graph: dict) -> tuple[dict, dict]:
    nodes = {n["id"]: n for n in graph["nodes"]}
    forward: dict[str, list[tuple[str, str]]] = {}
    reverse: dict[str, list[tuple[str, str]]] = {}
    for e in graph["edges"]:
        forward.setdefault(e["from"], []).append((e["to"], e["relation"]))
        reverse.setdefault(e["to"], []).append((e["from"], e["relation"]))
    return nodes, {"forward": forward, "reverse": reverse}


def traverse_impact(node_id: str, indexes: dict, direction: str = "both") -> list[dict]:
    """BFS from changed node along impact edges."""
    nodes = indexes if "forward" in indexes else indexes
    # Fix: use proper structure
    fwd = indexes["forward"]
    rev = indexes["reverse"]

    visited = set()
    queue = deque([(node_id, 0, "origin")])
    impacts = []

    while queue:
        current, depth, via = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        if current != node_id:
            impacts.append({"id": current, "depth": depth, "via": via})

        if direction in ("downstream", "both"):
            for target, rel in fwd.get(current, []):
                if rel in DOWNSTREAM and target not in visited:
                    queue.append((target, depth + 1, f"{current}--{rel}-->"))

        if direction in ("upstream", "both"):
            for source, rel in rev.get(current, []):
                if rel in DOWNSTREAM and source not in visited:
                    queue.append((source, depth + 1, f"{source}--{rel}-->{current}"))

    return impacts


def build_action_queue(graph: dict, changed_id: str, change_summary: str) -> dict:
    nodes_by_id, idx = build_indexes(graph)
    if changed_id not in nodes_by_id:
        return {"error": f"Node not found: {changed_id}"}

    changed = nodes_by_id[changed_id]
    impacts = traverse_impact(changed_id, idx, direction="both")

    actions = []
    actions.append({
        "priority": 1,
        "action": "record_change",
        "target": changed_id,
        "detail": change_summary,
        "owner": "harness",
    })

    seen = set()
    for imp in impacts:
        nid = imp["id"]
        if nid in seen:
            continue
        seen.add(nid)
        node = nodes_by_id.get(nid, {})
        ntype = node.get("type", "unknown")
        for action in ACTIONS.get(ntype, ["review_impact"]):
            actions.append({
                "priority": 2 + imp["depth"],
                "action": action,
                "target": nid,
                "target_type": ntype,
                "target_title": node.get("title", nid),
                "depth": imp["depth"],
                "via": imp["via"],
                "owner": node.get("owner", "systems_engineer"),
            })

    # Human judgment triggers
    human_required = [
        a for a in actions
        if a["action"] in ("surface_for_human_judgment", "re_review_requirement")
        or nodes_by_id.get(a["target"], {}).get("status") == "blocked"
    ]

    return {
        "changed_node": changed_id,
        "changed_title": changed.get("title"),
        "change_summary": change_summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "impact_count": len(impacts),
        "actions": sorted(actions, key=lambda x: x["priority"]),
        "human_judgment_required": len(human_required) > 0,
        "human_queue": human_required[:20],
    }


def write_audit(report: dict) -> Path:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = AUDIT_DIR / f"impact-{report['changed_node']}-{ts}.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Aerial Labs change impact analysis")
    parser.add_argument("--node", required=True, help="Changed node ID")
    parser.add_argument("--summary", default="Requirement or artifact changed", help="Change description")
    parser.add_argument("--audit", action="store_true", help="Write audit log")
    args = parser.parse_args()

    graph = load_graph()
    report = build_action_queue(graph, args.node, args.summary)
    if args.audit:
        write_audit(report)
    print(json.dumps(report, indent=2))
    return 0 if "error" not in report else 1


if __name__ == "__main__":
    sys.exit(main())
