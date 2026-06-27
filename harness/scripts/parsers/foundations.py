from __future__ import annotations

from pathlib import Path

from lib.graph import GraphBuilder
from lib.normalize import normalize
from lib.sources import collaborations_path, compliance_paths, foundation_id, registry_config, source_path

DEFAULT_ORGS = [
    ("org-example", "Example Organization", "https://example.com", "program_holding"),
]

CHECKLIST_SHEETS = {"Due Diligence Checklist", "Due Diligence Checklist (2)"}


def _registry_orgs() -> list[tuple[str, str, str | None, str]]:
    cfg = registry_config()
    orgs = cfg.get("organizations") or []
    out: list[tuple[str, str, str | None, str]] = []
    for item in orgs:
        if isinstance(item, dict) and item.get("id") and item.get("name"):
            out.append((
                str(item["id"]),
                str(item["name"]),
                item.get("url"),
                str(item.get("role") or "organization"),
            ))
    return out or DEFAULT_ORGS


def _registry_platforms() -> list[tuple[str, str, str, str]]:
    cfg = registry_config()
    platforms = cfg.get("platforms") or []
    out: list[tuple[str, str, str, str]] = []
    default_owner = _registry_orgs()[0][0]
    for item in platforms:
        if isinstance(item, dict) and item.get("id") and item.get("name"):
            out.append((
                str(item["id"]),
                str(item["name"]),
                str(item.get("path") or ""),
                str(item.get("owner") or default_owner),
            ))
    return out


def _registry_source_nodes() -> list[tuple[str, str, str, str]]:
    nodes: list[tuple[str, str, str, str]] = []
    proc = source_path("processes", "path")
    if proc:
        nodes.append(("source-overleaf", "Process library", str(proc), "artifact"))
    collab = collaborations_path()
    if collab:
        nodes.append(("source-collaborations", "Collaboration data", str(collab), "artifact"))
    for rid, path in regulation_paths_from_config():
        nodes.append((f"source-{rid}", rid, str(path), "regulation"))
    for cid, path, _domain in compliance_paths():
        nodes.append((f"source-{cid}", cid, str(path), "compliance_evidence"))
    return nodes


def regulation_paths_from_config():
    from lib.sources import regulation_paths
    return regulation_paths()


def ingest_foundations(g: GraphBuilder) -> None:
    cfg = registry_config()
    foundation_id_val = (cfg.get("foundation") or {}).get("id") or foundation_id()
    foundation_title = (cfg.get("foundation") or {}).get("title") or "Program foundation — regulations and in-house requirements"

    g.upsert({
        "id": foundation_id_val,
        "type": "requirement",
        "title": foundation_title,
        "status": "active",
        "owner": "systems_engineer",
        "metadata": {
            "role": "foundational_basis",
            "scope": "systems engineering, verification, compliance",
        },
    })
    g.bump("foundation", 1)

    for oid, name, url, role in _registry_orgs():
        g.upsert({
            "id": oid,
            "type": "platform",
            "title": name,
            "status": "active",
            "metadata": {"entity_type": "organization", "role": role, "url": url or ""},
        })
        g.edge(foundation_id_val, oid, "affects", f"{name} operates under program")
        g.edge(oid, foundation_id_val, "owned_by", "Organization under program foundation")
        g.bump("organizations", 1)

    for pid, name, path, owner in _registry_platforms():
        g.upsert({
            "id": pid,
            "type": "platform",
            "title": name,
            "status": "active",
            "source_path": path or None,
            "metadata": {"role": "product_surface"},
        })
        g.edge(pid, owner, "owned_by", f"{name} owned by {owner}")
        g.edge(foundation_id_val, pid, "affects", "Platform in program interconnect")
        g.bump("platforms", 1)

    for sid, title, path, ntype in _registry_source_nodes():
        p = Path(path)
        g.upsert({
            "id": sid,
            "type": ntype if ntype != "process" else "artifact",
            "title": title,
            "status": "active" if p.exists() else "blocked",
            "source_path": str(p),
            "metadata": {"role": "foundational_source_registry"},
        })
        g.edge(foundation_id_val, sid, "derives_from", f"Foundational basis: {title}")
        g.bump("registry_sources", 1)
