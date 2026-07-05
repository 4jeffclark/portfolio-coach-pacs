# Holdings taxonomy

Canonical holdings classification contract for PortfolioCoach portfolio analysis.

For persistence rules across durable portfolio memory versus report-local artifacts, see [`persistent-knowledge-model.md`](persistent-knowledge-model.md).

## Purpose

PortfolioCoach supports multiple reporting modalities:

- standards-based composition reporting
- thematic composition reporting
- thesis-driven composition reporting
- risk and rebalancing overlays
- cross-playbook enrichment for trade and activity reviews

Those modalities require separate namespaces. This contract keeps namespaces distinct so reports can change their primary rollup lens without changing the underlying symbol map.

## Core rule

Do not collapse instrument taxonomy, economic exposure, style, liquidity function, theme, and thesis into one or two columns.

| Layer | Namespace | Meaning | Owner |
| --- | --- | --- | --- |
| L0 | `AssetClass` | Instrument type | external / inferred |
| L1 | `AssetSubclass` | More specific instrument slice | external / inferred |
| L2 | `GICSSector` | Broad economic exposure | external / inferred |
| L3 | `GICSIndustry` | Granular economic exposure | external / inferred |
| L4 | `StyleBucket` | Equity style or regime role | PortfolioCoach |
| L5 | `LiquidityRole` | Portfolio cash-function role | user-confirmed |
| L6 | `ThemeId` | Structural megatrend exposure | external namespace or user-defined |
| L7 | `ThesisId` | Time-bound investment hypothesis | user-defined |

Full namespace value lists and reporting rules are defined in this contract.

## Primary report lens

Use playbook input:

```text
rollupLens: standards | theme | thesis
```

Default for `portfolio-composition-review`: `theme`.

## File contracts

### `HoldingsMap.csv`

Required for `portfolio-composition-review` and any playbook that enriches output with holdings classification.

```text
Symbol,AssetClass,AssetSubclass,GICSSector,GICSIndustry,StyleBucket,LiquidityRole,MappingConfidence,MappingSource,Notes
```

Durable promotion target: `{userDatastore}/knowledge/holdings/HoldingsMapCurrent.csv` (see layout resolution in [`user-datastore-layout.md`](user-datastore-layout.md)).

### `ThemeRegistry.csv` / `ThemeMap.csv`

Required when `rollupLens` is `theme` or `thesis`. Durable targets under `{userDatastore}/knowledge/themes/`.

**Inference precedence** (when durable files are absent):

1. `knowledge/themes/ThemeMapCurrent.csv` — user-confirmed assignments win (`MappingSource: knowledge`)
2. Deterministic rules in `pc-lib` — holdings layer (subclass, GICS sector), pack `assets/theme-rules/`, position-weighted coverage
3. `THEME_UNASSIGNED` — residual bucket; target < 40% period-end MV on first inference

`theme-map-inference` emits `ThemeCoverage.csv` and `InferenceLog.csv` (workspace assembly) with rule provenance per symbol.

### `ThesisRegistry.csv` / `ThesisAssignment.csv`

Required when `rollupLens` is `thesis`. Durable targets under `{userDatastore}/knowledge/theses/`.

### `MappingDiscovery.md`

Unified working copy for user confirmation during input discovery. Embed operative content in the delivered report file Appendix.

## Skill responsibilities

| Skill | Role |
| --- | --- |
| `holdings-standards-map` | Creates `HoldingsMap.csv` for the mapping universe |
| `theme-map-inference` | Creates theme registry and map when `rollupLens` in `[theme, thesis]` |
| `thesis-registry-inference` | Creates thesis registry and assignment when `rollupLens == thesis` |
| `holdings-map-confirmation` | User confirmation gate — agent-only interact |
| `theme-map-confirmation` | User confirmation gate — agent-only interact |
| `thesis-registry-confirmation` | User confirmation gate — agent-only interact |

## Input discovery gates

Aggregate state review must not proceed to quantification until required mapping gates for the chosen lens are complete.

| Gate | When |
| --- | --- |
| `holdings-map-confirmed` | Always |
| `theme-map-confirmed` | `rollupLens` in `[theme, thesis]` |
| `thesis-registry-confirmed` | `rollupLens == thesis` |

## Mapping universe

Union of: period-start holdings, period-end holdings, reference snapshot holdings, and all symbols with filled orders in the analysis period.

## Cross-playbook enrichment

`HoldingsMap.csv` is reusable across `portfolio-composition-review`, `market-regime-review`, `trading-activity-review`, and `symbol-trade-review`.
