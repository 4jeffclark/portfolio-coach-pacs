"""Shared analytics helpers for PortfolioCoach skills."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from pc_lib.canonical import in_period, parse_float, position_symbol, symbols_from_positions


def _order_date(row: dict[str, str]) -> str:
    return (row.get("Date") or row.get("Time") or "")[:10]


def _is_filled(row: dict[str, str]) -> bool:
    status = (row.get("Status") or "").lower()
    fill_qty = parse_float(row.get("FillQuantity"))
    return status == "filled" or fill_qty > 0


def filled_orders(
    orders: list[dict[str, str]],
    period_start: str | None = None,
    period_end: str | None = None,
    symbol: str | None = None,
) -> list[dict[str, str]]:
    sym = symbol.upper().strip() if symbol else None
    out: list[dict[str, str]] = []
    for row in orders:
        if not _is_filled(row):
            continue
        if sym and (row.get("Symbol") or "").upper() != sym:
            continue
        d = _order_date(row)
        if period_start or period_end:
            if not in_period(d, period_start, period_end):
                continue
        out.append(row)
    return out


def order_side(row: dict[str, str]) -> str:
    return (row.get("Side") or "").strip().lower()


def fill_notional(row: dict[str, str]) -> float:
    qty = parse_float(row.get("FillQuantity"))
    price = parse_float(row.get("FillPrice"))
    if qty and price:
        return qty * price
    return parse_float(row.get("Fill").split("@")[-1]) if "@" in (row.get("Fill") or "") else 0.0


def symbol_period_notionals(orders: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    """Buy, sell, and gross notional per symbol for a pre-filtered filled-order list."""
    totals: dict[str, dict[str, float]] = defaultdict(lambda: {"buy": 0.0, "sell": 0.0})
    for row in orders:
        if not _is_filled(row):
            continue
        sym = (row.get("Symbol") or "").upper()
        if not sym:
            continue
        notional = fill_notional(row)
        side = order_side(row)
        if side == "buy":
            totals[sym]["buy"] += notional
        elif side == "sell":
            totals[sym]["sell"] += notional
    return {
        sym: {
            "buy_notional": round(vals["buy"], 2),
            "sell_notional": round(vals["sell"], 2),
            "gross_notional": round(vals["buy"] + vals["sell"], 2),
        }
        for sym, vals in totals.items()
    }


def top_symbols_by_weight(
    end_mv: dict[str, float],
    end_total: float,
    limit: int = 10,
) -> list[tuple[str, float, float]]:
    """Return (symbol, market_value, weight_pct) sorted by weight descending."""
    if not end_total:
        return []
    ranked = sorted(
        ((sym, val, val / end_total * 100) for sym, val in end_mv.items() if val),
        key=lambda row: row[2],
        reverse=True,
    )
    return ranked[:limit]


def top_symbols_by_notional(
    notionals: dict[str, dict[str, float]],
    limit: int = 10,
) -> list[tuple[str, float]]:
    """Return (symbol, gross_notional) sorted by period gross notional descending."""
    ranked = sorted(
        ((sym, vals["gross_notional"]) for sym, vals in notionals.items() if vals["gross_notional"]),
        key=lambda row: row[1],
        reverse=True,
    )
    return ranked[:limit]


def activity_metrics(orders: list[dict[str, str]]) -> dict[str, Any]:
    filled = [r for r in orders if _is_filled(r)]
    buys = [r for r in filled if order_side(r) == "buy"]
    sells = [r for r in filled if order_side(r) == "sell"]
    symbols = sorted({(r.get("Symbol") or "").upper() for r in filled if r.get("Symbol")})
    buy_notional = sum(fill_notional(r) for r in buys)
    sell_notional = sum(fill_notional(r) for r in sells)
    dates = sorted({_order_date(r) for r in filled if _order_date(r)})
    return {
        "filled_orders": len(filled),
        "buy_count": len(buys),
        "sell_count": len(sells),
        "symbols_count": len(symbols),
        "buy_notional": round(buy_notional, 2),
        "sell_notional": round(sell_notional, 2),
        "gross_turnover": round(buy_notional + sell_notional, 2),
        "activity_date_min": dates[0] if dates else "",
        "activity_date_max": dates[-1] if dates else "",
    }


def symbol_metrics(orders: list[dict[str, str]], symbol: str) -> dict[str, Any]:
    sym = symbol.upper()
    filled = filled_orders(orders, symbol=sym)
    buys = [r for r in filled if order_side(r) == "buy"]
    sells = [r for r in filled if order_side(r) == "sell"]
    shares_bought = sum(parse_float(r.get("FillQuantity")) for r in buys)
    shares_sold = sum(parse_float(r.get("FillQuantity")) for r in sells)
    gross_buy = sum(fill_notional(r) for r in buys)
    gross_sell = sum(fill_notional(r) for r in sells)
    times = sorted(r.get("Time") or r.get("Date") or "" for r in filled if r.get("Time") or r.get("Date"))
    realized = 0.0
    lots: list[tuple[float, float]] = []
    for row in sorted(filled, key=lambda r: r.get("Time") or r.get("Date") or ""):
        qty = parse_float(row.get("FillQuantity"))
        price = parse_float(row.get("FillPrice"))
        if not qty or not price:
            continue
        if order_side(row) == "buy":
            lots.append((qty, price))
        elif order_side(row) == "sell":
            remaining = qty
            while remaining > 0 and lots:
                lot_qty, lot_price = lots[0]
                take = min(remaining, lot_qty)
                realized += take * (price - lot_price)
                remaining -= take
                if take >= lot_qty:
                    lots.pop(0)
                else:
                    lots[0] = (lot_qty - take, lot_price)
    ending = sum(q for q, _ in lots)
    max_shares = max((sum(parse_float(r.get("FillQuantity")) for r in buys[: i + 1]) for i in range(len(buys))), default=0)
    return {
        f"{sym}_order_records": len(filled),
        "shares_bought": round(shares_bought, 4),
        "shares_sold": round(shares_sold, 4),
        "ending_shares": round(ending, 4),
        "gross_buy_notional": round(gross_buy, 2),
        "gross_sell_notional": round(gross_sell, 2),
        "total_turnover": round(gross_buy + gross_sell, 2),
        "realized_pnl_fifo_ex_fees": round(realized, 2),
        "first_fill": times[0] if times else "",
        "last_fill": times[-1] if times else "",
        "max_shares_bought_cumulative": round(max_shares, 4),
    }


def mapping_universe(
    positions: list[dict[str, str]],
    orders: list[dict[str, str]],
    period_start: str | None,
    period_end: str | None,
) -> list[str]:
    pos_syms = set(symbols_from_positions(positions))
    order_syms = {
        (r.get("Symbol") or "").upper()
        for r in filled_orders(orders, period_start, period_end)
        if r.get("Symbol")
    }
    return sorted(pos_syms | order_syms)


_CASH_LIKE = {"SGOV", "BIL", "SHV", "VMFXX", "SPAXX", "FDRXX", "SPRXX", "VMMXX"}
_ETF_HINTS = {
    "VOO": ("Equity", "US Equity", "Broad Market ETF", "IndexFactor", "invested"),
    "SPY": ("Equity", "US Equity", "Broad Market ETF", "IndexFactor", "invested"),
    "QQQ": ("Equity", "US Equity", "Factor ETF", "Growth", "invested"),
    "MSFT": ("Equity", "US Equity", "Information Technology", "Growth", "invested"),
    "AAPL": ("Equity", "US Equity", "Information Technology", "Growth", "invested"),
    "GLD": ("Commodity", "Physical Precious Metal Trust", "Materials", "Defensive", "invested"),
    "SGOV": ("FixedIncome", "Treasury ETF", "Utilities", "Defensive", "cash_equivalent"),
}


def infer_holdings_row(symbol: str, knowledge: dict[str, str] | None = None) -> dict[str, str]:
    if knowledge:
        return {**knowledge, "Symbol": symbol}
    hint = _ETF_HINTS.get(symbol)
    if hint:
        ac, sub, sector, style, liq = hint
        return {
            "Symbol": symbol,
            "AssetClass": ac,
            "AssetSubclass": sub,
            "GICSSector": sector,
            "GICSIndustry": "",
            "StyleBucket": style,
            "LiquidityRole": liq,
            "MappingConfidence": "medium",
            "MappingSource": "heuristic",
            "Notes": "",
        }
    return {
        "Symbol": symbol,
        "AssetClass": "Equity",
        "AssetSubclass": "US Equity",
        "GICSSector": "",
        "GICSIndustry": "",
        "StyleBucket": "Other",
        "LiquidityRole": "invested",
        "MappingConfidence": "low",
        "MappingSource": "inferred",
        "Notes": "requires confirmation",
    }


def infer_holdings_map(
    symbols: list[str],
    knowledge_rows: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    by_sym = {(r.get("Symbol") or "").upper(): r for r in (knowledge_rows or [])}
    return [infer_holdings_row(s, by_sym.get(s)) for s in symbols]


def infer_theme_registry(symbols: list[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    themes = [
        ("THEME_TECH", "Technology & AI", "CUSTOM", "Structural technology exposure"),
        ("THEME_INCOME", "Income & Dividend", "CUSTOM", "Income-oriented holdings"),
        ("THEME_LIQUIDITY", "Liquidity & Cash", "CUSTOM", "Cash and cash-equivalent sleeve"),
        ("THEME_OTHER", "Residual / Other", "CUSTOM", "Unassigned or residual symbols"),
    ]
    registry = [
        {
            "ThemeId": tid,
            "ThemeLabel": label,
            "ThemeNamespace": ns,
            "ExternalThemeCode": "",
            "ParentThemeGroup": "",
            "Description": desc,
            "Status": "active",
        }
        for tid, label, ns, desc in themes
    ]
    theme_map: list[dict[str, str]] = []
    for sym in symbols:
        if sym in _CASH_LIKE:
            tid = "THEME_LIQUIDITY"
        elif sym in {"MSFT", "AAPL", "NVDA", "AMZN", "META", "GOOGL"}:
            tid = "THEME_TECH"
        elif sym in {"JEPQ", "JEPI", "VOO", "SPY"}:
            tid = "THEME_INCOME"
        else:
            tid = "THEME_OTHER"
        theme_map.append(
            {
                "Symbol": sym,
                "ThemeId": tid,
                "MappingConfidence": "low",
                "PrimaryFlag": "true",
                "Notes": "inferred — confirm",
            }
        )
    return registry, theme_map


def infer_thesis_registry(
    symbols: list[str], theme_map: list[dict[str, str]]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    theme_by_sym = {(r.get("Symbol") or "").upper(): r.get("ThemeId", "") for r in theme_map}
    registry = [
        {
            "ThesisId": "THESIS_ACTIVE_BOOK",
            "ThesisStatement": "Active portfolio positions under current construction thesis",
            "ParentThemeId": "THEME_OTHER",
            "HorizonStart": "",
            "HorizonEnd": "",
            "PrimaryCatalyst": "",
            "Status": "active",
            "Notes": "inferred placeholder",
        }
    ]
    assignments = [
        {
            "Symbol": sym,
            "ThesisId": "THESIS_ACTIVE_BOOK" if sym not in _CASH_LIKE else "",
            "AssignmentConfidence": "low",
            "PrimaryFlag": "true",
            "Notes": "" if sym not in _CASH_LIKE else "liquidity residual",
        }
        for sym in symbols
        if sym not in _CASH_LIKE
    ]
    return registry, assignments


def _parse_asof(row: dict[str, str]) -> str:
    return (row.get("AsOfLocal") or "")[:10].replace("/", "-")


def latest_snapshot_date(positions: list[dict[str, str]], boundary_iso: str | None) -> str:
    dates = sorted({_parse_asof(r) for r in positions if _parse_asof(r)})
    if not dates:
        return ""
    if not boundary_iso:
        return dates[-1]
    eligible = [d for d in dates if d <= boundary_iso[:10]]
    return eligible[-1] if eligible else ""


def positions_at_snapshot(positions: list[dict[str, str]], snapshot_date: str) -> list[dict[str, str]]:
    if not snapshot_date:
        return positions
    return [r for r in positions if _parse_asof(r) == snapshot_date]


def symbol_market_values(positions: list[dict[str, str]]) -> dict[str, float]:
    mv: dict[str, float] = defaultdict(float)
    for row in positions:
        sym = position_symbol(row)
        if not sym:
            continue
        mv[sym] += parse_float(row.get("MarketValue"))
    return dict(mv)


def total_market_value(positions: list[dict[str, str]]) -> float:
    return sum(symbol_market_values(positions).values())


def weights_table(
    start_mv: dict[str, float],
    end_mv: dict[str, float],
    bucket_fn,
    start_total: float,
    end_total: float,
) -> list[dict[str, str]]:
    buckets: set[str] = set()
    for mv in (start_mv, end_mv):
        for sym, val in mv.items():
            if val:
                buckets.add(bucket_fn(sym))
    rows: list[dict[str, str]] = []
    for bucket in sorted(buckets):
        s = sum(start_mv.get(sym, 0) for sym in start_mv if bucket_fn(sym) == bucket)
        e = sum(end_mv.get(sym, 0) for sym in end_mv if bucket_fn(sym) == bucket)
        sw = (s / start_total * 100) if start_total else 0
        ew = (e / end_total * 100) if end_total else 0
        rows.append(
            {
                "Bucket": bucket,
                "PeriodStartMV": f"{s:.2f}",
                "PeriodEndMV": f"{e:.2f}",
                "PeriodStartWeightPct": f"{sw:.2f}",
                "PeriodEndWeightPct": f"{ew:.2f}",
                "DeltaPp": f"{ew - sw:.2f}",
            }
        )
    return rows


def hhi(weight_pcts: list[float]) -> float:
    return round(sum((w / 100) ** 2 for w in weight_pcts), 4)


def stale_position_facts(positions: list[dict[str, str]], symbol: str) -> dict[str, Any]:
    sym = symbol.upper()
    rows = [r for r in positions if (r.get("Symbol") or "").upper() == sym]
    if not rows:
        return {"symbol": sym, "position_rows": 0}
    total_mv = sum(parse_float(r.get("MarketValue")) for r in rows)
    total_cost = sum(parse_float(r.get("CostBasis")) * parse_float(r.get("Quantity")) for r in rows)
    total_gain = sum(parse_float(r.get("OpenNetGain")) for r in rows)
    acquired = [r.get("DateAcquired") or "" for r in rows if r.get("DateAcquired")]
    return {
        "symbol": sym,
        "position_rows": len(rows),
        "total_market_value": round(total_mv, 2),
        "aggregate_open_gain": round(total_gain, 2),
        "earliest_acquired": min(acquired) if acquired else "",
        "return_vs_cost_pct": round((total_mv - total_cost) / total_cost * 100, 2) if total_cost else 0,
    }
