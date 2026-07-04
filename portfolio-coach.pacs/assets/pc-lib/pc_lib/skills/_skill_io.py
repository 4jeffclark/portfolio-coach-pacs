"""Shared skill I/O helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pc_lib.canonical import read_csv, write_csv, work_dir
from pc_lib.cli import SkillArgs


HOLDINGS_MAP_FIELDS = [
    "Symbol",
    "AssetClass",
    "AssetSubclass",
    "GICSSector",
    "GICSIndustry",
    "StyleBucket",
    "LiquidityRole",
    "MappingConfidence",
    "MappingSource",
    "Notes",
]

THEME_REGISTRY_FIELDS = [
    "ThemeId",
    "ThemeLabel",
    "ThemeNamespace",
    "ExternalThemeCode",
    "ParentThemeGroup",
    "Description",
    "Status",
]

THEME_MAP_FIELDS = ["Symbol", "ThemeId", "MappingConfidence", "PrimaryFlag", "Notes"]

THESIS_REGISTRY_FIELDS = [
    "ThesisId",
    "ThesisStatement",
    "ParentThemeId",
    "HorizonStart",
    "HorizonEnd",
    "PrimaryCatalyst",
    "Status",
    "Notes",
]

THESIS_ASSIGNMENT_FIELDS = ["Symbol", "ThesisId", "AssignmentConfidence", "PrimaryFlag", "Notes"]


def skill_out(args: SkillArgs, skill_id: str) -> Path:
    return work_dir(args.workspace, skill_id)


def upstream_csv(args: SkillArgs, skill_id: str, filename: str) -> list[dict[str, str]]:
    if args.input_dir:
        return read_csv(args.input_dir / filename)
    return read_csv(work_dir(args.workspace, skill_id) / filename)


def write_metrics(path: Path, metrics: dict[str, Any]) -> Path:
    rows = [{"Metric": k, "Value": str(v)} for k, v in metrics.items()]
    return write_csv(path, ["Metric", "Value"], rows)


def write_fragments(path: Path, fragments: dict[str, str]) -> Path:
    path.write_text(json.dumps(fragments, indent=2) + "\n", encoding="utf-8")
    return path


ROLLUP_LENS_FILENAME = "RollupLens.txt"


def write_rollup_lens(workspace: Path, lens: str) -> None:
    """Persist resolved rollup lens for downstream skills in the composition chain."""
    text = lens.strip() + "\n"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / ROLLUP_LENS_FILENAME).write_text(text, encoding="utf-8")
    weights_dir = work_dir(workspace, "portfolio-weights-table")
    weights_dir.mkdir(parents=True, exist_ok=True)
    (weights_dir / ROLLUP_LENS_FILENAME).write_text(text, encoding="utf-8")


def resolve_rollup_lens(args: SkillArgs) -> str:
    """Resolve rollup lens from CLI flag, workspace RollupLens.txt, or thematic default."""
    if args.rollup_lens:
        return args.rollup_lens.strip()
    for path in (
        args.workspace / ROLLUP_LENS_FILENAME,
        work_dir(args.workspace, "portfolio-weights-table") / ROLLUP_LENS_FILENAME,
    ):
        if path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text
    if args.thematic is True:
        return "theme"
    if args.thematic is False:
        return "standards"
    return "theme"


def write_mapping_discovery(path: Path, title: str, lines: list[str]) -> Path:
    body = ["# Mapping Discovery", "", f"## {title}", ""] + lines + [""]
    path.write_text("\n".join(body), encoding="utf-8")
    return path
