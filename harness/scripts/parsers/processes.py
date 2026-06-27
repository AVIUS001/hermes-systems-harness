from __future__ import annotations

import csv
from pathlib import Path

from lib.graph import GraphBuilder
from lib.normalize import normalize, slug
from lib.sources import foundation_id, source_path

ROLE_ORG = {
    "ACS": "org-aerial-industries-sg",
    "AMIN": "org-aerial-industries-sg",
    "AER8": "org-aerial-mechanica-usa",
    "NAI": "org-aerial-industries-sg",
}


def _overleaf_base() -> Path | None:
    return source_path("processes", "path")


def _ingest_project_row(g: GraphBuilder, row: dict, overleaf_base: Path, discovered: str = "manifest") -> None:
    project = row.get("project", "").strip()
    if not project:
        return
    title = normalize(row.get("title") or project)
    role = (row.get("role") or "ACS").strip()
    nid = f"process-{slug(project)}"
    src = overleaf_base / "projects" / project
    g.upsert({
        "id": nid,
        "type": "process",
        "title": title,
        "status": "active" if src.exists() else "blocked",
        "owner": "systems_engineer",
        "source_path": str(src),
        "source_kind": "process_library",
        "metadata": {
            "role": role,
            "extraction_method": row.get("extraction_method", ""),
            "headings": row.get("headings", ""),
            "original_source": row.get("source", ""),
            "discovered_via": discovered,
        },
    })
    g.edge(nid, foundation_id(), "derives_from", "In-house process standard under program foundation")
    g.edge(nid, "source-overleaf", "hosted_on", "Process document in process library")
    owner = ROLE_ORG.get(role, "org-aerial-labs")
    g.edge(nid, owner, "owned_by", f"Process family {role}")
    if role == "AMIN":
        g.edge(nid, "platform-droneconduct", "implements", "Operational/compliance procedures")
    if role == "AER8":
        g.edge(nid, "platform-avius", "implements", "Product engineering process data")
    g.bump("processes", 1)


def ingest_processes(g: GraphBuilder) -> None:
    overleaf_base = _overleaf_base()
    if not overleaf_base or not overleaf_base.exists():
        return

    manifest = overleaf_base / "manifest.csv"
    manifest_projects: set[str] = set()
    if manifest.exists():
        with manifest.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                manifest_projects.add(row.get("project", "").strip())
                _ingest_project_row(g, row, overleaf_base, "manifest")

    projects_dir = overleaf_base / "projects"
    if projects_dir.exists():
        for d in sorted(projects_dir.iterdir()):
            if not d.is_dir():
                continue
            if d.name in manifest_projects:
                continue
            title = d.name.replace("_", " ")
            main_tex = d / "main.tex"
            if main_tex.exists():
                head = main_tex.read_text(encoding="utf-8", errors="ignore")[:500]
                if "\\title{" in head:
                    import re
                    m = re.search(r"\\title\{([^}]+)\}", head)
                    if m:
                        title = normalize(m.group(1))
            role = "AMIN" if d.name.startswith("AMIN") else "AER8" if d.name.startswith("AER") else "ACS"
            _ingest_project_row(g, {
                "project": d.name,
                "title": title,
                "role": role,
                "source": d.name,
                "extraction_method": "filesystem_discovery",
                "headings": "",
            }, overleaf_base, "filesystem")
