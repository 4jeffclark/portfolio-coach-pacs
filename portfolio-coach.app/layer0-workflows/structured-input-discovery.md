# Workflow — structured-input-discovery

## Workflow Id

`structured-input-discovery`

## Layer

0 — infrastructure

## Purpose

Resolve playbook inputs from natural language before core execution.

## Procedure

1. **Parse** — infer `evaluation`, `analysisPeriodStart`, and `analysisPeriodEnd` from the user request, attachments, and bound `{userDatastore}` context
2. **Summarize** — present **Inputs Resolved** with each parameter marked `confirmed`, `default`, or `pending`
3. **Reconcile** — ask plain-language questions only for pending or ambiguous parameters
4. **Confirm** — finalize the input block before clearing the `inputs-resolved` gate (see `<playbook-id>.app.yaml`)

Users do not need fixed parameter syntax (for example `evaluation: false`).

## Outputs

- Final **Inputs Resolved** block (embed in report Appendix)
- Cleared `inputs-resolved` gate
