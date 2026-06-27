#!/usr/bin/env python3
"""
Hermes Systems Harness — full ingest orchestrator.

Ingests processes, collaborations, Excel requirement/regulation sources, compliance
CSVs, and work orders into the systems graph. Paths come from harness/config/sources.yaml
(copy from sources.yaml.example).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lib.graph import GraphBuilder  # noqa: E402
from lib.sources import foundation_id, source_path  # noqa: E402
from parsers.compliance_csv import ingest_compliance_csv  # noqa: E402
from parsers.excel_sources import ingest_excel_sources  # noqa: E402
from parsers.foundations import ingest_foundations  # noqa: E402
from parsers.processes import ingest_processes  # noqa: E402


def ingest_work_orders(g: GraphBuilder) -> None:
    wo_base = source_path("work_orders", "path")
    if not wo_base or not wo_base.exists():
        return
    fid = foundation_id()
    for doc in sorted(wo_base.glob("*.docx")):
        from lib.normalize import normalize, slug

        title = normalize(doc.stem.replace("_", " "))
        nid = f"test-{slug(doc.stem)}"
        g.upsert({
            "id": nid,
            "type": "test_procedure",
            "title": title,
            "status": "active",
            "owner": "quality",
            "source_path": str(doc),
            "source_kind": "work_order",
            "metadata": {"original_filename": doc.name},
        })
        g.edge(nid, fid, "derives_from", "Quality / test procedure work order")
        g.bump("work_orders", 1)


def run_ingest() -> dict:
    g = GraphBuilder()
    ingest_foundations(g)
    ingest_processes(g)
    ingest_excel_sources(g)
    ingest_compliance_csv(g)
    ingest_work_orders(g)
    archived = g.archive_absent(prefixes=("process-", "req-dd-", "req-rrl-", "req-sybel-"))
    g.bump("archived_stale", archived)
    return g.save()


def main() -> int:
    result = run_ingest()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
