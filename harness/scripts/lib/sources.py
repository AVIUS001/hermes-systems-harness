"""Load local source and platform registry configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

HARNESS = Path(__file__).resolve().parents[2]
CONFIG = HARNESS / "config"
PLATFORMS = HARNESS / "platforms"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sources_config() -> dict[str, Any]:
    """Return parsed sources.yaml; empty dict if not configured locally."""
    return _load_yaml(CONFIG / "sources.yaml")


def registry_config() -> dict[str, Any]:
    """Return parsed platforms/registry.yaml; empty dict if not configured locally."""
    return _load_yaml(PLATFORMS / "registry.yaml")


def organization_name() -> str:
    org = sources_config().get("organization") or {}
    return str(org.get("legal_name") or "Your Organization")


def foundation_id() -> str:
    reg = registry_config().get("foundation") or {}
    return str(reg.get("id") or "foundation-demo")


def source_path(key: str, *subkeys: str) -> Path | None:
    """Resolve a path from sources.yaml, e.g. source_path('processes', 'path')."""
    cfg = sources_config()
    node: Any = cfg.get("sources", {}).get(key)
    for sub in subkeys:
        if not isinstance(node, dict):
            return None
        node = node.get(sub)
    if not node or not isinstance(node, str):
        return None
    return Path(node).expanduser()


def regulation_paths() -> list[tuple[str, Path]]:
    """Return (id, path) pairs from sources.regulations."""
    regs = sources_config().get("sources", {}).get("regulations") or []
    out: list[tuple[str, Path]] = []
    for item in regs:
        if isinstance(item, dict) and item.get("path") and item.get("id"):
            out.append((str(item["id"]), Path(str(item["path"])).expanduser()))
    return out


def compliance_paths() -> list[tuple[str, Path, str]]:
    """Return (id, path, domain) from sources.compliance_mappings."""
    rows = sources_config().get("sources", {}).get("compliance_mappings") or []
    out: list[tuple[str, Path, str]] = []
    for item in rows:
        if isinstance(item, dict) and item.get("path") and item.get("id"):
            out.append((
                str(item["id"]),
                Path(str(item["path"])).expanduser(),
                str(item.get("domain") or ""),
            ))
    return out


def flight_test_paths() -> list[Path]:
    """Return optional flight/bench support CSV paths from sources.flight_test_support."""
    rows = sources_config().get("sources", {}).get("flight_test_support") or []
    out: list[Path] = []
    for item in rows:
        if isinstance(item, str):
            out.append(Path(item).expanduser())
        elif isinstance(item, dict) and item.get("path"):
            out.append(Path(str(item["path"])).expanduser())
    return out


def collaborations_path() -> Path | None:
    return source_path("collaborations", "path")


def watch_paths() -> list[str]:
    """Return filesystem paths to fingerprint during sync (from sources.yaml)."""
    cfg = sources_config()
    sync = cfg.get("sync") or {}
    explicit = sync.get("watch_paths")
    if isinstance(explicit, list) and explicit:
        return [str(p) for p in explicit]

    paths: list[str] = []
    proc = source_path("processes", "path")
    if proc:
        paths.append(str(proc))
    collab = collaborations_path()
    if collab:
        paths.append(str(collab))
    wo = source_path("work_orders", "path")
    if wo:
        paths.append(str(wo))
    for _rid, path in regulation_paths():
        paths.append(str(path))
    for _cid, path, _domain in compliance_paths():
        paths.append(str(path))
    for path in flight_test_paths():
        paths.append(str(path))
    return paths


def obsidian_symlink() -> Path | None:
    """Optional Obsidian export symlink target from sources.sync.obsidian_symlink."""
    cfg = sources_config()
    target = (cfg.get("sync") or {}).get("obsidian_symlink")
    if not target or not isinstance(target, str):
        return None
    return Path(target).expanduser()
