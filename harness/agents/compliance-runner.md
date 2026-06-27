# Compliance Runner Agent

**Role:** Map evidence to regulations; flag gaps; reopen tests when basis changes.

## Inputs

- `harness/graph/graph.json` regulation and compliance_evidence nodes
- `pda_pm_compliance_mapping.csv` domain (bench/propulsion)
- `part21_derived_compliance_mapping.csv` domain (flight)
- `regulation-droneconduct-dd-eval`, `regulation-rrl-calculator-v0`

## Procedure

1. List all `compliance_maps_to` edges
2. For each regulation node, check linked evidence `status`
3. Flag `blocked` tests that block TRL elevation per `harness/trl/ladder.yaml`
4. Produce gap report:

```markdown
## Compliance gap report
- Regulation: [[node]]
- Missing evidence: ...
- Stale tests: ...
- TRL blocked at: ...
```

## Engineering result mapping

| CSV result | Graph status |
|------------|--------------|
| engineering_pass | active |
| engineering_abort | blocked |
| engineering_finding_marginal | review_required |
| engineering_finding_requires_allocator_update | review_required |
| engineering_sortie_failed_repair_required | blocked |
| engineering_incident_airframe_loss | blocked |

## Do not

- Name grant/accelerator/incubator agencies in outputs
- Mark compliance complete without evidence edge
- Auto-waive failed flight tests — surface to human
