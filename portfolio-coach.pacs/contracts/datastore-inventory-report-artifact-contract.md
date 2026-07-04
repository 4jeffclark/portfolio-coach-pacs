# Datastore inventory report artifact contract

See [`report-delivery-contract.md`](report-delivery-contract.md) for delivery rules.

## Report folder pattern

```text
{userDatastore}/reports/<ReportBasename>/
```

| Token | Format |
| --- | --- |
| `ReportBasename` | `<GenerationTimestamp>-DatastoreInventory-<AnalysisStart>-<AnalysisEnd>` |
| `GenerationTimestamp` | `YYYYMMDD-HHMMSS` |
| `AnalysisStart` / `AnalysisEnd` | `YYYYMMDD` |

Example folder and delivered file:

```text
{userDatastore}/reports/20260623-143052-DatastoreInventory-20260501-20260531/
  20260623-143052-DatastoreInventory-20260501-20260531.md
```

## Delivered artifact

| File | Role |
| --- | --- |
| `<ReportBasename>.md` | Self-contained human-readable run output |

## Assembly inputs (workspace only)

Merge into the delivered file; do not copy to the report folder:

- `DataStoreInventory.csv`, `AccountCoverage.csv`, `Metrics.csv`, `RawManifestDrift.csv`
- `ReportSectionFragments.json`
- When `evaluation: true`: scorecard and exit-interview scaffold content from evaluation skills

## Delivered report — minimum sections

1. **Datastore inventory** — fragment section1 + inventory quantification (embed key `DataStoreInventory.csv` rows)
2. **Account coverage** — fragment section2 + per-account table (embed `AccountCoverage.csv`)
3. **Activity coverage** — fragment section3; extend from canonical tables
4. **Cash and income history** — fragment section4; label confidence layers
5. **Derived data quality** — fragment section5 + metrics; manifest drift summary and drift rows when detected (embed `RawManifestDrift.csv` when non-empty)
6. **Appendix: Inputs Resolved** — final resolved playbook inputs
7. **Evaluation** — when `evaluation: true`; include scorecard and exit-interview content formerly in separate markdown files

Core skill outputs are **scaffold**; the agent synthesizes narrative using fragments, embedded tables, and canonical queries.

## Post-run verification

Self-verify per [PACS post-run checklist](https://github.com/4jeffclark/pacs-workbench/blob/main/standard/post-run-checklist.md).
