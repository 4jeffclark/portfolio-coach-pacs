# Playbook index

Member playbooks and overlays are defined in the [repository README](../README.md). This file lists manifest ids for quick reference.

| Playbook | Report type |
| --- | --- |
| `datastore-inventory` | `DatastoreInventory` |
| `datastore-ingest` | `DatastoreIngest` |
| `market-regime-review` | `MarketRegimeReview` |
| `portfolio-composition-review` | `PortfolioCompositionReview` |
| `trading-activity-review` | `TradingActivityReview` |
| `symbol-trade-review` | `SymbolTradeReview` |

## Input presets

### `portfolio-composition-review`

| Intent | Key inputs |
| --- | --- |
| Composition by theme (default) | `rollupLens: theme` |
| Composition by thesis | `rollupLens: thesis` |
| Composition by standards | `rollupLens: standards` |
| Rebalancing focus | `rebalancingReview: true` |
| Risk focus | `riskReview: true` |

### `symbol-trade-review`

| Intent | Key inputs |
| --- | --- |
| Trade lifecycle | `reviewFocus: lifecycle`, `targetSymbol: <ticker>` |
| Stale position hygiene | `reviewFocus: stale`, `targetSymbol: <ticker>` |
| Event-driven trade | `reviewFocus: event`, `eventType: <type>`, `targetSymbol: <ticker>` |

### `market-regime-review`

| Menu / intent | Key inputs |
| --- | --- |
| Full market regime memo (#4) | `marketDepth: full`, `evaluation: false` |
| Brief market context (#5) | `marketDepth: summary`, `evaluation: false` |
| Market regime + coaching (#6) | `marketDepth: full`, `evaluation: true` |

Portfolio linkage ranks **exposure** by period-end weight % and **activity** by period gross notional from `market-environment` skill output. Do not use filled-order count as a conviction proxy.
