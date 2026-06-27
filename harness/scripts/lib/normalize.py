from __future__ import annotations

import re

DEFAULT_OPERATOR = "Your Organization"

DEFAULT_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)\blegacy_label\b"), "Your Organization Legal Name"),
]


def _replacements() -> list[tuple[re.Pattern[str], str]]:
    from lib.sources import sources_config

    cfg = sources_config()
    items = (cfg.get("terminology") or {}).get("replacements") or []
    out: list[tuple[re.Pattern[str], str]] = []
    for item in items:
        if isinstance(item, dict) and item.get("pattern") and item.get("replacement"):
            out.append((re.compile(str(item["pattern"])), str(item["replacement"])))
    return out or DEFAULT_REPLACEMENTS


def operator_name() -> str:
    from lib.sources import organization_name

    return organization_name()


OPERATOR = DEFAULT_OPERATOR


def normalize(text: str) -> str:
    if not text:
        return text
    if not isinstance(text, str):
        text = str(text)
    for pattern, repl in _replacements():
        text = pattern.sub(repl, text)
    return text.strip()


def slug(s: str) -> str:
    s = normalize(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:96] or "node"
