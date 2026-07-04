---
name: holdings-map-confirmation
compatibility: Requires Python 3.11+ when scripts are shipped
outputCompleteness: scaffold
description: "Agent-only holdings map confirmation interact."
metadata:
  packId: portfolio-coach
  layer: '1'
  migrationPhase: 'Phase 2'
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
