from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .normalize import OPERATOR, normalize

VAULT = Path(__file__).resolve().parents[3]
GRAPH_PATH = VAULT / "harness" / "graph" / "graph.json"


class GraphBuilder:
    def __init__(self) -> None:
        self.graph = self._load()
        self.seen: set[str] = set()
        self.stats: dict[str, int] = {}

    def _load(self) -> dict:
        if GRAPH_PATH.exists():
            return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
        return {
            "version": "1.1.0",
            "meta": {
                "program": "Demo Program",
                "operator": "Your Organization",
                "domain": "example.com",
                "last_ingest": None,
                "last_change": None,
            },
            "nodes": [],
            "edges": [],
        }

    def bump(self, key: str, n: int = 1) -> None:
        self.stats[key] = self.stats.get(key, 0) + n

    def upsert(self, node: dict) -> str:
        node["title"] = normalize(node.get("title", ""))
        if "body" in node:
            node["body"] = normalize(node["body"])
        meta = node.get("metadata") or {}
        node["metadata"] = {k: normalize(v) if isinstance(v, str) else v for k, v in meta.items()}
        nid = node["id"]
        self.seen.add(nid)
        for i, existing in enumerate(self.graph["nodes"]):
            if existing["id"] == nid:
                merged = {**existing, **node}
                if existing.get("status") == "archived":
                    merged["status"] = node.get("status", "active")
                self.graph["nodes"][i] = merged
                return nid
        self.graph["nodes"].append(node)
        return nid

    def edge(self, fr: str, to: str, relation: str, rationale: str = "", **meta: Any) -> None:
        key = (fr, to, relation)
        for e in self.graph["edges"]:
            if (e["from"], e["to"], e["relation"]) == key:
                return
        edge = {
            "from": fr,
            "to": to,
            "relation": relation,
            "rationale": normalize(rationale),
        }
        if meta:
            edge["metadata"] = meta
        self.graph["edges"].append(edge)
        self.seen.add(f"edge:{fr}:{to}:{relation}")

    def archive_absent(self, prefixes: tuple[str, ...] | None = None) -> int:
        """Mark nodes not touched this ingest as archived (optional type filter)."""
        count = 0
        for node in self.graph["nodes"]:
            if node["id"] in self.seen:
                continue
            if prefixes and not node["id"].startswith(prefixes):
                continue
            if node.get("status") == "archived":
                continue
            node["status"] = "archived"
            count += 1
        return count

    def save(self) -> dict:
        self.graph["meta"]["last_ingest"] = datetime.now(timezone.utc).isoformat()
        GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
        GRAPH_PATH.write_text(
            json.dumps(self.graph, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return {
            "nodes": len(self.graph["nodes"]),
            "edges": len(self.graph["edges"]),
            "stats": self.stats,
        }
