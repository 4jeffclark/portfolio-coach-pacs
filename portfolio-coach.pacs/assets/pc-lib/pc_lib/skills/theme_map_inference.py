"""Theme map inference skill."""

from __future__ import annotations

from pc_lib.analytics import infer_theme_registry
from pc_lib.canonical import read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import (
    THEME_MAP_FIELDS,
    THEME_REGISTRY_FIELDS,
    skill_out,
    write_fragments,
)


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "theme-map-inference")
    src = args.input_dir or (args.workspace / "holdings-map-confirmation")
    holdings = read_csv(src / "HoldingsMap.csv")
    symbols = [(r.get("Symbol") or "").upper() for r in holdings if r.get("Symbol")]
    registry, theme_map = infer_theme_registry(symbols)
    reg_path = write_csv(out / "ThemeRegistry.csv", THEME_REGISTRY_FIELDS, registry)
    map_path = write_csv(out / "ThemeMap.csv", THEME_MAP_FIELDS, theme_map)
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {"theme_inference": f"Inferred {len(registry)} themes for {len(theme_map)} symbol assignments."},
    )
    return SkillResult(
        skill="theme-map-inference",
        status="ok",
        artifacts=[str(reg_path), str(map_path), str(frag)],
        metrics={"themeCount": len(registry), "assignmentCount": len(theme_map)},
        messages=["Inferred theme registry and map"],
    )
