"""Trading activity analysis skill."""

from __future__ import annotations

from pc_lib.analytics import activity_metrics, filled_orders
from pc_lib.canonical import load_canonical, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_metrics


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "trading-activity-analysis")
    orders = load_canonical(args.datastore, "orders.csv")
    period_filled = filled_orders(orders, args.period_start, args.period_end)
    metrics = activity_metrics(period_filled)
    metrics["review_period_start"] = args.period_start or ""
    metrics["review_period_end"] = args.period_end or ""

    order_fields = [
        "Date", "Time", "AccountId", "Symbol", "Side", "Status",
        "FillQuantity", "FillPrice", "Description",
    ]
    orders_path = write_csv(out / "OrdersPeriod.csv", order_fields, period_filled[:500])
    met_path = write_metrics(out / "Metrics.csv", metrics)
    frag_path = write_fragments(
        out / "ReportSectionFragments.json",
        {
            "activity_quantification": (
                f"Period activity: {metrics['filled_orders']} filled orders across "
                f"{metrics['symbols_count']} symbols; gross turnover ${metrics['gross_turnover']:,.2f}. "
                "See OrdersPeriod.csv and Metrics.csv."
            )
        },
    )
    return SkillResult(
        skill="trading-activity-analysis",
        status="ok",
        artifacts=[str(orders_path), str(met_path), str(frag_path)],
        metrics=metrics,
        messages=["Wrote trading activity metrics and period order extract"],
    )
