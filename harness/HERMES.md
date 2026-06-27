# Hermes Integration Runbook

Hermes is the execution dispatcher wrapped around the Hermes Systems Harness graph. The vault graph remains the system of record; Hermes converts graph state into bounded work packets and writes results back as graph nodes, edges, audit JSON, and Obsidian notes.

## Runtime Split

| Runtime | Use | Boundary |
|---------|-----|----------|
| Local workstation | Canonical vault, CAD/sim context, Obsidian, local LLM | Full private engineering context stays here by default |
| Hostinger VPS | Always-on runner for sanitized checks, dashboards, simple APIs | No private raw sources unless explicitly approved |
| NVIDIA ecosystem | Candidate acceleration for simulation, digital twins, robotics/edge AI | Evaluate per workflow before moving data |
| Human | Architecture, tradeoffs, safety, certification, public/business decisions | Required for irreversible or external actions |

## Agent Loop

```text
read graph -> detect stale/review_required/revision_needed nodes
  -> create work packet
  -> execute allowed local action
  -> write audit/report
  -> export Obsidian
  -> queue human decisions
```

## Commands

```bash
python3 harness/scripts/bootstrap_hermes.py
python3 harness/scripts/overnight_health.py --write
python3 harness/scripts/memory_email_brief.py --write
python3 harness/scripts/export_obsidian.py
python3 harness/scripts/impact_analysis.py --node req-thermal-op-max --summary "Demo change" --audit
```

`./harness/scripts/sync.sh --force` refreshes ingest, Hermes seed nodes, and Obsidian export when local sources are configured.

## Approval Gates

Hermes agents may work while the human sleeps on read-only analysis, graph health, traceability checks, local summaries, draft test procedures, and impact audits.

Explicit approval is required before sending messages, posting publicly, buying/upgrading infrastructure, deploying production services, changing CAD source-of-record files, or submitting safety/certification evidence externally.

## Email Briefing Agent

`agent-email-briefing` compiles:

- today and yesterday memory file links or missing-file notices
- the newest weekly and overnight summaries
- a graph-derived to-do list from `review_required`, `stale`, `revision_needed`, and `blocked` nodes

Default command:

```bash
python3 harness/scripts/memory_email_brief.py --write
```

Send command after SMTP variables are configured:

```bash
python3 harness/scripts/memory_email_brief.py --send --yes
```

Or with a private env file copied from `harness/config/email.env.example`:

```bash
python3 harness/scripts/memory_email_brief.py --env-file harness/config/email.env --send --yes
```

Recipient defaults to `you@example.com`. Override with `HERMES_BRIEF_RECIPIENT` or `--recipient`.

## Program-Specific Seeds

Generic Hermes nodes ship in `bootstrap_hermes.py`. CAD assemblies, proprietary platform interconnects, and local artifact paths belong in `harness/local/bootstrap_extension.py` (gitignored). See `harness/local/README.example`.

## External References

- NVIDIA Inception: https://www.nvidia.com/en-us/startups/
- NVIDIA Developer Program: https://developer.nvidia.com/developer-program
- Hostinger VPS: https://www.hostinger.com/vps-hosting
