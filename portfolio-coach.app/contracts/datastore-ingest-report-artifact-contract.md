# Datastore ingest report artifact contract

## Report folder pattern

```text
{userDatastore}/reports/<GenerationTimestamp>-DatastoreIngest-<AnalysisStart>-<AnalysisEnd>/
```

## Required artifacts

| File | Role |
| --- | --- |
| `Report.md` | Ingest and validation summary |
| `MergeLog.csv` | Per-file staging outcomes |
| `Metrics.csv` | Rebuild and validation metrics |
| `ReportSectionFragments.json` | Scaffold section text for agent merge |

## Report.md

Minimum sections:

1. **Datastore layout** — resolved layout and path warnings
2. **Session attachments** — files copied from `inputs/` when present
3. **Canonical validation** — readability and validation outcomes
4. **Available date range** — summary for downstream playbooks
5. **Appendix: Inputs Resolved** — final resolved playbook inputs

## Post-run verification

Self-verify per [APP post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
