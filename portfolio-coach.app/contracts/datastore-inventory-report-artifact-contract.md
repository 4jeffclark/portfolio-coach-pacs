# Datastore inventory report artifact contract

## Report folder pattern

```text
{userDatastore}/reports/<GenerationTimestamp>-DatastoreInventory-<AnalysisStart>-<AnalysisEnd>/
```

| Token | Format |
| --- | --- |
| `GenerationTimestamp` | `YYYYMMDD-HHMMSS` (wall-clock at folder creation) |
| `PlaybookReportId` | `DatastoreInventory` |
| `AnalysisStart` / `AnalysisEnd` | `YYYYMMDD` |

Example:

```text
{userDatastore}/reports/20260623-143052-DatastoreInventory-20260501-20260531/
```

### Timestamp rules

- Use actual generation time — no placeholders.
- Never overwrite an existing folder; create a new timestamp if the path exists.

## Required artifacts

| File | Role |
| --- | --- |
| `Report.md` | Self-contained human-readable run output |
| `DataStoreInventory.csv` | Datastore inventory tables (from core skill) |
| `AccountCoverage.csv` | Account coverage profile |
| `Metrics.csv` | Summary metrics |
| `RawManifestDrift.csv` | Manifest vs on-disk raw drift rows (empty when aligned) |
| `ReportSectionFragments.json` | Scaffold section text from core skill (agent merges into Report.md) |

When `evaluation: true`, also include evaluation artifacts per the overlay and skill outputs (`ExitInterview.md`, `DatastoreInventoryScorecard.md`).

## Report.md

Minimum sections:

1. **Datastore inventory** — merge `ReportSectionFragments.json` section1 and CSV quantification from `datastore-inventory` skill
2. **Account coverage** — section2 fragment + `AccountCoverage.csv`
3. **Activity coverage** — section3 fragment; agent may extend from canonical tables
4. **Cash and income history** — section4 fragment; label confidence layers in narrative
5. **Derived data quality** — section5 fragment + `Metrics.csv`; include manifest drift summary and `RawManifestDrift.csv` when drift is detected
6. **Appendix: Inputs Resolved** — final resolved playbook inputs
7. **Evaluation** — present only when `evaluation: true` (overlay)

Core skill outputs are **scaffold** (`outputCompleteness: scaffold`); the agent synthesizes narrative using fragments, CSVs, and canonical queries.

## Post-run verification

Self-verify per [APP post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
