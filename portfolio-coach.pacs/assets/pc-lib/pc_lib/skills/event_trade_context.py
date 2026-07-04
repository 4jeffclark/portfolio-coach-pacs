"""Event trade context skill."""

from __future__ import annotations

from pc_lib.analytics import filled_orders, symbol_metrics
from pc_lib.canonical import load_canonical
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_metrics


def run(args: SkillArgs) -> SkillResult:
    if not args.symbol:
        return SkillResult(skill="event-trade-context", status="error", messages=["--symbol is required"])
    out = skill_out(args, "event-trade-context")
    sym = args.symbol.upper()
    event = args.event_type or "event"
    orders = load_canonical(args.datastore, "orders.csv")
    period_filled = filled_orders(orders, args.period_start, args.period_end, symbol=sym)
    metrics = symbol_metrics(orders, sym)
    metrics["event_type"] = event
    metrics["analysis_period_start"] = args.period_start or ""
    metrics["analysis_period_end"] = args.period_end or ""
    metrics["period_filled_orders"] = len(period_filled)

    lines = [
        f"# Event Trade Context — {sym}",
        "",
        f"**Event type:** {event}",
        "",
        "## Event window",
        "",
        f"Analysis period: {args.period_start} → {args.period_end}",
        "",
        "## Order reconstruction",
        "",
        f"Filled orders in period: {len(period_filled)}",
        "",
        "_Agent documents offering terms, market reception, lock-up constraints when applicable._",
        "",
    ]
    ctx_path = out / "EventContext.md"
    ctx_path.write_text("\n".join(lines), encoding="utf-8")
    met_path = write_metrics(out / "Metrics.csv", metrics)
    frag_path = write_fragments(
        out / "ReportSectionFragments.json",
        {"event_trade_context": f"Event ({event}) context for {sym} — see EventContext.md."},
    )
    return SkillResult(
        skill="event-trade-context",
        status="ok",
        artifacts=[str(ctx_path), str(met_path), str(frag_path)],
        metrics=metrics,
        messages=[f"Wrote event trade context scaffold for {sym}"],
    )
