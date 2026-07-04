# Symbol trade review report artifact contract

## Report folder pattern

```text
{userDatastore}/reports/<GenerationTimestamp>-SymbolTradeReview-<AnalysisStart>-<AnalysisEnd>/
```

## Required artifacts

| File | Role |
| --- | --- |
| `Report.md` | Symbol-scoped trade/position decision review |
| `Metrics.csv` | Symbol analysis metrics |

When `evaluation: true`, also include `Interview.md`, `ExitInterview.md`, trade scorecard, and verdict sections.

## Post-run verification

Self-verify per [PACS post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
