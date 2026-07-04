"""Market environment skill."""

from __future__ import annotations

from pc_lib.analytics import mapping_universe, symbols_from_positions
from pc_lib.canonical import default_period_windows, load_canonical, load_knowledge_csv, ymd_to_iso
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_metrics


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "market-environment")
    ps = args.period_start or ""
    pe = args.period_end or ""
    windows = default_period_windows(ps, pe) if ps and pe else None
    positions = load_canonical(args.datastore, "positions_lot_level.csv")
    orders = load_canonical(args.datastore, "orders.csv")
    symbols = mapping_universe(positions, orders, ps, pe)
    depth = args.market_depth or "full"

    lines = [
        "# Market Research",
        "",
        f"**Analysis period:** {ymd_to_iso(ps) or 'n/a'} → {ymd_to_iso(pe) or 'n/a'}",
        "",
        "## Broad Market Context",
        "",
        "_Agent synthesizes regime narrative across lookback, analysis, and follow-through windows._",
        "",
    ]
    if windows:
        lines.extend(
            [
                f"- Lookback: {ymd_to_iso(windows.lookback_start)} → {ymd_to_iso(windows.lookback_end)}",
                f"- Follow-through: {ymd_to_iso(windows.follow_through_start)} → {ymd_to_iso(windows.follow_through_end)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Portfolio symbol context",
            "",
            f"Symbols in scope ({len(symbols)}): {', '.join(symbols[:25])}"
            + (" …" if len(symbols) > 25 else ""),
            "",
            "## Sources",
            "",
            "_Agent adds cited sources with title, publisher, date, URL._",
            "",
        ]
    )
    if depth == "summary":
        lines.append("_Summary depth — abbreviated for parent report embed._\n")

    mr_path = out / "MarketResearch.md"
    mr_path.write_text("\n".join(lines), encoding="utf-8")
    metrics = {
        "marketDepth": depth,
        "portfolioSymbolCount": len(symbols),
        "analysisPeriodStart": ps,
        "analysisPeriodEnd": pe,
    }
    met_path = write_metrics(out / "Metrics.csv", metrics)
    frag_path = write_fragments(
        out / "ReportSectionFragments.json",
        {
            "market_context": (
                f"Market context scaffold for {len(symbols)} portfolio symbols. "
                "Merge all workspace market-research content into the delivered report file."
            )
        },
    )
    return SkillResult(
        skill="market-environment",
        status="ok",
        artifacts=[str(mr_path), str(met_path), str(frag_path)],
        metrics=metrics,
        messages=["Wrote market research scaffold and metrics"],
    )
