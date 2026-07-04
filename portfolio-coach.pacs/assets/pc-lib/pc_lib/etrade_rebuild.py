"""Rebuild canonical CSV tables from E*TRADE raw exports."""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pc_lib.canonical import (
    ResolvedLayout,
    is_lot_detail_position_raw,
    is_position_summary_row,
    read_csv,
    write_csv,
)
from pc_lib.derived_cash import rebuild_derived_cash_tables
from pc_lib.etrade_ingest import RAW_SUBFOLDERS, full_file_sha256, masked_account_from_label, parse_export_title


def _read_raw_rows(path: Path) -> tuple[str, list[list[str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        lines = list(csv.reader(f))
    if not lines:
        return "", []
    return lines[0][0] if lines[0] else "", lines[1:]


def _account_id_from_portfolio_title(title_line: str) -> str:
    """Extract account id from single-account exports: 'Account 499153345 Positions, ...'."""
    m = re.search(r"Account\s+(\d+)\s+Positions", title_line, re.I)
    return m.group(1) if m else ""


def _parse_order_description(desc: str) -> dict[str, str]:
    side = ""
    position_effect = ""
    quantity = ""
    order_type = ""
    order_price = ""
    m = re.match(
        r"(Buy|Sell)\s+([\d,]+)\s+Shares?\s+@\s+(.+?)\s+(Market|Limit)(?:\s+GTC)?\s+to\s+(Open|Close)",
        desc,
        re.I,
    )
    if m:
        side = m.group(1).title()
        quantity = m.group(2).replace(",", "")
        order_price = m.group(3).strip()
        order_type = m.group(4).title()
        position_effect = m.group(5).title()
    fill_qty = ""
    fill_price = ""
    fm = re.search(r"([\d,]+)\s+@\s+([\d.]+)", desc)
    if fm and "Shares" not in desc.split("@")[-1]:
        pass
    return {
        "Side": side,
        "PositionEffect": position_effect,
        "Quantity": quantity,
        "OrderType": order_type,
        "OrderPrice": order_price,
        "FillQuantity": fill_qty,
        "FillPrice": fill_price,
    }


def _parse_fill(fill: str, desc: str) -> tuple[str, str, str]:
    if fill and fill != "--":
        m = re.match(r"([\d,]+)\s+@\s+([\d.]+)", fill)
        if m:
            return fill, m.group(1).replace(",", ""), m.group(2)
    m = re.search(r"([\d,]+)\s+@\s+([\d.]+)", desc)
    if m:
        return f"{m.group(1)} @ {m.group(2)}", m.group(1).replace(",", ""), m.group(2)
    return fill or "--", "", ""


def _parse_orders_file(path: Path, source_hash: str, stored_path: str) -> list[dict[str, str]]:
    title, rows = _read_raw_rows(path)
    if len(rows) < 2:
        return []
    exported_at, tz = parse_export_title(title)
    header = rows[0]
    idx = {name.strip('"'): i for i, name in enumerate(header)}
    out: list[dict[str, str]] = []
    for row in rows[1:]:
        if not row or not any(cell.strip() for cell in row):
            continue
        symbol = row[idx.get("Symbol", 0)].strip()
        if not symbol:
            continue
        account_id = row[idx.get("Account", 6 if len(row) > 6 else -1)].strip()
        desc = row[idx.get("Description", 3)].strip()
        status = row[idx.get("Status", 1)].strip()
        fill_raw = row[idx.get("Fill", 2)].strip()
        market = row[idx.get("Market", 4)].strip()
        time_raw = row[idx.get("Time", 5)].strip()
        parsed = _parse_order_description(desc)
        fill, fill_qty, fill_price = _parse_fill(fill_raw, desc)
        date_part = ""
        if time_raw:
            try:
                dt = datetime.strptime(time_raw.strip(), "%m/%d/%Y, %I:%M:%S %p")
                date_part = dt.strftime("%Y-%m-%d")
                time_norm = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                time_norm = time_raw
        else:
            time_norm = ""
        out.append(
            {
                "SourceHash": source_hash,
                "RawStoredPath": stored_path,
                "ExportedAtLocal": exported_at,
                "ExportedAtTimeZone": tz,
                "AccountId": account_id,
                "MaskedAccount": "",
                "AccountLabel": "",
                "Symbol": symbol,
                "Status": status,
                "Side": parsed["Side"],
                "PositionEffect": parsed["PositionEffect"],
                "Quantity": parsed["Quantity"],
                "OrderType": parsed["OrderType"],
                "OrderPrice": parsed["OrderPrice"],
                "Fill": fill,
                "FillQuantity": fill_qty,
                "FillPrice": fill_price,
                "Market": market,
                "Time": time_norm,
                "Date": date_part,
                "Description": desc,
            }
        )
    return out


def _merge_orders(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    keyed: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = (
            row.get("Symbol", ""),
            row.get("Status", ""),
            row.get("Fill", ""),
            row.get("Description", ""),
            row.get("Market", ""),
            row.get("Time", ""),
            row.get("AccountId", ""),
        )
        existing = keyed.get(key)
        if not existing or row.get("ExportedAtLocal", "") >= existing.get("ExportedAtLocal", ""):
            keyed[key] = row
    return list(keyed.values())


def _parse_balances_file(path: Path, source_hash: str, stored_path: str) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    title, rows = _read_raw_rows(path)
    if len(rows) < 2:
        return [], [], []
    exported_at, tz = parse_export_title(title)
    header = rows[0]
    idx = {name: i for i, name in enumerate(header)}
    accounts: list[dict[str, str]] = []
    balances: list[dict[str, str]] = []
    cash: list[dict[str, str]] = []

    def _g(row: list[str], col: str) -> str:
        i = idx.get(col)
        return row[i].strip() if i is not None and i < len(row) else ""

    for row in rows[1:]:
        if not row or not any(cell.strip() for cell in row):
            continue
        account_label = _g(row, "Account")
        if not account_label or account_label.startswith("All Accounts"):
            bal = {
                "AsOfLocal": exported_at,
                "AsOfTimeZone": tz,
                "AccountId": "",
                "MaskedAccount": "",
                "AccountLabel": account_label,
                "AccountType": _g(row, "Account Type") or "--",
                "LiveAccountValue": _g(row, "Live Account Value"),
                "CashAvailToWithdraw": _g(row, "Cash Avail to W/D"),
                "CashBuyingPower": _g(row, "Cash BP"),
                "MarginBuyingPower": _g(row, "Margin BP"),
                "TodaysTradingGain": _g(row, "Today's Trading Gain"),
                "YtdTradingGain": _g(row, "YTD Trading Gain"),
                "NetCalls": _g(row, "Net Calls"),
                "SourceHash": source_hash,
                "RawStoredPath": stored_path,
            }
            balances.append(bal)
            for concept, col in (
                ("CashAvailToWithdraw", "Cash Avail to W/D"),
                ("CashBuyingPower", "Cash BP"),
                ("MarginBuyingPower", "Margin BP"),
            ):
                val = _g(row, col)
                if val and val != "--":
                    cash.append(
                        {
                            "AsOfLocal": exported_at,
                            "AsOfTimeZone": tz,
                            "AccountId": "",
                            "MaskedAccount": "",
                            "AccountLabel": account_label,
                            "CashConcept": concept,
                            "Amount": val,
                            "SourceExportType": "balances",
                            "SourceHash": source_hash,
                            "RawStoredPath": stored_path,
                        }
                    )
            continue

        account_id = ""
        masked = masked_account_from_label(account_label)
        accounts.append(
            {
                "AccountId": account_id,
                "MaskedAccount": masked,
                "AccountLabel": account_label,
                "AccountType": _g(row, "Account Type"),
                "FirstName": _g(row, "First Name"),
                "LastName": _g(row, "Last Name"),
                "SourceExportType": "balances",
                "SourceHash": source_hash,
                "AsOfLocal": exported_at,
                "AsOfTimeZone": tz,
            }
        )
        balances.append(
            {
                "AsOfLocal": exported_at,
                "AsOfTimeZone": tz,
                "AccountId": account_id,
                "MaskedAccount": masked,
                "AccountLabel": account_label,
                "AccountType": _g(row, "Account Type"),
                "LiveAccountValue": _g(row, "Live Account Value"),
                "CashAvailToWithdraw": _g(row, "Cash Avail to W/D"),
                "CashBuyingPower": _g(row, "Cash BP"),
                "MarginBuyingPower": _g(row, "Margin BP"),
                "TodaysTradingGain": _g(row, "Today's Trading Gain"),
                "YtdTradingGain": _g(row, "YTD Trading Gain"),
                "NetCalls": _g(row, "Net Calls"),
                "SourceHash": source_hash,
                "RawStoredPath": stored_path,
            }
        )
        for concept, col in (
            ("CashAvailToWithdraw", "Cash Avail to W/D"),
            ("CashBuyingPower", "Cash BP"),
            ("MarginBuyingPower", "Margin BP"),
        ):
            val = _g(row, col)
            if val and val != "--":
                cash.append(
                    {
                        "AsOfLocal": exported_at,
                        "AsOfTimeZone": tz,
                        "AccountId": account_id,
                        "MaskedAccount": masked,
                        "AccountLabel": account_label,
                        "CashConcept": concept,
                        "Amount": val,
                        "SourceExportType": "balances",
                        "SourceHash": source_hash,
                        "RawStoredPath": stored_path,
                    }
                )
    return accounts, balances, cash


def _parse_account_history_file(path: Path, source_hash: str, stored_path: str) -> list[dict[str, str]]:
    title, rows = _read_raw_rows(path)
    if len(rows) < 2:
        return []
    exported_at, tz = parse_export_title(title)
    account_id = ""
    m = re.match(r"^(\d+)", title.strip())
    if m:
        account_id = m.group(1)
    header = rows[0]
    idx = {name.strip(): i for i, name in enumerate(header)}
    out: list[dict[str, str]] = []
    for row in rows[1:]:
        if not row or not any(cell.strip() for cell in row):
            continue
        dt_raw = row[idx.get("Date / Time", 0)].strip()
        activity_type = row[idx.get("Type", 1)].strip()
        acct = row[idx.get("Account #", 2)].strip() or account_id
        acct_label = row[idx.get("Account Name", 3)].strip()
        desc = row[idx.get("Description", 4)].strip()
        fee = row[idx.get("Fee", 5)].strip().replace("$", "")
        comm = row[idx.get("Comm", 6)].strip().replace("$", "")
        amount = row[idx.get("Amount", 7)].strip().replace("$", "").replace(",", "")
        try:
            dt = datetime.strptime(dt_raw.strip(), "%m/%d/%Y %I:%M:%S %p")
            activity_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
            activity_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            activity_dt = dt_raw.strip()
            activity_date = dt_raw.strip()[:10]
        sym = ""
        sm = re.search(r"of\s+([A-Z0-9.]+)\s+@", desc)
        if sm:
            sym = sm.group(1)
        qty = ""
        qm = re.search(r"(\d+)\s+of\s+", desc)
        if qm:
            qty = qm.group(1)
        price = ""
        pm = re.search(r"@\s*\$?([\d.]+)", desc)
        if pm:
            price = pm.group(1)
        order_num = ""
        om = re.search(r"Order #\s*(\d+)", desc)
        if om:
            order_num = om.group(1)
        out.append(
            {
                "SourceHash": source_hash,
                "RawStoredPath": stored_path,
                "ExportedAtLocal": exported_at,
                "ExportedAtTimeZone": tz,
                "ActivityDateTime": activity_dt,
                "ActivityDate": activity_date,
                "ActivityType": activity_type,
                "AccountId": acct,
                "MaskedAccount": masked_account_from_label(acct_label),
                "AccountLabel": acct_label,
                "Description": desc,
                "Symbol": sym,
                "Quantity": qty,
                "Price": price,
                "OrderNumber": order_num,
                "Fee": fee if fee != "--" else "0.00",
                "Commission": comm if comm != "--" else "0.00",
                "Amount": amount,
                "CashActivityClass": "Trade" if activity_type in ("Bought", "Sold") else "Other",
                "IsTradeCashEffect": "true" if activity_type in ("Bought", "Sold") else "false",
                "IsEconomicCashFlow": "true",
                "IsSweep": "false",
                "IsTransfer": "false",
                "IsDividendOrInterest": "true" if activity_type in ("Dividend", "Interest") else "false",
            }
        )
    return out


def _merge_history(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    keyed: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = (
            row.get("AccountId", ""),
            row.get("ActivityDateTime", ""),
            row.get("ActivityType", ""),
            row.get("Description", ""),
            row.get("Amount", ""),
            row.get("Fee", ""),
            row.get("Commission", ""),
        )
        existing = keyed.get(key)
        if not existing or row.get("ExportedAtLocal", "") >= existing.get("ExportedAtLocal", ""):
            keyed[key] = row
    return list(keyed.values())


def _parse_portfolio_file(path: Path, source_hash: str, stored_path: str) -> list[dict[str, str]]:
    title, rows = _read_raw_rows(path)
    if len(rows) < 2:
        return []
    exported_at, tz = parse_export_title(title)
    out: list[dict[str, str]] = []
    current_account_id = _account_id_from_portfolio_title(title)
    current_masked = ""
    current_label = ""
    for row in rows[1:]:
        if not row:
            continue
        raw_position = row[0] if row else ""
        position_raw = raw_position.strip()
        if not position_raw:
            continue
        if raw_position.startswith("    ") or raw_position.startswith("\t"):
            stripped = position_raw.strip()
            if is_lot_detail_position_raw(stripped):
                continue
            if not is_position_summary_row({"PositionRaw": stripped}):
                continue
            sym = ""
            sm = re.match(r"^([A-Z0-9._-]+)\s+\+", stripped)
            if sm:
                sym = sm.group(1).upper()
            qty = row[1].strip() if len(row) > 1 else ""
            out.append(
                {
                    "SourceHash": source_hash,
                    "RawStoredPath": stored_path,
                    "AsOfLocal": exported_at,
                    "AsOfTimeZone": tz,
                    "AccountId": current_account_id,
                    "MaskedAccount": current_masked,
                    "AccountLabel": current_label,
                    "PositionRaw": position_raw.strip(),
                    "Symbol": sym,
                    "Quantity": qty,
                    "LotCount": re.search(r"\((\d+) lot", position_raw).group(1) if re.search(r"\((\d+) lot", position_raw) else "",
                    "DateAcquired": row[2].strip() if len(row) > 2 else "",
                    "Term": row[3].strip() if len(row) > 3 else "",
                    "CostBasis": row[4].strip() if len(row) > 4 else "",
                    "ULPrice": row[5].strip() if len(row) > 5 else "",
                    "ULChange": row[6].strip() if len(row) > 6 else "",
                    "Mark": row[7].strip() if len(row) > 7 else "",
                    "MarkChange": row[8].strip() if len(row) > 8 else "",
                    "NetCostBasis": row[9].strip() if len(row) > 9 else "",
                    "TodaysNetGain": row[10].strip() if len(row) > 10 else "",
                    "OpenNetGain": row[11].strip() if len(row) > 11 else "",
                    "MarketValue": row[12].strip() if len(row) > 12 else "",
                    "Bid": row[13].strip() if len(row) > 13 else "",
                    "Ask": row[14].strip() if len(row) > 14 else "",
                    "EarningsDate": row[15].strip() if len(row) > 15 else "",
                }
            )
            continue
        if "Shares" not in position_raw and "Share" not in position_raw:
            current_label = position_raw
            current_masked = masked_account_from_label(position_raw)
            current_account_id = ""
    return out


def _stored_path_for_file(layout: ResolvedLayout, subfolder: str, filename: str) -> str:
    if layout.name == "standard":
        return f"data/raw/etrade/{subfolder}/{filename}".replace("\\", "/")
    return f"raw/etrade/{subfolder}/{filename}".replace("\\", "/")


def _date_range(rows: list[dict[str, str]], col: str) -> tuple[str, str]:
    vals = sorted(r.get(col, "")[:10] for r in rows if r.get(col))
    return (vals[0], vals[-1]) if vals else ("", "")


def rebuild_canonical(datastore: Path, layout: ResolvedLayout) -> dict[str, Any]:
    """Rebuild canonical tables from all raw E*TRADE exports."""
    rebuilt_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    canon = layout.canonical
    canon.mkdir(parents=True, exist_ok=True)

    all_orders: list[dict[str, str]] = []
    all_history: list[dict[str, str]] = []
    all_accounts: dict[str, dict[str, str]] = {}
    all_balances: list[dict[str, str]] = []
    all_cash: list[dict[str, str]] = []
    all_positions: list[dict[str, str]] = []
    manifest_rows: list[dict[str, str]] = []

    for sub in RAW_SUBFOLDERS:
        folder = layout.raw_etrade / sub
        if not folder.is_dir():
            continue
        export_type = sub if sub != "portfolio_lot_level" else "portfolio_lot_level"
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            source_hash = full_file_sha256(path)
            stored = _stored_path_for_file(layout, sub, path.name)
            title, _ = _read_raw_rows(path)
            exported_at, tz = parse_export_title(title)
            row_count = ""
            min_date = ""
            max_date = ""

            if sub == "orders":
                parsed = _parse_orders_file(path, source_hash, stored)
                all_orders.extend(parsed)
                row_count = str(len(parsed))
                min_date, max_date = _date_range(parsed, "Date")
            elif sub == "account_history":
                parsed = _parse_account_history_file(path, source_hash, stored)
                all_history.extend(parsed)
                row_count = str(len(parsed))
                min_date, max_date = _date_range(parsed, "ActivityDate")
            elif sub == "balances":
                accounts, balances, cash = _parse_balances_file(path, source_hash, stored)
                for acct in accounts:
                    key = acct.get("AccountId") or acct.get("AccountLabel", path.name)
                    all_accounts[key] = acct
                all_balances.extend(balances)
                all_cash.extend(cash)
                row_count = str(len(balances))
            elif sub == "portfolio_lot_level":
                parsed = _parse_portfolio_file(path, source_hash, stored)
                all_positions.extend(parsed)
                row_count = str(len(parsed))
                min_date, max_date = _date_range(parsed, "AsOfLocal")

            manifest_rows.append(
                {
                    "ExportType": export_type.replace("portfolio_lot_level", "portfolio_lot_level"),
                    "SourceHash": source_hash,
                    "RawStoredPath": stored,
                    "OriginalFileName": path.name,
                    "ExportTitle": title,
                    "ExportedAtLocal": exported_at,
                    "ExportedAtTimeZone": tz,
                    "RowCount": row_count,
                    "MinDate": min_date,
                    "MaxDate": max_date,
                    "RebuiltAtLocal": rebuilt_at,
                }
            )

    merged_orders = _merge_orders(all_orders)
    merged_history = _merge_history(all_history)

    label_to_account: dict[str, str] = {}
    id_to_label: dict[str, dict[str, str]] = {}
    for row in merged_history:
        aid = row.get("AccountId", "")
        label = row.get("AccountLabel", "")
        if aid and label:
            label_to_account[label] = aid
            id_to_label[aid] = {
                "MaskedAccount": row.get("MaskedAccount", ""),
                "AccountLabel": label,
            }
    for row in merged_orders:
        aid = row.get("AccountId", "")
        if aid and aid not in id_to_label:
            id_to_label[aid] = {"MaskedAccount": "", "AccountLabel": ""}

    for row in merged_orders:
        meta = id_to_label.get(row.get("AccountId", ""), {})
        row["MaskedAccount"] = meta.get("MaskedAccount", row.get("MaskedAccount", ""))
        row["AccountLabel"] = meta.get("AccountLabel", row.get("AccountLabel", ""))

    for acct_id, acct in list(all_accounts.items()):
        if not acct_id and acct.get("AccountLabel") in label_to_account:
            new_id = label_to_account[acct["AccountLabel"]]
            all_accounts[new_id] = {**acct, "AccountId": new_id}
            del all_accounts[acct_id]
    for acct in all_accounts.values():
        label = acct.get("AccountLabel", "")
        if not acct.get("AccountId") and label in label_to_account:
            acct["AccountId"] = label_to_account[label]
        meta = id_to_label.get(acct.get("AccountId", ""), {})
        if meta.get("MaskedAccount"):
            acct["MaskedAccount"] = meta["MaskedAccount"]

    for row in all_balances:
        if not row.get("AccountId") and row.get("AccountLabel") in label_to_account:
            row["AccountId"] = label_to_account[row["AccountLabel"]]
            meta = id_to_label.get(row["AccountId"], {})
            row["MaskedAccount"] = meta.get("MaskedAccount", masked_account_from_label(row["AccountLabel"]))
    for row in all_cash:
        if not row.get("AccountId") and row.get("AccountLabel") in label_to_account:
            row["AccountId"] = label_to_account[row["AccountLabel"]]
            meta = id_to_label.get(row["AccountId"], {})
            row["MaskedAccount"] = meta.get("MaskedAccount", masked_account_from_label(row["AccountLabel"]))
    for acct in all_accounts.values():
        aid = acct.get("AccountId", "")
        if aid and aid not in id_to_label:
            id_to_label[aid] = {
                "MaskedAccount": acct.get("MaskedAccount", ""),
                "AccountLabel": acct.get("AccountLabel", ""),
            }

    for row in all_positions:
        if not row.get("AccountId") and row.get("AccountLabel") in label_to_account:
            row["AccountId"] = label_to_account[row["AccountLabel"]]
        aid = row.get("AccountId", "")
        if aid:
            meta = id_to_label.get(aid, {})
            if not row.get("AccountLabel"):
                row["AccountLabel"] = meta.get("AccountLabel", "")
            if not row.get("MaskedAccount"):
                row["MaskedAccount"] = meta.get("MaskedAccount", "")
            if not row.get("AccountLabel") or not row.get("MaskedAccount"):
                acct = all_accounts.get(aid) or next(
                    (a for a in all_accounts.values() if a.get("AccountId") == aid),
                    None,
                )
                if acct:
                    row["AccountLabel"] = row.get("AccountLabel") or acct.get("AccountLabel", "")
                    row["MaskedAccount"] = row.get("MaskedAccount") or acct.get("MaskedAccount", "")

    write_csv(
        canon / "orders.csv",
        list(merged_orders[0].keys()) if merged_orders else [
            "SourceHash", "RawStoredPath", "ExportedAtLocal", "ExportedAtTimeZone",
            "AccountId", "MaskedAccount", "AccountLabel", "Symbol", "Status", "Side",
            "PositionEffect", "Quantity", "OrderType", "OrderPrice", "Fill", "FillQuantity",
            "FillPrice", "Market", "Time", "Date", "Description",
        ],
        merged_orders,
    )
    write_csv(
        canon / "account_history.csv",
        list(merged_history[0].keys()) if merged_history else [],
        merged_history,
    )
    write_csv(
        canon / "accounts.csv",
        list(next(iter(all_accounts.values())).keys()) if all_accounts else [
            "AccountId", "MaskedAccount", "AccountLabel", "AccountType", "FirstName",
            "LastName", "SourceExportType", "SourceHash", "AsOfLocal", "AsOfTimeZone",
        ],
        list(all_accounts.values()),
    )
    write_csv(
        canon / "balances.csv",
        list(all_balances[0].keys()) if all_balances else [],
        all_balances,
    )
    write_csv(
        canon / "cash.csv",
        list(all_cash[0].keys()) if all_cash else [],
        all_cash,
    )
    write_csv(
        canon / "positions_lot_level.csv",
        list(all_positions[0].keys()) if all_positions else [],
        all_positions,
    )
    write_csv(
        canon / "ingestion_manifest.csv",
        [
            "ExportType", "SourceHash", "RawStoredPath", "OriginalFileName", "ExportTitle",
            "ExportedAtLocal", "ExportedAtTimeZone", "RowCount", "MinDate", "MaxDate", "RebuiltAtLocal",
        ],
        manifest_rows,
    )

    derived_stats = rebuild_derived_cash_tables(canon, merged_history, all_cash)

    return {
        "rebuiltAtLocal": rebuilt_at,
        "orderRows": len(merged_orders),
        "historyRows": len(merged_history),
        "accountRows": len(all_accounts),
        "balanceRows": len(all_balances),
        "positionRows": len(all_positions),
        "manifestRows": len(manifest_rows),
        **derived_stats,
    }
