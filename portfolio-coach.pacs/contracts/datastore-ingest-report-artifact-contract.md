# Datastore ingest report artifact contract

See [`report-delivery-contract.md`](report-delivery-contract.md) for delivery rules.

## Report folder pattern

```text
{userDatastore}/reports/<ReportBasename>/
```

| Token | Format |
| --- | --- |
| `ReportBasename` | `<GenerationTimestamp>-DatastoreIngest-<AnalysisStart>-<AnalysisEnd>` |

## Delivered artifact

| File | Role |
| --- | --- |
| `<ReportBasename>.md` | Ingest and validation summary |

## Assembly inputs (workspace only)

Merge into the delivered file:

- `MergeLog.csv`, `Metrics.csv`, `ReportSectionFragments.json`

## Delivered report — minimum sections

1. **Datastore layout** — resolved layout and path warnings
2. **Session attachments** — per-file staging outcomes (embed `MergeLog.csv`)
3. **Canonical validation** — readability and validation outcomes (embed `Metrics.csv` flags)
4. **Rebuild changelog** — when `portfolioSymbolCountDelta` ≠ 0, explain symbol-universe and position-row before/after counts (lot-detail ingest fixes may reduce inflated universes)
5. **Available date range** — summary for downstream playbooks
6. **Appendix: Inputs Resolved** — final resolved playbook inputs

## Post-run verification

Self-verify per [PACS post-run checklist](https://github.com/4jeffclark/pacs-workbench/blob/main/standard/post-run-checklist.md).
