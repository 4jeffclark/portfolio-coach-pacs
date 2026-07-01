---
name: evaluation-entry-interview
compatibility: Requires Python 3.11+ when running bundled scripts
outputCompleteness: scaffold
description: Conduct pre-report evaluation entry interview after quantification context is available; write Interview.md.
metadata:
  packId: portfolio-coach
  layer: '1'
---

## Procedure

1. Run `scripts/run.py` with `--evaluation true` when an evaluation overlay is active
2. Run only after input discovery, period confirmation (when applicable), and core quantification skills
3. **User present:** record verbatim Q&A in `Interview.md` and embed in `Report.md` Appendix
4. **Unattended:** record agent preliminary observations; mark `User responses: deferred` in Inputs Resolved

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/run.py` | Writes `Interview.md` template |

```powershell
python scripts/run.py --datastore $env:USER_DATASTORE --workspace $env:AGENT_WORKSPACE --evaluation true
```

## References

- Evaluation overlays on portfolio, trade, and activity playbooks

## Outputs

- `Interview.md` — entry interview template; agent fills responses or observations

## Used by

- Evaluation overlays on `portfolio-composition-review`, `symbol-trade-review`, `trading-activity-review`, and `market-regime-review`
