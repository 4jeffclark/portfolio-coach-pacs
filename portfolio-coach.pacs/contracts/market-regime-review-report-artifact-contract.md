# Market regime review report artifact contract

See [`report-delivery-contract.md`](report-delivery-contract.md) for delivery rules.

## Report folder pattern

```text
{userDatastore}/reports/<ReportBasename>/
```

| Token | Format |
| --- | --- |
| `ReportBasename` | `<GenerationTimestamp>-MarketRegimeReview-<AnalysisStart>-<AnalysisEnd>` |

## Delivered artifact

| File | Role |
| --- | --- |
| `<ReportBasename>.md` | Self-contained market regime memo |

## Assembly inputs (workspace only)

Merge into the delivered file:

- `Metrics.csv`, `ReportSectionFragments.json`
- When `marketDepth: full`: all content formerly written to `MarketResearch.md` (period windows, broad market context, index/factor highlights, sector map, sources, extended symbol context, scenario/outlook detail)
- When `evaluation: true`: exit-interview and judgment scaffold content

## Delivered report — minimum sections

1. **Executive summary** — regime label and portfolio-linked read
2. **Period windows** — lookback, analysis, follow-through (and user-requested outlook horizon when applicable)
3. **Q2 / analysis-period regime review** — macro, index, sector, volatility narrative
4. **Portfolio linkage** — symbol universe and period activity quantification from datastore
5. **Forward outlook** — when requested or implied by user intent
6. **Sources** — cited references (embed table formerly in `MarketResearch.md`)
7. **Appendix: Inputs Resolved** — final resolved playbook inputs and period confirmation
8. **Evaluation** — when `evaluation: true`; embed exit-interview and coaching judgment

When `marketDepth: summary` (embed in another playbook), produce abbreviated fragments in workspace only; the parent playbook's delivered report absorbs the summary sections.

## Post-run verification

Self-verify per [PACS post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
