# Datastore Contract

This document defines the persistent input data store for PortfolioCoach.

PortfolioCoach is a prompt/spec/artifact factory. This contract is the source of truth for datastore behavior. Execution agents may use any available tooling to satisfy the contract, but the repository does not require or provide executable ingestion tooling.

## Purpose

The datastore preserves all user-provided native E*TRADE exports and maintains normalized CSV tables that are easier for agents to inspect during playbook execution.

The repository is single-user. Unless a playbook explicitly narrows account scope or analysis period, all datastore content is relevant to future report requests.

## Folder Contract

```text
data/
  raw/
    etrade/
      account_history/
      balances/
      orders/
      portfolio_lot_level/
  canonical/
    accounts.csv
    account_history.csv
    balances.csv
    cash.csv
    cash_activity_daily.csv
    cash_balance_estimated.csv
    income_events.csv
    orders.csv
    positions_lot_level.csv
    ingestion_manifest.csv
```

## Raw Data Rules

Raw files are immutable source artifacts.

Agents must:

1. Store every newly provided native E*TRADE export under the appropriate `{userDatastore}/data/raw/etrade/` subfolder.
2. Preserve raw file contents unchanged.
3. Avoid creating duplicate raw copies when the same file is already represented.
4. Prefer a filename that records ingestion time, a short content hash if available, and the original filename.
5. Treat raw files as authoritative if derived canonical tables appear wrong.

## Canonical Data Rules

Canonical files are normalized CSV tables derived from raw files.

Agents must:

1. Rebuild or update canonical tables after adding raw files.
2. Keep stable column names.
3. Preserve provenance columns that identify source raw files.
4. Use canonical tables for account normalization, available date range detection, period selection, and routine analysis.
5. State any parsing or interpretation limitation in report artifacts when it affects conclusions.

Canonical files are derived artifacts. They may be regenerated when parsing rules improve.

## Supported E*TRADE Export Types

### Balances

Native shape:

- Line 1 is a title/as-of line.
- Line 2 is the CSV header.
- Remaining rows include one aggregate `All Accounts` row and one row per account.

Canonical outputs:

- `accounts.csv`
- `balances.csv`
- `cash.csv`
- `ingestion_manifest.csv`

### Account History

Native shape:

- Line 1 is an account/as-of title line.
- Line 2 is the CSV header.
- Each file covers one account.
- Rows are statement activity such as buys, sells, dividends, interest, margin interest, transfers, sweeps, and corporate actions.

Canonical outputs:

- `account_history.csv`
- `cash_activity_daily.csv`
- `cash_balance_estimated.csv`
- `income_events.csv`
- `ingestion_manifest.csv`

Account history exports are not historical balance snapshots. They are activity ledgers. They improve cash reconstruction because they include dividends, interest, fees, commissions, transfers, margin interest, and sweep activity that order exports alone cannot explain.

### Orders

Native shape:

- Line 1 is a title/as-of line.
- Line 2 is the CSV header.
- Remaining rows are order records.
- Account is represented as a full numeric account id.

Canonical outputs:

- `orders.csv`
- account identity fields joined from `accounts.csv` when possible
- `ingestion_manifest.csv`

### Portfolio Lot Level

Native shape:

- Line 1 is a title/as-of line.
- Line 2 is the CSV header.
- Account section headers appear as rows where quantity is `--`.
- Position rows follow the current account section until the next account section.
- `Portfolio Analysis` is a summary row, not a position.
- `Cash on Deposit: $...` is a cash summary row, not a position.

Canonical outputs:

- `positions_lot_level.csv`
- `cash.csv`
- `ingestion_manifest.csv`

## Account Normalization

E*TRADE exports identify accounts inconsistently:

- Balances and portfolio exports use masked account labels such as `Traditional IRA - x7232`.
- Orders exports use full account ids such as `120447232`.

Agents should normalize account identity using:

```text
AccountId
MaskedAccount
AccountLabel
AccountType
```

