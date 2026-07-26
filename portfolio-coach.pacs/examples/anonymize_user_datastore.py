#!/usr/bin/env python3
"""Build an anonymized demo userDatastore from a private PortfolioCoach tree.

Transforms raw E*TRADE exports (identity remap + money scale), writes the
standard layout under examples/demo-user-datastore/, then rebuilds canonical
tables via pc_lib so raw and canonical stay consistent.

Usage:
  python anonymize_user_datastore.py --source PATH/TO/PortfolioCoach
  python anonymize_user_datastore.py --source PATH --dest PATH/examples/demo-user-datastore
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

SCALE = 0.1

# Stable synthetic accounts (last-4 of AccountId matches MaskedAccount token).
ACCOUNT_MAP: dict[str, tuple[str, str, str]] = {
    # old_id -> (new_id, new_mask, new_label)
    "120447232": ("900001001", "x1001", "Traditional IRA - x1001"),
    "120447782": ("900001002", "x1002", "Individual Brokerage - x1002"),
    "215160142": ("900001003", "x1003", "Partnership / LLC / LLP - x1003"),
    "499153345": ("900001004", "x1004", "Individual 401(k) - x1004"),
}

LABEL_MAP = {
    "Traditional IRA - x7232": "Traditional IRA - x1001",
    "Individual Brokerage - x7782": "Individual Brokerage - x1002",
    "Partnership / LLC / LLP - x0142": "Partnership / LLC / LLP - x1003",
    "Individual 401(k) - x3345": "Individual 401(k) - x1004",
}

MASK_MAP = {
    "x7232": "x1001",
    "x7782": "x1002",
    "x0142": "x1003",
    "x3345": "x1004",
}

# Filename / title suffix tokens only (not applied to CSV cell bodies).
FILENAME_DIGIT_MAP = {
    "7232": "1001",
    "7782": "1002",
    "0142": "1003",
    "3345": "1004",
}

NAME_MAP = {
    "JEFFREY": "DEMO",
    "Jeffrey": "Demo",
    "jeffrey": "demo",
    "CHRISTINE": "DEMO",
    "Christine": "Demo",
    "christine": "demo",
    "CLARK": "USER",
    "Clark": "User",
    "clark": "user",
}

# Raw column headers whose numeric cells are money/prices (not share counts).
# "fill" cells are "qty @ price"; _scale_money_cell scales only the price part
# so FillPrice stays consistent with the scaled price inside Description.
MONEY_HEADERS = {
    "fill",
    "live account value",
    "cash avail to w/d",
    "cash bp",
    "margin bp",
    "today's trading gain",
    "ytd trading gain",
    "net calls",
    "fee",
    "comm",
    "amount",
    "market",
    "cost basis",
    "u/l price",
    "u/l change",
    "mark",
    "mark chg",
    "net cost basis",
    "today's net gain",
    "open net gain",
    "market value",
    "bid",
    "ask",
}

RAW_SUBFOLDERS = ("balances", "account_history", "orders", "portfolio_lot_level")


@dataclass(frozen=True)
class TransformStats:
    raw_files: int
    bytes_out: int


def _scale_number_string(token: str) -> str:
    """Scale a numeric token; preserve commas/sign/$ wrapper handled by callers."""
    raw = token.replace(",", "").strip()
    if not raw or raw in {"--", "-"}:
        return token
    try:
        value = float(raw)
    except ValueError:
        return token
    scaled = value * SCALE
    if abs(scaled - round(scaled)) < 1e-9:
        out = str(int(round(scaled)))
    else:
        out = f"{scaled:.10f}".rstrip("0").rstrip(".")
    if "," in token and abs(value) >= 1000:
        # Re-insert commas for readability in free text.
        parts = out.split(".")
        whole = parts[0]
        sign = ""
        if whole.startswith("-"):
            sign = "-"
            whole = whole[1:]
        grouped = ""
        while len(whole) > 3:
            grouped = "," + whole[-3:] + grouped
            whole = whole[:-3]
        whole = sign + whole + grouped
        out = whole + (("." + parts[1]) if len(parts) > 1 else "")
    return out


def _scale_money_cell(cell: str) -> str:
    s = cell.strip()
    if not s or s in {"--", "-", ""}:
        return cell
    # $1,234.56 or -$1,234.56
    m = re.fullmatch(r"(\$?)([+-]?)(\$?)([\d,]+\.?\d*)", s)
    if m and any(ch.isdigit() for ch in s):
        # Prefer leading $ form used in history Fee/Comm/Amount.
        if s.startswith("$") or s.startswith("-$") or s.startswith("+$"):
            sign = "-" if s.startswith("-") else ""
            num = s.lstrip("+-").lstrip("$")
            return f"{sign}${_scale_number_string(num)}"
        return _scale_number_string(s)
    # Fill forms: "150 @ 84.70" or "25@152.06"
    m = re.fullmatch(r"([\d,]+)\s*@\s*\$?([\d,]+\.?\d*)", s)
    if m:
        return f"{m.group(1)} @ {_scale_number_string(m.group(2))}"
    return cell


_DOLLAR_RE = re.compile(r"\$([\d,]+\.?\d*)")
_AT_PRICE_RE = re.compile(r"(@\s*)(\$?)([\d,]+\.?\d*)(\s+(?:Limit|Market|GTC|EXT|CLO)\b)", re.I)
_ORDER_NUM_RE = re.compile(r"(Order\s*#\s*)(\d+)", re.I)


def _scale_free_text(text: str) -> str:
    def dollar_sub(m: re.Match[str]) -> str:
        return "$" + _scale_number_string(m.group(1))

    text = _DOLLAR_RE.sub(dollar_sub, text)

    def at_sub(m: re.Match[str]) -> str:
        return f"{m.group(1)}{m.group(2)}{_scale_number_string(m.group(3))}{m.group(4)}"

    text = _AT_PRICE_RE.sub(at_sub, text)

    def order_sub(m: re.Match[str]) -> str:
        digest = int(hashlib.sha256(m.group(2).encode()).hexdigest()[:6], 16) % 9000 + 1000
        return f"{m.group(1)}{digest}"

    return _ORDER_NUM_RE.sub(order_sub, text)


def _remap_identity(text: str, *, filename: bool = False) -> str:
    # Longer account ids first.
    for old_id, (new_id, _mask, _label) in sorted(ACCOUNT_MAP.items(), key=lambda x: -len(x[0])):
        text = text.replace(old_id, new_id)
    for old_label, new_label in LABEL_MAP.items():
        text = text.replace(old_label, new_label)
    for old_mask, new_mask in MASK_MAP.items():
        text = text.replace(old_mask, new_mask)
    for old, new in NAME_MAP.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    text = text.replace("jc-", "demo-a-").replace("cc-", "demo-b-")
    text = text.replace("jc_", "demo_a_").replace("cc_", "demo_b_")
    if filename:
        for old_digits, new_digits in FILENAME_DIGIT_MAP.items():
            text = text.replace(old_digits, new_digits)
    return text


def _transform_csv_text(raw_text: str) -> str:
    """Identity-remap + scale money in an E*TRADE export (title + header + rows)."""
    # Remap identity on the full text first (titles, labels, account columns).
    text = _remap_identity(raw_text)
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if len(rows) < 2:
        return text

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    # Title row — also scale any leftover dollars in the title string.
    title = rows[0]
    if title:
        title = [_scale_free_text(c) for c in title]
    writer.writerow(title)

    header = rows[1]
    writer.writerow(header)
    money_idx = {
        i
        for i, h in enumerate(header)
        if (h or "").strip().lower() in MONEY_HEADERS
    }
    # Description / Position free-text columns (Fill is handled as money).
    text_idx = {
        i
        for i, h in enumerate(header)
        if (h or "").strip().lower() in {"description", "position"}
    }

    for row in rows[2:]:
        new_row: list[str] = []
        for i, cell in enumerate(row):
            if i in money_idx:
                new_row.append(_scale_money_cell(cell))
            elif i in text_idx:
                new_row.append(_scale_free_text(cell))
            else:
                new_row.append(cell)
        writer.writerow(new_row)
    return out.getvalue()


def _short_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:12]


def _rename_raw_filename(name: str, content: bytes) -> str:
    """Produce a stable anonymized filename; refresh content hash infix when present."""
    name = _remap_identity(name, filename=True)
    # Pattern: YYYYMMDD-HHMMSS-<12hex>-<rest>.csv
    m = re.match(r"^(\d{8}-\d{6})-([0-9a-f]{12})-(.+)$", name, re.I)
    if m:
        return f"{m.group(1)}-{_short_hash(content)}-{m.group(3)}"
    return name


def transform_raw_tree(source_raw: Path, dest_raw: Path) -> int:
    count = 0
    if dest_raw.exists():
        shutil.rmtree(dest_raw)
    for sub in RAW_SUBFOLDERS:
        src_dir = source_raw / sub
        if not src_dir.is_dir():
            continue
        out_dir = dest_raw / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(src_dir.glob("*.csv")):
            original = path.read_text(encoding="utf-8-sig")
            transformed = _transform_csv_text(original)
            payload = transformed.encode("utf-8")
            out_name = _rename_raw_filename(path.name, payload)
            (out_dir / out_name).write_bytes(payload)
            count += 1
    return count


def rebuild_demo_canonical(datastore: Path) -> dict:
    examples_dir = Path(__file__).resolve().parent
    pc_lib_root = examples_dir.parent / "assets" / "pc-lib"
    sys.path.insert(0, str(pc_lib_root))
    from pc_lib.canonical import resolve_layout
    from pc_lib.etrade_rebuild import rebuild_canonical

    layout = resolve_layout(datastore)
    return rebuild_canonical(datastore, layout)


def write_readme(dest: Path) -> None:
    (dest / "README.md").write_text(
        """# Demo user datastore

