# Workflow — datastore-merge-and-validate

## Workflow Id

`datastore-merge-and-validate`

## Layer

0 — infrastructure

## Workflow kind

**Validate-only prelude** for analytic playbooks. Confirms the bound datastore is readable and notes available date range. Does not stage attachments or rebuild canonical tables — use the `datastore-ingest` playbook for that.

## Purpose

Validate the bound datastore layout and report available date range for input discovery.

## Procedure

1. Resolve layout per [`contracts/user-datastore-layout.md`](../contracts/user-datastore-layout.md)
2. Validate existing canonical tables are present and readable; note layout warnings from `pc-lib`
3. Summarize available date range from `ingestion_manifest.csv` or canonical date columns
4. Clear the `datastore-merge-complete` gate (self-attested)

When the user supplies new exports, run `datastore-ingest` before analytic playbooks.

## Outputs

- Datastore range summary for structured input discovery
- Cleared `datastore-merge-complete` gate (self-attested)
