#!/usr/bin/env python3
"""Add an edge to graph.json from CLI."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

GRAPH = Path(__file__).resolve().parents[1] / "graph" / "graph.json"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="fr", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--relation", required=True)
    p.add_argument("--rationale", default="")
    args = p.parse_args()

    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    key = (args.fr, args.to, args.relation)
    for e in graph["edges"]:
        if (e["from"], e["to"], e["relation"]) == key:
            print("Edge already exists")
            return 0
    graph["edges"].append({
        "from": args.fr,
        "to": args.to,
        "relation": args.relation,
        "rationale": args.rationale,
    })
    graph["meta"]["last_change"] = datetime.now(timezone.utc).isoformat()
    GRAPH.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Added {args.fr} --{args.relation}--> {args.to}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
