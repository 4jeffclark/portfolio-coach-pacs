---
name: exit-interview
compatibility: Requires Python 3.11+ when running bundled scripts
outputCompleteness: scaffold
description: Conduct exit interview questions for evaluation overlays; write ExitInterview.md.
metadata:
  packId: portfolio-coach
  layer: '1'
---

## Procedure

1. Run `scripts/run.py` with `--evaluation true` when the evaluation overlay is active
2. **User present:** record verbatim Q&A in `ExitInterview.md` and embed in `Report.md` Appendix E
3. **Unattended (fire-and-forget):** record agent preliminary observations under the Unattended execution heading; mark `User responses: deferred` in Inputs Resolved appendix — do not leave prompts unanswered

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

- Evaluation overlays under `layer2-overlays/*-evaluation.md`

## Outputs

- `ExitInterview.md` — template with unattended-execution guidance; agent fills responses or observations

## Used by

- Evaluation overlays on member playbooks
