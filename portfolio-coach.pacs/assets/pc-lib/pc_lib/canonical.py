"""Canonical datastore CSV helpers and layout resolution."""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable


STANDARD_CANONICAL = Path("data") / "canonical"
STANDARD_RAW = Path("data") / "raw" / "etrade"
STANDARD_KNOWLEDGE = Path("data") / "knowledge"
LEGACY_CANONICAL = Path("canonical")
LEGACY_RAW = Path("raw") / "etrade"
LEGACY_KNOWLEDGE = Path("knowledge")

# Domain date columns per canonical table (see contracts/datastore-contract.md).
CANONICAL_DATE_COLUMNS: dict[str, list[str]] = {
    "accounts.csv": ["AsOfLocal"],
    "account_history.csv": ["ActivityDate", "ActivityDateTime"],
    "balances.csv": ["AsOfLocal"],
    "cash.csv": ["AsOfLocal"],
    "cash_activity_daily.csv": ["Date"],
    "cash_balance_estimated.csv": ["Date"],
    "income_events.csv": ["ActivityDate", "ActivityDateTime"],
    "orders.csv": ["Date"],
    "positions_lot_level.csv": ["AsOfLocal", "DateAcquired"],
    "ingestion_manifest.csv": ["MinDate", "MaxDate"],
}

DERIVED_CANONICAL_TABLES = (
    "cash_activity_daily.csv",
    "cash_balance_estimated.csv",
    "income_events.csv",
)


class DatastoreLayoutError(Exception):
    """Raised when the bound userDatastore cannot be resolved to a usable layout."""


@dataclass
class ResolvedLayout:
    name: str  # "standard" | "legacy"
    canonical: Path
    raw_etrade: Path
    knowledge: Path
    warnings: list[str] = field(default_factory=list)


@dataclass
class PeriodWindows:
    analysis_period_start: str
    analysis_period_end: str
    lookback_start: str
    lookback_end: str
    follow_through_start: str
    follow_through_end: str


