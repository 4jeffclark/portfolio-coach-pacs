# Overlay — risk-review

## Overlay Kind

`enrichment`

## Purpose

Risk posture, de-risking, and gain-harvesting analysis when `riskReview == true`.

## Procedure

When `riskReview == true`:

1. Extend portfolio composition quantification with risk-specific tables and scoreboard
2. Read `RiskHints.md` from `portfolio-concentration-resilience` skill output (HHI and largest-bucket scaffold)
3. Merge enrichment sections into the delivered report file