Where possible, match orders to balances/positions by joining the last four digits of `AccountId` to the masked `x####` token.

Known initial account mapping:

| AccountId | MaskedAccount | AccountLabel | AccountType |
|---|---|---|---|
| `120447232` | `x7232` | `Traditional IRA - x7232` | `CASH` |
| `120447782` | `x7782` | `Individual Brokerage - x7782` | `MARGIN` |
| `215160142` | `x0142` | `Partnership / LLC / LLP - x0142` | `CASH` |

## Canonical Schemas

### `accounts.csv`

```text
AccountId
MaskedAccount
AccountLabel
AccountType
FirstName
LastName
SourceExportType
SourceHash
AsOfLocal
AsOfTimeZone
```

### `balances.csv`

```text
AsOfLocal
AsOfTimeZone
AccountId
MaskedAccount
AccountLabel
AccountType
LiveAccountValue
CashAvailToWithdraw
CashBuyingPower
MarginBuyingPower
TodaysTradingGain
YtdTradingGain
NetCalls
SourceHash
RawStoredPath
```

### `cash.csv`

```text
AsOfLocal
AsOfTimeZone
AccountId
MaskedAccount
AccountLabel
CashConcept
Amount
SourceExportType
SourceHash
RawStoredPath
```

Cash concepts include:

```text
CashAvailToWithdraw
CashBuyingPower
MarginBuyingPower
PortfolioCashOnDeposit
```

These cash concepts may differ because E*TRADE uses different definitions across exports. Do not force them to reconcile.

### `account_history.csv`

```text
SourceHash
RawStoredPath
ExportedAtLocal
ExportedAtTimeZone
ActivityDateTime
ActivityDate
ActivityType
AccountId
MaskedAccount
AccountLabel
Description
Symbol
Quantity
Price
OrderNumber
Fee
Commission
Amount
CashActivityClass
IsTradeCashEffect
IsEconomicCashFlow
IsSweep
IsTransfer
IsDividendOrInterest
```

Implementation hints:

- Parse `Date / Time` into `yyyy-MM-dd HH:mm:ss`.
- Parse `Amount`, `Fee`, and `Comm` as signed numeric values.
- Parse trade descriptions like `<quantity> of <symbol> @ <price> (Order # <number>)` when possible.
- Preserve the original `Description`.
- Treat `Bought` and `Sold` as trade settlement cash effects. These may include fees and commissions and can be more precise than order notional for cash reconstruction.
- Treat `Dividend`, `Qualified Dividend`, `Interest`, `Interest Income`, and `Margin Interest` as non-trade income or expense.
- Treat `Online Transfer` as external cash movement.
- Treat `Transfer` as account-level transfer activity. It may be all-account neutral when paired with another account, but it is still relevant for account-level cash reconstruction.
- Treat `Sweep` as bank deposit program movement. Preserve it, but do not blindly count it as economic cash generation or loss.
- Treat stock splits and similar corporate actions as non-cash unless the amount is nonzero and the description indicates otherwise.

### `cash_activity_daily.csv`

```text
Date
AccountId
MaskedAccount
AccountLabel
TradeCashFlow
IncomeCashFlow
ExternalTransferCashFlow
InternalTransferCashFlow
SweepCashFlow
OtherCashFlow
NetCashActivityExcludingSweep
NetCashActivityIncludingSweep
BoughtAmount
SoldAmount
DividendAmount
InterestAmount
MarginInterestAmount
Fees
Commissions
ActivityRowCount
SourceHistoryRows
```

`NetCashActivityExcludingSweep` is the preferred daily cash reconstruction input unless an analysis specifically needs sweep mechanics. `NetCashActivityIncludingSweep` is preserved for audit and reconciliation.

### `cash_balance_estimated.csv`

```text
Date
AccountId
MaskedAccount
AccountLabel
CashConcept
EstimatedAmount
IsObservedAnchor
AnchorAsOfLocal
AnchorAmount
PriorAnchorAsOfLocal
NextAnchorAsOfLocal
CumulativeNetCashActivityFromAnchor
ReconciliationDelta
ReconciliationStatus
DerivationMethod
Confidence
Limitations
```

