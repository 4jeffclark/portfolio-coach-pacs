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
    coverage = read_csv(src / "ThemeCoverage.csv")
    inference_log = read_csv(src / "InferenceLog.csv")

    reg_path = write_csv(out / "ThemeRegistry.csv", THEME_REGISTRY_FIELDS, reg)
    map_path = write_csv(out / "ThemeMap.csv", THEME_MAP_FIELDS, tmap)

    lines = ["Review inferred theme assignments before quantification proceeds.", ""]
    if coverage:
        unassigned = next(
            (r for r in coverage if r.get("ThemeId") in ("THEME_UNASSIGNED", "THEME_OTHER")),
            None,
        )
        if unassigned:
            lines.append(
                f"**Unassigned MV:** {unassigned.get('WeightPct', '0')}% "
                f"({unassigned.get('SymbolCount', '0')} symbols) — refine taxonomy or confirm residual."
            )
            lines.append("")
        lines.append("### Theme coverage (by period-end weight)")
        lines.append("")
        lines.append("| ThemeId | WeightPct | SymbolCount | PeriodEndMV |")
        lines.append("| --- | ---: | ---: | ---: |")
        for row in coverage[:12]:
            lines.append(
                f"| {row.get('ThemeId', '')} | {row.get('WeightPct', '')} | "
                f"{row.get('SymbolCount', '')} | {row.get('PeriodEndMV', '')} |"
            )
        lines.append("")
    if inference_log:
        sorted_log = sorted(
            inference_log,
            key=lambda r: float(r.get("PeriodEndWeightPct") or 0),
            reverse=True,
        )
        lines.append("### Top symbols by weight (inference provenance)")
        lines.append("")
        lines.append("| Symbol | ThemeId | WeightPct | RuleId | Confidence |")
        lines.append("| --- | --- | ---: | --- | --- |")
        for row in sorted_log[:20]:
            if float(row.get("PeriodEndWeightPct") or 0) <= 0:
                continue
            lines.append(
                f"| {row.get('Symbol', '')} | {row.get('ThemeId', '')} | "
                f"{row.get('PeriodEndWeightPct', '')} | {row.get('RuleId', '')} | "
                f"{row.get('MappingConfidence', '')} |"
            )
        lines.append("")
    lines.append("_Agent presents theme registry and assignments for user confirmation._")

    md = write_mapping_discovery(out / "MappingDiscovery.md", "Theme map confirmation", lines)
    frag = write_fragments(out / "ReportSectionFragments.json", {"theme_confirmation": "Theme map gate scaffold."})
    return SkillResult(
        skill="theme-map-confirmation",
        status="ok",
        artifacts=[str(reg_path), str(map_path), str(md), str(frag)],
        messages=["Prepared theme map for confirmation gate"],
    )
