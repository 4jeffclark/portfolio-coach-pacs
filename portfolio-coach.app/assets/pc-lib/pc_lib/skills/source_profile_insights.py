"""Source profile insights skill."""

from __future__ import annotations

import csv
from pathlib import Path

from pc_lib.canonical import work_dir
from pc_lib.cli import SkillArgs, SkillResult


def run(args: SkillArgs) -> SkillResult:
    out = work_dir(args.workspace, "source-profile-insights")
    inv = work_dir(args.workspace, "datastore-inventory") / "DataStoreInventory.csv"
    scorecard = out / "SourceProfileScorecard.md"

    lines = ["# Source Profile Scorecard", ""]
    if inv.is_file():
        with inv.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        lines.append(f"- Canonical artifacts indexed: {len([r for r in rows if r.get('ArtifactType') == 'canonical'])}")
        lines.append(f"- Raw files indexed: {len([r for r in rows if r.get('ArtifactType') == 'raw'])}")
    else:
        lines.append("- Run datastore-inventory first for quantitative scorecard inputs.")

    lines.extend(
        [
            "",
            "## Agent reflection",
            "",
            "_Agent documents export gaps, useful insights, and coverage quality._",
            "",
        ]
    )
    if args.evaluation:
        lines.append("_Evaluation overlay: complete exit interview after scorecard._")

    scorecard.write_text("\n".join(lines), encoding="utf-8")
    return SkillResult(
        skill="source-profile-insights",
        status="ok",
        artifacts=[str(scorecard)],
        messages=["Wrote source profile scorecard scaffold"],
    )
