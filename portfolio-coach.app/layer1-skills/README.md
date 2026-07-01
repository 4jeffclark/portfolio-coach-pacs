# Skills

Layer 1 agentskills.io skills — all **shipped** with `pc-lib` scaffold scripts (`outputCompleteness: scaffold`).

## Data & interviews

| Skill | Playbooks |
| --- | --- |
| `datastore-inventory` | `datastore-inventory` |
| `datastore-inventory-insights` | `datastore-inventory` evaluation |
| `datastore-ingest` | `datastore-ingest` |
| `evaluation-entry-interview` | evaluation overlays |
| `exit-interview` | evaluation overlays |

## Market & trading

| Skill | Playbooks |
| --- | --- |
| `market-environment` | `market-regime-review`, embeds in `trading-activity-review`, `portfolio-composition-review`, `symbol-trade-review` |
| `trading-activity-analysis` | `trading-activity-review` |
| `symbol-trading-analysis` | `symbol-trade-review` |
| `stale-position-hygiene` | `symbol-trade-review` (`reviewFocus: stale`) |
| `event-trade-context` | `symbol-trade-review` (`reviewFocus: event`) |

## Portfolio mapping

| Skill | When |
| --- | --- |
| `holdings-standards-map` | `portfolio-composition-review` |
| `holdings-map-confirmation` | `portfolio-composition-review` |
| `theme-map-inference` | `rollupLens` theme or thesis |
| `theme-map-confirmation` | `rollupLens` theme or thesis |
| `thesis-registry-inference` | `rollupLens` thesis |
| `thesis-registry-confirmation` | `rollupLens` thesis |

## Portfolio quantification

| Skill | Order |
| --- | --- |
| `portfolio-holdings-state` | 1 |
| `period-weight-reconstruction` | 2 |
| `portfolio-weights-table` | 3 |
| `thesis-health` | 4 |
| `portfolio-period-flows` | 5 |
| `portfolio-evolution` | 6 |
| `portfolio-liquidity-analysis` | 7 |
| `portfolio-concentration-resilience` | 8 |

Shared helpers: `assets/pc-lib/` (`analytics.py`, `canonical.py`, `cli.py`).
