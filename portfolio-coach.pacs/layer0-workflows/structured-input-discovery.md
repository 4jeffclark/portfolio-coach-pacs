# Workflow — structured-input-discovery

## Workflow Id

`structured-input-discovery`

## Layer

0 — infrastructure

## Workflow kind

**Agent-only procedure** — no companion script. Minimum gate evidence: **Inputs Resolved** block embedded in report Appendix.

## Purpose

Resolve playbook inputs from natural language before core execution.

## Procedure

1. **Parse** — infer `evaluation`, `analysisPeriodStart`, and `analysisPeriodEnd` from the user request, attachments, and bound `{userDatastore}` context
2. **Summarize** — present **Inputs Resolved** with each parameter marked `confirmed`, `default`, or `pending`
3. **Reconcile** — ask plain-language questions only for pending or ambiguous parameters
4. **Period defaults** — when the user omits a period, apply playbook `defaultResolution.period` from `<playbook-id>.pacs.yaml`:
   - `fullAvailableRange` — widest range available in the bound datastore (default for `datastore-inventory`)
   - `latestCalendarMonth` — most recent complete calendar month in data
   - `requireExplicit` — do not infer; treat as pending
5. **Legacy treatment names** — when the user names a treatment (`PortfolioRebalancing`, `DayTrading`, etc.), resolve to the playbook id in [`contracts/playbook-index.md`](../contracts/playbook-index.md) (kebab-case id; PlaybookReportId is PascalCase)
6. **Confirm** — finalize the input block before clearing the `inputs-resolved` gate (see `<playbook-id>.pacs.yaml`)

Users do not need fixed parameter syntax (for example `evaluation: false`).

## Outputs

- Final **Inputs Resolved** block (embed in report Appendix)
- Cleared `inputs-resolved` gate (self-attested)
