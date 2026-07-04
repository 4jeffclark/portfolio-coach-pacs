# D3 exposure quality gate — test fixture

Exercise post-run checklist **D3** and `market-regime-review` exposure data-quality gate when `exposureNumericSymbolCount > 0`.

## Expected behavior

When `market-environment` sets `exposureQualityValid: false`:

1. Delivered report banners **`DATA QUALITY — EXPOSURE TABLE INVALID`**
2. **No** period-end exposure weight tables
3. Activity (notional) tables may remain if orders are valid
4. **No** exposure-based coaching (#6 overlay)
5. Post-run attestation: **`failed`** with failed item **`D3`**

## Synthetic corrupt rows

Append these rows to a **scratch copy** of `positions_lot_level.csv` (do not commit corrupt canonical to production datastores). Use a dedicated test datastore or restore from backup after the test.

```csv
testhash,raw/test/lot-bug.csv,2026-07-01 12:00:00,EST,999999999,x9999,Test Account,50  09/07/2018,,50,,09/07/2018,Short term,100,200,,200,,100,,12085,,,,
testhash,raw/test/lot-bug.csv,2026-07-01 12:00:00,EST,999999999,x9999,Test Account,100  01/15/2020,,100,,01/15/2020,Long term,50,300,,300,,50,,30000,,,,
```

With v4.0.2+ ingest, lot-detail rows should **not** appear after `datastore-ingest` rebuild. To exercise D3 on v4.0.3+, either:

- Temporarily revert `etrade_rebuild.py` lot-detail skip in a **throwaway branch**, rebuild, run #4/#6; or
- Manually append the rows above **after** rebuild (simulates pre-fix canonical)

## Verification prompt (execution session)

```text
Run market-regime-review #4 for 20260101–20260701 on <test-datastore>.
If exposureNumericSymbolCount > 0, banner DATA QUALITY — EXPOSURE TABLE INVALID,
omit exposure tables, and attest post-run failed (D3).
```

## Pass path regression

On a clean v4.0.3+ datastore after ingest rebuild:

```text
exposureNumericSymbolCount: 0
exposureQualityValid: true
```

See harness `Dev/fixtures/d3-exposure-quality/` for a copy-paste snippet.
