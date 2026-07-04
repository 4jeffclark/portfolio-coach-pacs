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


def write_mapping_discovery(path: Path, title: str, lines: list[str]) -> Path:
    body = ["# Mapping Discovery", "", f"## {title}", ""] + lines + [""]
    path.write_text("\n".join(body), encoding="utf-8")
    return path
