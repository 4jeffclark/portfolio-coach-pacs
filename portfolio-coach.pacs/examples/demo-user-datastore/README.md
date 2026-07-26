# Demo user datastore

Anonymized sample PortfolioCoach `{userDatastore}` for local quickstart.

- **Source:** private E*TRADE exports, identity-remapped and money-scaled (×0.1)
- **Layout:** standard (`data/raw/etrade/`, `data/canonical/`)
- **Not included:** `inputs/`, `knowledge/`, or prior analytic `reports/` (this folder stays empty until you run playbooks)
- **Not real:** synthetic account ids/names; real tickers and dates retained for realism

Bind your agent `userDatastore` to this folder (or a copy) and start with
`datastore-inventory`, then an analytic playbook for a period covered by the
positions snapshots (see [`../README.md`](../README.md)).

Regenerate from a private tree:

```bash
python ../anonymize_user_datastore.py --source /path/to/private/PortfolioCoach
```
