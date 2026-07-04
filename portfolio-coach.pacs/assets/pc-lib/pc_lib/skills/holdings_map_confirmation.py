"""Holdings map confirmation skill (scaffold template)."""

from __future__ import annotations

from pc_lib.canonical import read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import HOLDINGS_MAP_FIELDS, skill_out, write_fragments, write_mapping_discovery


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "holdings-map-confirmation")
    src = args.input_dir or (args.workspace / "holdings-standards-map")
    inferred = read_csv(src / "HoldingsMap.csv")
    path = write_csv(out / "HoldingsMap.csv", HOLDINGS_MAP_FIELDS, inferred)
    md = write_mapping_discovery(
        out / "MappingDiscovery.md",
        "Holdings map confirmation",
        [
            "_Agent presents inferred map; user confirms or corrects classifications._",
            f"Symbols pending review: {len(inferred)}",
        ],
    )
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {"mapping_discovery": "Embed MappingDiscovery.md holdings section in Report Appendix."},
    )
    return SkillResult(
        skill="holdings-map-confirmation",
        status="ok",
        artifacts=[str(path), str(md), str(frag)],
        messages=["Prepared holdings map for confirmation gate"],
    )
