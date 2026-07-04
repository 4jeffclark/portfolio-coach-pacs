"""Portfolio concentration resilience skill."""

from __future__ import annotations

from pc_lib.analytics import hhi
from pc_lib.canonical import read_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_metrics


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "portfolio-concentration-resilience")
    lens = args.rollup_lens or "theme"
    exp_file = (
        "ThesisExposure.csv" if lens == "thesis" else "ThemeExposure.csv" if lens == "theme" else "SectorExposure.csv"
    )
    exposure = read_csv((args.workspace / "portfolio-weights-table") / exp_file)
    id_col = "ThesisId" if lens == "thesis" else "ThemeId" if lens == "theme" else "GICSSector"
    weights = [float(r.get("PeriodEndWeightPct") or 0) for r in exposure]
    holdings = read_csv((args.workspace / "portfolio-holdings-state") / "Metrics.csv")
    hm = {r["Metric"]: r["Value"] for r in holdings if r.get("Metric")}
    metrics = {
        "rollupLens": lens,
        "PeriodEndTotalMV": hm.get("periodEndTotalMV", ""),
        "BucketHHI_PeriodEnd": hhi(weights),
        "LargestBucket": max(exposure, key=lambda r: float(r.get("PeriodEndWeightPct") or 0)).get(id_col, "")
        if exposure
        else "",
    }
    met_path = write_metrics(out / "Metrics.csv", metrics)
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {
            "concentration": (
                f"Period-end HHI ({lens}): {metrics['BucketHHI_PeriodEnd']}; "
                f"largest bucket: {metrics['LargestBucket']}."
            )
        },
    )
    return SkillResult(
        skill="portfolio-concentration-resilience",
        status="ok",
        artifacts=[str(met_path), str(frag)],
        metrics=metrics,
        messages=["Wrote concentration metrics"],
    )
