# PortfolioCoach user datastore layout

Bind `userDatastore` to a host directory. Use this structure beneath it:

```text
{userDatastore}/
  data/
    raw/etrade/
    canonical/
  reports/
  inputs/
```

## Raw data

`{userDatastore}/data/raw/etrade/` — immutable E*TRADE exports as provided by the user.

Supported export types: `balances`, `account_history`, `orders`, `portfolio_lot_level`.

## Canonical data

`{userDatastore}/data/canonical/` — normalized CSV tables derived from raw exports per [`datastore-contract.md`](datastore-contract.md).

## Reports

`{userDatastore}/reports/` — immutable run output folders per [`report-artifact-contract.md`](report-artifact-contract.md).

## Inputs

`{userDatastore}/inputs/` — optional session attachments pending merge.
