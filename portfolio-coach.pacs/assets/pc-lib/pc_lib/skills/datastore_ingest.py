"""Datastore ingest skill — stage attachments, rebuild canonical, validate."""

from __future__ import annotations

import json

from pc_lib.analytics import mapping_universe
from pc_lib.canonical import DatastoreLayoutError, load_canonical, validate_layout, work_dir, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.etrade_ingest import stage_inputs
from pc_lib.etrade_rebuild import rebuild_canonical


def _dedup_violations(rows: list[dict], keys: list[str]) -> int:
    seen: set[tuple[str, ...]] = set()
    dupes = 0
    for row in rows:
        key = tuple(row.get(k, "") for k in keys)
        if key in seen:
            dupes += 1
        seen.add(key)
    return dupes


def _available_range(datastore) -> tuple[str, str]:
    history = load_canonical(datastore, "account_history.csv")
    orders = load_canonical(datastore, "orders.csv")
    dates: list[str] = []
    for row in history:
        if row.get("ActivityDate"):
            dates.append(row["ActivityDate"][:10])
    for row in orders:
        if row.get("Date"):
            dates.append(row["Date"][:10])
    if not dates:
        return "", ""
    dates.sort()
    return dates[0].replace("-", ""), dates[-1].replace("-", "")


def run(args: SkillArgs) -> SkillResult:
    try:
        layout = validate_layout(args.datastore)
    except DatastoreLayoutError as exc:
        return SkillResult(skill="datastore-ingest", status="error", messages=[str(exc)])

    out = work_dir(args.workspace, "datastore-ingest")
    messages = list(layout.warnings)

    staged, stage_messages = stage_inputs(args.datastore, layout)
    messages.extend(stage_messages)

    positions_before: list[dict[str, str]] = []
    try:
        positions_before = load_canonical(args.datastore, "positions_lot_level.csv")
    except FileNotFoundError:
        positions_before = []
    position_rows_before = len(positions_before)
    symbol_count_before = len(mapping_universe(positions_before, [], None, None))

    rebuild_stats = rebuild_canonical(args.datastore, layout)
    messages.append(
        f"Rebuilt canonical tables at {rebuild_stats['rebuiltAtLocal']}: "
        f"{rebuild_stats['orderRows']} orders, {rebuild_stats['historyRows']} history rows, "
        f"{rebuild_stats.get('cashActivityDailyRows', 0)} cash-activity rows."
    )

    orders = load_canonical(args.datastore, "orders.csv")
    history = load_canonical(args.datastore, "account_history.csv")
    positions_after = load_canonical(args.datastore, "positions_lot_level.csv")
    position_rows_after = rebuild_stats.get("positionRows", len(positions_after))
    symbol_count_after = len(mapping_universe(positions_after, orders, None, None))
    symbol_count_delta = symbol_count_after - symbol_count_before
    orders_dedup = _dedup_violations(
        orders, ["Symbol", "Status", "Fill", "Description", "Market", "Time", "AccountId"]
    )
    history_dedup = _dedup_violations(
        history,
        ["AccountId", "ActivityDateTime", "ActivityType", "Description", "Amount", "Fee", "Commission"],
    )
    range_start, range_end = _available_range(args.datastore)

    merge_rows = staged or [{"OriginalFileName": "", "Action": "none", "Subfolder": "", "SourceHash": "", "StoredFileName": ""}]
    merge_path = write_csv(
        out / "MergeLog.csv",
        ["OriginalFileName", "Action", "Subfolder", "SourceHash", "StoredFileName", "RawStoredPath"],
        [{**row, "RawStoredPath": row.get("RawStoredPath", "")} for row in merge_rows],
    )

    metrics = {
        "layoutResolved": layout.name,
        "filesStaged": str(len([r for r in staged if r.get("Action") == "staged"])),
        "filesSkippedDuplicate": str(len([r for r in staged if r.get("Action") == "skipped_duplicate"])),
        "rebuiltAtLocal": rebuild_stats["rebuiltAtLocal"],
        "orderRows": str(rebuild_stats["orderRows"]),
        "historyRows": str(rebuild_stats["historyRows"]),
        "manifestRows": str(rebuild_stats["manifestRows"]),
        "cashActivityDailyRows": str(rebuild_stats.get("cashActivityDailyRows", 0)),
        "cashBalanceEstimatedRows": str(rebuild_stats.get("cashBalanceEstimatedRows", 0)),
        "incomeEventRows": str(rebuild_stats.get("incomeEventRows", 0)),
        "positionRowsBefore": str(position_rows_before),
        "positionRowsAfter": str(position_rows_after),
        "portfolioSymbolCountBefore": str(symbol_count_before),
        "portfolioSymbolCountAfter": str(symbol_count_after),
        "portfolioSymbolCountDelta": str(symbol_count_delta),
        "ordersDedupViolations": str(orders_dedup),
        "accountHistoryDedupViolations": str(history_dedup),
        "validationPass": str(orders_dedup == 0 and history_dedup == 0),
        "availableRangeStart": range_start,
        "availableRangeEnd": range_end,
    }
    met_path = write_csv(out / "Metrics.csv", ["Metric", "Value"], [{"Metric": k, "Value": v} for k, v in metrics.items()])

    fragments = {
        "section1_layout": (
            f"Datastore layout: **{layout.name}**. "
            f"Staged **{metrics['filesStaged']}** new file(s); "
            f"skipped **{metrics['filesSkippedDuplicate']}** duplicate(s)."
        ),
        "section2_attachments": "See `MergeLog.csv` for per-file staging outcomes.",
        "section3_validation": (
            f"Canonical rebuild completed at **{rebuild_stats['rebuiltAtLocal']}**. "
            f"Order dedup violations: **{orders_dedup}**. "
            f"Account history dedup violations: **{history_dedup}**. "
            f"Validation: **{'Pass' if metrics['validationPass'] == 'True' else 'Fail'}**. "
            f"Portfolio symbol universe: **{symbol_count_before}** → **{symbol_count_after}** "
            f"(delta **{symbol_count_delta:+d}**; position rows **{position_rows_before}** → **{position_rows_after}**)."
        ),
        "section4_available_range": (
            f"Available activity range after rebuild: **{range_start}** → **{range_end}** "
            "(from canonical orders and account_history)."
        ),
    }
    frag_path = out / "ReportSectionFragments.json"
    frag_path.write_text(json.dumps(fragments, indent=2) + "\n", encoding="utf-8")

    return SkillResult(
        skill="datastore-ingest",
        status="ok",
        artifacts=[str(merge_path), str(met_path), str(frag_path)],
        metrics=metrics,
        messages=messages,
    )
