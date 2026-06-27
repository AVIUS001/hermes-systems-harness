# TOOLS.example.md — copy to TOOLS.md (gitignored)

## Agentic Harness

- **Vault:** `/path/to/your/My-Knowledge-Base-Vault`
- **Graph SoT:** `harness/graph/graph.json`
- **Obsidian graph:** `graph/` (open as vault folder or subfolder)
- **Skill:** `harness/SKILL.md`

### Commands

```bash
./harness/scripts/init_local.sh
./harness/scripts/sync.sh              # auto sync when sources configured
./harness/scripts/sync.sh --force      # force full rebuild
python3 harness/scripts/impact_analysis.py --node <id> --summary "..." --audit
python3 harness/scripts/bootstrap_hermes.py
python3 harness/scripts/overnight_health.py --write
python3 harness/scripts/memory_email_brief.py --write
```

### Local config (never commit)

| File | Purpose |
|------|---------|
| `harness/config/sources.yaml` | Ingest paths |
| `harness/platforms/registry.yaml` | Platform repo paths |
| `harness/config/email.env` | SMTP credentials |
| `harness/local/bootstrap_extension.py` | Program-specific Hermes seeds |

## Platform paths

Fill in from `harness/platforms/registry.yaml` after local init.

## G-Stack

Global skills at `~/.claude/skills/gstack` (or your G-Stack install). Use for QA/review/ship on platform repos after graph updates.

## Hermes / Overnight Ops

- **Config:** `harness/config/hermes.yaml`
- **Runbook:** `harness/HERMES.md`
- **Email outbox:** `harness/outbox/`
- **Default boundary:** local read/analyze/export only

```bash
export HERMES_BRIEF_RECIPIENT=you@example.com
python3 harness/scripts/memory_email_brief.py --write
python3 harness/scripts/memory_email_brief.py --env-file harness/config/email.env --send --yes
```
