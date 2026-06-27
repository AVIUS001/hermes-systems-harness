# Local setup

Get a working Hermes Systems Harness vault after cloning the public repository.

## 1. Clone and initialize

```bash
git clone <repo-url> my-harness-vault
cd my-harness-vault
./harness/scripts/init_local.sh
```

`init_local.sh` creates gitignored local files from public examples:

- `harness/config/sources.yaml` ← `sources.yaml.example`
- `harness/platforms/registry.yaml` ← `registry.yaml.example`
- `harness/config/email.env` ← `email.env.example` (optional)
- `harness/graph/graph.json` ← `graph.sample.json`
- `memory/.gitkeep`

## 2. Personal agent context (optional)

```bash
cp USER.example.md USER.md
cp TOOLS.example.md TOOLS.md
```

Edit these with your name, program, and **local machine paths**. They are gitignored and never published.

## 3. Configure ingest paths

Edit `harness/config/sources.yaml`:

- `sources.processes.path` — process standards library
- `sources.work_orders.path` — test/quality procedures
- `sources.collaborations.path` — collaboration spreadsheets
- `sources.regulations` — due diligence / RRL workbooks
- `sources.compliance_mappings` — bench and flight CSV mappings
- `sync.obsidian_symlink` — optional symlink for Obsidian export (local only)
- `sync.watch_paths` — optional explicit fingerprint list (defaults derived from sources)

Edit `harness/platforms/registry.yaml` with your platform repo paths and organization IDs.

**Do not commit** `sources.yaml` or `registry.yaml`.

## 4. Program-specific Hermes seeds (optional)

For proprietary CAD assemblies, platform interconnects, and local artifact paths:

```bash
cp harness/local/README.example harness/local/README.md   # optional notes
# bootstrap_extension.py already lives locally if you copied from a private fork;
# otherwise create harness/local/bootstrap_extension.py with a seed(g) function.
```

See `harness/local/README.example`. The directory is gitignored except the example README.

## 5. Run the harness

```bash
python3 harness/scripts/bootstrap_hermes.py
python3 harness/scripts/ingest.py          # after sources.yaml is filled in
python3 harness/scripts/export_obsidian.py
./harness/scripts/sync.sh --force          # ingest + Hermes + export pipeline
```

## 6. Verify before publishing

Simulate what would be committed, then scan for leaks:

```bash
git add -n .
./harness/scripts/verify_public_safe.sh
```

Fix any reported leaks before `git push`.

## Email briefings

```bash
export HERMES_BRIEF_RECIPIENT=you@example.com
python3 harness/scripts/memory_email_brief.py --write
```

Configure SMTP in `harness/config/email.env` before using `--send --yes`.