Cash balance estimates are derived, not observed facts. They should be rebuilt whenever new account history or balance exports are added.

Rules:

- Balance exports and portfolio cash rows are observed anchors.
- Account history activity provides cash reconstruction inputs between anchors.
- When multiple anchors exist, rebuild the estimated curve between anchors and record reconciliation deltas when material.
- When only one anchor exists, estimates are lower confidence and should be described as backward or forward reconstruction from a single observed snapshot.
- Reports may use observed anchors as facts.
- Reports may use estimated cash curves as directional evidence.
- Reports must call out material gaps, single-anchor reconstruction, and reconciliation deltas.

Reconciliation rules:

- `PriorAnchorAsOfLocal` and `NextAnchorAsOfLocal` identify observed balance snapshots that bound an estimated interval when both are available.
- `ReconciliationDelta` is `ObservedNextAnchor - EstimatedNextAnchor`.
- `ReconciliationStatus` should be `single_anchor`, `reconciled`, `material_delta`, or `not_applicable`.
- Material reconciliation deltas represent non-order activity, sweep modeling error, missing history, transfers, dividends, fees, settlement effects, or parser limitations. Do not hide them.

### `income_events.csv`

```text
ActivityDate
ActivityDateTime
AccountId
MaskedAccount
AccountLabel
IncomeType
Description
Symbol
Amount
SourceHash
RawStoredPath
```

This table captures dividends, qualified dividends, interest, interest income, margin interest, and similar income/expense events from account history.

### `orders.csv`

```text
SourceHash
RawStoredPath
ExportedAtLocal
ExportedAtTimeZone
AccountId
MaskedAccount
AccountLabel
Symbol
Status
Side
PositionEffect
Quantity
OrderType
OrderPrice
Fill
FillQuantity
FillPrice
Market
Time
Date
Description
```

Implementation hints:

- Parse `Time` into `yyyy-MM-dd HH:mm:ss`.
- Parse `Date` into `yyyy-MM-dd`.
- Parse `Description` for side, quantity, order type, order price, and open/close intent when possible.
- Parse `Fill` for fill quantity and fill price when it matches `<quantity> @ <price>`.
- Preserve original `Description` and `Fill`.

Suggested order de-duplication key:

```text
Symbol
Status
Fill
Description
Market
Time
AccountId
```

### `positions_lot_level.csv`

```text
SourceHash
RawStoredPath
AsOfLocal
AsOfTimeZone
AccountId
MaskedAccount
AccountLabel
PositionRaw
Symbol
Quantity
LotCount
DateAcquired
Term
CostBasis
ULPrice
ULChange
Mark
MarkChange
NetCostBasis
TodaysNetGain
OpenNetGain
MarketValue
Bid
Ask
EarningsDate
```

Implementation hints:

- Carry the current account section header into each following position row.
- Parse `PositionRaw` for symbol and lot count when possible.
- Parse `DateAcquired` into `yyyy-MM-dd`.
- Preserve `PositionRaw` exactly enough to audit parsing decisions.

### `ingestion_manifest.csv`

```text
ExportType
SourceHash
RawStoredPath
OriginalFileName
ExportTitle
ExportedAtLocal
ExportedAtTimeZone
RowCount
MinDate
MaxDate
RebuiltAtLocal
```

Implementation hints:

- `MinDate` and `MaxDate` for orders should use order dates.
- `MinDate` and `MaxDate` for portfolio lot-level files should use `DateAcquired`.
- Balance exports may have blank `MinDate` and `MaxDate` because they are point-in-time snapshots.

## Incremental Merge and Rebuild

The datastore is cumulative. Later E*TRADE exports usually overlap prior exports. Agents must **merge** new data into the existing store; they must not replace the datastore with only the latest attachment.

