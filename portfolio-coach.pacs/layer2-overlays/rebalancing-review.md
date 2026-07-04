# Overlay — rebalancing-review

## Overlay Kind

`enrichment`

## Purpose

Rebalancing quality, churn, concentration, and redeployment analysis when `rebalancingReview == true`.

## Procedure

When `rebalancingReview == true`:

1. Extend portfolio composition quantification with rebalancing-specific tables and scoreboard
2. Read `RebalancingHints.md` from `portfolio-concentration-resilience` skill output (equal-weight delta scaffold)
3. Merge enrichment sections into the delivered report file