def _path_has_content(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file():
        return True
    return any(path.iterdir()) if path.is_dir() else False


def resolve_layout(datastore: Path) -> ResolvedLayout:
    """Resolve canonical and raw paths with documented precedence.

    1. **Standard** — `{userDatastore}/data/canonical/` and `data/raw/etrade/` when
       either path exists and has content.
    2. **Legacy** — `{userDatastore}/canonical/` and `raw/etrade/` when standard
       paths are absent but legacy paths exist.
    3. **Default** — standard paths for empty or new datastores.

    When both layouts exist, standard wins; a warning is recorded.
    """
    root = datastore.expanduser().resolve()
    warnings: list[str] = []

    standard_canon = root / STANDARD_CANONICAL
    standard_raw = root / STANDARD_RAW
    legacy_canon = root / LEGACY_CANONICAL
    legacy_raw = root / LEGACY_RAW

    has_standard = _path_has_content(standard_canon) or _path_has_content(standard_raw)
    has_legacy = _path_has_content(legacy_canon) or _path_has_content(legacy_raw)

    if has_standard and has_legacy:
        warnings.append(
            "Both standard (data/) and legacy (root) layouts detected; using standard paths."
        )
    standard_knowledge = root / STANDARD_KNOWLEDGE
    legacy_knowledge = root / LEGACY_KNOWLEDGE
    has_standard_knowledge = _path_has_content(standard_knowledge)
    has_legacy_knowledge = _path_has_content(legacy_knowledge)

    if has_standard and has_legacy:
        pass  # warning already recorded above
    if has_standard_knowledge and has_legacy_knowledge:
        warnings.append(
            "Both standard (data/knowledge/) and legacy (knowledge/) detected; using standard knowledge path."
        )

    if has_standard:
        knowledge = standard_knowledge
        if has_legacy_knowledge and not has_standard_knowledge:
            knowledge = legacy_knowledge
            warnings.append(
                "Standard data layout with legacy knowledge/ at root; using legacy knowledge path."
            )
        return ResolvedLayout("standard", standard_canon, standard_raw, knowledge, warnings)
    if has_legacy:
        warnings.append(
            "Legacy layout (canonical/ and raw/etrade/ at datastore root) in use. "
            "Prefer migrating to data/canonical/ and data/raw/etrade/ per user-datastore-layout.md."
        )
        knowledge = legacy_knowledge if has_legacy_knowledge else standard_knowledge
        return ResolvedLayout("legacy", legacy_canon, legacy_raw, knowledge, warnings)
    knowledge = standard_knowledge if has_standard_knowledge else legacy_knowledge
    return ResolvedLayout("standard", standard_canon, standard_raw, knowledge, warnings)


def validate_layout(datastore: Path) -> ResolvedLayout:
    """Resolve layout or fail fast with a clear error when nothing is usable."""
    layout = resolve_layout(datastore)
    root = datastore.expanduser().resolve()
    if (
        _path_has_content(layout.canonical)
        or _path_has_content(layout.raw_etrade)
        or _path_has_content(root / "inputs")
        or _path_has_content(root / "reports")
    ):
        return layout
    raise DatastoreLayoutError(
        f"No usable datastore layout under {datastore}. "
        "Expected data/canonical/ and data/raw/etrade/ (standard) or "
        "canonical/ and raw/etrade/ (legacy). See contracts/user-datastore-layout.md."
    )


def canonical_dir(datastore: Path) -> Path:
    return resolve_layout(datastore).canonical


def raw_dir(datastore: Path) -> Path:
    return resolve_layout(datastore).raw_etrade


def knowledge_dir(datastore: Path) -> Path:
    return resolve_layout(datastore).knowledge


def knowledge_subdir(datastore: Path, *parts: str) -> Path:
    return knowledge_dir(datastore).joinpath(*parts)


def load_knowledge_csv(datastore: Path, *parts: str) -> list[dict[str, str]]:
    return read_csv(knowledge_subdir(datastore, *parts))


def _parse_ymd(ymd: str | None) -> date | None:
    if not ymd:
        return None
    s = ymd.replace("-", "")[:8]
    if len(s) != 8 or not s.isdigit():
        return None
    return date(int(s[0:4]), int(s[4:6]), int(s[6:8]))


def _format_ymd(d: date) -> str:
    return d.strftime("%Y%m%d")


def default_period_windows(analysis_start_ymd: str, analysis_end_ymd: str) -> PeriodWindows:
    """Compute lookback and follow-through defaults per period-scope-confirmation workflow."""
    start = _parse_ymd(analysis_start_ymd)
    end = _parse_ymd(analysis_end_ymd)
    if not start or not end:
        return PeriodWindows(
            analysis_start_ymd, analysis_end_ymd, "", "", "", ""
        )
    lookback_start = start - timedelta(days=28)
    lookback_end = start - timedelta(days=1)
    follow_start = end + timedelta(days=1)
    follow_end = end + timedelta(days=7)
    return PeriodWindows(
        analysis_period_start=_format_ymd(start),
        analysis_period_end=_format_ymd(end),
        lookback_start=_format_ymd(lookback_start),
        lookback_end=_format_ymd(lookback_end),
        follow_through_start=_format_ymd(follow_start),
        follow_through_end=_format_ymd(follow_end),
    )


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


def date_range_for_table(rows: list[dict[str, str]], table_name: str) -> tuple[str, str]:
    """Return (min, max) using contract-defined date columns for the table."""
    if not rows:
        return "", ""
    for col in CANONICAL_DATE_COLUMNS.get(table_name, []):
        if col in rows[0]:
            dates = sorted(r.get(col, "")[:10] for r in rows if r.get(col))
            if dates:
                return dates[0], dates[-1]
    return "", ""


def file_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
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
    """Skill output directory under the active agent workspace run root."""
    d = args_workspace / skill_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def input_dir(args) -> Path:
    return args.input_dir if args.input_dir else work_dir(args.workspace, "_inputs")


def position_symbol(row: dict[str, str]) -> str:
    """Resolve ticker from Symbol column or PositionRaw (E*TRADE lot-level exports)."""
    sym = (row.get("Symbol") or "").strip().upper()
    if sym:
        return sym
    raw = (row.get("PositionRaw") or "").strip()
    if not raw:
        return ""
    match = re.match(r"^([A-Z0-9._-]+)", raw)
    return match.group(1).upper() if match else ""


def symbols_from_positions(positions: list[dict[str, str]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for row in positions:
        sym = position_symbol(row)
        if not sym or sym in seen:
            continue
        if sym in ("PORTFOLIO ANALYSIS", "--"):
            continue
        seen.add(sym)
        out.append(sym)
    return sorted(out)
