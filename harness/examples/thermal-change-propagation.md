# Example: Operating temperature limit change

Demonstrates how the harness propagates a cross-domain change.

## Scenario

Max operating temperature revised from 45°C → 50°C on electric propulsion inverter.

## Graph nodes (to create or identify)

| ID | Type | Title |
|----|------|-------|
| `req-thermal-op-max` | requirement | Max operating temperature 50°C |
| `budget-thermal-inverter` | budget | Inverter thermal margin |
| `process-q03004-finish` | process | Standard finish requirements |
| `test-ic2e-bench-f11` | test_procedure | Inner flow cooling bench |
| `regulation-tcca-awm-523-1041` | regulation | Cooling tests AWM 523.1041 |
| `artifact-ringwing76-config` | artifact | ringWing76.json sim config |

## Explicit `affects` edges to add

```
req-thermal-op-max → budget-thermal-inverter
req-thermal-op-max → process-q03004-finish (material/coating)
req-thermal-op-max → test-ic2e-bench-f11
req-thermal-op-max → regulation-tcca-awm-523-1041
req-thermal-op-max → artifact-ringwing76-config
```

Add edges with `harness/scripts/add_edge.py` or edit `graph.json`, then:

```bash
python3 harness/scripts/impact_analysis.py \
  --node req-thermal-op-max \
  --summary "Max op temp 45→50°C" \
  --audit
```

## Expected actions

1. `recompute_budget` on thermal budget
2. `mark_icd_stale` on finish process
3. `reopen_test` on bench F11
4. `re_run_compliance_check` on AWM 523.1041
5. `mark_revision_needed` on sim config
6. `surface_for_human_judgment` if material tradeoff affects mass/cert cost

Human approves material → agent updates graph statuses and re-ingests bench CSV.
