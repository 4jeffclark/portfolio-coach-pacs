# PortfolioCoach user datastore layout

Bind `userDatastore` to a host directory. Use this structure beneath it:

```text
{userDatastore}/
  data/
    raw/etrade/
    canonical/
    knowledge/          # standard knowledge root (optional)
  knowledge/            # legacy knowledge root (optional)
  reports/
  inputs/
```

## Layout resolution

`pc-lib` resolves paths with this precedence:

### Data paths

1. **Standard** — `data/canonical/` and `data/raw/etrade/` when either exists
2. **Legacy** — `canonical/` and `raw/etrade/` at datastore root when standard paths are absent
3. **Default** — standard paths for new datastores

When both data layouts exist, standard wins.

### Knowledge paths

1. **Standard** — `data/knowledge/` when present
2. **Legacy** — `knowledge/` at datastore root when standard knowledge path is absent
3. **Default** — `data/knowledge/` for new datastores

When both knowledge layouts exist, standard wins. Prefer migrating legacy layouts to the standard `data/` prefix.

## Raw data

`{userDatastore}/data/raw/etrade/` — immutable E*TRADE exports (or legacy `raw/etrade/`).

Supported export types: `balances`, `account_history`, `orders`, `portfolio_lot_level`.

## Canonical data

`{userDatastore}/data/canonical/` — normalized CSV tables per [`datastore-contract.md`](datastore-contract.md).

## Knowledge

`{userDatastore}/knowledge/` or `{userDatastore}/data/knowledge/` — durable portfolio memory per [`persistent-knowledge-model.md`](persistent-knowledge-model.md).

Domains: `holdings/`, `themes/`, `theses/`, `policies/`, `market/`, `reports/`, `analytics/`.

| Playbook | Reads knowledge? |
| --- | --- |
| `datastore-inventory` | Optional future extension (knowledge health inventory) |
| `portfolio-composition-review` | Yes — baseline maps and registries |
| `market-regime-review` | Optional — proxy registry |
| `symbol-trade-review` | Optional — holdings map for symbol context |
| `trading-activity-review` | Optional — holdings map for activity tagging |

## Reports

`{userDatastore}/reports/` — immutable run output folders per playbook report contracts.

## Inputs

`{userDatastore}/inputs/` — optional session attachments pending merge.

## Post-run verification

Self-verify report folders per [PACS post-run checklist](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/post-run-checklist.md).
