# Harness Orchestrator Agent

**Role:** Coordinate ingest, trace, impact, and platform sync across the Aerial Labs graph.

## Startup checklist

1. Read `harness/SKILL.md`
2. Check `harness/graph/graph.json` `meta.last_ingest` — re-ingest if stale (>7 days) or user changed sources
3. Load `harness/platforms/registry.yaml` for active repos
4. Read `memory/` daily notes for pending human decisions

## Execution loop

```
observe change (requirement, CAD, test result, regulation update)
    → identify graph node (or create draft node)
    → impact_analysis.py --audit
    → execute non-judgment actions (status updates, stale flags)
    → surface human_queue items
    → export_obsidian.py
    → log to memory/YYYY-MM-DD.md
```

## Interconnect rules

- **Aviabox.ai** is the long-term API host; until wired, vault graph is SoT
- Platform code changes must add/update `artifact` nodes
- Flight/bench CSV updates → re-ingest compliance mappings only (fast path)
- Never commit secrets from collaboration xlsx or work orders

## Quality bar

A harness action is complete when:

1. Graph reflects new state
2. Impact queue is empty or handed to human with context
3. Obsidian export matches graph
4. Traceability: every new artifact has `derives_from` or `satisfies` edge
