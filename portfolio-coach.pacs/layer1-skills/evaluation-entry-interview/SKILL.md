---
name: evaluation-entry-interview
compatibility: Requires Python 3.11+ when running bundled scripts
outputCompleteness: scaffold
description: Conduct pre-report evaluation entry interview after quantification context is available; workspace scaffold for merge into delivered report.
metadata:
  packId: portfolio-coach
  layer: '1'
---

## Procedure

1. Run `scripts/run.py` with `--evaluation true` when an evaluation overlay is active
2. Run only after input discovery, period confirmation (when applicable), and core quantification skills
3. **User present:** record verbatim Q&A and embed in the delivered report file (Appendix: Entry Interview)
4. **Unattended:** record agent preliminary observations in the delivered report; mark `User responses: deferred` in Inputs Resolved

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/run.py` | Writes assembly-only `Interview.md` workspace template |

```powershell
python scripts/run.py --datastore $env:USER_DATASTORE --workspace $env:AGENT_WORKSPACE --evaluation true
```

## References

- Evaluation overlays on portfolio, trade, and activity playbooks

## Outputs

- `Interview.md` — **assembly-only** workspace template; merge content into the delivered report file

## Used by

- Evaluation overlays on `portfolio-composition-review`, `symbol-trade-review`, `trading-activity-review`, and `market-regime-review`
