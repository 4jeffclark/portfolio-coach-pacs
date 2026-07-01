---
name: datastore-inventory
compatibility: Requires Python 3.11+ when running bundled scripts
outputCompleteness: scaffold
description: Inventory the bound user datastore for coverage, quality, and activity ranges. Core output for datastore-inventory playbook.
metadata:
  packId: portfolio-coach
  layer: '1'
---

## Procedure

1. Run `scripts/run.py` with `--datastore` and `--workspace`
2. Read `DataStoreInventory.csv`, `AccountCoverage.csv`, `Metrics.csv`, and `ReportSectionFragments.json`
3. Merge section fragments into `Report.md` per report contract; extend narrative from canonical tables where fragments are scaffold text

### Report sections (agent merges fragments + CSVs)

1. Inventory the datastore
2. Profile account coverage
3. Profile activity coverage
4. Profile cash and income history
5. Profile derived data quality

## Scripts

Run from this skill directory. Paths are relative to the skill root per [agentskills.io](https://agentskills.io/specification).

| Script | Purpose |
| --- | --- |
| `scripts/run.py` | Execute skill logic; writes workspace artifacts and `skill-result.json` |

```bash
python scripts/run.py --datastore "$USER_DATASTORE" --workspace "$AGENT_WORKSPACE"
```

```powershell
python scripts/run.py --datastore $env:USER_DATASTORE --workspace $env:AGENT_WORKSPACE
```

Pass `--workspace` as the platform's per-run subdirectory when available (`runs/<timestamp>-DatastoreInventory/`).

## References

- `contracts/datastore-contract.md` — canonical schemas and date columns

## Outputs

- `DataStoreInventory.csv`, `AccountCoverage.csv`, `Metrics.csv`
- `ReportSectionFragments.json` — scaffold text for report sections 1–5

## Used by

- `layer3-playbooks/datastore-inventory`
