"""Datastore inventory skill."""

from __future__ import annotations

import json
from pathlib import Path

from pc_lib.analytics import snapshot_dates
from pc_lib.canonical import (
    DERIVED_CANONICAL_TABLES,
    DatastoreLayoutError,
    canonical_dir,
    date_range_for_table,
    file_sha256,
    load_canonical,
    raw_dir,
    read_csv,
    resolve_layout,
    validate_layout,
    work_dir,
    write_csv,
)
from pc_lib.cli import SkillArgs, SkillResult

RAW_SUBFOLDERS = ("account_history", "balances", "orders", "portfolio_lot_level")


def _normalize_stored_path(path: str) -> str:
    return path.replace("\\", "/").strip().lstrip("./")


def _on_disk_raw_paths(datastore: Path, raw_root: Path) -> set[str]:
    root = datastore.expanduser().resolve()
    paths: set[str] = set()
    for sub in RAW_SUBFOLDERS:
        folder = raw_root / sub
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            if path.is_file():
                paths.add(path.relative_to(root).as_posix())
    return paths


def _manifest_path_aliases(stored: str) -> set[str]:
    normalized = _normalize_stored_path(stored)
    if not normalized:
        return set()
    aliases = {normalized}
    if normalized.startswith("data/raw/"):
        aliases.add(normalized[len("data/") :])
    elif normalized.startswith("raw/"):
        aliases.add(f"data/{normalized}")
    return aliases


def _detect_manifest_drift(
    datastore: Path,
    raw_root: Path,
    manifest_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[str]]:
    on_disk = _on_disk_raw_paths(datastore, raw_root)
    manifest_by_path: dict[str, dict[str, str]] = {}
    manifest_aliases: set[str] = set()
    for row in manifest_rows:
        stored = _normalize_stored_path(row.get("RawStoredPath", ""))
        if not stored:
            continue
        manifest_by_path[stored] = row
        manifest_aliases.update(_manifest_path_aliases(stored))

    drift_rows: list[dict[str, str]] = []
    for stored, row in manifest_by_path.items():
        if not _manifest_path_aliases(stored) & on_disk:
            drift_rows.append(
                {
                    "DriftType": "manifest_missing_on_disk",
                    "RawStoredPath": stored,
                    "SourceHash": row.get("SourceHash", ""),
                    "ExportType": row.get("ExportType", ""),
                    "Details": "ingestion_manifest.csv references a raw file that is absent on disk",
                }
            )

    for disk_path in sorted(on_disk):
        if disk_path not in manifest_aliases:
            drift_rows.append(
                {
                    "DriftType": "disk_not_in_manifest",
                    "RawStoredPath": disk_path,
                    "SourceHash": "",
                    "ExportType": "",
                    "Details": "raw file on disk is not listed in ingestion_manifest.csv",
                }
            )

    messages: list[str] = []
    if drift_rows:
        missing = sum(1 for row in drift_rows if row["DriftType"] == "manifest_missing_on_disk")
        extra = sum(1 for row in drift_rows if row["DriftType"] == "disk_not_in_manifest")
        messages.append(
            f"Manifest drift detected: {missing} manifest entry/entries missing on disk, "
            f"{extra} on-disk file(s) not in manifest. See RawManifestDrift.csv."
        )
    return drift_rows, messages


def _count_rows(rows: list[dict]) -> int:
    return len(rows)


def _account_activity_range(rows: list[dict], account_id: str, col: str) -> tuple[str, str]:
    subset = [r for r in rows if r.get("AccountId") == account_id and r.get(col)]
    if not subset:
        return "", ""
    dates = sorted(r.get(col, "")[:10] for r in subset)
    return dates[0], dates[-1]


def _latest_value(rows: list[dict], account_id: str, date_col: str, value_col: str) -> str:
    subset = [r for r in rows if r.get("AccountId") == account_id and r.get(date_col)]
    if not subset:
        return ""
    latest = max(subset, key=lambda r: r.get(date_col, ""))
    return latest.get(value_col, "")


