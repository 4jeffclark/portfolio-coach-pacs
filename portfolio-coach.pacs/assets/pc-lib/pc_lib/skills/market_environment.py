"""Market environment skill."""

from __future__ import annotations

from pc_lib.analytics import (
    activity_metrics,
    count_numeric_exposure_symbols,
    count_position_row_types,
    filled_orders,
    latest_snapshot_date,
    mapping_universe,
    positions_at_snapshot,
    snapshot_lag_days,
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
    "GrossNotionalPctOfTurnover",
    "ActivityToWeightRatio",
    "FilledOrderCount",
]

SNAPSHOT_LAG_WARN_DAYS = 14


def _portfolio_linkage_rows(
    symbols: list[str],
    end_mv: dict[str, float],
    end_total: float,
    notionals: dict[str, dict[str, float]],
    order_counts: dict[str, int],
    top_weight: list[tuple[str, float, float]],
    top_notional: list[tuple[str, float]],
    gross_turnover: float,
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
        gross_n = sym_notional.get("gross_notional", 0)
        gross_pct = (gross_n / gross_turnover * 100) if gross_turnover else 0.0
        activity_ratio = (gross_n / mv) if mv else ""
        rows.append(
            {
                "Symbol": sym,
                "PeriodEndWeightPct": f"{weight_pct:.2f}" if end_total else "",
                "PeriodEndMarketValue": f"{mv:.2f}" if mv else "",
                "PeriodBuyNotional": f"{sym_notional.get('buy_notional', 0):.2f}",
                "PeriodSellNotional": f"{sym_notional.get('sell_notional', 0):.2f}",
                "PeriodGrossNotional": f"{gross_n:.2f}",
                "GrossNotionalPctOfTurnover": f"{gross_pct:.2f}" if gross_turnover else "",
                "ActivityToWeightRatio": f"{activity_ratio:.2f}" if activity_ratio != "" else "",
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

    row_types = count_position_row_types(end_pos)
    numeric_symbol_count = count_numeric_exposure_symbols(end_mv)
    snapshot_lag = snapshot_lag_days(end_snap, pe)
    turnover_ratio = round(act["gross_turnover"] / end_total, 4) if end_total else 0.0

    exposure_available = bool(end_snap and end_total and numeric_symbol_count == 0)
    start_exposure_available = bool(start_snap and start_total)
    exposure_quality_valid = numeric_symbol_count == 0 and bool(end_snap and end_total)
    snapshot_lag_warn = snapshot_lag >= SNAPSHOT_LAG_WARN_DAYS if snapshot_lag >= 0 else False
    snapshot_lag_notice = 0 < snapshot_lag < SNAPSHOT_LAG_WARN_DAYS if snapshot_lag >= 0 else False

    top_weight = top_symbols_by_weight(end_mv, end_total, limit=10)
    top_notional = top_symbols_by_notional(notionals, limit=10)
    linkage_rows = _portfolio_linkage_rows(
        symbols, end_mv, end_total, notionals, order_counts, top_weight, top_notional, act["gross_turnover"]
    )
    linkage_path = write_csv(out / "PortfolioLinkage.csv", PORTFOLIO_LINKAGE_FIELDS, linkage_rows)

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
    if not exposure_quality_valid:
        lines.append(
            "_**DATA QUALITY — EXPOSURE TABLE INVALID** "
            f"({numeric_symbol_count} numeric-only symbols; "
            f"{row_types['lot_detail']} lot-detail rows in snapshot). "
            "Do not coach on exposure until canonical positions are rebuilt._"
        )
    elif exposure_available:
        if snapshot_lag_warn:
            lag_note = f" (**snapshot lag {snapshot_lag} days** vs period end — consider aligning `analysisPeriodEnd` to latest export)"
        elif snapshot_lag_notice:
            lag_note = f" (snapshot lag {snapshot_lag} days vs period end)"
        else:
            lag_note = ""
        lines.append(
            f"Period-end snapshot **{end_snap}**{lag_note}: total MV ${end_total:,.2f}. "
            "Embed top holdings by **PeriodEndWeightPct** from PortfolioLinkage.csv."
        )
    else:
        lines.append("_Period-end exposure unavailable — document snapshot gap in delivered report._")
    lines.extend(
        [
            "",
            f"Period activity: {act['filled_orders']} filled orders; "
            f"buy notional ${act['buy_notional']:,.2f}; sell notional ${act['sell_notional']:,.2f}; "
            f"gross turnover ${act['gross_turnover']:,.2f}; "
            f"turnover/MV ratio {turnover_ratio:.2f}. "
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
        "portfolioTurnoverRatio": turnover_ratio,
        "periodStartSnapshot": start_snap,
        "periodEndSnapshot": end_snap,
        "periodEndSnapshotLagDays": snapshot_lag,
        "periodStartTotalMV": round(start_total, 2),
        "periodEndTotalMV": round(end_total, 2),
        "periodStartExposureAvailable": start_exposure_available,
        "periodEndExposureAvailable": exposure_available,
        "exposureParentRowCount": row_types["summary"],
        "exposureLotDetailRowCount": row_types["lot_detail"],
        "exposureNumericSymbolCount": numeric_symbol_count,
        "exposureQualityValid": exposure_quality_valid,
        "snapshotLagWarn": snapshot_lag_warn,
        "snapshotLagNotice": snapshot_lag_notice,
    }
    met_path = write_metrics(out / "Metrics.csv", metrics)

    weight_summary = ", ".join(f"{sym} {pct:.1f}%" for sym, _, pct in top_weight[:5]) or "n/a"
    notional_summary = ", ".join(f"{sym} ${val:,.0f}" for sym, val in top_notional[:5]) or "n/a"

    linkage_fragment = (
        f"Universe: {len(symbols)} symbols. "
        f"Period-end snapshot {end_snap or 'unavailable'} "
        f"(${end_total:,.2f} total MV; lag {snapshot_lag} days). "
        f"Top exposure by weight: {weight_summary}. "
        f"Top period activity by gross notional: {notional_summary}. "
        f"Period gross turnover ${act['gross_turnover']:,.2f}; turnover/MV {turnover_ratio:.2f}. "
        "Embed PortfolioLinkage.csv in the delivered report. "
        "Distinguish exposure (PeriodEndWeightPct), activity (PeriodGrossNotional), "
        "and conviction. Use GrossNotionalPctOfTurnover and ActivityToWeightRatio for coaching. "
        "Do not rank symbols by FilledOrderCount or describe "
        "order-count share as conviction or capital concentration."
    )
    if not exposure_quality_valid:
        linkage_fragment += (
            " **DATA QUALITY — EXPOSURE TABLE INVALID** "
            f"(exposureNumericSymbolCount={numeric_symbol_count}). "
            "Do not deliver exposure tables or exposure-based coaching. "
            "Attest post-run failed (data quality) or warn prominently."
        )
    elif snapshot_lag_warn:
        linkage_fragment += (
            f" Snapshot lag {snapshot_lag} days (warn) — note in period windows; "
            "confirm user accepts lag or set analysisPeriodEnd to latest export date."
        )
    elif snapshot_lag_notice:
        linkage_fragment += (
            f" Snapshot lag {snapshot_lag} days (notice) — exposure is valid but stale; "
            "document in period windows; recommend latest export date for aligned weights."
        )
    else:
        linkage_fragment += (
            " Defer full conviction and period weight delta analysis to portfolio-composition-review "
            "when period-start weights are unavailable."
        )

    frag_path = write_fragments(
        out / "ReportSectionFragments.json",
        {
            "market_context": (
                f"Market context scaffold for {len(symbols)} portfolio symbols. "
                "Merge all workspace market-research content into the delivered report file."
            ),
            "portfolio_linkage": linkage_fragment,
            "skill_metrics_appendix": (
                "Embed Appendix: Skill Metrics table from Metrics.csv with at minimum: "
                "portfolioSymbolCount, periodEndSnapshot, periodEndSnapshotLagDays, "
                "snapshotLagWarn, snapshotLagNotice, periodEndTotalMV, periodGrossTurnover, "
                "portfolioTurnoverRatio, exposureQualityValid, exposureNumericSymbolCount, "
                "exposureParentRowCount, exposureLotDetailRowCount."
            ),
        },
    )

    status = "ok"
    messages = ["Wrote market research scaffold, portfolio linkage, and metrics"]
    if not exposure_quality_valid:
        status = "warn"
        messages.append(
            f"Exposure quality invalid: {numeric_symbol_count} numeric-only symbols in exposure table"
        )
    elif snapshot_lag_warn:
        status = "warn"
        messages.append(f"Period-end snapshot lags analysis end by {snapshot_lag} days")

    return SkillResult(
        skill="market-environment",
        status=status,
        artifacts=[str(mr_path), str(met_path), str(frag_path), str(linkage_path)],
        metrics=metrics,
        messages=messages,
    )
