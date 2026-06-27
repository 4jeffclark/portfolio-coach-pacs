# Workflow — datastore-merge-and-validate

## Workflow Id

`datastore-merge-and-validate`

## Layer

0 — infrastructure

## Purpose

Merge session attachments into the persistent datastore, rebuild canonical tables, validate, and report available date range.

## Procedure

Follow [`contracts/datastore-contract.md`](../contracts/datastore-contract.md):

1. Hash-check session attachments; skip duplicates already in `{userDatastore}/data/raw/etrade/`
2. Copy new exports to appropriate `{userDatastore}/data/raw/etrade/` subfolders
3. Rebuild all tables under `{userDatastore}/data/canonical/` from all raw files
4. Deduplicate orders and account history per contract keys
5. Validate merged canonical datastore
6. Report datastore range summary for input discovery
7. Clear the `datastore-merge-complete` gate (see `<playbook-id>.app.yaml`)

## Outputs

- Updated canonical tables
- Datastore range summary for structured input discovery