def _dedup_key_violations(rows: list[dict], keys: list[str]) -> int:
    seen: set[tuple[str, ...]] = set()
    dupes = 0
    for row in rows:
        key = tuple(row.get(k, "") for k in keys)
        if key in seen:
            dupes += 1
        seen.add(key)
    return dupes


def _build_section_fragments(
    layout_name: str,
    inventory_rows: list[dict],
    coverage_rows: list[dict],
    metrics: dict[str, str],
    derived_rows: list[dict[str, str]],
) -> dict[str, str]:
    canon_count = len([r for r in inventory_rows if r.get("ArtifactType") == "canonical"])
    derived_count = len([r for r in inventory_rows if r.get("ArtifactType") == "derived"])
    raw_count = len([r for r in inventory_rows if r.get("ArtifactType") == "raw"])
    orders_row = next((r for r in inventory_rows if r.get("Name") == "orders.csv"), {})

    derived_lines = []
    for row in derived_rows:
        name = row.get("Name", "")
        rows = row.get("RowCount", "0")
        dmin = row.get("DateMin", "")
        dmax = row.get("DateMax", "")
        range_text = f"{dmin} -> {dmax}" if dmin and dmax else "n/a"
        derived_lines.append(f"- `{name}`: {rows} rows ({range_text})")

    section4 = (
        "Cash and income derived tables profiled from canonical rebuild output. "
        f"Cash table present: {metrics.get('cashTablePresent', 'false')}.\n\n"
        + ("\n".join(derived_lines) if derived_lines else "- No derived tables present on disk.")
    )

    manifest_rows = metrics.get("ingestionManifestRows", "0")
    drift_note = ""
    if metrics.get("manifestDriftDetected") == "True":
        drift_note = (
            f" **Manifest drift:** {metrics.get('manifestMissingOnDiskCount', '0')} manifest "
            f"entry/entries missing on disk; {metrics.get('diskNotInManifestCount', '0')} on-disk "
            "file(s) not in manifest. See `RawManifestDrift.csv`."
        )

    section5 = (
        f"Layout resolved: {layout_name}. "
        f"Order dedup key violations: {metrics.get('ordersDedupViolations', '0')}. "
        f"Account history dedup violations: {metrics.get('accountHistoryDedupViolations', '0')}. "
        f"Manifest rows: {manifest_rows}; on-disk raw files: {raw_count}. "
        f"Manifest drift: {'detected' if metrics.get('manifestDriftDetected') == 'True' else 'none'}. "
        "See `Metrics.csv` for summary flags."
    )

    return {
        "section1_inventory": (
            f"Datastore layout: **{layout_name}**. "
            f"Indexed {raw_count} raw file(s), {canon_count} core canonical table(s), "
            f"and {derived_count} derived table(s). "
            f"Ingestion manifest lists {manifest_rows} raw export(s).{drift_note} "
            f"See `DataStoreInventory.csv` for row counts, date ranges, and hashes."
        ),
        "section2_account_coverage": (
            f"Profiled {len(coverage_rows)} account(s). "
            "Per-account activity ranges, balances, and row counts are in `AccountCoverage.csv`."
        ),
        "section3_activity_coverage": (
            "Activity coverage derived from canonical orders and account_history tables. "
            f"Orders date range (canonical): {orders_row.get('DateMin', 'n/a')} → {orders_row.get('DateMax', 'n/a')}. "
            f"Position snapshots: {metrics.get('positionSnapshotCount', '0')} "
            f"({metrics.get('positionSnapshotDateMin', 'n/a')} → {metrics.get('positionSnapshotDateMax', 'n/a')})."
            + (
                " **Warning:** fewer than two position snapshots — period weight reconstruction may use earliest-snapshot fallback."
                if metrics.get("positionSnapshotSparseWarn") == "True"
                else ""
            )
        ),
        "section4_cash_income": section4,
        "section5_data_quality": section5,
    }


