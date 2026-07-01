# Overlay — trading-activity-evaluation

## Overlay Kind

`evaluation`

## Purpose

Trading activity period evaluation: entry interview, activity scorecard, exit interview.

## Procedure

When `evaluation == true` on `trading-activity-review`:

1. Run `evaluation-entry-interview` after `trading-activity-analysis`
2. Agent synthesizes activity scorecard
3. Run `exit-interview`
4. Merge into `Report.md`

## Used skills

- `layer1-skills/evaluation-entry-interview`
- `layer1-skills/exit-interview`
