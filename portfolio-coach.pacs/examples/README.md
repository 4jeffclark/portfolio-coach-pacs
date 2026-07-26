# PortfolioCoach examples

## Demo user datastore

[`demo-user-datastore/`](demo-user-datastore/) is a ready-to-bind anonymized `{userDatastore}` for local quickstart.

| Path | Role |
| --- | --- |
| `demo-user-datastore/data/raw/etrade/` | Anonymized E*TRADE exports |
| `demo-user-datastore/data/canonical/` | Rebuildable canonical tables |
| `demo-user-datastore/reports/` | Empty — playbooks write here |

**Not included:** session `inputs/`, `knowledge/`, or prior `reports/` (generate those by running playbooks).

### Anonymization

- Account ids / masks / labels remapped to synthetic values (`900001001` / `x1001`, …)
- Person names replaced with `DEMO` / `USER`
- Dollar amounts and per-share prices scaled by **0.1**; share quantities unchanged
- The `Fill` column (`qty @ price`) is scaled with the same factor as the price text inside `Description`, so `FillPrice` and Description limit prices agree (earlier demo builds scaled only `Description`, leaving `FillPrice` 10x too high)
- Real tickers and calendar dates retained so theme/regime behavior stays realistic
- This is **demo data**, not a real account and not financial advice

Regenerate after refreshing a private source tree:

```bash
python portfolio-coach.pacs/examples/anonymize_user_datastore.py ^
  --source /path/to/private/PortfolioCoach
```

### Quickstart

1. Bind the execution agent `userDatastore` to  
   `portfolio-coach.pacs/examples/demo-user-datastore`  
   (or copy that folder somewhere writable if you prefer not to dirty the repo).
2. Run **`datastore-inventory`** over the available span (canonical activity roughly `20210126`–`20260701`).
3. Run an analytic playbook for a window that has positions snapshots, for example:
   - `portfolio-composition-review` with `analysisPeriodStart: 20260101`, `analysisPeriodEnd: 20260701`
   - `market-regime-review` for the same end date
   - `trading-activity-review` for a shorter recent window if you want a tighter debrief

Snapshot-backed exposure in this demo is densest around mid/late June–1 Jul 2026 exports; prefer period ends on or near `20260701` when linking regime and composition.
