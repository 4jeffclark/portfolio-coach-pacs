"""Portfolio liquidity analysis skill."""

from __future__ import annotations

from pc_lib.analytics import latest_snapshot_date, positions_at_snapshot
from pc_lib.canonical import load_canonical, read_csv, write_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "portfolio-liquidity-analysis")
    positions = load_canonical(args.datastore, "positions_lot_level.csv")
    cash = load_canonical(args.datastore, "cash.csv")
    hmap = read_csv((args.workspace / "holdings-map-confirmation") / "HoldingsMap.csv")
    liq_by_sym = {(r.get("Symbol") or "").upper(): r.get("LiquidityRole", "invested") for r in hmap}

    from pc_lib.canonical import ymd_to_iso

    start_snap = latest_snapshot_date(positions, ymd_to_iso(args.period_start) or "")
    end_snap = latest_snapshot_date(positions, ymd_to_iso(args.period_end) or "")
    rows = []
    for label, snap in (("period_start", start_snap), ("period_end", end_snap)):
        for row in positions_at_snapshot(positions, snap):
            sym = (row.get("Symbol") or "").upper()
            rows.append(
                {
                    "Snapshot": label,
                    "Component": liq_by_sym.get(sym, "invested"),
                    "Symbol": sym,
                    "AccountLabel": row.get("AccountLabel", ""),
                    "MarketValue": row.get("MarketValue", ""),
                    "LiquidityRole": liq_by_sym.get(sym, "invested"),
                }
            )
    if cash:
        for row in cash[-6:]:
            rows.append(
                {
                    "Snapshot": "period_end",
                    "Component": "broker_cash",
                    "Symbol": "CASH",
                    "AccountLabel": row.get("AccountLabel", ""),
                    "MarketValue": row.get("CashAvailToWithdraw", row.get("PortfolioCashOnDeposit", "")),
                    "LiquidityRole": "broker_cash",
                }
            )
    path = write_csv(
        out / "LiquidityBreakdown.csv",
        ["Snapshot", "Component", "Symbol", "AccountLabel", "MarketValue", "LiquidityRole"],
        rows,
    )
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {"liquidity": f"Liquidity breakdown: {len(rows)} component rows."},
    )
    return SkillResult(
        skill="portfolio-liquidity-analysis",
        status="ok",
        artifacts=[str(path), str(frag)],
        messages=["Wrote liquidity breakdown"],
    )
