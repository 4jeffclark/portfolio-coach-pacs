# Overlay — datastore-inventory-evaluation

## Overlay Kind

`evaluation`

## Layer

2 — `layer2-overlays/`

## Purpose

Readiness insights, coverage-gap reflection, and exit interview on top of datastore inventory.

## Procedure

When `evaluation: true` on `datastore-inventory`:

1. Run `datastore-inventory-insights` per its `SKILL.md`
2. Run `exit-interview` per its `SKILL.md`
3. Merge evaluation sections into the delivered report file
4. **Unattended runs:** use agent preliminary observations in the delivered report exit-interview section when the user is not present; defer live Q&A

## Used skills

- `layer1-skills/datastore-inventory-insights`
- `layer1-skills/exit-interview`