def run(args: SkillArgs) -> SkillResult:
    try:
        layout = validate_layout(args.datastore)
    except DatastoreLayoutError as exc:
        return SkillResult(skill="datastore-inventory", status="error", messages=[str(exc)])

    out = work_dir(args.workspace, "datastore-inventory")
    canon = canonical_dir(args.datastore)
    raw = raw_dir(args.datastore)
    messages = list(layout.warnings)

    inventory_rows: list[dict[str, str]] = []
    for sub in RAW_SUBFOLDERS:
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
        rows = read_csv(path) if path.is_file() else []
        dmin, dmax = date_range_for_table(rows, name)
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

    derived_inventory_rows: list[dict[str, str]] = []
    for name in DERIVED_CANONICAL_TABLES:
        path = canon / name
        rows = read_csv(path) if path.is_file() else []
        dmin, dmax = date_range_for_table(rows, name)
        derived_inventory_rows.append(
            {
                "ArtifactType": "derived",
                "Name": name,
                "Subfolder": "canonical",
                "RowCount": str(_count_rows(rows)),
                "DateMin": dmin,
                "DateMax": dmax,
                "Sha256Prefix": file_sha256(path) if path.is_file() else "",
            }
        )
        inventory_rows.append(derived_inventory_rows[-1])

    orders = load_canonical(args.datastore, "orders.csv")
    history = load_canonical(args.datastore, "account_history.csv")
    balances = load_canonical(args.datastore, "balances.csv")
    positions = load_canonical(args.datastore, "positions_lot_level.csv")
    pos_snaps = snapshot_dates(positions)
    pos_snap_count = len(pos_snaps)
    pos_snap_min = pos_snaps[0] if pos_snaps else ""
    pos_snap_max = pos_snaps[-1] if pos_snaps else ""
    pos_snap_sparse = pos_snap_count < 2

    accounts = load_canonical(args.datastore, "accounts.csv")

    coverage_rows: list[dict[str, str]] = []
    for acct in accounts:
        aid = acct.get("AccountId", "")
        acct_orders = [r for r in orders if r.get("AccountId") == aid]
        acct_history = [r for r in history if r.get("AccountId") == aid]
        order_dmin, order_dmax = _account_activity_range(acct_orders, aid, "Date")
        hist_dmin, hist_dmax = _account_activity_range(acct_history, aid, "ActivityDate")
        if not hist_dmin:
            hist_dmin, hist_dmax = _account_activity_range(acct_history, aid, "ActivityDateTime")
        latest_balance = _latest_value(balances, aid, "AsOfLocal", "LiveAccountValue")
        latest_as_of = _latest_value(balances, aid, "AsOfLocal", "AsOfLocal")
        gaps: list[str] = []
        if not acct_orders:
            gaps.append("no_orders")
        if not acct_history:
            gaps.append("no_account_history")
        if not latest_as_of:
            gaps.append("no_balance_snapshot")
        coverage_rows.append(
            {
                "AccountId": aid,
                "MaskedAccount": acct.get("MaskedAccount", ""),
                "AccountLabel": acct.get("AccountLabel", ""),
                "OrderRows": str(len(acct_orders)),
                "AccountHistoryRows": str(len(acct_history)),
                "OrderDateMin": order_dmin,
                "OrderDateMax": order_dmax,
                "ActivityDateMin": hist_dmin,
                "ActivityDateMax": hist_dmax,
                "LatestBalanceAsOf": latest_as_of,
                "LatestLiveAccountValue": latest_balance,
                "PositionRows": str(len([r for r in positions if r.get("AccountId") == aid])),
                "CoverageGaps": ";".join(gaps) if gaps else "",
                "Notes": "",
            }
        )

    orders_dedup = _dedup_key_violations(
        orders, ["Symbol", "Status", "Fill", "Description", "Market", "Time", "AccountId"]
    )
    history_dedup = _dedup_key_violations(
        history,
        ["AccountId", "ActivityDateTime", "ActivityType", "Description", "Amount", "Fee", "Commission"],
    )
    cash_path = canon / "cash.csv"
    manifest_rows = load_canonical(args.datastore, "ingestion_manifest.csv")
    drift_rows, drift_messages = _detect_manifest_drift(args.datastore, raw, manifest_rows)
    raw_file_count = len([r for r in inventory_rows if r["ArtifactType"] == "raw"])
    missing_on_disk = sum(1 for row in drift_rows if row["DriftType"] == "manifest_missing_on_disk")
    not_in_manifest = sum(1 for row in drift_rows if row["DriftType"] == "disk_not_in_manifest")

    metrics: dict[str, str] = {
        "canonicalTableCount": str(sum(1 for n in canonical_tables if (canon / n).is_file())),
        "derivedTableCount": str(sum(1 for n in DERIVED_CANONICAL_TABLES if (canon / n).is_file())),
        "rawFileCount": str(raw_file_count),
        "layoutResolved": layout.name,
        "cashTablePresent": str(cash_path.is_file()),
        "ingestionManifestRows": str(len(manifest_rows)),
        "manifestDriftDetected": str(bool(drift_rows)),
        "manifestMissingOnDiskCount": str(missing_on_disk),
        "diskNotInManifestCount": str(not_in_manifest),
        "manifestDriftPass": str(not drift_rows),
        "ordersDedupViolations": str(orders_dedup),
        "accountHistoryDedupViolations": str(history_dedup),
        "validationPass": str(orders_dedup == 0 and history_dedup == 0),
        "accountCount": str(len(accounts)),
        "positionSnapshotCount": str(pos_snap_count),
        "positionSnapshotDateMin": pos_snap_min,
        "positionSnapshotDateMax": pos_snap_max,
        "positionSnapshotSparseWarn": str(pos_snap_sparse),
    }
    for row in derived_inventory_rows:
        metric_key = row["Name"].replace(".csv", "Rows")
        metrics[metric_key] = row["RowCount"]

    inv_path = write_csv(
        out / "DataStoreInventory.csv",
        ["ArtifactType", "Name", "Subfolder", "RowCount", "DateMin", "DateMax", "Sha256Prefix"],
        inventory_rows,
    )
    cov_path = write_csv(
        out / "AccountCoverage.csv",
        [
            "AccountId",
            "MaskedAccount",
            "AccountLabel",
            "OrderRows",
            "AccountHistoryRows",
            "OrderDateMin",
            "OrderDateMax",
            "ActivityDateMin",
            "ActivityDateMax",
            "LatestBalanceAsOf",
            "LatestLiveAccountValue",
            "PositionRows",
            "CoverageGaps",
            "Notes",
        ],
        coverage_rows,
    )
    met_path = write_csv(
        out / "Metrics.csv",
        ["Metric", "Value"],
        [{"Metric": k, "Value": v} for k, v in metrics.items()],
    )
    drift_path = write_csv(
        out / "RawManifestDrift.csv",
        ["DriftType", "RawStoredPath", "SourceHash", "ExportType", "Details"],
        drift_rows,
    )

    fragments = _build_section_fragments(layout.name, inventory_rows, coverage_rows, metrics, derived_inventory_rows)
    frag_path = out / "ReportSectionFragments.json"
    frag_path.write_text(json.dumps(fragments, indent=2) + "\n", encoding="utf-8")

    return SkillResult(
        skill="datastore-inventory",
        status="ok",
        artifacts=[str(inv_path), str(cov_path), str(met_path), str(drift_path), str(frag_path)],
        metrics={k: v for k, v in metrics.items()},
        messages=messages + drift_messages + ["Wrote datastore inventory artifacts and report section fragments"],
    )
