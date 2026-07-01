# PortfolioCoach Python library

Shared stdlib-only helpers for `layer1-skills/*/scripts/run.py`.

Skill scripts resolve this path:

```text
../../assets/pc-lib
```

(relative to `portfolio-coach.app/` instance root)

## Layout resolution

`pc_lib.canonical.resolve_layout()` selects datastore paths:

| Precedence | Canonical | Raw E*TRADE | Knowledge |
| --- | --- | --- | --- |
| Standard (preferred) | `{userDatastore}/data/canonical/` | `{userDatastore}/data/raw/etrade/` | `{userDatastore}/data/knowledge/` |
| Legacy | `{userDatastore}/canonical/` | `{userDatastore}/raw/etrade/` | `{userDatastore}/knowledge/` |

When both exist, standard wins. `validate_layout()` fails fast with a clear error when no usable layout is found.

## Period helpers

`default_period_windows(analysis_start_ymd, analysis_end_ymd)` computes lookback and follow-through defaults per `period-scope-confirmation` workflow.

## Workspace

Skills write under `{agentWorkspace}/<skill-id>/`. The platform should pass the active per-run subdirectory as `--workspace` when available (see APP `app-execution.md`).

## Date columns

`CANONICAL_DATE_COLUMNS` maps each canonical table to contract-defined date fields (e.g. `orders.csv` uses `Date`, not `ExportedAtLocal`).

## E*TRADE ingest and rebuild

- `pc_lib.etrade_ingest` — classify and stage `inputs/` attachments into `raw/etrade/`
- `pc_lib.etrade_rebuild` — rebuild canonical CSV tables from all raw exports
- `datastore-ingest` skill — orchestrates staging, rebuild, and validation for the ingest playbook
