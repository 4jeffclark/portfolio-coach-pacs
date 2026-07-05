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
3. Check `Metrics.csv` for **`exposureQualityValid`**, **`exposureNumericSymbolCount`**, **`periodEndSnapshotLagDays`**, **`snapshotLagNotice`** (1–13 days), **`snapshotLagWarn`** (≥ 14 days)
4. If `exposureQualityValid` is **false**: do not embed exposure weight tables; attest data-quality failure per output contract
5. Merge all scaffold output into the delivered report file per `contracts/report-delivery-contract.md` and the playbook output contract; extend narrative where scaffold
6. For **portfolio linkage**, embed tables from `PortfolioLinkage.csv` and `Metrics.csv`. Rank exposure by **PeriodEndWeightPct** and activity by **PeriodGrossNotional**. Use **GrossNotionalPctOfTurnover** and **ActivityToWeightRatio** for coaching signals. Do not rank by `FilledOrderCount`

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
- `Metrics.csv` — period activity totals, snapshot metadata, exposure quality flags, turnover ratio
- `PortfolioLinkage.csv` — top symbols with period-end weight %, period notional, turnover share, activity/weight ratio, fill count (supplementary)
- `ReportSectionFragments.json` — assembly hints including `portfolio_linkage` and `skill_metrics_appendix` fragments

### Key metrics

| Metric | Meaning |
| --- | --- |
| `exposureQualityValid` | false when numeric-only symbols appear in exposure |
| `exposureNumericSymbolCount` | Count of invalid ticker tokens in exposure |
| `periodEndSnapshotLagDays` | Days from snapshot to analysis period end |
| `snapshotLagNotice` | true when lag is 1–13 days (informational; prefer aligned period end) |
| `snapshotLagWarn` | true when lag ≥ 14 days |
| `portfolioTurnoverRatio` | periodGrossTurnover / periodEndTotalMV |

Skill returns `status: warn` when exposure quality is invalid or snapshot lag exceeds threshold.

## Used by

See `layer3-playbooks/` manifests referencing this skill.
