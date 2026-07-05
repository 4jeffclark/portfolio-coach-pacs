---
name: portfolio-weights-table
compatibility: Requires Python 3.11+ when scripts are shipped
outputCompleteness: scaffold
description: "Primary weights table (start % to end %)."
metadata:
  packId: portfolio-coach
  layer: '1'
  migrationPhase: 'Phase 2'
  shipped: true
---

## Procedure

1. Run `scripts/run.py` with `--datastore` and `--workspace` (plus playbook-specific flags)
2. Read skill output CSVs and `ReportSectionFragments.json`
3. Merge all scaffold output into the delivered report file per `contracts/report-delivery-contract.md` and the playbook output contract; extend narrative where scaffold

## Scripts

```powershell
python scripts/run.py --datastore $env:USER_DATASTORE --workspace $env:AGENT_WORKSPACE --rollup-lens theme
```

When this skill runs in `portfolio-composition-review`, pass `--rollup-lens` matching the playbook `rollupLens` input. The skill writes `RollupLens.txt` for downstream lens-aware skills.

See skill module for additional flags (`--period-start`, `--rollup-lens`, `--symbol`, etc.).

## References

- `contracts/holdings-taxonomy.md` (when applicable)

## Outputs

TBD per legacy capability contract.

## Used by

See `layer3-playbooks/` manifests referencing this skill.
