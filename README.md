# Hermes Systems Harness

Open-source **agentic systems engineering harness**: requirements, tests, artifacts, and compliance evidence as an explicit graph with change propagation, Hermes execution agents, and Obsidian export.

[![G-Stack](https://img.shields.io/badge/G--Stack-ready-blue)](https://github.com)

This repository publishes the **framework** and a **sample graph** (`harness/graph/graph.sample.json`). Your private program data, full graph, memory files, and local paths stay **outside** the public boundary — see [docs/SETUP.md](docs/SETUP.md).

## What you get

- **Graph-native engineering** — nodes and edges, not tribal knowledge
- **Impact analysis** — propagate requirement changes across budgets, tests, and artifacts
- **Hermes agents** — bounded overnight work with human approval gates
- **Obsidian export** — human-navigable `graph/` from `graph.json`
- **G-Stack compatible** — use global G-Stack skills for QA/review/ship on your platform repos

## Quick start (demo, no private sources)

```bash
git clone <this-repo> my-harness-vault
cd my-harness-vault
./harness/scripts/init_local.sh

# Try impact analysis on the sample thermal scenario
python3 harness/scripts/impact_analysis.py \
  --node req-thermal-op-max \
  --summary "Max op temp 45→50°C" \
  --audit
```

See [harness/examples/thermal-change-propagation.md](harness/examples/thermal-change-propagation.md) for the walkthrough.

## Private vault boundary

| Public (this repo) | Private (gitignored, local only) |
|--------------------|----------------------------------|
| `harness/graph/graph.sample.json` | `harness/graph/graph.json` |
| `*.example` configs | `sources.yaml`, `registry.yaml`, `email.env` |
| Generic `bootstrap_hermes.py` | `harness/local/bootstrap_extension.py` |
| `USER.example.md`, `TOOLS.example.md` | `USER.md`, `TOOLS.md`, `MEMORY.md`, `memory/` |

Before pushing to GitHub, run:

```bash
./harness/scripts/verify_public_safe.sh
```

## Documentation

| Path | Purpose |
|------|---------|
| [docs/SETUP.md](docs/SETUP.md) | Clone, init, configure local paths |
| [harness/README.md](harness/README.md) | Harness commands and architecture |
| [harness/SKILL.md](harness/SKILL.md) | Agent operating procedures |
| [harness/HERMES.md](harness/HERMES.md) | Hermes runbook |
| [SECURITY.md](SECURITY.md) | Security policy |

## License

See [LICENSE](LICENSE).
