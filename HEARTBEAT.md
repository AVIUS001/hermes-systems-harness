# HEARTBEAT.md

## Harness checks (rotate)

- [ ] Run `./harness/scripts/sync.sh` if any watch path changed (overleaf, Excel, CSV, work orders)
- [ ] `harness/state/sync-state.json` — last_sync recent?
- [ ] Nodes with `status: blocked` or `review_required` needing human?
- [ ] Platform paths in `registry.yaml` still exist?

If nothing needs attention: `HEARTBEAT_OK`
