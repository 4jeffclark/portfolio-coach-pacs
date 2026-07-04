---
name: market-environment
compatibility: Requires Python 3.11+ when scripts are shipped
outputCompleteness: scaffold
description: "Market regime memo scaffold for market-regime-review and embeds."
metadata:
  packId: portfolio-coach
  layer: '1'
  migrationPhase: 'Phase 1'
  shipped: true
---

## Procedure

1. Run `scripts/run.py` with `--datastore` and `--workspace` (plus playbook-specific flags)
2. Read skill output CSVs and `ReportSectionFragments.json`
3. Merge all scaffold output into the delivered report file per `contracts/report-delivery-contract.md` and the playbook output contract; extend narrative where scaffold
4. For **portfolio linkage**, embed tables from `PortfolioLinkage.csv` and `Metrics.csv`. Rank exposure by **PeriodEndWeightPct** and activity by **PeriodGrossNotional**. Do not rank by `FilledOrderCount` or infer conviction from order count

## Scripts

```powershell
python scripts/run.py --datastore $env:USER_DATASTORE --workspace $env:AGENT_WORKSPACE --period-start $PERIOD_START --period-end $PERIOD_END --market-depth full
```

See skill module for additional flags (`--rollup-lens`, `--symbol`, etc.).

## References

- `contracts/holdings-taxonomy.md` (when applicable)
- `contracts/market-regime-review-report-artifact-contract.md` (portfolio linkage assembly rules)

## Outputs

Assembly-only under `{agentWorkspace}` (merge into delivered report; see `contracts/market-regime-review-report-artifact-contract.md`):

- `MarketResearch.md` — research scaffold sections
- `Metrics.csv` — period activity totals, snapshot metadata, symbol count
- `PortfolioLinkage.csv` — top symbols with period-end weight %, period buy/sell/gross notional, and fill count (count is supplementary only)
- `ReportSectionFragments.json` — assembly hints including `portfolio_linkage` fragment

## Used by

See `layer3-playbooks/` manifests referencing this skill.
