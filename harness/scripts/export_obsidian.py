#!/usr/bin/env python3
"""Export graph.json to Obsidian-compatible markdown with wikilinks."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
GRAPH_PATH = VAULT / "harness" / "graph" / "graph.json"
OBSIDIAN_ROOT = VAULT / "graph"

TYPE_DIRS = {
    "requirement": "requirements",
    "regulation": "regulations",
    "test_procedure": "tests",
    "artifact": "artifacts",
    "process": "processes",
    "platform": "platforms",
    "compliance_evidence": "evidence",
    "budget": "budgets",
    "interface": "interfaces",
    "decision": "decisions",
    "agent": "agents",
    "service": "services",
}


def wikilink(node_id: str, title: str) -> str:
    safe = re.sub(r"[^\w\-]", "-", node_id)
    return f"[[{safe}|{title}]]"


def export_graph() -> dict:
    OBSIDIAN_ROOT.mkdir(parents=True, exist_ok=True)
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]}

    out_edges: dict[str, list] = {}
    in_edges: dict[str, list] = {}
    for e in graph["edges"]:
        out_edges.setdefault(e["from"], []).append(e)
        in_edges.setdefault(e["to"], []).append(e)

    counts = {"files": 0, "dirs": 0}

    # Index
    index_lines = [
        "# Aerial Labs Systems Graph",
        "",
        f"Operator: **{graph['meta'].get('operator', 'Aerial Industries Pte. Ltd. Singapore')}**",
        f"Last ingest: {graph['meta'].get('last_ingest', 'never')}",
        "",
        "## Foundation",
        "",
        "Hub node: [[foundation-aerial-labs|Aerial Labs Program Foundation]]",
        "",
        "Subsidiaries: [[org-aerial-labs|Aerial Labs]] · [[org-aerial-industries-sg|Aerial Industries SG]] · "
        "[[org-aerial-mechanica-usa|Aerial Mechanica USA]] · [[org-avius-ai|avius.ai]] · "
        "[[org-aviabox-ai|aviabox.ai]] · [[org-sybel-investments|Sybel Investments]] · "
        "[[org-farmingcourses|FarmingCourses]]",
        "",
        "Foundational sources: [[source-dd-eval]] · [[source-rrl-calculator]] · [[source-pda-pm-csv]] · "
        "[[source-part21-csv]] · [[source-overleaf]] · [[source-sybel-excel]]",
        "",
        "## Visual graph (all connecting nodes)",
        "",
        "Obsidian vault **Business-KB** → `Cmd+G` or:",
        "",
        "```bash",
        "open \"obsidian://graph?vault=Business-KB\"",
        "```",
        "",
        "Folder filter: `Aerial-Labs-Graph`. Local subgraph: open any note → **Local graph** → depth 2–3.",
        "",
        "## Automated sync",
        "",
        "```bash",
        "./harness/scripts/sync.sh          # when sources change",
        "./harness/scripts/sync.sh --force",
        "```",
        "",
        "## Node counts by type",
        "",
    ]
    by_type: dict[str, int] = {}
    for n in graph["nodes"]:
        by_type[n["type"]] = by_type.get(n["type"], 0) + 1
    for t, c in sorted(by_type.items()):
        index_lines.append(f"- {t}: {c}")
    index_lines.append("")
    index_lines.append("## Quick navigation")
    index_lines.append("")
    for t in sorted(TYPE_DIRS):
        index_lines.append(f"- [[{TYPE_DIRS[t]}/_index|{t}]]")
    (OBSIDIAN_ROOT / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    counts["files"] += 1

    for ntype, subdir in TYPE_DIRS.items():
        dirpath = OBSIDIAN_ROOT / subdir
        dirpath.mkdir(parents=True, exist_ok=True)
        counts["dirs"] += 1
        type_nodes = [n for n in graph["nodes"] if n["type"] == ntype]
        idx_lines = [f"# {ntype.replace('_', ' ').title()}", "", f"Total: {len(type_nodes)}", ""]
        for n in sorted(type_nodes, key=lambda x: x["title"])[:500]:
            safe = re.sub(r"[^\w\-]", "-", n["id"])
            idx_lines.append(f"- [[{safe}|{n['title']}]]")
        (dirpath / "_index.md").write_text("\n".join(idx_lines) + "\n", encoding="utf-8")
        counts["files"] += 1

        for n in type_nodes:
            safe = re.sub(r"[^\w\-]", "-", n["id"])
            lines = [
                f"# {n['title']}",
                "",
                f"- **ID:** `{n['id']}`",
                f"- **Type:** {n['type']}",
                f"- **Status:** {n.get('status', 'unknown')}",
            ]
            if n.get("owner"):
                lines.append(f"- **Owner:** {n['owner']}")
            if n.get("source_path"):
                lines.append(f"- **Source:** `{n['source_path']}`")
            lines.append("")

            if n.get("body"):
                lines.extend(["## Body", "", n["body"], ""])

            meta = n.get("metadata") or {}
            if meta:
                lines.extend(["## Metadata", ""])
                for k, v in list(meta.items())[:30]:
                    lines.append(f"- **{k}:** {v}")
                lines.append("")

            outs = out_edges.get(n["id"], [])
            if outs:
                lines.extend(["## Outgoing links", ""])
                for e in outs:
                    tgt = nodes.get(e["to"], {})
                    title = tgt.get("title", e["to"])
                    lines.append(f"- `{e['relation']}` → {wikilink(e['to'], title)}")
                    if e.get("rationale"):
                        lines.append(f"  - _{e['rationale']}_")
                lines.append("")

            ins = in_edges.get(n["id"], [])
            if ins:
                lines.extend(["## Incoming links", ""])
                for e in ins:
                    src = nodes.get(e["from"], {})
                    title = src.get("title", e["from"])
                    lines.append(f"- `{e['relation']}` ← {wikilink(e['from'], title)}")
                lines.append("")

            lines.extend([
                "## Traceability",
                "",
                "_Every artifact links to the requirement that created it. Navigate incoming `derives_from` / `satisfies` edges to see why this exists._",
                "",
            ])

            (dirpath / f"{safe}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
            counts["files"] += 1

    return counts


def main() -> int:
    if not GRAPH_PATH.exists():
        print("Run ingest.py first", file=sys.stderr)
        return 1
    counts = export_graph()
    print(json.dumps(counts, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
