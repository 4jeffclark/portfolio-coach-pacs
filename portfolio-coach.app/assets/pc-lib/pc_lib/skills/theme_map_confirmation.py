"""Theme map confirmation skill."""

from __future__ import annotations

from pc_lib.canonical import read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import (
    THEME_MAP_FIELDS,
    THEME_REGISTRY_FIELDS,
    skill_out,
    write_fragments,
    write_mapping_discovery,
)


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "theme-map-confirmation")
    src = args.input_dir or (args.workspace / "theme-map-inference")
    reg = read_csv(src / "ThemeRegistry.csv")
    tmap = read_csv(src / "ThemeMap.csv")
    reg_path = write_csv(out / "ThemeRegistry.csv", THEME_REGISTRY_FIELDS, reg)
    map_path = write_csv(out / "ThemeMap.csv", THEME_MAP_FIELDS, tmap)
    md = write_mapping_discovery(
        out / "MappingDiscovery.md",
        "Theme map confirmation",
        ["_Agent presents theme registry and assignments for user confirmation._"],
    )
    frag = write_fragments(out / "ReportSectionFragments.json", {"theme_confirmation": "Theme map gate scaffold."})
    return SkillResult(
        skill="theme-map-confirmation",
        status="ok",
        artifacts=[str(reg_path), str(map_path), str(md), str(frag)],
        messages=["Prepared theme map for confirmation gate"],
    )
