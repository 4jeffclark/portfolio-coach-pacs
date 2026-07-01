"""E*TRADE raw file staging and classification for datastore ingest."""

from __future__ import annotations

import hashlib
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from pc_lib.canonical import ResolvedLayout, file_sha256

RAW_SUBFOLDERS = ("account_history", "balances", "orders", "portfolio_lot_level")


def full_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_raw_subfolder(path: Path) -> str | None:
    name = path.name.lower()
    if "order" in name:
        return "orders"
    if "history" in name:
        return "account_history"
    if "balance" in name or "summary" in name:
        return "balances"
    if "portfolio" in name or "position" in name or "lot" in name:
        return "portfolio_lot_level"
    try:
        first = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()[0].lower()
    except OSError:
        return None
    if "order" in first:
        return "orders"
    if "history" in first or "date / time" in path.read_text(encoding="utf-8-sig", errors="replace")[:500].lower():
        return "account_history"
    if "all accounts" in first and "account\"" in path.read_text(encoding="utf-8-sig", errors="replace")[:800].lower():
        return "balances"
    if "position" in first:
        return "portfolio_lot_level"
    return None


def _existing_raw_hashes(raw_root: Path) -> set[str]:
    hashes: set[str] = set()
    for sub in RAW_SUBFOLDERS:
        folder = raw_root / sub
        if not folder.is_dir():
            continue
        for f in folder.iterdir():
            if f.is_file():
                hashes.add(full_file_sha256(f))
    return hashes


def _stored_path(layout: ResolvedLayout, subfolder: str, filename: str) -> str:
    if layout.name == "standard":
        return f"data/raw/etrade/{subfolder}/{filename}"
    return f"raw/etrade/{subfolder}/{filename}"


def stage_inputs(datastore: Path, layout: ResolvedLayout) -> tuple[list[dict[str, str]], list[str]]:
    """Copy new files from inputs/ into raw subfolders. Returns staged rows and messages."""
    inputs_dir = datastore / "inputs"
    messages: list[str] = []
    staged: list[dict[str, str]] = []
    if not inputs_dir.is_dir() or not any(inputs_dir.iterdir()):
        messages.append("No session attachments in inputs/; staging skipped.")
        return staged, messages

    existing = _existing_raw_hashes(layout.raw_etrade)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    for src in sorted(inputs_dir.rglob("*")):
        if not src.is_file():
            continue
        subfolder = classify_raw_subfolder(src)
        if not subfolder:
            messages.append(f"Skipped unclassified attachment: {src.name}")
            continue
        digest = full_file_sha256(src)
        if digest in existing:
            messages.append(f"Duplicate skipped (hash match): {src.name}")
            staged.append(
                {
                    "OriginalFileName": src.name,
                    "Action": "skipped_duplicate",
                    "Subfolder": subfolder,
                    "SourceHash": digest,
                    "StoredFileName": "",
                }
            )
            continue
        dest_name = f"{ts}-{digest[:12]}-{src.name}"
        dest_dir = layout.raw_etrade / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / dest_name
        shutil.copy2(src, dest)
        existing.add(digest)
        messages.append(f"Staged {src.name} -> {subfolder}/{dest_name}")
        staged.append(
            {
                "OriginalFileName": src.name,
                "Action": "staged",
                "Subfolder": subfolder,
                "SourceHash": digest,
                "StoredFileName": dest_name,
                "RawStoredPath": _stored_path(layout, subfolder, dest_name),
            }
        )
    return staged, messages


def masked_account_from_label(label: str) -> str:
    m = re.search(r"x\d{4}", label)
    return m.group(0) if m else ""


def parse_export_title(title_line: str) -> tuple[str, str]:
    """Return (ExportedAtLocal, ExportedAtTimeZone) from E*TRADE title row."""
    tz = "EST"
    if " EST" in title_line:
        tz = "EST"
    m = re.search(r"as of (\d{2}/\d{2}/\d{2}) at (\d{2}:\d{2} [AP]M)", title_line, re.I)
    if not m:
        return "", tz
    date_part, time_part = m.group(1), m.group(2)
    try:
        dt = datetime.strptime(f"{date_part} {time_part}", "%m/%d/%y %I:%M %p")
        return dt.strftime("%Y-%m-%d %H:%M:%S"), tz
    except ValueError:
        return "", tz
