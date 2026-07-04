"""Portfolio period flows skill."""

from __future__ import annotations

from collections import defaultdict

from pc_lib.analytics import fill_notional, filled_orders, order_side
from pc_lib.canonical import load_canonical, read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import resolve_rollup_lens, skill_out, write_fragments


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "portfolio-period-flows")
    orders = load_canonical(args.datastore, "orders.csv")
    period = filled_orders(orders, args.period_start, args.period_end)
    lens = resolve_rollup_lens(args)
    hmap = read_csv((args.workspace / "holdings-map-confirmation") / "HoldingsMap.csv")
    sector_by_sym = {(r.get("Symbol") or "").upper(): r.get("GICSSector") or "Unclassified" for r in hmap}
    if lens == "theme":
        tmap = read_csv((args.workspace / "theme-map-confirmation") / "ThemeMap.csv")
        bucket_by_sym = {(r.get("Symbol") or "").upper(): r.get("ThemeId") or "Unassigned" for r in tmap}
    elif lens == "thesis":
        amap = read_csv((args.workspace / "thesis-registry-confirmation") / "ThesisAssignment.csv")
        bucket_by_sym = {(r.get("Symbol") or "").upper(): r.get("ThesisId") or "Unassigned" for r in amap}
    else:
        bucket_by_sym = sector_by_sym

    agg: dict[str, dict[str, float]] = defaultdict(lambda: {"buy": 0.0, "sell": 0.0})
    for row in period:
        sym = (row.get("Symbol") or "").upper()
        bucket = bucket_by_sym.get(sym, "Unassigned")
        side = order_side(row)
        notional = fill_notional(row)
        if side == "buy":
            agg[bucket]["buy"] += notional
        elif side == "sell":
            agg[bucket]["sell"] += notional

    rows = [
        {
            "Bucket": b,
            "BuyNotional": f"{v['buy']:.2f}",
            "SellNotional": f"{v['sell']:.2f}",
            "NetFlow": f"{v['buy'] - v['sell']:.2f}",
            "GrossTurnover": f"{v['buy'] + v['sell']:.2f}",
        }
        for b, v in sorted(agg.items())
    ]
    path = write_csv(
        out / "PeriodFlows.csv",
        ["Bucket", "BuyNotional", "SellNotional", "NetFlow", "GrossTurnover"],
        rows,
    )
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {"period_flows": f"Order flows aggregated across {len(rows)} buckets."},
    )
    return SkillResult(
        skill="portfolio-period-flows",
        status="ok",
        artifacts=[str(path), str(frag)],
        metrics={"bucketCount": len(rows)},
        messages=["Wrote portfolio period flows"],
    )
