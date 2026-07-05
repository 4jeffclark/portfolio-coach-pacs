"""Holdings standards inference from reference catalogs and durable knowledge."""

from __future__ import annotations

from pc_lib.reference_data import CASH_LIKE, equity_gics_seed, etf_catalog


def infer_holdings_row(symbol: str, knowledge: dict[str, str] | None = None) -> dict[str, str]:
    sym = symbol.upper()
    if knowledge:
        row = {**knowledge, "Symbol": sym}
        if not row.get("MappingSource"):
            row["MappingSource"] = "knowledge"
        if not row.get("MappingConfidence"):
            row["MappingConfidence"] = "high"
        return row

    etf = etf_catalog().get(sym)
    if etf:
        liq = etf.get("liquidityRole") or ("cash_equivalent" if sym in CASH_LIKE else "invested")
        return {
            "Symbol": sym,
            "AssetClass": etf.get("assetClass", "Equity"),
            "AssetSubclass": etf.get("assetSubclass", ""),
            "GICSSector": etf.get("gicsSector", ""),
            "GICSIndustry": "",
            "StyleBucket": etf.get("styleBucket", "Other"),
            "LiquidityRole": liq,
            "MappingConfidence": "medium",
            "MappingSource": "etf_catalog",
            "Notes": "",
        }

    eq = equity_gics_seed().get(sym)
    if eq:
        return {
            "Symbol": sym,
            "AssetClass": "Equity",
            "AssetSubclass": "US Equity",
            "GICSSector": eq.get("gicsSector", ""),
            "GICSIndustry": eq.get("gicsIndustry", ""),
            "StyleBucket": eq.get("styleBucket", "Other"),
            "LiquidityRole": "cash_equivalent" if sym in CASH_LIKE else "invested",
            "MappingConfidence": "medium",
            "MappingSource": "equity_gics_seed",
            "Notes": "",
        }

    if sym in CASH_LIKE:
        return {
            "Symbol": sym,
            "AssetClass": "FixedIncome",
            "AssetSubclass": "Treasury ETF",
            "GICSSector": "Fixed Income",
            "GICSIndustry": "",
            "StyleBucket": "Defensive",
            "LiquidityRole": "cash_equivalent",
            "MappingConfidence": "medium",
            "MappingSource": "cash_like_set",
            "Notes": "",
        }

    return {
        "Symbol": sym,
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
