"""Common CLI for PortfolioCoach skill scripts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


@dataclass
class SkillArgs:
    datastore: Path
    workspace: Path
    period_start: str | None = None
    period_end: str | None = None
    symbol: str | None = None
    thematic: bool | None = None
    input_dir: Path | None = None
    evaluation: bool = False


@dataclass
class SkillResult:
    skill: str
    status: str
    artifacts: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_parser(skill_id: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"PortfolioCoach skill: {skill_id}")
    p.add_argument("--datastore", required=True, type=Path, help="userDatastore root")
    p.add_argument("--workspace", required=True, type=Path, help="agentWorkspace output root")
    p.add_argument("--period-start", help="analysis period start YYYYMMDD")
    p.add_argument("--period-end", help="analysis period end YYYYMMDD")
    p.add_argument("--symbol", help="target symbol for unit-level skills")
    p.add_argument(
        "--thematic",
        choices=("true", "false"),
        help="thematic rollup lens for aggregate skills",
    )
    p.add_argument("--input-dir", type=Path, help="directory with upstream skill CSV outputs")
    p.add_argument(
        "--evaluation",
        choices=("true", "false"),
        default="false",
        help="evaluation overlay active",
    )
    return p


def parse_args(skill_id: str, argv: list[str] | None = None) -> SkillArgs:
    ns = build_parser(skill_id).parse_args(argv)
    thematic = None if ns.thematic is None else ns.thematic == "true"
    return SkillArgs(
        datastore=ns.datastore.expanduser().resolve(),
        workspace=ns.workspace.expanduser().resolve(),
        period_start=ns.period_start,
        period_end=ns.period_end,
        symbol=ns.symbol,
        thematic=thematic,
        input_dir=ns.input_dir.expanduser().resolve() if ns.input_dir else None,
        evaluation=ns.evaluation == "true",
    )


def write_result(workspace: Path, skill_id: str, result: SkillResult) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    result.skill = skill_id
    out = workspace / "skill-result.json"
    payload = result.to_dict()
    payload["completedAt"] = datetime.now(timezone.utc).isoformat()
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def run_main(skill_id: str, run_fn: Callable[[SkillArgs], SkillResult], argv: list[str] | None = None) -> int:
    try:
        args = parse_args(skill_id, argv)
        args.workspace.mkdir(parents=True, exist_ok=True)
        result = run_fn(args)
        write_result(args.workspace, skill_id, result)
        for msg in result.messages:
            print(msg, file=sys.stderr)
        if result.status != "ok":
            print(f"skill {skill_id}: {result.status}", file=sys.stderr)
            return 1
        return 0
    except Exception as exc:  # noqa: BLE001 — skill scripts report failure to agent
        fail = SkillResult(skill=skill_id, status="error", messages=[str(exc)])
        try:
            args = parse_args(skill_id, argv)
            write_result(args.workspace, skill_id, fail)
        except Exception:
            pass
        print(str(exc), file=sys.stderr)
        return 1
