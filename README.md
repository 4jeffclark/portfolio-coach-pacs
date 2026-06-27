# PortfolioCoach APP

Published **APP distribution repo** for PortfolioCoach — domain workflows for E*TRADE datastore inventory and quality review.

| Pack | Description |
| --- | --- |
| [`portfolio-coach.app/`](portfolio-coach.app/) | Source profile playbook — datastore inventory and quality review |

## Layout

```text
portfolio-coach-app/
  README.md                 ← this file (pack index)
  portfolio-coach.app/      ← pack instance
```

Pack entry: [`portfolio-coach.app/pack.app.yaml`](portfolio-coach.app/pack.app.yaml).

## Standards

APP format and execution rules are defined in the [APP Standards Workbench](https://github.com/4jeffclark/agent-playbook-pack):

- Authoring standard: [`standard/app-authoring.md`](https://github.com/4jeffclark/agent-playbook-pack/blob/main/standard/app-authoring.md)
- Reference instance (minimal): [`hello-world.app`](https://github.com/4jeffclark/agent-playbook-pack/tree/main/examples/hello-world.app)

Execution agents learn APP from the workbench standard, then consume this repo's pack manifests and referenced layer artifacts. Pack `README.md` files are user welcome only — not execution authority.

## Try it

- *Run a source profile for May 2026.*
- *Profile my datastore without the evaluation overlay.*

Persistent data and reports belong under the bound `{userDatastore}` (see `portfolio-coach.app/contracts/user-datastore-layout.md`), not in this behavior repo.
