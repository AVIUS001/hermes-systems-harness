# Aerial Labs Agentic Harness — Architecture

**Program:** [www.aerial-labs.ca](https://www.aerial-labs.ca)  
**Operator:** Aerial Industries Pte. Ltd. Singapore (legacy source label `bayer` normalized on ingest)  
**System of record:** Connected graph in `harness/graph/` + Obsidian export in `graph/`

## Purpose

Execution harness for systems engineering — not a design wiki. Agents maintain consistency across requirements, artifacts, tests, compliance evidence, budgets, and interfaces while the human systems engineer stays at the architecture and tradeoff layer.

## Three Pillars

| Pillar | Role | Location |
|--------|------|----------|
| **Obsidian systems graph** | Human-navigable linked model | `graph/` (exported from harness) |
| **Knowledge Base Vault** | Agent continuity, memory, harness config | This repo root |
| **G-Stack** | QA, ship, investigate, document-release on connected repos | `~/.claude/skills/gstack` |

## Graph Model

Every node has: `id`, `type`, `title`, `status`, `owner`, `source_path`, `metadata`.

Every edge has: `from`, `to`, `relation`, `rationale` (why the link exists).

### Node types

- `requirement` — shall-statement or constraint driving design
- `regulation` — external rule (CAR, Part 21, DO-160, etc.)
- `test_procedure` — verification step elevating TRL / compliance
- `artifact` — CAD, ICD, code, sim config, drawing, report
- `process` — ACS/Q-series process standard
- `platform` — product surface (Aviabox, droneCONDUCT, etc.)
- `compliance_evidence` — bench/flight run proving a basis
- `budget` — mass, thermal, power, cost envelope
- `interface` — ICD boundary between subsystems
- `decision` — recorded tradeoff with alternatives rejected
- `agent` — bounded execution role operating on graph-derived work
- `service` — external or local runtime used by agents, platforms, or hosting

### Edge relations

| Relation | Meaning |
|----------|---------|
| `derives_from` | Artifact/test produced because of requirement |
| `satisfies` | Artifact/test meets requirement or regulation |
| `verifies` | Test procedure checks requirement |
| `implements` | Code/CAD realizes requirement |
| `affects` | Change propagates (requirement → budget, material, test) |
| `hosted_on` | Artifact lives in platform repo |
| `compliance_maps_to` | Evidence maps to regulatory basis |
| `owned_by` | Human or agent role accountable |
| `blocks` | Unmet dependency prevents TRL advance |

## Change Propagation

When any node changes:

1. Traverse all `affects`, `derives_from`, `satisfies`, `verifies` edges (downstream).
2. Re-flag dependent requirements `status: review_required`.
3. Reopen affected tests `status: stale`.
4. Mark ICDs/artifacts `status: revision_needed`.
5. Recompute linked budgets (metadata hooks).
6. Queue compliance re-run for mapped regulations.
7. Surface `decision` nodes where human judgment is required.
8. Write audit entry to `harness/audit/`.

Run: `python3 harness/scripts/impact_analysis.py --node <id>`

## Agent Roles

| Agent | Executes |
|-------|----------|
| **Ingest** | Pull sources, normalize labels, append graph |
| **Trace** | Bidirectional requirement ↔ artifact queries |
| **Impact** | Propagate changes, generate action queue |
| **Compliance** | Map evidence to regulations, flag gaps |
| **Platform** | Sync registry with repo state |
| **Harness** | Orchestrate above within vault + gstack boundaries |
| **Hermes** | Dispatch graph-derived tasks to bounded agents and collect audit output |

Human-in-the-loop: tradeoffs, safety releases, certification submissions.

## Hermes Execution Layer

Hermes is the execution layer wrapped around the vault graph. It does not replace the graph; it reads the graph, turns stale/review-required nodes into work packets, dispatches bounded agents, and writes evidence back as nodes, edges, audits, and Obsidian notes.

Runtime tiers:

| Tier | Role |
|------|------|
| Local MacBook Pro | Canonical vault, CAD/sim file access, Obsidian, Fusion, local Gemma/Ollama |
| Hostinger VPS | Optional always-on runner for non-secret, low-risk agents and public site automation |
| NVIDIA ecosystem | Candidate acceleration path for simulation, digital twin, robotics/edge AI, and GPU-backed inference |
| Human systems engineer | Approves safety, certification, public posting, spending, and irreversible infrastructure actions |

Default guardrail: overnight agents may read, analyze, summarize, re-export, and mark nodes stale. They may not send external messages, publish, spend money, mutate CAD, or change production systems without explicit approval.

## Data Flow

```
External sources (processes, collabs, work orders, regs, flight/bench CSV)
        ↓ ingest.py (normalize bayer → Aerial Industries Pte. Ltd. Singapore)
        ↓ graph.json (system of record)
        ↓ export_obsidian.py
        ↓ graph/ (Obsidian vault)
        ↓ agents read/write via harness/SKILL.md procedures
        ↓ impact_analysis.py on change
        ↓ action queue → human or agent execution
```

## TRL Ladder (agency-neutral)

Tests elevate readiness without naming grant/incubator bodies:

| TRL | Gate tests (examples) |
|-----|-------------------------|
| 3 | Bench substantiation, material/process conformity |
| 4 | Component integration, EMC/cyber screening |
| 5 | Vehicle-in-loop, allocator/thermal margins |
| 6 | Flight envelope segments, Part 21 analog matrix |
| 7 | Operational SOP, maintenance, service provider assessment |
| 8 | Certification evidence package, noise/DO-160 planning |
| 9 | Production PMA/PM repeatability, field operations |

Linked from `harness/trl/ladder.yaml` to `test_procedure` and `regulation` nodes.

## Platform interconnect

All platforms registered in `harness/platforms/registry.yaml`. Each platform node links to:

- Hosted artifacts (simulators, bundles, browsers)
- Satisfied requirements
- Active test procedures
- Compliance evidence sources

Target end state: **Aviabox.ai** orchestrates harness API; sibling sites consume graph slices.

## Learning Loop Cadence

The local update layer is in `harness/updates/` and runs on an every-three-days plus weekly cadence.

| Cadence | Purpose | Script |
|---------|---------|--------|
| Every 3 days | Execution queue, recent memory, graph health, Calendar window, local app surface | `python3 harness/scripts/local_update.py --mode tri_day --calendar --llm` |
| Weekly | Seven-day synthesis, stale graph links, human judgment queue | `python3 harness/scripts/local_update.py --mode weekly --calendar --llm` |

The update script attempts offline Gemma synthesis through local Ollama. If a Gemma model is not available, the update still writes a deterministic summary and records the fallback reason.

Configured adapters live in `harness/config/app_integrations.json`. Installed apps discovered on this MacBook Pro are written to `harness/config/macos_apps.generated.json`.
