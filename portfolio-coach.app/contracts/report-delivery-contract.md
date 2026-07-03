# Report delivery contract

Cross-playbook rules for PortfolioCoach run output. Playbook-specific output contracts reference this file and add section minimums.

## Delivered artifact

Each run produces **exactly one user-facing markdown file** in the report folder:

```text
{userDatastore}/reports/<ReportBasename>/<ReportBasename>.md
```

| Token | Rule |
| --- | --- |
| `ReportBasename` | Same string as the report folder name: `<GenerationTimestamp>-<PlaybookReportId>-<PrimaryParameters>` |
| `GenerationTimestamp` | `YYYYMMDD-HHMMSS` (wall-clock at folder creation) |
| `PlaybookReportId` | PascalCase id from the playbook manifest (e.g. `MarketRegimeReview`) |
| `PrimaryParameters` | Playbook-specific suffix matching the folder pattern in each output contract (typically `<AnalysisStart>-<AnalysisEnd>`) |

Example:

```text
{userDatastore}/reports/20260703-103613-MarketRegimeReview-20260401-20260630/
  20260703-103613-MarketRegimeReview-20260401-20260630.md
```

### Timestamp rules

- Use actual generation time — no placeholders.
- Never overwrite an existing folder; create a new timestamp if the path exists.

## Assembly versus delivery

| Phase | Location | Lifecycle |
| --- | --- | --- |
| **Assembly** | `{agentWorkspace}` | CSVs, JSON fragments, scaffold markdown (e.g. `ReportSectionFragments.json`, `MarketResearch.md`, `Interview.md`, `ExitInterview.md`, scorecards). Temporary — not user delivery. |
| **Delivery** | `{userDatastore}/reports/<ReportBasename>/` | Single `<ReportBasename>.md` only. |

Execution agents:

1. Run skills; read assembly artifacts from `{agentWorkspace}`.
2. **Merge all narrative and quantitative content** from assembly artifacts into the delivered report file. Preserve the **union of content** the prior multi-file shape produced — do not drop sections because they moved out of separate files.
3. Embed tabular skill output as markdown tables or structured lists in the delivered report (do not rely on sibling CSV files for user-readable quantification).
4. Write only `<ReportBasename>.md` under the report folder.
5. Remove `{agentWorkspace}` for the run after verification (unless debugging or user requested retention).

Prior standalone markdown files (`MarketResearch.md`, `Interview.md`, `ExitInterview.md`, `*Scorecard.md`) and report-folder CSVs are **retired as delivery targets**. Their content belongs **inside** the delivered report file.

## Manifest pathTemplate

Playbook manifests set `outputs.primary.pathTemplate` to the delivered file path, for example:

```yaml
pathTemplate: >-
  {userDatastore}/reports/{timestamp}-MarketRegimeReview-{{analysisPeriodStart}}-{{analysisPeriodEnd}}/
  {timestamp}-MarketRegimeReview-{{analysisPeriodStart}}-{{analysisPeriodEnd}}.md
```

## Post-run verification

Self-verify per [APP post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md):

- Report folder exists and contains **only** the delivered `.md` file (unless the user explicitly requested assembly retention for debugging).
- Delivered filename matches the report folder basename.
- All sections required by the playbook output contract are present in the delivered file, including content formerly split across separate markdown or CSV deliverables.
