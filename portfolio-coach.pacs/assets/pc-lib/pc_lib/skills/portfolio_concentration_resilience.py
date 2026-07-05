"""Portfolio concentration resilience skill."""

from __future__ import annotations

from pathlib import Path

from pc_lib.analytics import hhi
from pc_lib.canonical import read_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import resolve_rollup_lens, skill_out, write_fragments, write_metrics


def _write_enrichment_scaffolds(out: Path, lens: str, exposure: list, id_col: str, metrics: dict) -> list[str]:
    """Optional rebalancing/risk hint files for overlay enrichment."""
    artifacts: list[str] = []
    if not exposure:
        return artifacts
    reb_lines = [
        "# Rebalancing hints (scaffold)",
        "",
        f"Rollup lens: **{lens}**",
        "",
        "## Largest period-end weights",
        "",
    ]
    sorted_exp = sorted(exposure, key=lambda r: float(r.get("PeriodEndWeightPct") or 0), reverse=True)
    n = len(sorted_exp) or 1
    equal = round(100 / n, 2)
    for row in sorted_exp[:8]:
        bucket = row.get(id_col, "")
        end_w = float(row.get("PeriodEndWeightPct") or 0)
        delta = round(end_w - equal, 2)
        reb_lines.append(f"- **{bucket}**: {end_w:.2f}% (vs equal-weight {equal:.2f}%, delta {delta:+.2f} pp)")
    reb_path = out / "RebalancingHints.md"
    reb_path.write_text("\n".join(reb_lines) + "\n", encoding="utf-8")
    artifacts.append(str(reb_path))

    risk_lines = [
        "# Risk hints (scaffold)",
        "",
        f"- Period-end bucket HHI: **{metrics.get('BucketHHI_PeriodEnd', 'n/a')}**",
        f"- Largest bucket: **{metrics.get('LargestBucket', 'n/a')}**",
        "- Agent extends with stress scenarios and de-risking notes when riskReview overlay is enabled.",
        "",
    ]
    risk_path = out / "RiskHints.md"
    risk_path.write_text("\n".join(risk_lines) + "\n", encoding="utf-8")
    artifacts.append(str(risk_path))
    return artifacts


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "portfolio-concentration-resilience")
    lens = resolve_rollup_lens(args)
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
            ),
            "rebalancing_hints": "See RebalancingHints.md for equal-weight delta scaffold.",
            "risk_hints": "See RiskHints.md for concentration risk scaffold.",
        },
    )
    scaffold_paths = _write_enrichment_scaffolds(out, lens, exposure, id_col, metrics)
    return SkillResult(
        skill="portfolio-concentration-resilience",
        status="ok",
        artifacts=[str(met_path), str(frag), *scaffold_paths],
        metrics=metrics,
        messages=["Wrote concentration metrics"],
    )
