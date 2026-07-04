# Overlay — symbol-trade-evaluation

## Overlay Kind

`evaluation`

## Purpose

Trade decision evaluation: entry interview, scorecard, verdict, exit interview.

## Procedure

When `evaluation == true` on `symbol-trade-review`:

1. Run `evaluation-entry-interview` after core symbol analysis
2. Agent synthesizes trade scorecard and verdict
3. Run `exit-interview`
4. Merge into `Report.md`

## Used skills

- `layer1-skills/evaluation-entry-interview`
- `layer1-skills/exit-interview`
