"""Datastore inventory insights skill."""

from __future__ import annotations

import csv
from pathlib import Path

from pc_lib.canonical import work_dir
from pc_lib.cli import SkillArgs, SkillResult


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run(args: SkillArgs) -> SkillResult:
    out = work_dir(args.workspace, "datastore-inventory-insights")
    inv_dir = work_dir(args.workspace, "datastore-inventory")
    inv = inv_dir / "DataStoreInventory.csv"
    cov = inv_dir / "AccountCoverage.csv"
    met = inv_dir / "Metrics.csv"
    scorecard = out / "DatastoreInventoryScorecard.md"

    inv_rows = _read_csv(inv)
    cov_rows = _read_csv(cov)
    met_rows = {r["Metric"]: r["Value"] for r in _read_csv(met) if r.get("Metric")}

    canon = [r for r in inv_rows if r.get("ArtifactType") == "canonical"]
    raw = [r for r in inv_rows if r.get("ArtifactType") == "raw"]
    orders = next((r for r in canon if r.get("Name") == "orders.csv"), {})
    gaps = [r for r in cov_rows if r.get("CoverageGaps")]

    lines = [
        "# Datastore Inventory Scorecard",
        "",
        "## Coverage summary",
        "",
        f"- Layout resolved: **{met_rows.get('layoutResolved', 'unknown')}**",
        f"- Accounts profiled: **{met_rows.get('accountCount', str(len(cov_rows)))}**",
        f"- Raw files indexed: **{len(raw)}**",
        f"- Canonical tables indexed: **{len(canon)}**",
        f"- Orders date range: {orders.get('DateMin', 'n/a')} → {orders.get('DateMax', 'n/a')}",
        f"- Validation pass (dedup keys): **{met_rows.get('validationPass', 'unknown')}**",
        f"- Position snapshots: **{met_rows.get('positionSnapshotCount', '0')}** "
        f"({met_rows.get('positionSnapshotDateMin', 'n/a')} → {met_rows.get('positionSnapshotDateMax', 'n/a')})",
        "",
        "## Export readiness",
        "",
    ]
    if gaps:
        lines.append(f"- Accounts with coverage gaps: **{len(gaps)}**")
        for row in gaps[:5]:
            lines.append(
                f"  - {row.get('AccountLabel', row.get('AccountId', ''))}: {row.get('CoverageGaps', '')}"
            )
        if len(gaps) > 5:
            lines.append(f"  - … and {len(gaps) - 5} more (see AccountCoverage.csv)")
    else:
        lines.append("- No account-level coverage gaps flagged in AccountCoverage.csv")

    if met_rows.get("positionSnapshotSparseWarn") == "True":
        lines.extend(
            [
                "",
                "## Position snapshot readiness",
                "",
                "- **Warning:** fewer than two position snapshots in canonical data. "
                "Composition and regime reviews may rely on earliest-snapshot fallback for period-start weights.",
            ]
        )

    lines.extend(
        [
            "",
            "## Useful insights supported by this datastore",
            "",
            "- Order and account-history activity ranges per account (AccountCoverage.csv)",
            "- Canonical inventory hashes and row counts (DataStoreInventory.csv)",
            "- Dedup validation flags (Metrics.csv)",
            "",
            "## Agent reflection",
            "",
            "Document export cadence gaps, parser limitations, and follow-up export actions. "
            "Do not infer trading coaching from this scorecard.",
            "",
        ]
    )
    if args.evaluation:
        lines.append("_Evaluation overlay: complete exit interview after scorecard._")

    scorecard.write_text("\n".join(lines), encoding="utf-8")
    return SkillResult(
        skill="datastore-inventory-insights",
        status="ok",
        artifacts=[str(scorecard)],
        messages=["Wrote quantitative datastore inventory scorecard"],
    )
