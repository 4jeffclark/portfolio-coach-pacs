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

- `Metrics.csv`, `ReportSectionFragments.json`, `PortfolioLinkage.csv`
- When `marketDepth: full`: all content formerly written to `MarketResearch.md` (period windows, broad market context, index/factor highlights, sector map, sources, extended symbol context, scenario/outlook detail)
- When `evaluation: true`: exit-interview and judgment scaffold content

## Report title and period labeling

Use **calendar date range** in the report title and period windows when `analysisPeriodEnd` does not match a standard calendar boundary:

| Analysis end | Preferred title label |
| --- | --- |
| `20260630` | H1 2026 (Jan 1 – Jun 30) |
| `20260701` | Jan 1 – Jul 1, 2026 *(not "H1 2026" alone — includes one extra calendar day)* |
| `20260930` | Q3 2026 (Jul 1 – Sep 30) |

Macro narrative may still reference "H1" when discussing market history, but **portfolio linkage activity scope** must match resolved `analysisPeriodStart`–`analysisPeriodEnd`.

## Delivered report — minimum sections

1. **Executive summary** — regime label and portfolio-linked read
2. **Period windows** — lookback, analysis, follow-through (and user-requested outlook horizon when applicable)
3. **Analysis-period regime review** — macro, index, sector, volatility narrative
4. **Portfolio linkage** — symbol universe, **period-end exposure** (top holdings by weight % when snapshot available), and **period activity** (buy/sell notional and gross turnover from skill output). Distinguish exposure, activity, and conviction explicitly
5. **Forward outlook** — when requested or implied by user intent
6. **Sources** — cited references (embed table formerly in `MarketResearch.md`)
7. **Appendix: Inputs Resolved** — final resolved playbook inputs and period confirmation
8. **Appendix: Skill Metrics** — embed key rows from `Metrics.csv` (see below)
9. **Evaluation** — when `evaluation: true`; embed exit-interview and coaching judgment

### Appendix: Skill Metrics (required subset)

Embed a markdown table sourced from `Metrics.csv`:

| Metric | Value |
| --- | --- |
| `portfolioSymbolCount` | |
| `periodEndSnapshot` | |
| `periodEndSnapshotLagDays` | |
| `snapshotLagNotice` | |
| `snapshotLagWarn` | |
| `periodEndTotalMV` | |
| `periodGrossTurnover` | |
| `portfolioTurnoverRatio` | |
| `exposureQualityValid` | |
| `exposureNumericSymbolCount` | |
| `exposureParentRowCount` | |
| `exposureLotDetailRowCount` | |

### Portfolio linkage assembly rules

Execution agents **must**:

- Embed `PortfolioLinkage.csv` (or equivalent markdown tables derived from it) for exposure and activity quantification
- Rank **exposure** by `PeriodEndWeightPct` and **activity** by `PeriodGrossNotional`
- Cite period-end snapshot date and total MV from `Metrics.csv` when exposure is available
- Document snapshot gaps when `periodEndExposureAvailable` is false

Execution agents **must not**:

- Rank symbols by `FilledOrderCount` or present order-count share as conviction, capital concentration, or thesis sizing
- Invent weights, notionals, or turnover figures not present in skill output (`Metrics.csv`, `PortfolioLinkage.csv`)
- Describe high trading frequency as proof of high conviction — defer full conviction analysis to `portfolio-composition-review`

When period-start weights are unavailable (`periodStartExposureAvailable: false`), state the gap; do not imply period weight change without `period-weight-reconstruction`.

### Exposure data quality gate

When `exposureQualityValid` is **false** in `Metrics.csv` (typically `exposureNumericSymbolCount > 0` from lot-detail rows misparsed as tickers):

- Banner the delivered report: **`DATA QUALITY — EXPOSURE TABLE INVALID`**
- **Do not** embed period-end exposure weight tables or exposure-based portfolio linkage narrative
- **Do not** apply `market-regime-evaluation` coaching on exposure, concentration, or MV totals
- Activity tables (gross notional) may still be embedded when order data is valid
- Attest **`Post-run checklist: failed`** with failed item **`D3`** — do not claim pass

When `snapshotLagWarn` is **true** (`periodEndSnapshotLagDays` **≥ 14**):

- Document lag in period windows and Inputs Resolved
- Recommend setting `analysisPeriodEnd` to the latest positions export date when user wants aligned exposure, or obtain user acknowledgment of stale snapshot

When `snapshotLagNotice` is **true** (`periodEndSnapshotLagDays` between **1** and **13**):

- Document lag in period windows (exposure valid but stale)
- Note whether user accepts lag or prefers aligned `analysisPeriodEnd`

### Paired runs (#4 + #6)

When running full memo and coaching for the same analysis window, use the **same** `analysisPeriodStart` and `analysisPeriodEnd` on both runs. Prefer the **latest positions export date** for `analysisPeriodEnd` when aligned exposure matters (e.g. `#4` at `20260701` then `#6` at `20260701`).

## Summary depth delivery

When `marketDepth: summary`:

- **Standalone run** (menu item or direct user request): deliver an abbreviated report meeting sections 1–7 above with condensed narrative; portfolio linkage tables may be shortened (top 5 by weight and notional)
- **Embed run** (invoked as context for another playbook): produce abbreviated fragments in workspace only; the parent playbook's delivered report absorbs the summary sections

## Post-run verification

Self-verify per [PACS post-run checklist](https://github.com/4jeffclark/pacs-workbench/blob/main/standard/post-run-checklist.md).
