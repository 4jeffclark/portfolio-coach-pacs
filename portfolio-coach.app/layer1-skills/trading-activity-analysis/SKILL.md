---
name: trading-activity-analysis
compatibility: Requires Python 3.11+ when scripts are shipped
outputCompleteness: scaffold
description: "Day/week trading activity metrics for trading-activity-review."
metadata:
  packId: portfolio-coach
  layer: '1'
  migrationPhase: 'Phase 1'
  shipped: true
---

## Procedure

1. Run `scripts/run.py` with `--datastore` and `--workspace` (plus playbook-specific flags)
2. Read skill output CSVs and `ReportSectionFragments.json`
3. Merge fragments into `Report.md` per report contract; extend narrative where scaffold

## Scripts

```powershell
python scripts/run.py --datastore $env:USER_DATASTORE --workspace $env:AGENT_WORKSPACE
```

See skill module for additional flags (`--period-start`, `--rollup-lens`, `--symbol`, etc.).

## References

- `contracts/holdings-taxonomy.md` (when applicable)

## Outputs

TBD per legacy capability contract.

## Used by

See `layer3-playbooks/` manifests referencing this skill.
