---
name: datastore-inventory
compatibility: Requires Python 3.11+ when running bundled scripts
description: Inventory and profile the bound user datastore for coverage, quality, and activity ranges. Use during source-profile playbook core output.
metadata:
  packId: portfolio-coach
  layer: '1'
---

## Procedure

### Step 1 — Inventory the datastore

Raw files by type, canonical tables, row counts, date ranges, account coverage, hashes, truncation risk, missing export types.

### Step 2 — Profile account coverage

Per account: activity ranges, latest snapshots, row counts, gaps, symmetry across accounts.

### Step 3 — Profile activity coverage

Orders, fills, notional by period, top symbols, account-history activity types, open positions.

### Step 4 — Profile cash and income history

Observed cash, account-history activity, estimated cash curves; document confidence layers.

### Step 5 — Profile derived data quality

Normalization, parsing quality, duplicate detection, provenance; label Observed / Derived / Estimated / Low Confidence.

## Scripts

Run from this skill directory. Paths are relative to the skill root per [agentskills.io](https://agentskills.io/specification).

| Script | Purpose |
| --- | --- |
| `scripts/run.py` | Execute skill logic; writes workspace artifacts and `skill-result.json` |

```bash
python scripts/run.py --datastore "$USER_DATASTORE" --workspace "$AGENT_WORKSPACE"
```

Set `compatibility: Requires Python 3.11+` when the runtime must execute bundled scripts.

## References

None.

## Outputs

- `DataStoreInventory.csv`, `AccountCoverage.csv`, `Metrics.csv`
- Report quantification sections 1–5

## Used by

- `layer3-playbooks/source-profile`