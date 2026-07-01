# Market regime review report artifact contract

## Report folder pattern

```text
{userDatastore}/reports/<GenerationTimestamp>-MarketRegimeReview-<AnalysisStart>-<AnalysisEnd>/
```

## Required artifacts

| File | Role |
| --- | --- |
| `Report.md` | Self-contained market regime memo |
| `MarketResearch.md` | Extended market research (when `marketDepth: full`) |
| `Metrics.csv` | Summary metrics scaffold |

When `evaluation: true`, include judgment sections and `ExitInterview.md` per `market-regime-evaluation` overlay.

## Post-run verification

Self-verify per [APP post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
