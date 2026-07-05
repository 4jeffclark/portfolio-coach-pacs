---
name: theme-map-inference
compatibility: Requires Python 3.11+ when scripts are shipped
outputCompleteness: scaffold
description: "Position-aware theme registry and map inference when rollupLens is theme or thesis."
metadata:
  packId: portfolio-coach
  layer: '1'
  migrationPhase: 'Phase 2'
  shipped: true
---

## Procedure

1. Run `scripts/run.py` with `--datastore` and `--workspace` after `holdings-map-confirmation`
2. Skill loads `HoldingsMap.csv`, period-end positions for MV weighting, and optional `knowledge/themes/ThemeMapCurrent.csv`
3. Read `ThemeRegistry.csv`, `ThemeMap.csv`, `ThemeCoverage.csv`, `InferenceLog.csv`, and `Metrics.csv`
4. Merge scaffold output into the delivered report file per output contract

## Scripts

```powershell
python scripts/run.py --datastore $env:USER_DATASTORE --workspace $env:AGENT_WORKSPACE --period-start $PERIOD_START --period-end $PERIOD_END
```

## References

- `contracts/holdings-taxonomy.md`
- `assets/theme-rules/` — sector and symbol override tables
- `assets/reference/` — ETF and equity GICS seed catalogs

## Outputs

Assembly-only under `{agentWorkspace}`:

- `ThemeRegistry.csv`, `ThemeMap.csv`
- `ThemeCoverage.csv` — theme-level MV weights
- `InferenceLog.csv` — per-symbol rule provenance
- `Metrics.csv` — `themeCount`, `unassignedWeightPct`, `inferenceCoveragePct`

## Used by

`portfolio-composition-review` when `rollupLens` in `[theme, thesis]`
