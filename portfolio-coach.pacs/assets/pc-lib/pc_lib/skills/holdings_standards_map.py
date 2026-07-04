"""Holdings standards map skill."""

from __future__ import annotations

from pc_lib.analytics import infer_holdings_map, mapping_universe
from pc_lib.canonical import load_canonical, load_knowledge_csv
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import HOLDINGS_MAP_FIELDS, skill_out, write_fragments
from pc_lib.canonical import write_csv


def run(args: SkillArgs) -> SkillResult:
    out = skill_out(args, "holdings-standards-map")
    positions = load_canonical(args.datastore, "positions_lot_level.csv")
    orders = load_canonical(args.datastore, "orders.csv")
    knowledge = load_knowledge_csv(args.datastore, "holdings", "HoldingsMapCurrent.csv")
    symbols = mapping_universe(positions, orders, args.period_start, args.period_end)
    rows = infer_holdings_map(symbols, knowledge or None)
    path = write_csv(out / "HoldingsMap.csv", HOLDINGS_MAP_FIELDS, rows)
    frag = write_fragments(
        out / "ReportSectionFragments.json",
        {"holdings_map": f"Inferred HoldingsMap for {len(rows)} symbols — requires confirmation."},
    )
    return SkillResult(
        skill="holdings-standards-map",
        status="ok",
        artifacts=[str(path), str(frag)],
        metrics={"symbolCount": len(rows)},
        messages=[f"Inferred holdings map for {len(rows)} symbols"],
    )
