---
name: exit-interview
compatibility: Requires Python 3.11+ when running bundled scripts
description: Conduct exit interview questions for source-profile evaluation overlay; write ExitInterview.md.
metadata:
  packId: portfolio-coach
  layer: '1'
---

## Procedure

1. Ask concise exit interview questions per `layer2-overlays/source-profile-evaluation.md`
2. Store responses in `ExitInterview.md`
3. Embed verbatim in `Report.md` Appendix E
4. Generate PDFs when available after integration

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

- `ExitInterview.md`

## Used by

- `layer3-playbooks/source-profile` (evaluation overlay only)