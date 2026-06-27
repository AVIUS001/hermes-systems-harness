from __future__ import annotations

import csv
from pathlib import Path

from lib.graph import GraphBuilder
from lib.normalize import normalize, slug
from lib.sources import compliance_paths, foundation_id


def ingest_compliance_csv(g: GraphBuilder) -> None:
    fid = foundation_id()
    for cid, path, domain in compliance_paths():
        if not path.exists():
            continue
        if "bench" in cid or "pda" in domain:
            _ingest_pda_pm(g, path, cid, fid)
        else:
            _ingest_part21(g, path, cid, fid)


def _ingest_pda_pm(g: GraphBuilder, path: Path, source_id: str, foundation: str) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            basis = normalize(row.get("requirement_basis", ""))
            if not basis:
                continue
            rid = f"regulation-{slug(basis)}"
            g.upsert({
                "id": rid,
                "type": "regulation",
                "title": basis,
                "status": "active",
                "owner": "certification",
                "source_path": str(path),
                "metadata": {
                    "applicability": normalize(row.get("applicability_to_ic2e", "")),
                    "evidence_type": normalize(row.get("bench_lab_evidence_type", "")),
                    "linked_bench_runs": normalize(row.get("linked_bench_runs", "")),
                    "limitation": normalize(row.get("limitation_or_follow_on", "")),
                    "domain": "propulsion_manufacturing",
                },
            })
            g.edge(rid, foundation, "derives_from", "Bench compliance basis")
            g.edge(rid, f"source-{source_id}", "hosted_on", f"Row in {path.name}")

            req_id = f"req-pda-{slug(basis)}"
            g.upsert({
                "id": req_id,
                "type": "requirement",
                "title": f"Substantiate: {basis}",
                "status": "active",
                "owner": "certification",
                "metadata": {"requirement_class": "compliance_substantiation"},
            })
            g.edge(req_id, rid, "satisfies", "In-house requirement to meet regulatory basis")
            g.edge(req_id, foundation, "derives_from", "Derived from bench compliance mapping")

            runs = normalize(row.get("linked_bench_runs", ""))
            if runs:
                eid = f"evidence-pda-{i}"
                g.upsert({
                    "id": eid,
                    "type": "compliance_evidence",
                    "title": f"Bench evidence: {runs} for {basis}",
                    "status": "active",
                    "source_path": str(path),
                    "metadata": {"bench_runs": runs, "row_index": i},
                })
                g.edge(eid, rid, "compliance_maps_to", row.get("limitation_or_follow_on", ""))
                g.edge(eid, req_id, "verifies", "Bench lab run substantiation")
            g.bump("pda_regulations", 1)


def _ingest_part21(g: GraphBuilder, path: Path, source_id: str, foundation: str) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            test_id = normalize(row.get("test_id", f"row-{i}"))
            basis = normalize(row.get("part21_basis", ""))
            if not test_id:
                continue
            tid = f"test-{slug(test_id)}"
            result = normalize(row.get("engineering_result", ""))
            status = "active"
            if any(x in result.lower() for x in ("abort", "failed", "incident", "repair")):
                status = "blocked"
            elif "marginal" in result.lower() or "requires" in result.lower():
                status = "review_required"

            g.upsert({
                "id": tid,
                "type": "test_procedure",
                "title": test_id,
                "status": status,
                "source_path": str(path),
                "metadata": {k: normalize(v) for k, v in row.items()},
            })
            g.edge(tid, foundation, "derives_from", "Flight test compliance matrix")
            g.edge(tid, f"source-{source_id}", "hosted_on", f"Row in {path.name}")

            if basis:
                rid = f"regulation-{slug(basis)}"
                g.upsert({
                    "id": rid,
                    "type": "regulation",
                    "title": basis,
                    "status": "active",
                    "metadata": {"part21_analog": True},
                })
                g.edge(tid, rid, "compliance_maps_to", row.get("multicopter_equivalent", ""))
                g.edge(rid, foundation, "derives_from", "Regulatory basis from flight test mapping")

                req_id = f"req-flight-{slug(test_id)}"
                g.upsert({
                    "id": req_id,
                    "type": "requirement",
                    "title": f"Demonstrate: {row.get('multicopter_equivalent', test_id)}",
                    "status": status,
                    "metadata": {"engineering_result": result},
                })
                g.edge(req_id, rid, "satisfies", "Equivalent requirement for regulatory basis")
                g.edge(tid, req_id, "verifies", "Flight test verifies requirement")

            vehicle = row.get("vehicle_code", "")
            if vehicle:
                vid = f"vehicle-{slug(vehicle)}"
                g.upsert({
                    "id": vid,
                    "type": "artifact",
                    "title": vehicle,
                    "status": "active",
                    "metadata": {"vehicle_program": True},
                })
                g.edge(tid, vid, "verifies", f"Flight {row.get('flight_number', '')}")
            g.bump("flight_tests", 1)
