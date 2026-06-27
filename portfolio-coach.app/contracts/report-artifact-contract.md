# Report output contract

## Report folder pattern

```text
{userDatastore}/reports/<GenerationTimestamp>-<PlaybookReportId>-<AnalysisStart>-<AnalysisEnd>/
```

| Token | Format |
| --- | --- |
| `GenerationTimestamp` | `YYYYMMDD-HHMMSS` (wall-clock at folder creation) |
| `PlaybookReportId` | `SourceProfile` |
| `AnalysisStart` / `AnalysisEnd` | `YYYYMMDD` |

Example:

```text
{userDatastore}/reports/20260623-143052-SourceProfile-20260501-20260531/
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

When `evaluation: true`, also include evaluation artifacts per the overlay and skill outputs (`ExitInterview.md`, `SourceProfileScorecard.md`).

## Report.md

Minimum sections:

1. **Datastore inventory** — core output from `datastore-inventory` skill
2. **Appendix: Inputs Resolved** — final resolved playbook inputs
3. **Evaluation** — present only when `evaluation: true` (overlay)
