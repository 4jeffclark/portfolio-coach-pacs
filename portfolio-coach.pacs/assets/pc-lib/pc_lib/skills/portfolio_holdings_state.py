"""Portfolio holdings state skill."""

from __future__ import annotations

from pc_lib.analytics import (
    latest_snapshot_date,
    positions_at_snapshot,
    resolve_period_start_snapshot,
    symbol_market_values,
    total_market_value,
)
from pc_lib.canonical import load_canonical, ymd_to_iso
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_metrics


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "portfolio-holdings-state")
    positions = load_canonical(args.datastore, "positions_lot_level.csv")
    start_iso = ymd_to_iso(args.period_start) or ""
    end_iso = ymd_to_iso(args.period_end) or ""
    start_snap, start_fallback = resolve_period_start_snapshot(positions, start_iso)
    end_snap = latest_snapshot_date(positions, end_iso)
    start_pos = positions_at_snapshot(positions, start_snap)
    end_pos = positions_at_snapshot(positions, end_snap)
    start_total = total_market_value(start_pos)
    end_total = total_market_value(end_pos)
    metrics = {
        "periodStartSnapshot": start_snap,
        "periodEndSnapshot": end_snap,
        "periodStartSnapshotFallback": str(start_fallback),
        "periodStartTotalMV": round(start_total, 2),
        "periodEndTotalMV": round(end_total, 2),
        "periodStartSymbolCount": len(symbol_market_values(start_pos)),
        "periodEndSymbolCount": len(symbol_market_values(end_pos)),
    }
    met_path = write_metrics(out / "Metrics.csv", metrics)
    start_note = " (earliest available; no export on/before period start)" if start_fallback else ""
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {
            "holdings_state": (
                f"Boundary snapshots: start {start_snap}{start_note} (${start_total:,.2f}), "
                f"end {end_snap} (${end_total:,.2f})."
            )
        },
    )
    return SkillResult(
        skill="portfolio-holdings-state",
        status="ok",
        artifacts=[str(met_path), str(frag)],
        metrics=metrics,
        messages=["Computed portfolio holdings boundary state"],
    )
