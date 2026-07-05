"""Portfolio weights table skill."""

from __future__ import annotations

from pc_lib.analytics import weights_table
from pc_lib.canonical import read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_rollup_lens


def _lens(args: SkillArgs) -> str:
    from pc_lib.skills._skill_io import resolve_rollup_lens

    if args.rollup_lens:
        return args.rollup_lens.strip()
    if args.thematic is True:
        return "theme"
    if args.thematic is False:
        return "standards"
    return resolve_rollup_lens(args)


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "portfolio-weights-table")
    lens = _lens(args)
    write_rollup_lens(args.workspace, lens)
    weights_src = args.input_dir or (args.workspace / "period-weight-reconstruction")
    sym_weights = read_csv(weights_src / "SymbolWeights.csv")

    if lens == "standards":
        map_src = args.workspace / "holdings-map-confirmation"
        hmap = read_csv(map_src / "HoldingsMap.csv")
        sector_by_sym = {(r.get("Symbol") or "").upper(): r.get("GICSSector") or "Unclassified" for r in hmap}
        bucket_fn = lambda s: sector_by_sym.get(s, "Unclassified")  # noqa: E731
        outfile = "SectorExposure.csv"
    elif lens == "thesis":
        map_src = args.workspace / "thesis-registry-confirmation"
        amap = read_csv(map_src / "ThesisAssignment.csv")
        thesis_by_sym = {(r.get("Symbol") or "").upper(): r.get("ThesisId") or "Unassigned" for r in amap}
        bucket_fn = lambda s: thesis_by_sym.get(s, "Unassigned")  # noqa: E731
        outfile = "ThesisExposure.csv"
    else:
        map_src = args.workspace / "theme-map-confirmation"
        tmap = read_csv(map_src / "ThemeMap.csv")
        theme_by_sym = {(r.get("Symbol") or "").upper(): r.get("ThemeId") or "Unassigned" for r in tmap}
        bucket_fn = lambda s: theme_by_sym.get(s, "Unassigned")  # noqa: E731
        outfile = "ThemeExposure.csv"

    start_mv = {r["Symbol"]: float(r.get("PeriodStartMV") or 0) for r in sym_weights}
    end_mv = {r["Symbol"]: float(r.get("PeriodEndMV") or 0) for r in sym_weights}
    start_total = sum(start_mv.values()) or 1
    end_total = sum(end_mv.values()) or 1
    rows = weights_table(start_mv, end_mv, bucket_fn, start_total, end_total)
    for row in rows:
        row["PeriodStartWeightSource"] = "observed_snapshot"
        row["PeriodEndWeightSource"] = "observed_snapshot"
        if lens == "thesis":
            row["ThesisId"] = row.pop("Bucket")
        elif lens == "theme":
            row["ThemeId"] = row.pop("Bucket")
        else:
            row["GICSSector"] = row.pop("Bucket")

    if lens == "thesis":
        fields = [
            "ThesisId", "PeriodStartMV", "PeriodEndMV",
            "PeriodStartWeightPct", "PeriodEndWeightPct", "DeltaPp",
            "PeriodStartWeightSource", "PeriodEndWeightSource",
        ]
    elif lens == "theme":
        fields = [
            "ThemeId", "PeriodStartMV", "PeriodEndMV",
            "PeriodStartWeightPct", "PeriodEndWeightPct", "DeltaPp",
            "PeriodStartWeightSource", "PeriodEndWeightSource",
        ]
    else:
        fields = [
            "GICSSector", "PeriodStartMV", "PeriodEndMV",
            "PeriodStartWeightPct", "PeriodEndWeightPct", "DeltaPp",
            "PeriodStartWeightSource", "PeriodEndWeightSource",
        ]
    path = write_csv(out / outfile, fields, rows)
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {
            "primary_weights_table": (
                f"Primary weights table ({lens} lens): {len(rows)} rollup rows in {outfile}."
            )
        },
    )
    return SkillResult(
        skill="portfolio-weights-table",
        status="ok",
        artifacts=[str(path), str(frag)],
        metrics={"rollupLens": lens, "rowCount": len(rows)},
        messages=[f"Wrote {lens} exposure weights table"],
    )
