# Workflow — period-scope-confirmation

## Workflow Id

`period-scope-confirmation`

## Layer

0 — infrastructure

## Workflow kind

**Agent-only procedure** — no companion script. Minimum gate evidence: confirmed period parameters in **Inputs Resolved** and, when applicable, weight-reconstruction plan summary in report Appendix.

## Purpose

Confirm analysis period, lookback, follow-through, and snapshot/reconstruction anchors after datastore merge and structured input discovery.

Required for playbooks that analyze a bounded period with weight reconstruction or period-scoped trading activity. **Not required** for `datastore-inventory` (inventory-only).

## Procedure

After `structured-input-discovery` resolves `analysisPeriodStart` and `analysisPeriodEnd`, confirm or default the extended period windows:

| Window | Parameters | Default |
| --- | --- | --- |
| Analysis period | `analysisPeriodStart`, `analysisPeriodEnd` | From input discovery or full datastore range |
| Lookback | `lookbackStart`, `lookbackEnd` | 4 weeks before analysis start → day before start |
| Follow-through | `followThroughStart`, `followThroughEnd` | Day after analysis end → +1 week when data exists |
| Period-end snapshot | `periodEndSnapshot` | Latest holdings on/before analysis end |
| Period-start snapshot | `periodStartSnapshot` | Latest holdings on/before analysis start |

1. **Present** — show analysis period and derived lookback/follow-through windows; mark each `confirmed`, `default`, or `pending`
2. **Reconcile** — ask plain-language questions only when the user narrowed or contradicted defaults
3. **Snapshot plan** — when exact holdings snapshots do not exist on period boundaries, note weight-reconstruction approach (see `period-weight-reconstruction` skill when shipped)
4. **Snapshot lag** — compute `periodEndSnapshotLagDays` from skill output or holdings metadata. When lag exceeds 14 days, present the gap and either (a) confirm user accepts stale exposure, or (b) set `analysisPeriodEnd` to the latest positions export date (`YYYYMMDD`) for aligned exposure
5. **Export alignment** — prefer `analysisPeriodEnd` matching the latest `positions_lot_level` export date when the user wants period-end weights in portfolio linkage; document the choice in Inputs Resolved
6. **Confirm** — embed final period block in report Appendix before clearing `period-confirmed` gate

Use `pc-lib` period helpers (`default_period_windows`) when computing defaults from YYYYMMDD bounds.

## Outputs

- Confirmed period parameters in **Inputs Resolved**
- Weight reconstruction plan summary when period boundaries lack exact snapshots
- Cleared `period-confirmed` gate (self-attested)
