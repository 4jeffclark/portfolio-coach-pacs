"""Symbol trading analysis skill."""

from __future__ import annotations

from pc_lib.analytics import filled_orders, symbol_metrics
from pc_lib.canonical import load_canonical, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_metrics


def run(args: SkillArgs) -> SkillResult:
    if not args.symbol:
        return SkillResult(
            skill="symbol-trading-analysis",
            status="error",
            messages=["--symbol is required"],
        )
    out = skill_out(args, "symbol-trading-analysis")
    sym = args.symbol.upper()
    orders = load_canonical(args.datastore, "orders.csv")
    period_filled = filled_orders(orders, args.period_start, args.period_end, symbol=sym)
    metrics = symbol_metrics(orders, sym, args.period_start, args.period_end)
    metrics["analysis_period_start"] = args.period_start or ""
    metrics["analysis_period_end"] = args.period_end or ""

    fields = ["Date", "Time", "Side", "FillQuantity", "FillPrice", "Status", "Description"]
    orders_path = write_csv(out / f"Orders_{sym}.csv", fields, period_filled)
    met_path = write_metrics(out / "Metrics.csv", metrics)
    lifetime_text = (
        f"{metrics.get(f'{sym}_order_records', 0)} filled records lifetime; "
        f"realized P&L lifetime (FIFO ex fees) ${metrics.get('realized_pnl_fifo_ex_fees_lifetime', 0):,.2f}."
    )
    if args.period_start or args.period_end:
        fragment = (
            f"Symbol {sym}: {metrics.get('order_records_period', 0)} filled records in period "
            f"{args.period_start or 'open'}-{args.period_end or 'open'}; "
            f"realized P&L in period (FIFO ex fees) ${metrics.get('realized_pnl_fifo_ex_fees_period', 0):,.2f}. "
            f"Lifetime context: {lifetime_text}"
        )
    else:
        fragment = f"Symbol {sym}: {lifetime_text}"
    frag_path = write_fragments(
        out / "ReportSectionFragments.json",
        {"symbol_lifecycle_quantification": fragment},
    )
    return SkillResult(
        skill="symbol-trading-analysis",
        status="ok",
        artifacts=[str(orders_path), str(met_path), str(frag_path)],
        metrics=metrics,
        messages=[f"Wrote symbol lifecycle metrics for {sym}"],
    )
