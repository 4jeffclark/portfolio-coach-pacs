"""Thesis health skill."""

from __future__ import annotations

from pc_lib.canonical import read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "thesis-health")
    lens = args.rollup_lens or ("thesis" if args.thematic else "theme")
    weights_src = args.workspace / "portfolio-weights-table"
    if lens == "thesis":
        exposure = read_csv(weights_src / "ThesisExposure.csv")
        rows = [
            {
                "ThesisId": r.get("ThesisId", ""),
                "PeriodEndWeightPct": r.get("PeriodEndWeightPct", ""),
                "HealthClassification": "watch",
                "PeriodEndScore": "50",
                "Notes": "scaffold — agent extends with proxy research",
            }
            for r in exposure
            if r.get("ThesisId") and r.get("ThesisId") != "Unassigned"
        ]
        path = write_csv(
            out / "ThesisHealth.csv",
            ["ThesisId", "PeriodEndWeightPct", "HealthClassification", "PeriodEndScore", "Notes"],
            rows,
        )
    else:
        exposure = read_csv(weights_src / "ThemeExposure.csv")
        rows = [
            {
                "ThemeId": r.get("ThemeId", ""),
                "HealthClassification": "neutral",
                "ThemeHealthScore": "50",
                "Notes": "scaffold",
            }
            for r in exposure
            if r.get("ThemeId") and r.get("ThemeId") != "Unassigned"
        ]
        path = write_csv(
            out / "ThemeHealth.csv",
            ["ThemeId", "HealthClassification", "ThemeHealthScore", "Notes"],
            rows,
        )
    frag = write_fragments(out / "ReportSectionFragments.json", {"thesis_health": f"Health scaffold ({lens} lens)."})
    return SkillResult(
        skill="thesis-health",
        status="ok",
        artifacts=[str(path), str(frag)],
        messages=["Wrote health classification scaffold"],
    )
