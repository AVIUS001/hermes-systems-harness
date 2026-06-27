# Security Policy

## Supported versions

Security fixes apply to the latest commit on the default branch.

## Reporting a vulnerability

Do **not** open a public GitHub issue for security-sensitive findings.

Email **security@aerial-labs.ca** with:

- Description of the issue
- Steps to reproduce
- Impact assessment (if known)

We aim to acknowledge reports within 5 business days.

## What must never be committed

This repository is designed as an **open framework**. The following must stay local and gitignored:

| Category | Examples |
|----------|----------|
| Credentials | SMTP passwords, API keys, tokens, `.env` files |
| Personal data | Private emails, home directory paths, daily memory logs |
| Proprietary engineering | Full `graph.json` ingest, compliance CSV exports, work orders, CAD-linked graph slices |
| Operational artifacts | Email outbox drafts, sync state, overnight health logs |

Before pushing, run:

```bash
./harness/scripts/verify_public_safe.sh
```

## Safe defaults

- Email briefing: draft-only unless SMTP env vars and `--send --yes` are explicitly set
- Hermes agents: local read/analyze/export; external actions require human approval
- Ingest: reads only paths you configure in private `sources.yaml`

## Accidental exposure

If secrets or proprietary data were pushed:

1. Rotate all exposed credentials immediately
2. Remove the data from git history (not just the latest commit)
3. Notify security@aerial-labs.ca if the exposure included credentials
