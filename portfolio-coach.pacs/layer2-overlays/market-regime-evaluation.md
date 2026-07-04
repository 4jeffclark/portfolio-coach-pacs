# Overlay — market-regime-evaluation

## Overlay Kind

`evaluation`

## Layer

2 — `layer2-overlays/`

## Purpose

Regime interpretation judgment, coaching notes, and exit interview on top of the market regime memo.

## Procedure

When `evaluation: true` on `market-regime-review`:

1. Read `Metrics.csv` from `market-environment` **before** synthesizing coaching
2. If `exposureQualityValid` is **false**: skip exposure-based coaching; record data-quality limitation; do not compare MV or weight tables
3. Agent synthesizes regime interpretation judgment after `market-environment` core output (activity + valid exposure only)
4. Run `exit-interview` per its `SKILL.md`
5. Merge evaluation sections into the delivered report file

### Portfolio linkage in coaching

Coaching judgment **must** reference skill-produced exposure and activity when valid:

- Cite **period-end weight %** (`PeriodEndWeightPct`) for capital concentration observations
- Cite **period gross notional** (`PeriodGrossNotional`) and **ActivityToWeightRatio** for activity intensity
- When exposure is unavailable or invalid, say so and point the user to `portfolio-composition-review` (menu #7) for conviction sizing

Coaching **must not**:

- Use filled-order count or order-count share as a conviction or concentration proxy
- Recommend caps or sizing actions based solely on order frequency
- Treat numeric-only symbols (e.g. `50`, `100`) as holdings — indicates ingest failure
- Claim snapshot alignment or MV step-changes when `exposureQualityValid` is false

### Exit interview completion

- **User present:** collect verbatim responses before attesting post-run pass; embed Q&A in the delivered report
- **User absent / fire-and-forget:** mark `User responses: deferred` in Inputs Resolved and record agent preliminary observations per `exit-interview` SKILL — do not leave prompts unanswered with a "passed" attestation
- Do not attest `Post-run checklist: passed` while exit-interview prompts remain pending when the user is present
- Do not attest `Post-run checklist: passed` when `exposureQualityValid` is false and the report includes exposure-based coaching

## Used skills

- `layer1-skills/exit-interview`
