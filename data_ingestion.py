from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

SUMMARY_PATH = REPORTS_DIR / "day1_data_quality_summary.md"


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def find_column(columns: Iterable[str], keywords: Iterable[str]) -> str | None:
    normalized = {column.lower().strip(): column for column in columns}
    for keyword in keywords:
        for normalized_name, original_name in normalized.items():
            if keyword in normalized_name:
                return original_name
    return None


def describe_anomalies(df: pd.DataFrame) -> list[str]:
    anomalies: list[str] = []

    if df.empty:
        anomalies.append("dataset is empty")

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows:
        anomalies.append(f"{duplicate_rows} duplicate rows")

    missing_values = df.isna().sum()
    columns_with_missing = missing_values[missing_values > 0]
    if not columns_with_missing.empty:
        top_missing = columns_with_missing.sort_values(ascending=False).head(5)
        formatted = ", ".join(f"{col}: {count}" for col, count in top_missing.items())
        anomalies.append(f"missing values in {len(columns_with_missing)} columns ({formatted})")

    unnamed_columns = [column for column in df.columns if str(column).lower().startswith("unnamed")]
    if unnamed_columns:
        anomalies.append(f"unnamed columns: {', '.join(map(str, unnamed_columns))}")

    all_null_columns = [column for column in df.columns if df[column].isna().all()]
    if all_null_columns:
        anomalies.append(f"all-null columns: {', '.join(map(str, all_null_columns))}")

    return anomalies or ["no immediate anomalies detected"]


def print_dataset_profile(path: Path, df: pd.DataFrame, anomalies: list[str]) -> None:
    print(f"\n{'=' * 80}")
    print(f"Dataset: {path.name}")
    print(f"Shape: {df.shape}")
    print("\nDtypes:")
    print(df.dtypes)
    print("\nHead:")
    print(df.head())
    print("\nAnomalies:")
    for anomaly in anomalies:
        print(f"- {anomaly}")


def discover_key_file(csv_paths: list[Path], keywords: Iterable[str]) -> Path | None:
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for path in csv_paths:
        stem = path.stem.lower()
        if all(keyword in stem for keyword in lowered_keywords):
            return path
    return None


def explore_fund_master(df: pd.DataFrame) -> list[str]:
    notes: list[str] = []
    column_map = {
        "fund houses": find_column(df.columns, ["fund house", "amc", "mutual fund"]),
        "categories": find_column(df.columns, ["category"]),
        "sub-categories": find_column(df.columns, ["sub category", "subcategory", "sub-category"]),
        "risk grades": find_column(df.columns, ["risk grade", "riskometer", "risk"]),
        "scheme codes": find_column(df.columns, ["scheme code", "amfi code", "code"]),
    }

    print(f"\n{'=' * 80}")
    print("Fund master exploration")
    for label, column in column_map.items():
        if not column:
            message = f"{label}: matching column not found"
            print(message)
            notes.append(message)
            continue

        unique_values = df[column].dropna().astype(str).str.strip().sort_values().unique()
        print(f"\nUnique {label} ({column}) [{len(unique_values)}]:")
        print(unique_values[:100])
        if len(unique_values) > 100:
            print(f"... {len(unique_values) - 100} more")

    code_column = column_map["scheme codes"]
    if code_column:
        numeric_ratio = pd.to_numeric(df[code_column], errors="coerce").notna().mean()
        note = (
            f"AMFI scheme code structure: column '{code_column}' is "
            f"{numeric_ratio:.1%} numeric-convertible; codes are treated as stable scheme identifiers."
        )
        print(f"\n{note}")
        notes.append(note)

    return notes


def validate_amfi_codes(fund_master: pd.DataFrame, nav_history: pd.DataFrame) -> list[str]:
    fund_code_column = find_column(fund_master.columns, ["scheme code", "amfi code", "code"])
    nav_code_column = find_column(nav_history.columns, ["scheme code", "amfi code", "code"])

    if not fund_code_column or not nav_code_column:
        return [
            "AMFI validation skipped: could not identify scheme code columns in "
            "fund_master and nav_history."
        ]

    fund_codes = set(fund_master[fund_code_column].dropna().astype(str).str.strip())
    nav_codes = set(nav_history[nav_code_column].dropna().astype(str).str.strip())
    missing_codes = sorted(fund_codes - nav_codes)

    if missing_codes:
        preview = ", ".join(missing_codes[:25])
        suffix = f" ... and {len(missing_codes) - 25} more" if len(missing_codes) > 25 else ""
        return [
            f"AMFI validation failed: {len(missing_codes)} fund_master codes are absent from nav_history.",
            f"Missing code preview: {preview}{suffix}",
        ]

    return [
        f"AMFI validation passed: all {len(fund_codes)} fund_master scheme codes exist in nav_history."
    ]


def write_summary(
    profiles: dict[str, list[str]],
    fund_master_notes: list[str],
    validation_notes: list[str],
) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Day 1 Data Quality Summary",
        "",
        "## Dataset Anomalies",
        "",
    ]

    for dataset_name, anomalies in profiles.items():
        lines.append(f"### {dataset_name}")
        lines.extend(f"- {anomaly}" for anomaly in anomalies)
        lines.append("")

    lines.append("## Fund Master Exploration")
    lines.extend(f"- {note}" for note in (fund_master_notes or ["fund_master.csv not available"]))
    lines.append("")
    lines.append("## AMFI Code Validation")
    lines.extend(f"- {note}" for note in (validation_notes or ["validation not run"]))
    lines.append("")

    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote data quality summary: {SUMMARY_PATH}")


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    csv_paths = sorted(path for path in RAW_DIR.glob("*.csv") if path.is_file())
    if not csv_paths:
        print(f"No CSV files found in {RAW_DIR}. Add the 10 provided datasets and rerun.")
        write_summary({}, [], ["validation not run because no raw CSV files were found"])
        return

    if len(csv_paths) != 10:
        print(f"Expected 10 provided CSV datasets; found {len(csv_paths)}.")

    dataframes: dict[str, pd.DataFrame] = {}
    profiles: dict[str, list[str]] = {}

    for path in csv_paths:
        df = load_csv(path)
        dataframes[path.name] = df
        anomalies = describe_anomalies(df)
        profiles[path.name] = anomalies
        print_dataset_profile(path, df, anomalies)

    fund_master_path = discover_key_file(csv_paths, ["fund", "master"])
    nav_history_path = discover_key_file(csv_paths, ["nav", "history"])

    fund_master_notes: list[str] = []
    validation_notes: list[str] = []

    if fund_master_path:
        fund_master_notes = explore_fund_master(dataframes[fund_master_path.name])
    else:
        fund_master_notes = ["fund_master dataset not found by filename."]

    if fund_master_path and nav_history_path:
        validation_notes = validate_amfi_codes(
            dataframes[fund_master_path.name],
            dataframes[nav_history_path.name],
        )
        print(f"\n{'=' * 80}")
        print("AMFI code validation")
        for note in validation_notes:
            print(f"- {note}")
    else:
        validation_notes = ["AMFI validation skipped: fund_master or nav_history dataset not found."]

    write_summary(profiles, fund_master_notes, validation_notes)


if __name__ == "__main__":
    main()
