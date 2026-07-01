"""Portfolio evolution skill."""

from __future__ import annotations

from pc_lib.canonical import read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "portfolio-evolution")
    lens = args.rollup_lens or "theme"
    weights = read_csv((args.workspace / "portfolio-weights-table") / (
        "ThesisExposure.csv" if lens == "thesis" else "ThemeExposure.csv" if lens == "theme" else "SectorExposure.csv"
    ))
    flows = read_csv((args.workspace / "portfolio-period-flows") / "PeriodFlows.csv")
    flow_by_bucket = {r.get("Bucket", ""): r for r in flows}
    id_col = "ThesisId" if lens == "thesis" else "ThemeId" if lens == "theme" else "GICSSector"

    rows = []
    for w in weights:
        bucket = w.get(id_col, "")
        f = flow_by_bucket.get(bucket, {})
        rows.append(
            {
                id_col: bucket,
                "PeriodStartWeightPct": w.get("PeriodStartWeightPct", ""),
                "PeriodEndWeightPct": w.get("PeriodEndWeightPct", ""),
                "BuyNotional": f.get("BuyNotional", "0"),
                "SellNotional": f.get("SellNotional", "0"),
                "NetFlow": f.get("NetFlow", "0"),
                "GrossTurnover": f.get("GrossTurnover", "0"),
            }
        )
    evo_file = (
        "ThesisEvolution.csv" if lens == "thesis" else "ThemeEvolution.csv" if lens == "theme" else "SectorEvolution.csv"
    )
    fields = [id_col, "PeriodStartWeightPct", "PeriodEndWeightPct", "BuyNotional", "SellNotional", "NetFlow", "GrossTurnover"]
    path = write_csv(out / evo_file, fields, rows)
    rot_rows = [
        {"FromBucket": r[id_col], "ToBucket": "Liquidity", "EstimatedRotationNotional": r.get("SellNotional", "0"), "Notes": "scaffold"}
        for r in rows
        if float(r.get("SellNotional") or 0) > 0
    ][:10]
    rot_file = (
        "ThesisRotationMatrix.csv" if lens == "thesis" else "ThemeRotationMatrix.csv" if lens == "theme" else "SectorRotationMatrix.csv"
    )
    rot_path = write_csv(out / rot_file, ["FromBucket", "ToBucket", "EstimatedRotationNotional", "Notes"], rot_rows)
    frag = write_fragments(out / "ReportSectionFragments.json", {"evolution": f"Evolution and rotation scaffold ({lens})."})
    return SkillResult(
        skill="portfolio-evolution",
        status="ok",
        artifacts=[str(path), str(rot_path), str(frag)],
        messages=["Wrote evolution and rotation scaffolds"],
    )
