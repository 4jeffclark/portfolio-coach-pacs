"""Market environment skill."""

from __future__ import annotations

from pc_lib.analytics import (
    activity_metrics,
    filled_orders,
    latest_snapshot_date,
    mapping_universe,
    positions_at_snapshot,
    symbol_market_values,
    symbol_period_notionals,
    top_symbols_by_notional,
    top_symbols_by_weight,
    total_market_value,
)
from pc_lib.canonical import default_period_windows, load_canonical, write_csv, ymd_to_iso
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_metrics

PORTFOLIO_LINKAGE_FIELDS = [
    "Symbol",
    "PeriodEndWeightPct",
    "PeriodEndMarketValue",
    "PeriodBuyNotional",
    "PeriodSellNotional",
    "PeriodGrossNotional",
    "FilledOrderCount",
]


def _portfolio_linkage_rows(
    symbols: list[str],
    end_mv: dict[str, float],
    end_total: float,
    notionals: dict[str, dict[str, float]],
    order_counts: dict[str, int],
    top_weight: list[tuple[str, float, float]],
    top_notional: list[tuple[str, float]],
    limit: int = 15,
) -> list[dict[str, str]]:
    ranked_syms: list[str] = []
    for sym, _, _ in top_weight:
        if sym not in ranked_syms:
            ranked_syms.append(sym)
    for sym, _ in top_notional:
        if sym not in ranked_syms:
            ranked_syms.append(sym)
    for sym in symbols:
        if sym not in ranked_syms:
            ranked_syms.append(sym)
        if len(ranked_syms) >= limit:
            break
    rows: list[dict[str, str]] = []
    for sym in ranked_syms[:limit]:
        mv = end_mv.get(sym, 0.0)
        weight_pct = (mv / end_total * 100) if end_total else 0.0
        sym_notional = notionals.get(sym, {})
        rows.append(
            {
                "Symbol": sym,
                "PeriodEndWeightPct": f"{weight_pct:.2f}" if end_total else "",
                "PeriodEndMarketValue": f"{mv:.2f}" if mv else "",
                "PeriodBuyNotional": f"{sym_notional.get('buy_notional', 0):.2f}",
                "PeriodSellNotional": f"{sym_notional.get('sell_notional', 0):.2f}",
                "PeriodGrossNotional": f"{sym_notional.get('gross_notional', 0):.2f}",
                "FilledOrderCount": str(order_counts.get(sym, 0)),
            }
        )
    return rows


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "market-environment")
    ps = args.period_start or ""
    pe = args.period_end or ""
    windows = default_period_windows(ps, pe) if ps and pe else None
    positions = load_canonical(args.datastore, "positions_lot_level.csv")
    orders = load_canonical(args.datastore, "orders.csv")
    symbols = mapping_universe(positions, orders, ps, pe)
    depth = args.market_depth or "full"

    period_filled = filled_orders(orders, ps, pe)
    act = activity_metrics(period_filled)
    notionals = symbol_period_notionals(period_filled)
    order_counts: dict[str, int] = {}
    for row in period_filled:
        sym = (row.get("Symbol") or "").upper()
        if sym:
            order_counts[sym] = order_counts.get(sym, 0) + 1

    start_iso = ymd_to_iso(ps) or ""
    end_iso = ymd_to_iso(pe) or ""
    start_snap = latest_snapshot_date(positions, start_iso)
    end_snap = latest_snapshot_date(positions, end_iso)
    start_pos = positions_at_snapshot(positions, start_snap) if start_snap else []
    end_pos = positions_at_snapshot(positions, end_snap) if end_snap else []
    end_mv = symbol_market_values(end_pos)
    end_total = total_market_value(end_pos)
    start_total = total_market_value(start_pos)

    top_weight = top_symbols_by_weight(end_mv, end_total, limit=10)
    top_notional = top_symbols_by_notional(notionals, limit=10)
    linkage_rows = _portfolio_linkage_rows(
        symbols, end_mv, end_total, notionals, order_counts, top_weight, top_notional
    )
    linkage_path = write_csv(out / "PortfolioLinkage.csv", PORTFOLIO_LINKAGE_FIELDS, linkage_rows)

    exposure_available = bool(end_snap and end_total)
    start_exposure_available = bool(start_snap and start_total)

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
            "## Portfolio linkage scaffold",
            "",
            f"Symbols in universe ({len(symbols)}): {', '.join(symbols[:25])}"
            + (" …" if len(symbols) > 25 else ""),
            "",
        ]
    )
    if exposure_available:
        lines.append(
            f"Period-end snapshot **{end_snap}**: total MV ${end_total:,.2f}. "
            "Embed top holdings by **PeriodEndWeightPct** from PortfolioLinkage.csv."
        )
    else:
        lines.append("_Period-end exposure unavailable — document snapshot gap in delivered report._")
    lines.extend(
        [
            "",
            f"Period activity: {act['filled_orders']} filled orders; "
            f"buy notional ${act['buy_notional']:,.2f}; sell notional ${act['sell_notional']:,.2f}; "
            f"gross turnover ${act['gross_turnover']:,.2f}. "
            "Rank activity by **PeriodGrossNotional**, not FilledOrderCount.",
            "",
            "## Sources",
            "",
            "_Agent adds cited sources with title, publisher, date, URL._",
            "",
        ]
    )
    if depth == "summary":
        lines.append("_Summary depth — abbreviated for standalone or parent report embed._\n")

    mr_path = out / "MarketResearch.md"
    mr_path.write_text("\n".join(lines), encoding="utf-8")

    metrics = {
        "marketDepth": depth,
        "portfolioSymbolCount": len(symbols),
        "analysisPeriodStart": ps,
        "analysisPeriodEnd": pe,
        "periodFilledOrders": act["filled_orders"],
        "periodBuyCount": act["buy_count"],
        "periodSellCount": act["sell_count"],
        "periodBuyNotional": act["buy_notional"],
        "periodSellNotional": act["sell_notional"],
        "periodGrossTurnover": act["gross_turnover"],
        "periodStartSnapshot": start_snap,
        "periodEndSnapshot": end_snap,
        "periodStartTotalMV": round(start_total, 2),
        "periodEndTotalMV": round(end_total, 2),
        "periodStartExposureAvailable": start_exposure_available,
        "periodEndExposureAvailable": exposure_available,
    }
    met_path = write_metrics(out / "Metrics.csv", metrics)

    weight_summary = ", ".join(f"{sym} {pct:.1f}%" for sym, _, pct in top_weight[:5]) or "n/a"
    notional_summary = ", ".join(f"{sym} ${val:,.0f}" for sym, val in top_notional[:5]) or "n/a"
    frag_path = write_fragments(
        out / "ReportSectionFragments.json",
        {
            "market_context": (
                f"Market context scaffold for {len(symbols)} portfolio symbols. "
                "Merge all workspace market-research content into the delivered report file."
            ),
            "portfolio_linkage": (
                f"Universe: {len(symbols)} symbols. "
                f"Period-end snapshot {end_snap or 'unavailable'} "
                f"(${end_total:,.2f} total MV). "
                f"Top exposure by weight: {weight_summary}. "
                f"Top period activity by gross notional: {notional_summary}. "
                f"Period gross turnover ${act['gross_turnover']:,.2f}. "
                "Embed PortfolioLinkage.csv in the delivered report. "
                "Distinguish exposure (PeriodEndWeightPct), activity (PeriodGrossNotional), "
                "and conviction. Do not rank symbols by FilledOrderCount or describe "
                "order-count share as conviction or capital concentration. "
                "Defer full conviction and period weight delta analysis to portfolio-composition-review "
                "when period-start weights are unavailable."
            ),
        },
    )
    return SkillResult(
        skill="market-environment",
        status="ok",
        artifacts=[str(mr_path), str(met_path), str(frag_path), str(linkage_path)],
        metrics=metrics,
        messages=["Wrote market research scaffold, portfolio linkage, and metrics"],
    )
