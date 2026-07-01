# Overlay — portfolio-composition-evaluation

## Overlay Kind

`evaluation`

## Layer

2 — `layer2-overlays/`

## Purpose

Structured portfolio evaluation: entry interview, scorecard, judgment, exit interview.

## Procedure

When `evaluation == true` on `portfolio-composition-review`:

1. Run `evaluation-entry-interview` after mapping gates and core quantification
2. Agent synthesizes portfolio evaluation scorecard and judgment sections
3. Run `exit-interview`
4. Merge into `Report.md` Evaluation section

## Used skills

- `layer1-skills/evaluation-entry-interview`
- `layer1-skills/exit-interview`
