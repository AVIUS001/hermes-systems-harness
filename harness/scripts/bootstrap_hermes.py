#!/usr/bin/env python3
"""Seed generic Hermes execution-layer nodes into the systems graph."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lib.graph import GraphBuilder  # noqa: E402
from lib.sources import foundation_id  # noqa: E402

FOUNDATION = foundation_id()
BRIEF_RECIPIENT = os.environ.get("HERMES_BRIEF_RECIPIENT", "you@example.com")


def node(g: GraphBuilder, **data: object) -> str:
    g.upsert(data)  # type: ignore[arg-type]
    return str(data["id"])


def seed_requirements(g: GraphBuilder) -> None:
    requirements = [
        {
            "id": "req-system-graph-source-of-record",
            "title": "The systems graph shall be the source of record for requirements, artifacts, tests, interfaces, budgets, decisions, and compliance evidence.",
            "body": "All agent work must start from graph context and write results back to the graph, audit log, or Obsidian export.",
        },
        {
            "id": "req-hermes-overnight-guardrails",
            "title": "Hermes agents shall perform overnight work only inside approved read/analyze/write-vault boundaries unless the human approves escalation.",
            "body": "Blocked actions include public posting, email, external submissions, CAD source mutation, production deployment, and spending.",
        },
        {
            "id": "req-cad-revision-impact-trace",
            "title": "Every CAD assembly revision shall trace to affected requirements, interfaces, budgets, tests, and compliance evidence before release.",
            "body": "A CAD change is incomplete until impact analysis has identified downstream mass, thermal, power, verification, and interface effects.",
        },
        {
            "id": "req-platform-graph-interconnect",
            "title": "Product and public surfaces shall consume graph-derived program context through controlled sanitized slices.",
            "body": "Business and public platforms may receive sanitized outputs, while private engineering sources remain local by default.",
        },
        {
            "id": "req-compliance-evidence-loop",
            "title": "Bench, flight, and service evidence shall continuously map to regulatory bases, TRL gates, and reopened tests when requirements change.",
            "body": "Compliance evidence must not become stale silently; changed requirements reopen linked tests and re-run mapping checks.",
        },
    ]
    for req in requirements:
        node(
            g,
            id=req["id"],
            type="requirement",
            title=req["title"],
            status="active",
            owner="systems_engineer",
            source_kind="hermes_bootstrap",
            metadata={"program_layer": "hermes"},
            body=req["body"],
        )
        g.edge(req["id"], FOUNDATION, "derives_from", "Top-level systems engineering intent")


def seed_processes(g: GraphBuilder) -> None:
    processes = [
        ("process-hermes-execution-loop", "Hermes graph-native execution loop"),
        ("process-overnight-agent-operations", "Overnight agent operations and approval gates"),
        ("process-sanitized-public-graph-slices", "Sanitized public graph slices for websites and open-source publication"),
    ]
    for pid, title in processes:
        node(
            g,
            id=pid,
            type="process",
            title=title,
            status="active",
            owner="harness",
            source_path="harness/HERMES.md",
            source_kind="hermes_runbook",
            metadata={"cadence": "continuous"},
        )
        g.edge(pid, "req-system-graph-source-of-record", "derives_from", "Hermes process exists to execute graph-derived work")

    g.edge("process-overnight-agent-operations", "req-hermes-overnight-guardrails", "satisfies", "Runbook enforces overnight guardrails")
    g.edge("process-sanitized-public-graph-slices", "req-platform-graph-interconnect", "satisfies", "Public surfaces receive controlled graph exports")


def seed_services(g: GraphBuilder) -> None:
    services = [
        ("service-hostinger-vps", "Hostinger VPS always-on runner", "https://www.hostinger.com/vps-hosting", "hosting"),
        ("service-nvidia-inception", "NVIDIA Inception Program", "https://www.nvidia.com/en-us/startups/", "startup_ecosystem"),
        ("service-nvidia-developer", "NVIDIA Developer Program", "https://developer.nvidia.com/developer-program", "developer_ecosystem"),
        ("service-github-open-source", "GitHub open-source publication surface", "https://github.com", "publication"),
        ("service-cursor-pro", "Cursor Pro software development surface", "", "software_development"),
        ("service-claude-code", "Claude Code software development and review surface", "", "software_development"),
        ("service-local-gemma-ollama", "Local Gemma/Ollama synthesis runtime", "", "local_llm"),
    ]
    for sid, title, url, role in services:
        node(
            g,
            id=sid,
            type="service",
            title=title,
            status="active",
            owner="systems_engineer",
            source_kind="service_registry",
            metadata={"url": url, "role": role, "approval_required_for_external_action": True},
        )
        g.edge(sid, "req-hermes-overnight-guardrails", "satisfies", "External service use is governed by Hermes approval gates")

    g.edge("service-hostinger-vps", "process-overnight-agent-operations", "implements", "Candidate always-on runner for sanitized overnight jobs")
    g.edge("service-local-gemma-ollama", "process-hermes-execution-loop", "implements", "Local synthesis without exporting private engineering context")


def seed_agents(g: GraphBuilder) -> None:
    agents = [
        ("agent-hermes-orchestrator", "Hermes Orchestrator Agent", "Coordinate graph-derived work packets and collect audit output"),
        ("agent-requirements-curator", "Requirements Curator Agent", "Normalize requirements and maintain bidirectional traceability"),
        ("agent-cad-interface-steward", "CAD Interface Steward Agent", "Track Fusion CAD assemblies, interfaces, and budget impact"),
        ("agent-compliance-runner", "Compliance Runner Agent", "Map evidence to regulations and reopen stale tests"),
        ("agent-platform-operator", "Platform Operator Agent", "Sync platform registry and sanitized website/API slices"),
        ("agent-publication-operator", "Publication Operator Agent", "Draft public/open-source artifacts for approval"),
        ("agent-overnight-sentinel", "Overnight Sentinel Agent", "Run read-only health checks and queue morning decisions"),
        (
            "agent-email-briefing",
            "Email Briefing Agent",
            f"Compile memory links, weekly summary, and graph-derived to-do list for {BRIEF_RECIPIENT}",
        ),
    ]
    for aid, title, scope in agents:
        node(
            g,
            id=aid,
            type="agent",
            title=title,
            status="active",
            owner="harness",
            source_path="harness/config/hermes.yaml",
            source_kind="hermes_agent",
            metadata={"scope": scope, "human_approval_required_for_external_action": True},
        )
        g.edge(aid, "process-hermes-execution-loop", "implements", scope)
        g.edge(aid, "req-hermes-overnight-guardrails", "satisfies", "Agent is bounded by Hermes guardrails")

    g.edge("agent-overnight-sentinel", "process-overnight-agent-operations", "implements", "Runs local health checks while the human sleeps")
    g.edge("agent-email-briefing", "process-overnight-agent-operations", "implements", "Drafts memory and to-do briefings for the human")
    g.edge("agent-publication-operator", "service-github-open-source", "hosted_on", "Drafts public artifacts before human-approved publication")


def seed_platforms(g: GraphBuilder) -> None:
    node(
        g,
        id="platform-hermes-vault-control-plane",
        type="platform",
        title="Hermes Vault Control Plane",
        status="active",
        owner="systems_engineer",
        source_path="harness/config/hermes.yaml",
        source_kind="platform_registry",
        metadata={"role": "local"},
    )
    g.edge("platform-hermes-vault-control-plane", "req-system-graph-source-of-record", "satisfies", "Hermes runs from the vault graph")
    g.edge("platform-hermes-vault-control-plane", "req-platform-graph-interconnect", "satisfies", "Local control plane for graph-fed workflows")


def seed_interfaces_and_budgets(g: GraphBuilder) -> None:
    interfaces = [
        ("interface-hermes-obsidian-graph", "Hermes to Obsidian graph export interface", "Graph JSON and Markdown export boundary"),
        ("interface-hermes-hostinger-mcp", "Hermes to Hostinger MCP/VPS boundary", "Sanitized always-on runner boundary"),
        ("interface-platform-graph-api", "Platform graph API / sanitized slice interface", "Product surfaces consume graph slices"),
    ]
    for iid, title, desc in interfaces:
        node(
            g,
            id=iid,
            type="interface",
            title=title,
            status="active",
            owner="systems_engineer",
            source_kind="hermes_bootstrap",
            metadata={"description": desc},
        )
        g.edge(iid, "req-system-graph-source-of-record", "derives_from", "Interfaces make change impact computable")

    budgets = [
        ("budget-thermal-inverter", "Inverter thermal margin budget"),
        ("budget-demo-mass", "Demo mass budget"),
        ("budget-demo-power", "Demo power budget"),
    ]
    for bid, title in budgets:
        node(
            g,
            id=bid,
            type="budget",
            title=title,
            status="review_required",
            owner="systems_engineer",
            source_kind="hermes_bootstrap",
            metadata={"state": "placeholder_until_next_properties_export"},
        )
        g.edge(bid, "req-cad-revision-impact-trace", "derives_from", "CAD revisions must recompute linked budgets")

    g.edge("interface-hermes-obsidian-graph", "platform-hermes-vault-control-plane", "implements", "Local graph export is Hermes' primary context boundary")
    g.edge("interface-hermes-hostinger-mcp", "service-hostinger-vps", "hosted_on", "Hostinger is the candidate remote runner boundary")


def seed_decision(g: GraphBuilder) -> None:
    node(
        g,
        id="decision-hermes-local-first",
        type="decision",
        title="Stage Hermes locally first, then mirror sanitized work to optional remote runners",
        status="active",
        owner="systems_engineer",
        source_path="harness/HERMES.md",
        source_kind="architecture_decision",
        metadata={
            "decision_date": "2026-06-27",
            "rationale": "Private engineering context remains local; remote runners receive sanitized jobs only after approval.",
        },
    )
    g.edge("decision-hermes-local-first", "req-hermes-overnight-guardrails", "satisfies", "Preserves local-first safety boundary")
    g.edge("decision-hermes-local-first", "service-hostinger-vps", "affects", "Hostinger is candidate remote runner after approval")


def load_extension(g: GraphBuilder) -> None:
    ext_path = SCRIPTS.parent / "local" / "bootstrap_extension.py"
    if not ext_path.exists():
        return
    spec = importlib.util.spec_from_file_location("bootstrap_extension", ext_path)
    if not spec or not spec.loader:
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "seed"):
        mod.seed(g)


def run() -> dict:
    g = GraphBuilder()
    seed_requirements(g)
    seed_processes(g)
    seed_services(g)
    seed_agents(g)
    seed_platforms(g)
    seed_interfaces_and_budgets(g)
    seed_decision(g)
    load_extension(g)
    now = datetime.now(timezone.utc).isoformat()
    g.graph["meta"]["last_change"] = now
    g.graph["meta"]["hermes_seeded"] = now
    result = g.save()
    result["hermes_seeded_at"] = now
    return result


def main() -> int:
    print(json.dumps(run(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
