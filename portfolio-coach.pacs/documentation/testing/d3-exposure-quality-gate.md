# D3 exposure quality gate — test fixture

Exercise post-run checklist **D3** and `market-regime-review` exposure data-quality gate when `exposureNumericSymbolCount > 0`.

## Expected behavior

When `market-environment` sets `exposureQualityValid: false`:

1. Delivered report banners **`DATA QUALITY — EXPOSURE TABLE INVALID`**
2. **No** period-end exposure weight tables
3. Activity (notional) tables may remain if orders are valid
4. **No** exposure-based coaching (#6 overlay)
5. Post-run attestation: **`failed`** with failed item **`D3`**

## v4.0.2+ pass path — lot-detail snippet (Session 4)

Append these rows to a **scratch copy** of `positions_lot_level.csv`:

```csv
testhash,raw/test/lot-bug.csv,2026-07-01 12:00:00,EST,999999999,x9999,Test Account,50  09/07/2018,,50,,09/07/2018,Short term,100,200,,200,,100,,12085,,,,
testhash,raw/test/lot-bug.csv,2026-07-01 12:00:00,EST,999999999,x9999,Test Account,100  01/15/2020,,100,,01/15/2020,Long term,50,300,,300,,50,,30000,,,,
```

On **v4.0.2+**, ingest skips lot-detail rows and `market-environment` excludes them from exposure aggregation. Expect:

```text
exposureLotDetailRowCount: > 0 (rows may remain in CSV)
exposureNumericSymbolCount: 0
exposureQualityValid: true
Post-run D3: passed
```

This validates **fail-closed ingest**, not D3 failure. Session 4 confirmed this pass path.

## D3 failure path — when to use

With v4.0.3+ `symbol_market_values` and `position_symbol` hardening, **numeric tokens cannot enter the exposure MV map** from CSV fixtures alone. To exercise D3 **failure**:

| Approach | Use when |
| --- | --- |
| **Historical golden report** | Reference pre-v4.0.2 run `20260704-101835-MarketRegimeReview-20260101-20260701` (numeric symbols, ~$4.09M MV double-count) |
| **Throwaway branch** | Temporarily revert lot-detail skip in `etrade_rebuild.py` and summary-row filter in `analytics.py`; rebuild scratch datastore; run #4/#6 |
| **Manual pre-fix canonical** | Restore a canonical backup from before v4.0.2 lot-detail fix |

Do **not** expect D3 failure from the lot-detail snippet alone on v4.0.3+.

## Verification prompt (execution session)

Manifest inputs only:

```text
Run market-regime-review #4 on <scratch-datastore>.
analysisPeriodStart: 20260101
analysisPeriodEnd: 20260701
marketDepth: full
evaluation: false
```

**Reviewer checklist (not playbook inputs):** if `exposureNumericSymbolCount > 0`, expect D3 banner and post-run failed (D3).

## Pass path regression (production datastore)

On a clean v4.0.3+ datastore after ingest rebuild:

```text
exposureNumericSymbolCount: 0
exposureQualityValid: true
```

See harness `Dev/fixtures/d3-exposure-quality/` for the lot-detail pass-path snippet.
