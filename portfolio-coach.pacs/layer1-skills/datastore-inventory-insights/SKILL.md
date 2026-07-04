---
name: datastore-inventory-insights
compatibility: Requires Python 3.11+ when running bundled scripts
outputCompleteness: scaffold
description: Synthesize datastore readiness insights and scorecard for datastore-inventory evaluation overlay.
metadata:
  packId: portfolio-coach
  layer: '1'
---

## Procedure

1. Run `scripts/run.py` after `datastore-inventory` completes
2. Read scorecard scaffold from workspace and merge into the delivered report file Evaluation section
3. Add agent reflection on export gaps and coverage (scorecard provides quantitative baseline)

## Scripts

Run from this skill directory. Paths are relative to the skill root per [agentskills.io](https://agentskills.io/specification).

| Script | Purpose |
| --- | --- |
| `scripts/run.py` | Execute skill logic; writes workspace artifacts and `skill-result.json` |

```bash
python scripts/run.py --datastore "$USER_DATASTORE" --workspace "$AGENT_WORKSPACE" --evaluation true
```

```powershell
python scripts/run.py --datastore $env:USER_DATASTORE --workspace $env:AGENT_WORKSPACE --evaluation true
```

## References

None.

## Outputs

- `DatastoreInventoryScorecard.md` — **assembly-only** quantitative baseline; merge into delivered report Evaluation section

## Used by

- `layer3-playbooks/datastore-inventory` (evaluation overlay only)