Anonymized sample PortfolioCoach `{userDatastore}` for local quickstart.

- **Source:** private E*TRADE exports, identity-remapped and money-scaled (×0.1)
- **Layout:** standard (`data/raw/etrade/`, `data/canonical/`)
- **Not included:** `reports/`, `inputs/`, `knowledge/`
- **Not real:** synthetic account ids/names; real tickers and dates retained for realism

Bind your agent `userDatastore` to this folder (or a copy) and start with
`datastore-inventory`, then an analytic playbook for a period covered by the
positions snapshots (see `../README.md`).

Regenerate from a private tree:

```bash
python anonymize_user_datastore.py --source /path/to/private/PortfolioCoach
```
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Private PortfolioCoach userDatastore root (legacy or standard layout)",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Output demo datastore root (default: examples/demo-user-datastore)",
    )
    parser.add_argument(
        "--skip-rebuild",
        action="store_true",
        help="Only write anonymized raw files; do not rebuild canonical",
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    dest = (args.dest or (Path(__file__).resolve().parent / "demo-user-datastore")).expanduser().resolve()

    # Locate raw tree (legacy or standard).
    if (source / "data" / "raw" / "etrade").is_dir():
        source_raw = source / "data" / "raw" / "etrade"
    elif (source / "raw" / "etrade").is_dir():
        source_raw = source / "raw" / "etrade"
    else:
        print(f"ERROR: no raw/etrade under {source}", file=sys.stderr)
        return 1

    if dest.exists():
        shutil.rmtree(dest)
    dest_raw = dest / "data" / "raw" / "etrade"
    dest_raw.parent.mkdir(parents=True, exist_ok=True)

    n = transform_raw_tree(source_raw, dest_raw)
    (dest / "reports").mkdir(parents=True, exist_ok=True)
    write_readme(dest)

    print(f"Wrote {n} anonymized raw files -> {dest_raw}")
    if args.skip_rebuild:
        return 0

    summary = rebuild_demo_canonical(dest)
    print("Rebuilt canonical:", summary)
    # Scrub any residual real names if rebuild pulled from balances (should already be Demo/User).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
