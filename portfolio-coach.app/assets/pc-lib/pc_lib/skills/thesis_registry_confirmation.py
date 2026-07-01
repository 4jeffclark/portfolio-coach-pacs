"""Thesis registry confirmation skill."""

from __future__ import annotations

from pc_lib.canonical import read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import (
    THESIS_ASSIGNMENT_FIELDS,
    THESIS_REGISTRY_FIELDS,
    skill_out,
    write_fragments,
    write_mapping_discovery,
)


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "thesis-registry-confirmation")
    src = args.input_dir or (args.workspace / "thesis-registry-inference")
    reg = read_csv(src / "ThesisRegistry.csv")
    asn = read_csv(src / "ThesisAssignment.csv")
    reg_path = write_csv(out / "ThesisRegistry.csv", THESIS_REGISTRY_FIELDS, reg)
    asn_path = write_csv(out / "ThesisAssignment.csv", THESIS_ASSIGNMENT_FIELDS, asn)
    md = write_mapping_discovery(
        out / "MappingDiscovery.md",
        "Thesis registry confirmation",
        ["_Agent presents thesis registry and assignments for user confirmation._"],
    )
    frag = write_fragments(out / "ReportSectionFragments.json", {"thesis_confirmation": "Thesis gate scaffold."})
    return SkillResult(
        skill="thesis-registry-confirmation",
        status="ok",
        artifacts=[str(reg_path), str(asn_path), str(md), str(frag)],
        messages=["Prepared thesis registry for confirmation gate"],
    )