### Raw layer

1. Compute a SHA-256 content hash for every newly supplied file.
2. Compare the hash against existing raw files and `ingestion_manifest.csv`.
3. If the hash already exists, do **not** create another raw copy. Record the file as already present.
4. If the hash is new, store the native export unchanged under the appropriate `{userDatastore}/data/raw/etrade/` subfolder using the filename pattern:

```text
<ingestionTimestamp>-<hashPrefix>-<originalFileName>
```

Raw files are append-only. Never edit or delete prior raw exports during a merge.

### Canonical layer

After any new raw file is added, rebuild canonical tables from **all** raw files currently in `{userDatastore}/data/raw/etrade/`.

Canonical rebuild is a full re-derivation, not an in-place patch. Derived tables may be regenerated when parsing rules improve.

### Merge rules by export type

| Export type | Merge behavior | Dedup key | Prefer on conflict |
|---|---|---|---|
| `orders` | Union all raw order exports | `Symbol`, `Status`, `Fill`, `Description`, `Market`, `Time`, `AccountId` | Row from the export with the later `ExportedAtLocal` |
| `account_history` | Union all account-specific history exports | `AccountId`, `ActivityDateTime`, `ActivityType`, `Description`, `Amount`, `Fee`, `Commission` | Row from the export with the later `ExportedAtLocal` |
| `balances` | Keep every snapshot | none — snapshots coexist | n/a |
| `portfolio_lot_level` | Keep every snapshot | none — snapshots coexist by `AsOfLocal` | n/a |
| `accounts.csv` | Derived from balances | one row per `AccountId` from the latest balance snapshot | latest `AsOfLocal` |
| `cash.csv` | Derived from balances and portfolio snapshots | snapshot rows coexist | n/a |
| `cash_activity_daily.csv` | Rebuilt from merged `account_history.csv` | n/a | n/a |
| `income_events.csv` | Rebuilt from merged `account_history.csv` | n/a | n/a |
| `cash_balance_estimated.csv` | Rebuilt from merged balances + daily cash activity | n/a | n/a |

### Important merge expectations

- A newer orders export may contain **fewer rows** than an older export because E*TRADE order downloads can be rolling windows. Preserve rows that exist only in older raw files.
- A newer account-history export for one account may contain **far fewer rows** than an older export for the same account. Preserve older-only activity rows.
- Overlapping rows between exports are expected and must be deduplicated, not double-counted.
- Point-in-time exports (`balances`, `portfolio_lot_level`) accumulate as historical snapshots. Treat the latest snapshot as current context unless an analysis explicitly compares snapshots.
- After rebuild, update `ingestion_manifest.csv` from all raw files and set `RebuiltAtLocal` to the rebuild time.

### Post-merge validation

Before period selection or analysis, verify at minimum:

1. Every `ingestion_manifest.csv` row points to an existing raw file whose hash matches `SourceHash`.
2. Canonical dedup keys contain no duplicates for `orders.csv` and `account_history.csv`.
3. Combined date ranges in canonical tables reflect the merged result, not just the newest attachment.
4. Newly expected dates or accounts from the supplied files appear in canonical output.
5. Raw file count increased only for truly new hashes.

State any validation failure, partial merge, or parser limitation explicitly before proceeding.

## Datastore-Aware Period Selection

Before structured input discovery, agents must:

1. Inspect the current canonical datastore.
2. Evaluate any newly supplied files.
3. Add non-duplicate raw files to `{userDatastore}/data/raw/etrade/`.
4. Rebuild canonical CSV tables from all raw files using the merge rules above.
5. Validate the merged canonical datastore.
6. Determine the combined available date range from canonical data.

Structured input discovery must then ask whether the user wants to add more data, use the full available range, or select a subset.

## Legacy Entry Limitation

Open positions may have acquisition dates before the available order history. This is expected.

Agents may report on legacy entries associated with recent exits, but must not claim full lifecycle reconstruction unless the raw order history or user-provided notes support it.
