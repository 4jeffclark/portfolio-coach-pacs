# Portfolio composition review report artifact contract

## Report folder pattern

```text
{userDatastore}/reports/<GenerationTimestamp>-PortfolioCompositionReview-<AnalysisStart>-<AnalysisEnd>/
```

## Required artifacts

| File | Role |
| --- | --- |
| `Report.md` | Portfolio composition and change narrative |
| `HoldingsMap.csv` | Confirmed holdings classifications |
| `Metrics.csv` | Summary metrics |
| `LiquidityBreakdown.csv` | Liquidity slice breakdown |

Lens-specific artifacts per [`holdings-taxonomy.md`](holdings-taxonomy.md):

- `rollupLens: theme` — `ThemeRegistry.csv`, `ThemeMap.csv`
- `rollupLens: thesis` — above plus `ThesisRegistry.csv`, `ThesisAssignment.csv`

Primary weights table artifact from `portfolio-weights-table` skill (filename TBD at implementation).

When `evaluation: true`, include `Interview.md`, `ExitInterview.md`, and evaluation scorecard sections.

When `rebalancingReview: true` or `riskReview: true`, include overlay enrichment sections per overlay contracts.

## Post-run verification

Self-verify per [PACS post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
