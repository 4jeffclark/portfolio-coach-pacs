"""Stale position hygiene skill."""

from __future__ import annotations

from pc_lib.analytics import stale_position_facts
from pc_lib.canonical import load_canonical
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._skill_io import skill_out, write_fragments, write_metrics


def run(args: SkillArgs) -> SkillResult:
    if not args.symbol:
        return SkillResult(skill="stale-position-hygiene", status="error", messages=["--symbol is required"])
    out = skill_out(args, "stale-position-hygiene")
    sym = args.symbol.upper()
    positions = load_canonical(args.datastore, "positions_lot_level.csv")
    facts = stale_position_facts(positions, sym, args.period_end)
    facts["analysis_period_start"] = args.period_start or ""
    facts["analysis_period_end"] = args.period_end or ""
    met_path = write_metrics(out / "Metrics.csv", facts)
    stale_note = " (stalePositionFlag=true)" if facts.get("stalePositionFlag") else ""
    frag_path = write_fragments(
        out / "ReportSectionFragments.json",
        {
            "stale_position_review": (
                f"Stale hygiene facts for {sym} at snapshot {facts.get('snapshot_date', 'n/a')}: "
                f"MV ${facts.get('total_market_value', 0):,.2f}, "
                f"earliest acquired {facts.get('earliest_acquired', 'n/a')}, "
                f"days held {facts.get('days_held_at_snapshot', 'n/a')}{stale_note}. "
                "Agent documents thesis drift and stale-risk rules."
            )
        },
    )
    return SkillResult(
        skill="stale-position-hygiene",
        status="ok",
        artifacts=[str(met_path), str(frag_path)],
        metrics=facts,
        messages=[f"Wrote stale position hygiene facts for {sym}"],
    )
