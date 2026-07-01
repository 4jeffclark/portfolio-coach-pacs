"""Period weight reconstruction skill."""

from __future__ import annotations

from pc_lib.analytics import latest_snapshot_date, positions_at_snapshot, symbol_market_values, total_market_value
from pc_lib.canonical import load_canonical, write_csv, ymd_to_iso
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_metrics


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "period-weight-reconstruction")
    positions = load_canonical(args.datastore, "positions_lot_level.csv")
    start_iso = ymd_to_iso(args.period_start) or ""
    end_iso = ymd_to_iso(args.period_end) or ""
    start_snap = latest_snapshot_date(positions, start_iso)
    end_snap = latest_snapshot_date(positions, end_iso)
    start_mv = symbol_market_values(positions_at_snapshot(positions, start_snap))
    end_mv = symbol_market_values(positions_at_snapshot(positions, end_snap))
    start_total = total_market_value(positions_at_snapshot(positions, start_snap)) or 1
    end_total = total_market_value(positions_at_snapshot(positions, end_snap)) or 1
    symbols = sorted(set(start_mv) | set(end_mv))
    rows = []
    for sym in symbols:
        smv = start_mv.get(sym, 0)
        emv = end_mv.get(sym, 0)
        rows.append(
            {
                "Symbol": sym,
                "PeriodStartMV": f"{smv:.2f}",
                "PeriodEndMV": f"{emv:.2f}",
                "PeriodStartWeightPct": f"{smv / start_total * 100:.2f}",
                "PeriodEndWeightPct": f"{emv / end_total * 100:.2f}",
                "PeriodStartWeightSource": "observed_snapshot" if smv else "unavailable",
                "PeriodEndWeightSource": "observed_snapshot" if emv else "unavailable",
            }
        )
    path = write_csv(
        out / "SymbolWeights.csv",
        [
            "Symbol", "PeriodStartMV", "PeriodEndMV",
            "PeriodStartWeightPct", "PeriodEndWeightPct",
            "PeriodStartWeightSource", "PeriodEndWeightSource",
        ],
        rows,
    )
    metrics = {
        "periodStartSnapshot": start_snap,
        "periodEndSnapshot": end_snap,
        "reconstructedSymbolCount": len(rows),
    }
    met_path = write_metrics(out / "Metrics.csv", metrics)
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {"weight_reconstruction": f"Reconstructed weights for {len(rows)} symbols from snapshot anchors."},
    )
    return SkillResult(
        skill="period-weight-reconstruction",
        status="ok",
        artifacts=[str(path), str(met_path), str(frag)],
        metrics=metrics,
        messages=["Wrote period weight reconstruction table"],
    )
