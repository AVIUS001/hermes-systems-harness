# Aerial Labs Agentic Harness

Use this skill when performing systems engineering work across Aerial Labs technologies: agriculture drones, eVTOL/UAM, airborne wind energy, certification, and connected platforms.

## When to use

- Ingesting or updating engineering context from external sources
- Tracing requirements ↔ artifacts ↔ tests ↔ compliance
- Propagating a design or requirement change through the model
- Connecting platforms (Aviabox, droneCONDUCT, Sybel, FarmingCourses, Aerial-USA)
- Running Hermes-style overnight agent work from the vault graph
- Re-running compliance or reopening tests after a change
- Any task where "what does this change break?" matters

## System of record

1. **Graph JSON:** `harness/graph/graph.json` — canonical connected model
2. **Obsidian export:** `graph/` — human navigation with wikilinks
3. **Vault memory:** `memory/`, `MEMORY.md` — session continuity

Never treat loose documents as authoritative. Derive actions from the graph.

## Terminology

On ingest and in all generated text, replace legacy **bayer** with **Aerial Industries Pte. Ltd. Singapore**.

## Standard workflows

### 0. Learning-loop update

```bash
python3 harness/scripts/discover_macos_apps.py --write
python3 harness/scripts/local_update.py --mode tri_day --calendar --llm
python3 harness/scripts/local_update.py --mode weekly --calendar --llm
```

The cadence is every three days plus weekly. The script uses local offline Gemma through Ollama when available and falls back to deterministic extraction if the model is unavailable.

### 1. Refresh engineering context

```bash
./harness/scripts/sync.sh          # auto-skip if sources unchanged
./harness/scripts/sync.sh --force  # full re-ingest + Obsidian export
```

Or manually:

```bash
harness/.venv/bin/python harness/scripts/ingest.py
harness/.venv/bin/python harness/scripts/export_obsidian.py
```

### 1A. Hermes execution layer

```bash
python3 harness/scripts/bootstrap_hermes.py
python3 harness/scripts/overnight_health.py --write
python3 harness/scripts/memory_email_brief.py --write
```

Hermes reads the graph, dispatches bounded agents, and writes audits back to the vault. It may do local read/analyze/export work while the human sleeps. It must not publish, spend money, send messages, mutate CAD, or change production systems without explicit approval.

Email briefings are external actions. Drafts are safe by default in `harness/outbox/`; sending requires SMTP environment variables and an explicit `--send --yes`.

### 2. Trace why an artifact exists

1. Open node in `graph/` or query `graph.json` by `id`
2. Follow **incoming** edges: `derives_from`, `satisfies`, `compliance_maps_to`
3. Report requirement chain to user

### 3. Propagate a change

```bash
python3 harness/scripts/impact_analysis.py --node <id> --summary "..." --audit
```

Execute returned action queue:

| Action | Agent does |
|--------|------------|
| `re_review_requirement` | Set status `review_required`, list linked artifacts |
| `reopen_test` | Set test `stale`, link to changed requirement |
| `mark_revision_needed` | Flag ICD/CAD/code artifact |
| `re_run_compliance_check` | Compare evidence vs regulation metadata |
| `recompute_budget` | Update mass/thermal/power metadata hooks |
| `surface_for_human_judgment` | Present tradeoff — do not auto-resolve |
| `sync_registry` | Verify `harness/platforms/registry.yaml` paths |

### 4. Platform interconnect work

Read `harness/platforms/registry.yaml`. When modifying a repo under a platform:

1. Update artifact node `source_path` / metadata if structure changed
2. Add `implements` or `hosted_on` edges to new requirements
3. Re-export Obsidian

### 5. G-Stack integration

For code changes in platform repos, use gstack skills in order:

1. `/gstack-investigate` — root cause before fixing
2. `/gstack-review` — pre-merge structural review
3. `/gstack-qa` — verify simulators and web apps
4. `/gstack-document-release` — sync docs after ship

Always write significant outcomes back to the graph (new `decision` or `artifact` nodes).

## Agent boundaries

**Agents execute:**

- Graph maintenance, ingest, impact analysis
- Consistency checks across requirements/tests/compliance
- Surfacing stale or blocked nodes
- Drafting ICD/test revisions linked to requirements

**Human decides:**

- Safety releases, certification submissions
- Tradeoffs affecting mass/thermal/cert cost
- Waiving or changing top-level requirements

## TRL elevation (no agency names)

Use `harness/trl/ladder.yaml`. Tests elevate TRL when linked evidence passes. Do not reference grant/incubator bodies — only test procedures and compliance mappings.

## Example: temperature limit change

1. User changes operating temperature requirement node
2. Run `impact_analysis.py --node req-thermal-op-limit --summary "Max op temp 45→50°C"`
3. Actions hit: thermal budget, material Q03-series process, bench F11/F18, DO-160 planning
4. Agent marks artifacts `revision_needed`, reopens tests, queues human review on material tradeoff
5. User approves material change → agent updates graph, re-ingests evidence CSVs

## Files

| Path | Purpose |
|------|---------|
| `harness/ARCHITECTURE.md` | Full design |
| `harness/config/sources.yaml` | External source registry |
| `harness/platforms/registry.yaml` | Platform interconnect |
| `harness/trl/ladder.yaml` | TRL gates |
| `harness/scripts/ingest.py` | Ingest pipeline |
| `harness/scripts/impact_analysis.py` | Change propagation |
| `harness/scripts/export_obsidian.py` | Obsidian export |
| `harness/scripts/bootstrap_hermes.py` | Seeds Hermes agents, services, CAD, and hosting graph nodes |
| `harness/scripts/overnight_health.py` | Read-only overnight guardrail and graph health report |
| `harness/scripts/memory_email_brief.py` | Draft/send today-yesterday-weekly memory briefing and to-do list |
