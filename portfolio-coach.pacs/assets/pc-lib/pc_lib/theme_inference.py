"""Position-aware thematic inference."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from pc_lib.reference_data import (
    CASH_LIKE,
    SUBCLASS_TO_THEME,
    sector_to_theme,
    symbol_theme_overrides,
    theme_registry_seed,
)


def _registry_row(theme_id: str, label: str, description: str) -> dict[str, str]:
    return {
        "ThemeId": theme_id,
        "ThemeLabel": label,
        "ThemeNamespace": "CUSTOM",
        "ExternalThemeCode": "",
        "ParentThemeGroup": "",
        "Description": description,
        "Status": "active",
    }


def _seed_registry() -> dict[str, dict[str, str]]:
    return {
        row["themeId"]: {
            "label": row["themeLabel"],
            "description": row["description"],
        }
        for row in theme_registry_seed()
    }


def _assign_from_holdings(symbol: str, holdings_row: dict[str, str]) -> tuple[str, str, str]:
    """Return theme_id, rule_id, confidence."""
    sym = symbol.upper()
    override = symbol_theme_overrides().get(sym)
    if override:
        return override["themeId"], override.get("ruleId", "symbol_override"), override.get("confidence", "medium")

    if sym in CASH_LIKE:
        return "THEME_LIQUIDITY", "cash_like", "high"

    liq = (holdings_row.get("LiquidityRole") or "").lower()
    if liq == "cash_equivalent":
        return "THEME_LIQUIDITY", "liquidity_role", "high"

    subclass = holdings_row.get("AssetSubclass") or ""
    if subclass in SUBCLASS_TO_THEME:
        return SUBCLASS_TO_THEME[subclass], f"subclass:{subclass}", "medium"

    sector = holdings_row.get("GICSSector") or ""
    if sector:
        tid = sector_to_theme().get(sector)
        if tid:
            return tid, f"sector:{sector}", "medium"

    style = (holdings_row.get("StyleBucket") or "").lower()
    if style == "tactical":
        return "THEME_TACTICAL", "style_tactical", "low"

    return "THEME_UNASSIGNED", "residual", "low"


def infer_theme_registry(
    holdings: list[dict[str, str]],
    symbol_mv: dict[str, float] | None = None,
    knowledge_theme_map: list[dict[str, str]] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """
    Returns registry, theme_map, theme_coverage, inference_log.
    knowledge_theme_map rows override rule inference when Symbol matches.
    """
    seed = _seed_registry()
    knowledge_by_sym = {
        (r.get("Symbol") or "").upper(): r
        for r in (knowledge_theme_map or [])
        if r.get("Symbol")
    }
    holdings_by_sym = {(r.get("Symbol") or "").upper(): r for r in holdings if r.get("Symbol")}
    symbols = sorted(set(holdings_by_sym) | set(knowledge_by_sym))
    mv = symbol_mv or {}
    total_mv = sum(mv.values()) or 1.0

    theme_map: list[dict[str, str]] = []
    inference_log: list[dict[str, str]] = []
    theme_mv: dict[str, float] = defaultdict(float)
    theme_counts: dict[str, int] = defaultdict(int)

    for sym in symbols:
        if sym in knowledge_by_sym:
            krow = knowledge_by_sym[sym]
            tid = krow.get("ThemeId") or "THEME_UNASSIGNED"
            conf = krow.get("MappingConfidence") or "high"
            rule_id = "knowledge"
            notes = krow.get("Notes") or "source=knowledge"
            source = "knowledge"
        else:
            hrow = holdings_by_sym.get(sym, {"Symbol": sym})
            tid, rule_id, conf = _assign_from_holdings(sym, hrow)
            source = "rule"
            notes = f"source={source}; rule={rule_id}; confirm"

        theme_map.append(
            {
                "Symbol": sym,
                "ThemeId": tid,
                "MappingConfidence": conf,
                "PrimaryFlag": "true",
                "Notes": notes,
            }
        )
        inference_log.append(
            {
                "Symbol": sym,
                "ThemeId": tid,
                "RuleId": rule_id,
                "MappingConfidence": conf,
                "PeriodEndMV": f"{mv.get(sym, 0):.2f}",
                "PeriodEndWeightPct": f"{(mv.get(sym, 0) / total_mv * 100):.2f}" if mv.get(sym) else "0.00",
            }
        )
        theme_mv[tid] += mv.get(sym, 0)
        theme_counts[tid] += 1

    active_themes = {r["ThemeId"] for r in theme_map}
    registry: list[dict[str, str]] = []
    for tid in sorted(active_themes):
        meta = seed.get(tid, {"label": tid.replace("THEME_", "").replace("_", " ").title(), "description": ""})
        registry.append(_registry_row(tid, meta["label"], meta["description"]))

    theme_coverage: list[dict[str, str]] = []
    for tid in sorted(theme_mv, key=lambda t: theme_mv[t], reverse=True):
        weight = theme_mv[tid] / total_mv * 100 if total_mv else 0
        meta = seed.get(tid, {"label": tid})
        theme_coverage.append(
            {
                "ThemeId": tid,
                "ThemeLabel": meta.get("label", tid),
                "SymbolCount": str(theme_counts[tid]),
                "PeriodEndMV": f"{theme_mv[tid]:.2f}",
                "WeightPct": f"{weight:.2f}",
            }
        )

    return registry, theme_map, theme_coverage, inference_log


def infer_thesis_registry(
    symbols: list[str],
    theme_map: list[dict[str, str]],
    theme_coverage: list[dict[str, str]] | None = None,
    clustered: bool = True,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    theme_by_sym = {(r.get("Symbol") or "").upper(): r.get("ThemeId", "") for r in theme_map}
    skip_theses = {"THEME_LIQUIDITY", "THEME_UNASSIGNED", "THEME_OTHER"}

    if not clustered:
        registry = [
            {
                "ThesisId": "THESIS_ACTIVE_BOOK",
                "ThesisStatement": "Active portfolio positions under current construction thesis",
                "ParentThemeId": "THEME_UNASSIGNED",
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
                "ThesisId": "THESIS_ACTIVE_BOOK" if sym not in CASH_LIKE else "",
                "AssignmentConfidence": "low",
                "PrimaryFlag": "true",
                "Notes": "" if sym not in CASH_LIKE else "liquidity residual",
            }
            for sym in symbols
            if sym not in CASH_LIKE
        ]
        return registry, assignments

    weight_by_theme = {
        (r.get("ThemeId") or ""): float(r.get("WeightPct") or 0)
        for r in (theme_coverage or [])
    }
    active_themes = sorted(
        {
            tid
            for tid in set(theme_by_sym.values())
            if tid and tid not in skip_theses
        },
        key=lambda t: weight_by_theme.get(t, 0),
        reverse=True,
    )

    registry: list[dict[str, str]] = []
    for tid in active_themes:
        thesis_id = tid.replace("THEME_", "THESIS_")
        registry.append(
            {
                "ThesisId": thesis_id,
                "ThesisStatement": f"Portfolio sleeve aligned to {tid}",
                "ParentThemeId": tid,
                "HorizonStart": "",
                "HorizonEnd": "",
                "PrimaryCatalyst": "",
                "Status": "active",
                "Notes": "inferred from theme cluster",
            }
        )

    if not registry:
        registry = [
            {
                "ThesisId": "THESIS_ACTIVE_BOOK",
                "ThesisStatement": "Active portfolio positions under current construction thesis",
                "ParentThemeId": "THEME_UNASSIGNED",
                "HorizonStart": "",
                "HorizonEnd": "",
                "PrimaryCatalyst": "",
                "Status": "active",
                "Notes": "inferred placeholder",
            }
        ]

    thesis_by_theme = {r["ParentThemeId"]: r["ThesisId"] for r in registry if r.get("ParentThemeId")}
    assignments: list[dict[str, str]] = []
    for sym in symbols:
        if sym in CASH_LIKE:
            continue
        tid = theme_by_sym.get(sym, "")
        if tid in skip_theses:
            thesis_id = "THESIS_ACTIVE_BOOK" if "THESIS_ACTIVE_BOOK" in {r["ThesisId"] for r in registry} else ""
        else:
            thesis_id = thesis_by_theme.get(tid, registry[0]["ThesisId"])
        if not thesis_id:
            continue
        assignments.append(
            {
                "Symbol": sym,
                "ThesisId": thesis_id,
                "AssignmentConfidence": "medium" if tid not in skip_theses else "low",
                "PrimaryFlag": "true",
                "Notes": f"parent_theme={tid}" if tid else "",
            }
        )
    return registry, assignments


def theme_inference_metrics(theme_coverage: list[dict[str, str]]) -> dict[str, Any]:
    weights = {r["ThemeId"]: float(r.get("WeightPct") or 0) for r in theme_coverage}
    unassigned = weights.get("THEME_UNASSIGNED", 0) + weights.get("THEME_OTHER", 0)
    assigned = 100.0 - unassigned
    return {
        "themeCount": len(theme_coverage),
        "unassignedWeightPct": round(unassigned, 2),
        "inferenceCoveragePct": round(assigned, 2),
    }
