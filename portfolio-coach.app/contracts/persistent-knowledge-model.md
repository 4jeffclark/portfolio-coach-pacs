# Persistent knowledge model

Canonical persistence model for PortfolioCoach beyond raw broker inputs and rebuildable canonical tables.

Defines what persists as reusable portfolio knowledge, what remains execution-local in report folders, and how report-generated data may be promoted into durable state.

## Four persistence tiers

| Tier | Location (standard) | Purpose |
| --- | --- | --- |
| 1 — Immutable source | `{userDatastore}/data/raw/` | Append-only broker exports |
| 2 — Rebuildable canonical | `{userDatastore}/data/canonical/` | Deterministic factual transforms |
| 3 — Persistent knowledge | `{userDatastore}/knowledge/` | User-confirmed semantic state |
| 4 — Execution-local reports | `{userDatastore}/reports/` | Per-run immutable artifacts |

Legacy layouts use root `canonical/`, `raw/etrade/`, and `knowledge/` without the `data/` prefix. `pc-lib` resolves paths per [`user-datastore-layout.md`](user-datastore-layout.md).

## Durable versus execution-local

> Should future executions inherit this as current or historical portfolio understanding?

If yes → promote to `{userDatastore}/knowledge/`. If no → keep in the report folder.

## Knowledge layout

```text
{userDatastore}/
  knowledge/                    # or data/knowledge/ (standard)
    holdings/
    themes/
    theses/
    policies/
    market/
    reports/
    analytics/
```

### Holdings knowledge

| File | Role |
| --- | --- |
| `holdings/HoldingsMapCurrent.csv` | Latest confirmed symbol classifications |
| `holdings/HoldingsMapHistory.csv` | Historical classification changes |
| `holdings/LiquidityIntentCurrent.csv` | Confirmed liquidity intent |

### Theme knowledge

| File | Role |
| --- | --- |
| `themes/ThemeRegistry.csv` | Durable theme catalog |
| `themes/ThemeMapCurrent.csv` | Latest symbol → theme assignments |
| `themes/ThemeMapHistory.csv` | Assignment history |

### Thesis knowledge

| File | Role |
| --- | --- |
| `theses/ThesisRegistry.csv` | Active and historical theses |
| `theses/ThesisAssignmentCurrent.csv` | Latest symbol → thesis assignments |
| `theses/ThesisAssignmentHistory.csv` | Assignment history |
| `theses/ThesisEvents.csv` | Thesis lifecycle events |

### Policy, market, reports, analytics

Full schemas for `policies/`, `market/`, `reports/ReportRegistry.csv`, and `analytics/` are defined in this contract.

## Promotion rules

**Auto-promote** when structured, reusable, user-confirmed, and not merely a period-specific metric snapshot:

- confirmed holdings map
- confirmed theme registry and theme map
- confirmed thesis registry and assignments

**Keep report-local by default:** the delivered report file, interview content embedded therein, and period-specific quantification formerly in CSV/scorecard assembly artifacts.

## Playbook roles

| Playbook | Knowledge interaction |
| --- | --- |
| `datastore-inventory` | Eventually inventory knowledge health (coverage, staleness) |
| `portfolio-composition-review` | Load current knowledge as baseline; promote confirmed changes after run |

## Design principles

1. Raw inputs are immutable.
2. Canonical tables are rebuildable.
3. Portfolio knowledge is durable and historized.
4. Reports are immutable run artifacts, not the primary memory system.
5. Future executions inherit confirmed understanding from `knowledge/`, not by searching old reports.
