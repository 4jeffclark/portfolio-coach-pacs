"""Thesis registry inference skill."""

from __future__ import annotations

from pc_lib.canonical import read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import (
    THESIS_ASSIGNMENT_FIELDS,
    THESIS_REGISTRY_FIELDS,
    skill_out,
    write_fragments,
)
from pc_lib.theme_inference import infer_thesis_registry


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "thesis-registry-inference")
    src = args.input_dir or (args.workspace / "theme-map-confirmation")
    holdings_src = args.workspace / "holdings-map-confirmation"
    theme_inference_src = args.workspace / "theme-map-inference"
    holdings = read_csv(holdings_src / "HoldingsMap.csv")
    theme_map = read_csv(src / "ThemeMap.csv")
    coverage = read_csv(theme_inference_src / "ThemeCoverage.csv")
    symbols = [(r.get("Symbol") or "").upper() for r in holdings if r.get("Symbol")]
    registry, assignments = infer_thesis_registry(
        symbols, theme_map, theme_coverage=coverage, clustered=True
    )
    reg_path = write_csv(out / "ThesisRegistry.csv", THESIS_REGISTRY_FIELDS, registry)
    asn_path = write_csv(out / "ThesisAssignment.csv", THESIS_ASSIGNMENT_FIELDS, assignments)
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {"thesis_inference": f"Inferred {len(registry)} theses, {len(assignments)} assignments (clustered)."},
    )
    return SkillResult(
        skill="thesis-registry-inference",
        status="ok",
        artifacts=[str(reg_path), str(asn_path), str(frag)],
        metrics={"thesisCount": len(registry)},
        messages=["Inferred thesis registry and assignments"],
    )
