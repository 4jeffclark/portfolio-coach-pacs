"""Datastore inventory skill."""

from __future__ import annotations

from pathlib import Path

from pc_lib.canonical import (
    canonical_dir,
    file_sha256,
    load_canonical,
    raw_dir,
    work_dir,
    write_csv,
)
from pc_lib.cli import SkillArgs, SkillResult


def _count_rows(rows: list[dict]) -> int:
    return len(rows)


def _date_range(rows: list[dict], col: str) -> tuple[str, str]:
    dates = sorted(r.get(col, "")[:10] for r in rows if r.get(col))
    if not dates:
        return "", ""
    return dates[0], dates[-1]


def run(args: SkillArgs) -> SkillResult:
    out = work_dir(args.workspace, "datastore-inventory")
    canon = canonical_dir(args.datastore)
    raw = raw_dir(args.datastore)

    inventory_rows = []
    for sub in ("account_history", "balances", "orders", "portfolio_lot_level"):
        folder = raw / sub
        if folder.is_dir():
            for f in sorted(folder.glob("*")):
                if f.is_file():
                    inventory_rows.append(
                        {
                            "ArtifactType": "raw",
                            "Name": f.name,
                            "Subfolder": sub,
                            "RowCount": "",
                            "DateMin": "",
                            "DateMax": "",
                            "Sha256Prefix": file_sha256(f),
                        }
                    )

    canonical_tables = [
        "accounts.csv",
        "account_history.csv",
        "balances.csv",
        "cash.csv",
        "orders.csv",
        "positions_lot_level.csv",
        "ingestion_manifest.csv",
    ]
    for name in canonical_tables:
        path = canon / name
        rows = load_canonical(args.datastore, name) if path.is_file() else []
        dmin, dmax = "", ""
        for col in ("ActivityDate", "AsOfLocal", "ExportedAtLocal", "TradeDate"):
            if rows and col in rows[0]:
                dmin, dmax = _date_range(rows, col)
                if dmin:
                    break
        inventory_rows.append(
            {
                "ArtifactType": "canonical",
                "Name": name,
                "Subfolder": "canonical",
                "RowCount": str(_count_rows(rows)),
                "DateMin": dmin,
                "DateMax": dmax,
                "Sha256Prefix": file_sha256(path) if path.is_file() else "",
            }
        )

    accounts = load_canonical(args.datastore, "accounts.csv")
    coverage_rows = []
    for acct in accounts:
        aid = acct.get("AccountId", "")
        orders = [r for r in load_canonical(args.datastore, "orders.csv") if r.get("AccountId") == aid]
        coverage_rows.append(
            {
                "AccountId": aid,
                "MaskedAccount": acct.get("MaskedAccount", ""),
                "AccountLabel": acct.get("AccountLabel", ""),
                "OrderRows": str(len(orders)),
                "Notes": "",
            }
        )

    metrics = {
        "canonicalTableCount": sum(1 for n in canonical_tables if (canon / n).is_file()),
        "rawFileCount": len([r for r in inventory_rows if r["ArtifactType"] == "raw"]),
    }

    inv_path = write_csv(
        out / "DataStoreInventory.csv",
        ["ArtifactType", "Name", "Subfolder", "RowCount", "DateMin", "DateMax", "Sha256Prefix"],
        inventory_rows,
    )
    cov_path = write_csv(
        out / "AccountCoverage.csv",
        ["AccountId", "MaskedAccount", "AccountLabel", "OrderRows", "Notes"],
        coverage_rows,
    )
    met_path = write_csv(
        out / "Metrics.csv",
        ["Metric", "Value"],
        [{"Metric": k, "Value": str(v)} for k, v in metrics.items()],
    )

    return SkillResult(
        skill="datastore-inventory",
        status="ok",
        artifacts=[str(inv_path), str(cov_path), str(met_path)],
        metrics=metrics,
        messages=["Wrote datastore inventory artifacts"],
    )
