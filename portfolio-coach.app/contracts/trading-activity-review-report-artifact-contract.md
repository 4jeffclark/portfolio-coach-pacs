# Trading activity review report artifact contract

## Report folder pattern

```text
{userDatastore}/reports/<GenerationTimestamp>-TradingActivityReview-<AnalysisStart>-<AnalysisEnd>/
```

## Required artifacts

| File | Role |
| --- | --- |
| `Report.md` | Trading activity debrief |
| `Metrics.csv` | Activity metrics from `trading-activity-analysis` skill |

When `evaluation: true`, also include `Interview.md`, `ExitInterview.md`, and activity scorecard sections.

## Post-run verification

Self-verify per [APP post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
