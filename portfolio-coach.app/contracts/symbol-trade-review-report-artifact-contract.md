# Symbol trade review report artifact contract

See [`report-delivery-contract.md`](report-delivery-contract.md) for delivery rules.

## Report folder pattern

```text
{userDatastore}/reports/<ReportBasename>/
```

| Token | Format |
| --- | --- |
| `ReportBasename` | `<GenerationTimestamp>-SymbolTradeReview-<AnalysisStart>-<AnalysisEnd>` |

## Delivered artifact

| File | Role |
| --- | --- |
| `<ReportBasename>.md` | Symbol-scoped trade/position decision review |

## Assembly inputs (workspace only)

Merge into the delivered file:

- `Metrics.csv` and skill fragments from symbol analysis, stale hygiene, event context, and `market-environment` as applicable
- When `evaluation: true`: entry interview, exit interview, trade scorecard, and verdict scaffold content

## Delivered report — minimum sections

Symbol forensic timeline or hygiene/event findings per `reviewFocus`, embedded market context, resolved `targetSymbol` in header metadata, evaluation/interview appendices when `evaluation: true`.

## Post-run verification

Self-verify per [APP post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
