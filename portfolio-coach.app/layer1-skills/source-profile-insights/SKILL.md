---
name: source-profile-insights
compatibility: Requires Python 3.11+ when running bundled scripts
description: Synthesize datastore insights, scorecard, and coverage readiness for source-profile evaluation overlay.
metadata:
  packId: portfolio-coach
  layer: '1'
---

## Procedure

1. Optional developer/trader reflection on coverage gaps and export practices (not trading coaching)
2. Document most useful insights the datastore supports
3. Scorecard on coverage, quality, and export readiness

## Scripts

Run from this skill directory. Paths are relative to the skill root per [agentskills.io](https://agentskills.io/specification).

| Script | Purpose |
| --- | --- |
| `scripts/run.py` | Execute skill logic; writes workspace artifacts and `skill-result.json` |

```bash
python scripts/run.py --datastore "$USER_DATASTORE" --workspace "$AGENT_WORKSPACE" --evaluation true
```

Set `compatibility: Requires Python 3.11+` when the runtime must execute bundled scripts.

## References

None.

## Outputs

- `SourceProfileScorecard.md`

## Used by

- `layer3-playbooks/source-profile` (evaluation overlay only)