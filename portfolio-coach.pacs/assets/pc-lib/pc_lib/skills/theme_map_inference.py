"""Theme map inference skill."""

from __future__ import annotations

from pc_lib.analytics import (
    latest_snapshot_date,
    positions_at_snapshot,
    symbol_market_values,
    theme_inference_metrics,
)
from pc_lib.canonical import load_canonical, load_knowledge_csv, read_csv, write_csv, ymd_to_iso
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import (
    THEME_MAP_FIELDS,
    THEME_REGISTRY_FIELDS,
    skill_out,
    write_fragments,
    write_metrics,
)
from pc_lib.theme_inference import infer_theme_registry


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "theme-map-inference")
    src = args.input_dir or (args.workspace / "holdings-map-confirmation")
    holdings = read_csv(src / "HoldingsMap.csv")

    positions = load_canonical(args.datastore, "positions_lot_level.csv")
    end_iso = ymd_to_iso(args.period_end) if args.period_end else None
    snap = latest_snapshot_date(positions, end_iso)
    snap_positions = positions_at_snapshot(positions, snap)
    symbol_mv = symbol_market_values(snap_positions)

    knowledge = load_knowledge_csv(args.datastore, "themes", "ThemeMapCurrent.csv")

    registry, theme_map, coverage, inference_log = infer_theme_registry(
        holdings, symbol_mv=symbol_mv, knowledge_theme_map=knowledge or None
    )

    reg_path = write_csv(out / "ThemeRegistry.csv", THEME_REGISTRY_FIELDS, registry)
    map_path = write_csv(out / "ThemeMap.csv", THEME_MAP_FIELDS, theme_map)
    cov_path = write_csv(
        out / "ThemeCoverage.csv",
        ["ThemeId", "ThemeLabel", "SymbolCount", "PeriodEndMV", "WeightPct"],
        coverage,
    )
    log_path = write_csv(
        out / "InferenceLog.csv",
        ["Symbol", "ThemeId", "RuleId", "MappingConfidence", "PeriodEndMV", "PeriodEndWeightPct"],
        inference_log,
    )
    metrics = theme_inference_metrics(coverage)
    metrics["assignmentCount"] = len(theme_map)
    metrics["periodEndSnapshot"] = snap
    met_path = write_metrics(out / "Metrics.csv", metrics)
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {
            "theme_inference": (
                f"Inferred {len(registry)} themes for {len(theme_map)} symbols; "
                f"coverage {metrics['inferenceCoveragePct']}% MV; "
                f"unassigned {metrics['unassignedWeightPct']}%."
            )
        },
    )
    return SkillResult(
        skill="theme-map-inference",
        status="ok",
        artifacts=[str(reg_path), str(map_path), str(cov_path), str(log_path), str(met_path), str(frag)],
        metrics=metrics,
        messages=[f"Inferred theme registry and map ({len(registry)} themes)"],
    )
