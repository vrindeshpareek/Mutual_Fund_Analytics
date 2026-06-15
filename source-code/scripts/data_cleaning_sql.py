from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_PATH = PROJECT_ROOT / "bluestock_mf.db"
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"
QUERIES_PATH = PROJECT_ROOT / "queries.sql"
DATA_DICTIONARY_PATH = PROJECT_ROOT / "data_dictionary.md"

RAW_FILES = {
    "fund_master": "01_fund_master.csv",
    "nav_history": "02_nav_history.csv",
    "aum_by_fund_house": "03_aum_by_fund_house.csv",
    "monthly_sip_inflows": "04_monthly_sip_inflows.csv",
    "category_inflows": "05_category_inflows.csv",
    "industry_folio_count": "06_industry_folio_count.csv",
    "scheme_performance": "07_scheme_performance.csv",
    "investor_transactions": "08_investor_transactions.csv",
    "portfolio_holdings": "09_portfolio_holdings.csv",
    "benchmark_indices": "10_benchmark_indices.csv",
}

KYC_ALLOWED = {"Verified", "Pending", "Rejected", "Expired"}


def read_raw(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / RAW_FILES[name], low_memory=False)


def write_clean(name: str, df: pd.DataFrame) -> Path:
    path = PROCESSED_DIR / f"{name}_cleaned.csv"
    df.to_csv(path, index=False)
    return path


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def clean_fund_master(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    numeric_columns = [
        "amfi_code",
        "expense_ratio_pct",
        "exit_load_pct",
        "min_sip_amount",
        "min_lumpsum_amount",
    ]
    df = to_numeric(df, numeric_columns)
    df = df.dropna(subset=["amfi_code", "scheme_name"]).drop_duplicates("amfi_code")
    df["amfi_code"] = df["amfi_code"].astype("int64")
    return df.sort_values("amfi_code")


def clean_nav_history(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = to_numeric(df, ["amfi_code", "nav"])
    df = df.dropna(subset=["amfi_code", "date", "nav"])
    df = df[df["nav"] > 0]
    df["amfi_code"] = df["amfi_code"].astype("int64")
    df = df.drop_duplicates(["amfi_code", "date"], keep="last")
    df = df.sort_values(["amfi_code", "date"])

    filled_groups: list[pd.DataFrame] = []
    for amfi_code, group in df.groupby("amfi_code", sort=True):
        group = group.set_index("date").sort_index()
        full_dates = pd.date_range(group.index.min(), group.index.max(), freq="D")
        filled = group.reindex(full_dates)
        filled["amfi_code"] = amfi_code
        filled["nav"] = filled["nav"].ffill()
        filled = filled.dropna(subset=["nav"]).rename_axis("date").reset_index()
        filled_groups.append(filled[["amfi_code", "date", "nav"]])

    return pd.concat(filled_groups, ignore_index=True).sort_values(["amfi_code", "date"])


def clean_aum(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = to_numeric(df, ["aum_lakh_crore", "aum_crore", "num_schemes"])
    return df.dropna(subset=["date", "fund_house"]).drop_duplicates(["date", "fund_house"])


def clean_monthly_sip(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    numeric_columns = [
        "sip_inflow_crore",
        "active_sip_accounts_crore",
        "new_sip_accounts_lakh",
        "sip_aum_lakh_crore",
        "yoy_growth_pct",
    ]
    df = to_numeric(df, numeric_columns)
    return df.dropna(subset=["month"]).drop_duplicates("month").sort_values("month")


def clean_category_inflows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df = to_numeric(df, ["net_inflow_crore"])
    return df.dropna(subset=["month", "category"]).drop_duplicates(["month", "category"])


def clean_folio_count(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    numeric_columns = [column for column in df.columns if column.endswith("_crore")]
    df = to_numeric(df, numeric_columns)
    return df.dropna(subset=["month"]).drop_duplicates("month").sort_values("month")


def clean_scheme_performance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    return_columns = [column for column in df.columns if "return" in column or column in {"alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct"}]
    df = to_numeric(df, ["amfi_code", *return_columns])
    df["performance_anomaly_flag"] = False
    for column in return_columns:
        df["performance_anomaly_flag"] |= df[column].isna()
    df["performance_anomaly_flag"] |= ~df["expense_ratio_pct"].between(0.1, 2.5, inclusive="both")
    df = df.dropna(subset=["amfi_code", "scheme_name"]).drop_duplicates("amfi_code")
    df["amfi_code"] = df["amfi_code"].astype("int64")
    return df.sort_values("amfi_code")


def standardize_transaction_type(value: object) -> str | float:
    if pd.isna(value):
        return np.nan
    normalized = str(value).strip().lower().replace("_", " ").replace("-", " ")
    if normalized in {"sip", "systematic investment plan"}:
        return "SIP"
    if normalized in {"lumpsum", "lump sum", "purchase", "one time"}:
        return "Lumpsum"
    if normalized in {"redemption", "redeem", "sell"}:
        return "Redemption"
    return str(value).strip()


def clean_investor_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["transaction_type"] = df["transaction_type"].map(standardize_transaction_type)
    df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.title()
    df = to_numeric(df, ["amfi_code", "amount_inr", "annual_income_lakh"])
    df["transaction_quality_flag"] = ""
    df.loc[~df["transaction_type"].isin(["SIP", "Lumpsum", "Redemption"]), "transaction_quality_flag"] += "invalid_transaction_type;"
    df.loc[df["amount_inr"] <= 0, "transaction_quality_flag"] += "invalid_amount;"
    df.loc[~df["kyc_status"].isin(KYC_ALLOWED), "transaction_quality_flag"] += "invalid_kyc_status;"
    df = df.dropna(subset=["investor_id", "transaction_date", "amfi_code", "amount_inr"])
    df = df[df["amount_inr"] > 0]
    df["amfi_code"] = df["amfi_code"].astype("int64")
    return df.drop_duplicates().sort_values(["transaction_date", "investor_id"])


def clean_portfolio_holdings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["portfolio_date"] = pd.to_datetime(df["portfolio_date"], errors="coerce")
    df = to_numeric(df, ["amfi_code", "weight_pct", "market_value_cr", "current_price_inr"])
    df = df.dropna(subset=["amfi_code", "stock_symbol", "portfolio_date"])
    df["amfi_code"] = df["amfi_code"].astype("int64")
    return df.drop_duplicates(["amfi_code", "stock_symbol", "portfolio_date"])


def clean_benchmark_indices(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = to_numeric(df, ["close_value"])
    df = df.dropna(subset=["date", "index_name", "close_value"])
    return df.drop_duplicates(["date", "index_name"]).sort_values(["index_name", "date"])


def build_dim_date(*frames: pd.DataFrame) -> pd.DataFrame:
    dates: list[pd.Series] = []
    for frame in frames:
        for column in ["date", "month", "transaction_date", "portfolio_date", "launch_date"]:
            if column in frame.columns:
                dates.append(pd.to_datetime(frame[column], errors="coerce"))
    all_dates = pd.concat(dates).dropna().drop_duplicates().sort_values()
    dim = pd.DataFrame({"date": all_dates.dt.date.astype(str)})
    parsed = pd.to_datetime(dim["date"])
    dim["year"] = parsed.dt.year
    dim["quarter"] = parsed.dt.quarter
    dim["month"] = parsed.dt.month
    dim["month_name"] = parsed.dt.month_name()
    dim["day"] = parsed.dt.day
    dim["day_of_week"] = parsed.dt.day_name()
    return dim


def serialize_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in ["date", "month", "transaction_date", "portfolio_date", "launch_date", "drawdown_start", "drawdown_trough"]:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce").dt.strftime("%Y-%m-%d")
    return df


SCHEMA_SQL = """
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount REAL,
    min_lumpsum_amount REAL,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE dim_date (
    date TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day INTEGER NOT NULL,
    day_of_week TEXT NOT NULL
);

CREATE TABLE fact_nav (
    amfi_code INTEGER NOT NULL,
    date TEXT NOT NULL,
    nav REAL NOT NULL CHECK (nav > 0),
    PRIMARY KEY (amfi_code, date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr REAL NOT NULL CHECK (amount_inr > 0),
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    transaction_quality_flag TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date)
);

CREATE TABLE fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT,
    performance_anomaly_flag INTEGER,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_aum (
    date TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER,
    PRIMARY KEY (date, fund_house),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);
"""


QUERIES_SQL = """
-- 1. Top 5 funds by AUM
SELECT f.scheme_name, f.fund_house, p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT d.year, d.month, ROUND(AVG(n.nav), 2) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON d.date = n.date
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 3. SIP YoY growth
SELECT strftime('%Y-%m', month) AS month, sip_inflow_crore, yoy_growth_pct
FROM monthly_sip_inflows_cleaned
ORDER BY month;

-- 4. Transactions by state
SELECT state, COUNT(*) AS transaction_count, ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- 5. Funds with expense ratio below 1%
SELECT scheme_name, fund_house, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1
ORDER BY expense_ratio_pct, scheme_name;

-- 6. Net inflow by category
SELECT category, ROUND(SUM(net_inflow_crore), 2) AS total_net_inflow_crore
FROM category_inflows_cleaned
GROUP BY category
ORDER BY total_net_inflow_crore DESC;

-- 7. Monthly folio growth
SELECT month, total_folios_crore,
       ROUND(total_folios_crore - LAG(total_folios_crore) OVER (ORDER BY month), 2) AS mom_growth_crore
FROM industry_folio_count_cleaned
ORDER BY month;

-- 8. Direct vs regular average expense ratio
SELECT plan, ROUND(AVG(expense_ratio_pct), 2) AS avg_expense_ratio_pct
FROM dim_fund
GROUP BY plan;

-- 9. City tier SIP contribution
SELECT city_tier, ROUND(SUM(amount_inr), 2) AS sip_amount_inr
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY city_tier
ORDER BY sip_amount_inr DESC;

-- 10. Benchmark daily return volatility
WITH returns AS (
    SELECT index_name,
           date,
           close_value / LAG(close_value) OVER (PARTITION BY index_name ORDER BY date) - 1 AS daily_return
    FROM benchmark_indices_cleaned
)
SELECT index_name, ROUND(AVG(daily_return), 6) AS avg_daily_return,
       ROUND(SQRT(AVG(daily_return * daily_return) - AVG(daily_return) * AVG(daily_return)) * SQRT(252), 4) AS annualized_volatility
FROM returns
WHERE daily_return IS NOT NULL
GROUP BY index_name;
"""


def write_static_artifacts(cleaned: dict[str, pd.DataFrame]) -> None:
    SCHEMA_PATH.write_text(SCHEMA_SQL.strip() + "\n", encoding="utf-8")
    QUERIES_PATH.write_text(QUERIES_SQL.strip() + "\n", encoding="utf-8")

    lines = [
        "# Mutual Fund Analytics Data Dictionary",
        "",
        "Source files live in `data/raw/`; cleaned files live in `data/processed/`.",
        "",
    ]
    definitions = {
        "amfi_code": "AMFI scheme identifier used as the fund key.",
        "nav": "Net asset value for a scheme on a date.",
        "aum_crore": "Assets under management in INR crore.",
        "expense_ratio_pct": "Annual expense ratio percentage.",
        "transaction_type": "Standardized investor transaction category: SIP, Lumpsum, or Redemption.",
        "kyc_status": "Investor KYC status enum after cleaning.",
        "net_inflow_crore": "Net category inflow in INR crore.",
        "weight_pct": "Portfolio holding weight percentage.",
        "close_value": "Benchmark index closing level.",
    }
    for name, frame in cleaned.items():
        source = RAW_FILES.get(name, "derived")
        lines.append(f"## {name}_cleaned")
        lines.append(f"Source: `{source}`")
        lines.append("")
        lines.append("| Column | Data type | Business definition |")
        lines.append("|---|---:|---|")
        for column, dtype in frame.dtypes.items():
            definition = definitions.get(column, f"{column.replace('_', ' ').title()} from `{source}`.")
            lines.append(f"| `{column}` | `{dtype}` | {definition} |")
        lines.append("")
    DATA_DICTIONARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def load_sqlite(cleaned: dict[str, pd.DataFrame], dim_date: pd.DataFrame) -> dict[str, int]:
    if DB_PATH.exists():
        DB_PATH.unlink()
    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.begin() as conn:
        for statement in SCHEMA_SQL.split(";"):
            if statement.strip():
                conn.execute(text(statement))

    cleaned["fund_master"].pipe(serialize_dates).to_sql("dim_fund", engine, if_exists="append", index=False)
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    cleaned["nav_history"].pipe(serialize_dates).to_sql("fact_nav", engine, if_exists="append", index=False)

    tx = serialize_dates(cleaned["investor_transactions"])
    tx.to_sql("fact_transactions", engine, if_exists="append", index=False)

    performance_columns = [
        "amfi_code",
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "aum_crore",
        "expense_ratio_pct",
        "morningstar_rating",
        "risk_grade",
        "performance_anomaly_flag",
    ]
    cleaned["scheme_performance"][performance_columns].to_sql("fact_performance", engine, if_exists="append", index=False)
    cleaned["aum_by_fund_house"].pipe(serialize_dates).to_sql("fact_aum", engine, if_exists="append", index=False)

    extra_tables = [
        "monthly_sip_inflows",
        "category_inflows",
        "industry_folio_count",
        "portfolio_holdings",
        "benchmark_indices",
    ]
    for name in extra_tables:
        cleaned[name].pipe(serialize_dates).to_sql(f"{name}_cleaned", engine, if_exists="replace", index=False)

    with engine.connect() as conn:
        tables = [
            "dim_fund",
            "dim_date",
            "fact_nav",
            "fact_transactions",
            "fact_performance",
            "fact_aum",
            *[f"{name}_cleaned" for name in extra_tables],
        ]
        return {
            table: conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            for table in tables
        }


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    cleaned = {
        "fund_master": clean_fund_master(read_raw("fund_master")),
        "nav_history": clean_nav_history(read_raw("nav_history")),
        "aum_by_fund_house": clean_aum(read_raw("aum_by_fund_house")),
        "monthly_sip_inflows": clean_monthly_sip(read_raw("monthly_sip_inflows")),
        "category_inflows": clean_category_inflows(read_raw("category_inflows")),
        "industry_folio_count": clean_folio_count(read_raw("industry_folio_count")),
        "scheme_performance": clean_scheme_performance(read_raw("scheme_performance")),
        "investor_transactions": clean_investor_transactions(read_raw("investor_transactions")),
        "portfolio_holdings": clean_portfolio_holdings(read_raw("portfolio_holdings")),
        "benchmark_indices": clean_benchmark_indices(read_raw("benchmark_indices")),
    }

    for name, frame in cleaned.items():
        path = write_clean(name, frame)
        print(f"Wrote {path} ({len(frame):,} rows)")

    dim_date = build_dim_date(*cleaned.values())
    write_static_artifacts(cleaned)
    row_counts = load_sqlite(cleaned, dim_date)

    print(f"\nCreated SQLite database: {DB_PATH}")
    print("Database row counts:")
    for table, count in row_counts.items():
        print(f"- {table}: {count:,}")

    print("\nCleaned row count verification:")
    for name, frame in cleaned.items():
        db_table = {
            "fund_master": "dim_fund",
            "nav_history": "fact_nav",
            "investor_transactions": "fact_transactions",
            "scheme_performance": "fact_performance",
            "aum_by_fund_house": "fact_aum",
        }.get(name, f"{name}_cleaned")
        print(f"- {name}: cleaned={len(frame):,}, sqlite={row_counts[db_table]:,}")


if __name__ == "__main__":
    main()
