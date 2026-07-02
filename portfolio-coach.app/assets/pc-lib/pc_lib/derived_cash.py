"""Rebuild derived cash tables from merged canonical account history and cash anchors."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from pc_lib.canonical import parse_float, write_csv

INCOME_TYPES = frozenset(
    {"Dividend", "Qualified Dividend", "Interest", "Interest Income", "Margin Interest"}
)

CASH_ACTIVITY_FIELDS = [
    "Date",
    "AccountId",
    "MaskedAccount",
    "AccountLabel",
    "TradeCashFlow",
    "IncomeCashFlow",
    "ExternalTransferCashFlow",
    "InternalTransferCashFlow",
    "SweepCashFlow",
    "OtherCashFlow",
    "NetCashActivityExcludingSweep",
    "NetCashActivityIncludingSweep",
    "BoughtAmount",
    "SoldAmount",
    "DividendAmount",
    "InterestAmount",
    "MarginInterestAmount",
    "Fees",
    "Commissions",
    "ActivityRowCount",
    "SourceHistoryRows",
]

INCOME_EVENT_FIELDS = [
    "ActivityDate",
    "ActivityDateTime",
    "AccountId",
    "MaskedAccount",
    "AccountLabel",
    "IncomeType",
    "Description",
    "Symbol",
    "Amount",
    "SourceHash",
    "RawStoredPath",
]

CASH_BALANCE_ESTIMATED_FIELDS = [
    "Date",
    "AccountId",
    "MaskedAccount",
    "AccountLabel",
    "CashConcept",
    "EstimatedAmount",
    "IsObservedAnchor",
    "AnchorAsOfLocal",
    "AnchorAmount",
    "PriorAnchorAsOfLocal",
    "NextAnchorAsOfLocal",
    "CumulativeNetCashActivityFromAnchor",
    "ReconciliationDelta",
    "ReconciliationStatus",
    "DerivationMethod",
    "Confidence",
    "Limitations",
]


def _fmt_amount(val: float) -> str:
    return f"{val:.2f}"


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _date_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _empty_daily_bucket() -> dict[str, float | int]:
    return {
        "TradeCashFlow": 0.0,
        "IncomeCashFlow": 0.0,
        "ExternalTransferCashFlow": 0.0,
        "InternalTransferCashFlow": 0.0,
        "SweepCashFlow": 0.0,
        "OtherCashFlow": 0.0,
        "BoughtAmount": 0.0,
        "SoldAmount": 0.0,
        "DividendAmount": 0.0,
        "InterestAmount": 0.0,
        "MarginInterestAmount": 0.0,
        "Fees": 0.0,
        "Commissions": 0.0,
        "ActivityRowCount": 0,
        "SourceHistoryRows": 0,
    }


def _classify_history_row(row: dict[str, str]) -> str:
    activity_type = row.get("ActivityType", "")
    if activity_type in ("Bought", "Sold"):
        return "trade"
    if activity_type in ("Dividend", "Qualified Dividend"):
        return "dividend"
    if activity_type in ("Interest", "Interest Income"):
        return "interest"
    if activity_type == "Margin Interest":
        return "margin_interest"
    if activity_type == "Online Transfer":
        return "external"
    if activity_type == "Transfer":
        return "internal"
    if activity_type == "Sweep":
        return "sweep"
    return "other"


def build_income_events(history: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in history:
        activity_type = row.get("ActivityType", "")
        if activity_type not in INCOME_TYPES:
            continue
        out.append(
            {
                "ActivityDate": row.get("ActivityDate", ""),
                "ActivityDateTime": row.get("ActivityDateTime", ""),
                "AccountId": row.get("AccountId", ""),
                "MaskedAccount": row.get("MaskedAccount", ""),
                "AccountLabel": row.get("AccountLabel", ""),
                "IncomeType": activity_type,
                "Description": row.get("Description", ""),
                "Symbol": row.get("Symbol", ""),
                "Amount": row.get("Amount", ""),
                "SourceHash": row.get("SourceHash", ""),
                "RawStoredPath": row.get("RawStoredPath", ""),
            }
        )
    out.sort(key=lambda r: (r.get("ActivityDate", ""), r.get("AccountId", ""), r.get("Description", "")))
    return out


def build_cash_activity_daily(history: list[dict[str, str]]) -> list[dict[str, str]]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    labels: dict[tuple[str, str], dict[str, str]] = {}

    for row in history:
        activity_date = row.get("ActivityDate", "")[:10]
        account_id = row.get("AccountId", "")
        if not activity_date or not account_id:
            continue
        key = (account_id, activity_date)
        bucket = buckets.setdefault(key, _empty_daily_bucket())
        labels[key] = {
            "MaskedAccount": row.get("MaskedAccount", ""),
            "AccountLabel": row.get("AccountLabel", ""),
        }
        amount = parse_float(row.get("Amount"))
        fee = parse_float(row.get("Fee"))
        commission = parse_float(row.get("Commission"))
        bucket["Fees"] = float(bucket["Fees"]) + fee
        bucket["Commissions"] = float(bucket["Commissions"]) + commission
        bucket["ActivityRowCount"] = int(bucket["ActivityRowCount"]) + 1
        bucket["SourceHistoryRows"] = int(bucket["SourceHistoryRows"]) + 1

        kind = _classify_history_row(row)
        if kind == "trade":
            bucket["TradeCashFlow"] = float(bucket["TradeCashFlow"]) + amount
            if row.get("ActivityType") == "Bought":
                bucket["BoughtAmount"] = float(bucket["BoughtAmount"]) + abs(amount)
            else:
                bucket["SoldAmount"] = float(bucket["SoldAmount"]) + abs(amount)
        elif kind == "dividend":
            bucket["IncomeCashFlow"] = float(bucket["IncomeCashFlow"]) + amount
            bucket["DividendAmount"] = float(bucket["DividendAmount"]) + amount
        elif kind == "interest":
            bucket["IncomeCashFlow"] = float(bucket["IncomeCashFlow"]) + amount
            bucket["InterestAmount"] = float(bucket["InterestAmount"]) + amount
        elif kind == "margin_interest":
            bucket["IncomeCashFlow"] = float(bucket["IncomeCashFlow"]) + amount
            bucket["MarginInterestAmount"] = float(bucket["MarginInterestAmount"]) + amount
        elif kind == "external":
            bucket["ExternalTransferCashFlow"] = float(bucket["ExternalTransferCashFlow"]) + amount
        elif kind == "internal":
            bucket["InternalTransferCashFlow"] = float(bucket["InternalTransferCashFlow"]) + amount
        elif kind == "sweep":
            bucket["SweepCashFlow"] = float(bucket["SweepCashFlow"]) + amount
        else:
            bucket["OtherCashFlow"] = float(bucket["OtherCashFlow"]) + amount

    out: list[dict[str, str]] = []
    for (account_id, activity_date), bucket in sorted(buckets.items()):
        net_ex = (
            float(bucket["TradeCashFlow"])
            + float(bucket["IncomeCashFlow"])
            + float(bucket["ExternalTransferCashFlow"])
            + float(bucket["InternalTransferCashFlow"])
            + float(bucket["OtherCashFlow"])
        )
        net_in = net_ex + float(bucket["SweepCashFlow"])
        meta = labels[(account_id, activity_date)]
        out.append(
            {
                "Date": activity_date,
                "AccountId": account_id,
                "MaskedAccount": meta["MaskedAccount"],
                "AccountLabel": meta["AccountLabel"],
                "TradeCashFlow": _fmt_amount(float(bucket["TradeCashFlow"])),
                "IncomeCashFlow": _fmt_amount(float(bucket["IncomeCashFlow"])),
                "ExternalTransferCashFlow": _fmt_amount(float(bucket["ExternalTransferCashFlow"])),
                "InternalTransferCashFlow": _fmt_amount(float(bucket["InternalTransferCashFlow"])),
                "SweepCashFlow": _fmt_amount(float(bucket["SweepCashFlow"])),
                "OtherCashFlow": _fmt_amount(float(bucket["OtherCashFlow"])),
                "NetCashActivityExcludingSweep": _fmt_amount(net_ex),
                "NetCashActivityIncludingSweep": _fmt_amount(net_in),
                "BoughtAmount": _fmt_amount(float(bucket["BoughtAmount"])),
                "SoldAmount": _fmt_amount(float(bucket["SoldAmount"])),
                "DividendAmount": _fmt_amount(float(bucket["DividendAmount"])),
                "InterestAmount": _fmt_amount(float(bucket["InterestAmount"])),
                "MarginInterestAmount": _fmt_amount(float(bucket["MarginInterestAmount"])),
                "Fees": _fmt_amount(float(bucket["Fees"])),
                "Commissions": _fmt_amount(float(bucket["Commissions"])),
                "ActivityRowCount": str(int(bucket["ActivityRowCount"])),
                "SourceHistoryRows": str(int(bucket["SourceHistoryRows"])),
            }
        )
    return out


def _anchors_from_cash(cash_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in cash_rows:
        if row.get("CashConcept") != "CashAvailToWithdraw":
            continue
        account_id = row.get("AccountId", "")
        as_of = row.get("AsOfLocal", "")
        if not account_id or not as_of:
            continue
        by_account[account_id].append(row)
    for account_id in by_account:
        by_account[account_id].sort(key=lambda r: r.get("AsOfLocal", ""))
    return by_account


def build_cash_balance_estimated(
    cash_activity_daily: list[dict[str, str]],
    cash_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    daily_by_account: dict[str, list[tuple[date, float]]] = defaultdict(list)
    account_meta: dict[str, dict[str, str]] = {}
    for row in cash_activity_daily:
        account_id = row.get("AccountId", "")
        d = _parse_date(row.get("Date", ""))
        if not account_id or not d:
            continue
        account_meta[account_id] = {
            "MaskedAccount": row.get("MaskedAccount", ""),
            "AccountLabel": row.get("AccountLabel", ""),
        }
        daily_by_account[account_id].append((d, parse_float(row.get("NetCashActivityExcludingSweep"))))

    anchors_by_account = _anchors_from_cash(cash_rows)
    out: list[dict[str, str]] = []

    for account_id, daily_points in daily_by_account.items():
        if not daily_points:
            continue
        daily_points.sort(key=lambda item: item[0])
        meta = account_meta.get(account_id, {"MaskedAccount": "", "AccountLabel": ""})
        anchors = anchors_by_account.get(account_id, [])
        if not anchors:
            continue

        anchor_entries = [
            {
                "as_of_local": row.get("AsOfLocal", ""),
                "as_of_date": _parse_date(row.get("AsOfLocal", "")),
                "amount": parse_float(row.get("Amount")),
            }
            for row in anchors
            if _parse_date(row.get("AsOfLocal", "")) is not None
        ]
        if not anchor_entries:
            continue

        first_date = daily_points[0][0]
        last_anchor_date = anchor_entries[-1]["as_of_date"]
        assert last_anchor_date is not None
        last_date = max(daily_points[-1][0], last_anchor_date)
        net_by_date = {d: net for d, net in daily_points}
        observed_dates = {entry["as_of_date"] for entry in anchor_entries}

        running = 0.0
        cumsum_by_date: dict[date, float] = {}
        cursor = first_date
        while cursor <= last_date:
            running += net_by_date.get(cursor, 0.0)
            cumsum_by_date[cursor] = running
            cursor += timedelta(days=1)

        cursor = first_date
        while cursor <= last_date:
            if cursor >= last_anchor_date:
                primary_anchor = anchor_entries[-1]
            elif len(anchor_entries) >= 2:
                primary_anchor = anchor_entries[-2]
            else:
                primary_anchor = anchor_entries[-1]

            anchor_date = primary_anchor["as_of_date"]
            assert anchor_date is not None
            anchor_cumsum = cumsum_by_date.get(anchor_date, 0.0)
            prior_anchor = next(
                (entry for entry in reversed(anchor_entries) if entry["as_of_date"] < anchor_date),
                None,
            )
            next_anchor = next(
                (entry for entry in anchor_entries if entry["as_of_date"] > anchor_date),
                None,
            )

            cumulative = cumsum_by_date.get(cursor, 0.0)
            estimated = primary_anchor["amount"] + cumulative - anchor_cumsum
            is_observed = cursor in observed_dates
            if is_observed:
                for entry in anchor_entries:
                    if entry["as_of_date"] == cursor:
                        estimated = entry["amount"]
                        break

            prior_local = prior_anchor["as_of_local"] if prior_anchor else ""
            next_local = next_anchor["as_of_local"] if next_anchor else ""
            if len(anchor_entries) == 1:
                status = "single_anchor"
                confidence = "medium"
            else:
                status = "reconciled"
                confidence = "high"

            reconciliation_delta = ""
            if is_observed and prior_anchor and cursor == anchor_date:
                estimated_before = primary_anchor["amount"] + cumulative - anchor_cumsum
                reconciliation_delta = _fmt_amount(primary_anchor["amount"] - estimated_before)
                if abs(parse_float(reconciliation_delta)) > 1.0:
                    status = "material_delta"

            out.append(
                {
                    "Date": _date_str(cursor),
                    "AccountId": account_id,
                    "MaskedAccount": meta["MaskedAccount"],
                    "AccountLabel": meta["AccountLabel"],
                    "CashConcept": "CashAvailToWithdrawEstimated",
                    "EstimatedAmount": _fmt_amount(estimated),
                    "IsObservedAnchor": "true" if is_observed else "false",
                    "AnchorAsOfLocal": primary_anchor["as_of_local"],
                    "AnchorAmount": _fmt_amount(primary_anchor["amount"]),
                    "PriorAnchorAsOfLocal": prior_local,
                    "NextAnchorAsOfLocal": next_local,
                    "CumulativeNetCashActivityFromAnchor": _fmt_amount(cumulative),
                    "ReconciliationDelta": reconciliation_delta,
                    "ReconciliationStatus": status,
                    "DerivationMethod": (
                        "Backward/forward reconstruction from observed CashAvailToWithdraw "
                        "anchor(s) using account_history NetCashActivityExcludingSweep"
                    ),
                    "Confidence": confidence,
                    "Limitations": (
                        "Estimate excludes sweep mechanics and depends on account-history export coverage"
                    ),
                }
            )
            cursor += timedelta(days=1)

    out.sort(key=lambda r: (r.get("AccountId", ""), r.get("Date", "")))
    return out


def rebuild_derived_cash_tables(
    canon,
    history: list[dict[str, str]],
    cash_rows: list[dict[str, str]],
) -> dict[str, int]:
    income_events = build_income_events(history)
    cash_activity_daily = build_cash_activity_daily(history)
    cash_balance_estimated = build_cash_balance_estimated(cash_activity_daily, cash_rows)

    write_csv(canon / "income_events.csv", INCOME_EVENT_FIELDS, income_events)
    write_csv(canon / "cash_activity_daily.csv", CASH_ACTIVITY_FIELDS, cash_activity_daily)
    write_csv(canon / "cash_balance_estimated.csv", CASH_BALANCE_ESTIMATED_FIELDS, cash_balance_estimated)

    return {
        "incomeEventRows": len(income_events),
        "cashActivityDailyRows": len(cash_activity_daily),
        "cashBalanceEstimatedRows": len(cash_balance_estimated),
    }
