---
name: datastore-ingest
compatibility: Requires Python 3.11+ when running bundled scripts
outputCompleteness: scaffold
description: Stage session exports, rebuild canonical E*TRADE tables, and validate merged datastore.
metadata:
  packId: portfolio-coach
  layer: '1'
---

## Procedure

1. Run `scripts/run.py` with `--datastore` and `--workspace`
2. Read `MergeLog.csv`, `Metrics.csv`, and `ReportSectionFragments.json`
3. Merge section fragments into `Report.md` per `contracts/datastore-ingest-report-artifact-contract.md`

## Scripts

```powershell
python scripts/run.py --datastore $env:USER_DATASTORE --workspace $env:AGENT_WORKSPACE
```

## References

- `contracts/datastore-contract.md` — merge and rebuild rules

## Outputs

- `MergeLog.csv` — staging outcomes for `inputs/` attachments
- `Metrics.csv` — rebuild and validation summary
- `ReportSectionFragments.json` — scaffold text for ingest report sections

## Used by

- `layer3-playbooks/datastore-ingest`
