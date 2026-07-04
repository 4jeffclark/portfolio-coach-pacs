# PortfolioCoach PACS

Published **PACS distribution repo** for PortfolioCoach.

**Status:** The tables below are the **pack catalog**. Playbook manifests and overlays align to this document as of v4.0.0.

### Conventions

| Topic | Rule |
| --- | --- |
| **Playbook** | Kebab-case manifest `id` under `layer3-playbooks/<id>/` |
| **Report folder** | `{timestamp}-{PascalCasePlaybook}-{period}/` under `{userDatastore}/reports/` — contains one delivered file `{timestamp}-{PascalCasePlaybook}-{period}.md`; overlays extend the same report |
| **Overlay** | Layer-2 augmentation; `—` = core run only. Multiple overlays may compose on one run |
| **Knowledge domains** | Documentation grouping only — not in manifests or schema |

Pack entry: [`portfolio-coach.pacs/pack.pacs.yaml`](portfolio-coach.pacs/pack.pacs.yaml).

---

## DataManagement

| User asks | Playbook | Overlay | Delivers |
| --- | --- | --- | --- |
| “Inventory my datastore” / “What data do I have?” / “What can I analyze?” | `datastore-inventory` | — | `DatastoreInventory` report: artifact catalog (`DataStoreInventory.csv`); per-account coverage (`AccountCoverage.csv`); activity, cash, and income date spans; structural validation (`Metrics.csv`); report sections 1–5 |
| “Inventory my datastore and coach me on gaps” / “Is my data ready for analysis?” | `datastore-inventory` | `datastore-inventory-evaluation` · `evaluation: true` | Adds evaluation section, `DatastoreInventoryScorecard.md`, gap/readiness insights, export-cadence notes, `ExitInterview.md` |
| “Ingest these exports” / “Merge session files into canonical” | `datastore-ingest` | — | `DatastoreIngest` report: layout resolution; `inputs/` attachment handling when present; canonical readability validation; merge/validation log; updated canonical tables when merge tooling runs |

Analytic playbooks use a lighter validate-only prelude (`datastore-merge-and-validate`); full ingest is the dedicated `datastore-ingest` playbook.

---

## MarketAnalysis

| User asks | Playbook | Overlay | Delivers |
| --- | --- | --- | --- |
| “What’s the market regime for this period?” / “Full market backdrop memo” | `market-regime-review` | — · `marketDepth: full` | `MarketRegimeReview` report: period-scoped regime memo (`market-environment` skill); standalone full memo |
| “Brief market context for this period” (embed or lightweight run) | `market-regime-review` | — · `marketDepth: summary` | Abbreviated regime memo fragments suitable for embedding in another playbook’s report |
| “What’s the market regime?” (with coaching judgment) | `market-regime-review` | `market-regime-evaluation` · `evaluation: true` | Adds regime interpretation judgment, coaching notes, `ExitInterview.md` |

---

## PortfolioAnalysis

| User asks | Playbook | Overlay | Delivers |
| --- | --- | --- | --- |
| “How is my portfolio composed?” / “What changed this period?” | `portfolio-composition-review` | — · `rollupLens: theme` (default) | `PortfolioCompositionReview` report: holdings map by theme; period weights and flows; thesis health; evolution, liquidity, concentration tables; embedded market context |
| “How is my portfolio composed by thesis?” | `portfolio-composition-review` | — · `rollupLens: thesis` | Same report family; thesis registry drives rollup; thesis-health sections emphasized |
| “How is my portfolio composed by standards?” | `portfolio-composition-review` | — · `rollupLens: standards` | Same report family; standards taxonomy drives rollup |
| “How is my portfolio composed?” (with coaching) | `portfolio-composition-review` | `portfolio-composition-evaluation` · `evaluation: true` | Adds entry interview, portfolio scorecard, judgment section, `ExitInterview.md` |
| “Should I rebalance?” / “What trades would rebalance me?” | `portfolio-composition-review` | `rebalancing-review` · `rebalancingReview: true` | Adds target-weight analysis, rebalance suggestions, rebalancing narrative sections |
| “What’s my risk exposure?” / “Rotation/risk posture review” | `portfolio-composition-review` | `risk-review` · `riskReview: true` | Adds risk posture, concentration/stress notes, rotation-oriented sections |

Core + any subset of overlays may run together (e.g. evaluation + rebalancing). Each overlay row describes what that overlay adds when enabled.

---

## TradingAnalysis — activity

| User asks | Playbook | Overlay | Delivers |
| --- | --- | --- | --- |
| “Debrief my trading this period” / “How active was I?” | `trading-activity-review` | — | `TradingActivityReview` report: period trading-activity metrics and debrief (`trading-activity-analysis`); embedded market context |
| “Debrief my trading this period” (with coaching) | `trading-activity-review` | `trading-activity-evaluation` · `evaluation: true` | Adds activity scorecard, coaching judgment, `ExitInterview.md` |

---

## TradingAnalysis — symbol

| User asks | Playbook | Overlay | Delivers |
| --- | --- | --- | --- |
| “Review my trades in this symbol” / “Walk the lifecycle” | `symbol-trade-review` | — · `reviewFocus: lifecycle` | `SymbolTradeReview` report: symbol forensic trade timeline (`symbol-trading-analysis`); embedded market context |
| “Is this position stale?” / “Hygiene check on this holding” | `symbol-trade-review` | — · `reviewFocus: stale` | Stale-position hygiene findings (`stale-position-hygiene`); symbol context |
| “How did I trade this IPO?” / “Event-driven trade review” | `symbol-trade-review` | — · `reviewFocus: event` · `eventType: <type>` | Event-driven trade context (`event-trade-context`); symbol forensic timeline |
| “Review trades in this symbol” (with coaching) | `symbol-trade-review` | `symbol-trade-evaluation` · `evaluation: true` | Adds trade scorecard, decision judgment, `ExitInterview.md` |

---

## Layout

```text
portfolio-coach-pacs/
  README.md
  portfolio-coach.pacs/
```

## PACS standard

Read in order from the [PACS Standards Workbench](https://github.com/4jeffclark/pacs-workbench):

1. [Authoring standard](https://github.com/4jeffclark/pacs-workbench/blob/main/standard/pacs-authoring.md)
2. [Execution guide](https://github.com/4jeffclark/pacs-workbench/blob/main/standard/pacs-execution.md)
3. [Post-run checklist](https://github.com/4jeffclark/pacs-workbench/blob/main/standard/post-run-checklist.md)

Persistent data and reports belong under `{userDatastore}`, not in this behavior repo.
