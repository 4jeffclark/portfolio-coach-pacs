# Trading activity review report artifact contract

See [`report-delivery-contract.md`](report-delivery-contract.md) for delivery rules.

## Report folder pattern

```text
{userDatastore}/reports/<ReportBasename>/
```

| Token | Format |
| --- | --- |
| `ReportBasename` | `<GenerationTimestamp>-TradingActivityReview-<AnalysisStart>-<AnalysisEnd>` |

## Delivered artifact

| File | Role |
| --- | --- |
| `<ReportBasename>.md` | Trading activity debrief |

## Assembly inputs (workspace only)

Merge into the delivered file:

- `Metrics.csv` and skill fragments from `trading-activity-analysis` and `market-environment`
- When `evaluation: true`: entry interview, exit interview, and activity scorecard scaffold content

## Delivered report — minimum sections

Period trading-activity metrics and debrief, embedded market context, evaluation/interview appendices when `evaluation: true`.

## Post-run verification

Self-verify per [APP post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
