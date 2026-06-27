"""Canonical datastore CSV helpers."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any, Iterable


CANONICAL_DIR = Path("data") / "canonical"
RAW_DIR = Path("data") / "raw" / "etrade"


def canonical_dir(datastore: Path) -> Path:
    return datastore / CANONICAL_DIR


def raw_dir(datastore: Path) -> Path:
    return datastore / RAW_DIR


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})
    return path


def load_canonical(datastore: Path, name: str) -> list[dict[str, str]]:
    return read_csv(canonical_dir(datastore) / name)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def parse_float(val: str | None, default: float = 0.0) -> float:
    if val is None or val == "":
        return default
    try:
        return float(str(val).replace(",", "").replace("$", "").strip())
    except ValueError:
        return default


def ymd_to_iso(ymd: str | None) -> str | None:
    if not ymd or len(ymd) != 8:
        return None
    return f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"


def in_period(date_str: str, start_ymd: str | None, end_ymd: str | None) -> bool:
    if not date_str:
        return False
    d = date_str[:10].replace("/", "-")
    if len(d) == 8 and d.isdigit():
        d = ymd_to_iso(d) or d
    start = ymd_to_iso(start_ymd) if start_ymd else None
    end = ymd_to_iso(end_ymd) if end_ymd else None
    if start and d < start:
        return False
    if end and d > end:
        return False
    return True


def work_dir(args_workspace: Path, skill_id: str) -> Path:
    d = args_workspace / skill_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def input_dir(args) -> Path:
    return args.input_dir if args.input_dir else work_dir(args.workspace, "_inputs")


def symbols_from_positions(positions: list[dict[str, str]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for row in positions:
        sym = (row.get("Symbol") or "").strip().upper()
        if not sym or sym in seen:
            continue
        if sym in ("PORTFOLIO ANALYSIS", "--"):
            continue
        seen.add(sym)
        out.append(sym)
    return sorted(out)
