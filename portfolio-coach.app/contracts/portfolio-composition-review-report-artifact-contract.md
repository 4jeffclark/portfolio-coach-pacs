# Portfolio composition review report artifact contract

See [`report-delivery-contract.md`](report-delivery-contract.md) for delivery rules.

## Report folder pattern

```text
{userDatastore}/reports/<ReportBasename>/
```

| Token | Format |
| --- | --- |
| `ReportBasename` | `<GenerationTimestamp>-PortfolioCompositionReview-<AnalysisStart>-<AnalysisEnd>` |

## Delivered artifact

| File | Role |
| --- | --- |
| `<ReportBasename>.md` | Portfolio composition and change narrative |

## Assembly inputs (workspace only)

Merge into the delivered file:

- `HoldingsMap.csv`, `Metrics.csv`, `LiquidityBreakdown.csv`
- Lens-specific CSVs per [`holdings-taxonomy.md`](holdings-taxonomy.md):
  - `rollupLens: theme` — `ThemeRegistry.csv`, `ThemeMap.csv`
  - `rollupLens: thesis` — above plus `ThesisRegistry.csv`, `ThesisAssignment.csv`
- Primary weights table from `portfolio-weights-table` skill
- Skill `ReportSectionFragments.json` outputs from composition skills
- When `evaluation: true`: entry interview, exit interview, and scorecard scaffold content
- When `rebalancingReview: true` or `riskReview: true`: overlay enrichment fragments

## Delivered report — minimum sections

Embed all quantitative tables from assembly CSVs. Include composition narrative, weights, flows, thesis health, evolution, liquidity, concentration, embedded market context, overlay sections when enabled, and evaluation/interview appendices when `evaluation: true`.

## Post-run verification

Self-verify per [APP post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
