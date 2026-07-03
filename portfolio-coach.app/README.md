# PortfolioCoach

APP pack — **six member playbooks** with composable overlays. Catalog: [repository README](../README.md).

## Execution model

Scaffold skills write CSVs and `ReportSectionFragments.json` under `{agentWorkspace}`. Agents merge all content into a single delivered report file:

```text
{userDatastore}/reports/{timestamp}-{PlaybookReportId}-{params}/{timestamp}-{PlaybookReportId}-{params}.md
```

See [`contracts/report-delivery-contract.md`](contracts/report-delivery-contract.md).

## Try it

- *Inventory my datastore.*
- *Portfolio composition review for May 2026.*
- *Symbol trade review for MSFT.*
