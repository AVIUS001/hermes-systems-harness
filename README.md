# Building an Engineering Command Center

![Engineering Command Center](docs/assets/engineering-command-center.jpg)

I'm thrilled to share a major milestone in how I run Aerial MECHANICA. After weeks of testing and iteration, I've built a living engineering command center — not just another folder of notes, but a connected graph that treats every part of our aerial technologies, websites, CAD models, test data, regulations, and business plans as one intelligent system.

The simple idea: **The graph is the map. Hermes is the dispatcher. Agents are the workers. I remain the chief engineer setting priorities and making tradeoffs.**

Think of Aerial Labs like a biological body — or in our case, a complex aircraft. A single change (e.g., "make this aircraft carry more weight") ripples across:

- CAD geometry  
- Motor sizing & interfaces  
- Battery/power & thermal budgets  
- Test plans  
- Compliance evidence  
- Website claims and investor messaging  

Previously, I carried those interconnections in my head. Now the vault calculates the impact for me.

### Core Mental Model
Requirements → CAD → Interfaces → Budgets → Tests → Compliance → Business artifacts.  

Hermes scans the graph and asks:  
**What changed? What does it touch? What needs review? What can agents handle? What requires my judgment?**

### My Daily Workflow
1. **Morning Brief**  
   Open the latest dashboard from `harness/outbox`. It summarizes yesterday's activity, weekly highlights, blockers, CAD/test items needing attention, and more.  
   One command:  
   `python3 harness/scripts/memory_email_brief.py --write`  
   Then send it to email/calendar.

2. **Graph Health Check**  
   `python3 harness/scripts/overnight_health.py --write`  
   This system inspection flags broken links, stale requirements, missing files, budgets needing recomputation, and more.

3. **Sync & Refresh**  
   `./harness/scripts/sync.sh --force`  
   Re-ingests sources, refreshes the Hermes graph, and exports an Obsidian-readable systems map.

4. **Impact Analysis on Changes**  
   When updating a requirement:  
   `python3 harness/scripts/impact_analysis.py --node ... --summary "Updated CAD revision..." --audit`  
   The system tells me exactly what else needs attention — reopen tests, revise budgets, review interfaces, etc.

5. **Work from the To-Do List, Not Memory**  
   Current focus areas (CAD assemblies, mass/thermal/power budgets, flight test blocks, compliance, traceability) are surfaced clearly. The system flags weak links before we scale automation.

A normal day now flows like this:  
**Morning** — Review the Hermes brief and pick 1-3 priorities.  
**Midday** — Deep work on Fusion 360, simulators, requirements, or test data, then link updates.  
**Afternoon** — Run impact analysis; agents handle mechanical fixes while I own safety, certification, and strategic decisions.  
**Evening** — Overnight health + brief snapshot.

I'm building aircraft, drones, and aviation software with thousands of interconnected details. In the past, inconsistency across staff, clients, and partners has been called out — and I'm hell-bent on fixing that. This vault turns the entire company into a smart, traceable map. Every requirement, model, test, regulation, and artifact becomes a node with clear cause-and-effect links.

**The Rule Going Forward:**  
Never treat files as isolated. Every important artifact must be a node in the graph — linked to what caused it and what it affects.

This setup, powered by Obsidian, Hermes, Karpathy-inspired knowledge base practices, Garry Tan's GStack thinking, Google Gemma, and Hostinger infrastructure, is already transforming how I engineer. It keeps me focused on high-judgment decisions while the system maintains consistency at scale.

---

Open-source **agentic systems engineering harness**: requirements, tests, artifacts, and compliance evidence as an explicit graph with change propagation, Hermes execution agents, and Obsidian export.

[![G-Stack](https://img.shields.io/badge/G--Stack-ready-blue)](https://github.com)

This repository publishes the **framework** and a **sample graph** (`harness/graph/graph.sample.json`). Your private program data, full graph, memory files, and local paths stay **outside** the public boundary — see [docs/SETUP.md](docs/SETUP.md).

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
| [docs/ENGINEERING_COMMAND_CENTER.md](docs/ENGINEERING_COMMAND_CENTER.md) | Narrative: graph-as-map, Hermes dispatcher, daily workflow |
| [docs/SETUP.md](docs/SETUP.md) | Clone, init, configure local paths |
| [harness/README.md](harness/README.md) | Harness commands and architecture |
| [harness/SKILL.md](harness/SKILL.md) | Agent operating procedures |
| [harness/HERMES.md](harness/HERMES.md) | Hermes runbook |
| [SECURITY.md](SECURITY.md) | Security policy |

## License

See [LICENSE](LICENSE).
