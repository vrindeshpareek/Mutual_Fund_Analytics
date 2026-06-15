from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import nbformat as nbf
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import linregress


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "Performance_Analytics.ipynb"
CHART_DIR = PROJECT_ROOT / "reports" / "charts" / "performance"
SCORECARD_PATH = PROJECT_ROOT / "data" / "processed" / "fund_scorecard.csv"
ALPHA_BETA_PATH = PROJECT_ROOT / "data" / "processed" / "alpha_beta.csv"
DAILY_RETURNS_PATH = PROJECT_ROOT / "data" / "processed" / "daily_returns.csv"

RISK_FREE_RATE = 0.065

sns.set_theme(style="whitegrid")


def read_clean(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / f"{name}_cleaned.csv", parse_dates=parse_dates)


def calculate_daily_returns(nav: pd.DataFrame) -> pd.DataFrame:
    nav = nav.sort_values(["amfi_code", "date"]).copy()
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
    return nav.dropna(subset=["daily_return"])


def calculate_cagr(nav: pd.DataFrame, years: int) -> pd.Series:
    max_date = nav["date"].max()
    start_cutoff = max_date - pd.DateOffset(years=years)
    rows = []
    for amfi_code, group in nav.groupby("amfi_code"):
        group = group.sort_values("date")
        start_group = group[group["date"] >= start_cutoff]
        if start_group.empty:
            rows.append((amfi_code, np.nan))
            continue
        start_nav = start_group.iloc[0]["nav"]
        end_nav = group.iloc[-1]["nav"]
        rows.append((amfi_code, (end_nav / start_nav) ** (1 / years) - 1))
    return pd.Series(dict(rows), name=f"cagr_{years}yr")


def calculate_risk_metrics(returns: pd.DataFrame) -> pd.DataFrame:
    rows = []
    daily_rf = RISK_FREE_RATE / 252
    for amfi_code, group in returns.groupby("amfi_code"):
        r = group["daily_return"].dropna()
        annual_return = r.mean() * 252
        annual_vol = r.std(ddof=1) * np.sqrt(252)
        downside = r[r < 0].std(ddof=1) * np.sqrt(252)
        sharpe = (annual_return - RISK_FREE_RATE) / annual_vol if annual_vol and annual_vol > 0 else np.nan
        sortino = ((r - daily_rf).mean() * 252) / downside if downside and downside > 0 else np.nan
        rows.append(
            {
                "amfi_code": amfi_code,
                "annualized_return": annual_return,
                "annualized_volatility": annual_vol,
                "sharpe_ratio_calc": sharpe,
                "sortino_ratio_calc": sortino,
            }
        )
    return pd.DataFrame(rows)


def calculate_drawdowns(nav: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for amfi_code, group in nav.groupby("amfi_code"):
        group = group.sort_values("date").copy()
        group["running_max"] = group["nav"].cummax()
        group["drawdown"] = group["nav"] / group["running_max"] - 1
        trough_idx = group["drawdown"].idxmin()
        trough = group.loc[trough_idx]
        peak_window = group[group["date"] <= trough["date"]]
        peak = peak_window.loc[peak_window["nav"].idxmax()]
        rows.append(
            {
                "amfi_code": amfi_code,
                "max_drawdown": trough["drawdown"],
                "drawdown_start": peak["date"],
                "drawdown_trough": trough["date"],
            }
        )
    return pd.DataFrame(rows)


def benchmark_returns(benchmark: pd.DataFrame) -> pd.DataFrame:
    benchmark = benchmark.sort_values(["index_name", "date"]).copy()
    benchmark["benchmark_return"] = benchmark.groupby("index_name")["close_value"].pct_change()
    return benchmark.dropna(subset=["benchmark_return"])


def calculate_alpha_beta(returns: pd.DataFrame, benchmark: pd.DataFrame) -> pd.DataFrame:
    bench_returns = benchmark_returns(benchmark)
    nifty100_name = next((name for name in bench_returns["index_name"].unique() if "100" in name), bench_returns["index_name"].iloc[0])
    nifty100 = bench_returns[bench_returns["index_name"] == nifty100_name][["date", "benchmark_return"]]

    rows = []
    for amfi_code, group in returns.groupby("amfi_code"):
        merged = group[["date", "daily_return"]].merge(nifty100, on="date", how="inner").dropna()
        if len(merged) < 30:
            rows.append({"amfi_code": amfi_code, "benchmark": nifty100_name, "alpha": np.nan, "beta": np.nan, "r_value": np.nan, "p_value": np.nan})
            continue
        regression = linregress(merged["benchmark_return"], merged["daily_return"])
        rows.append(
            {
                "amfi_code": amfi_code,
                "benchmark": nifty100_name,
                "alpha": regression.intercept * 252,
                "beta": regression.slope,
                "r_value": regression.rvalue,
                "p_value": regression.pvalue,
            }
        )
    return pd.DataFrame(rows)


def build_scorecard(fund: pd.DataFrame, performance: pd.DataFrame, nav: pd.DataFrame, benchmark: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    returns = calculate_daily_returns(nav)
    daily_returns_out = returns.merge(fund[["amfi_code", "scheme_name", "fund_house", "plan"]], on="amfi_code", how="left")
    daily_returns_out.to_csv(DAILY_RETURNS_PATH, index=False)

    risk = calculate_risk_metrics(returns)
    drawdowns = calculate_drawdowns(nav)
    alpha_beta = calculate_alpha_beta(returns, benchmark)

    cagr_table = pd.DataFrame({"amfi_code": sorted(nav["amfi_code"].unique())})
    for years in [1, 3, 5]:
        cagr_table = cagr_table.merge(calculate_cagr(nav, years).reset_index().rename(columns={"index": "amfi_code"}), on="amfi_code", how="left")

    scorecard = (
        fund[["amfi_code", "fund_house", "scheme_name", "category", "sub_category", "plan", "expense_ratio_pct"]]
        .merge(cagr_table, on="amfi_code", how="left")
        .merge(risk, on="amfi_code", how="left")
        .merge(alpha_beta[["amfi_code", "alpha", "beta"]], on="amfi_code", how="left")
        .merge(drawdowns, on="amfi_code", how="left")
        .merge(performance[["amfi_code", "aum_crore"]], on="amfi_code", how="left")
    )

    scorecard["return_rank"] = scorecard["cagr_3yr"].rank(pct=True)
    scorecard["sharpe_rank"] = scorecard["sharpe_ratio_calc"].rank(pct=True)
    scorecard["alpha_rank"] = scorecard["alpha"].rank(pct=True)
    scorecard["expense_rank_inverse"] = (-scorecard["expense_ratio_pct"]).rank(pct=True)
    scorecard["max_dd_rank_inverse"] = scorecard["max_drawdown"].rank(pct=True)
    scorecard["fund_score"] = 100 * (
        0.30 * scorecard["return_rank"]
        + 0.25 * scorecard["sharpe_rank"]
        + 0.20 * scorecard["alpha_rank"]
        + 0.15 * scorecard["expense_rank_inverse"]
        + 0.10 * scorecard["max_dd_rank_inverse"]
    )

    tracking_errors = calculate_tracking_error(returns, benchmark, scorecard.nlargest(5, "fund_score")["amfi_code"].tolist())
    scorecard = scorecard.merge(tracking_errors, on="amfi_code", how="left")
    scorecard = scorecard.sort_values("fund_score", ascending=False)
    alpha_beta = alpha_beta.merge(fund[["amfi_code", "scheme_name", "fund_house", "plan"]], on="amfi_code", how="left")

    scorecard.to_csv(SCORECARD_PATH, index=False)
    alpha_beta.to_csv(ALPHA_BETA_PATH, index=False)
    return scorecard, alpha_beta, daily_returns_out


def calculate_tracking_error(returns: pd.DataFrame, benchmark: pd.DataFrame, amfi_codes: list[int]) -> pd.DataFrame:
    bench_returns = benchmark_returns(benchmark)
    nifty100_name = next((name for name in bench_returns["index_name"].unique() if "100" in name), bench_returns["index_name"].iloc[0])
    nifty100 = bench_returns[bench_returns["index_name"] == nifty100_name][["date", "benchmark_return"]]
    rows = []
    for amfi_code in amfi_codes:
        merged = returns[returns["amfi_code"] == amfi_code][["date", "daily_return"]].merge(nifty100, on="date", how="inner").dropna()
        tracking_error = (merged["daily_return"] - merged["benchmark_return"]).std(ddof=1) * np.sqrt(252)
        rows.append({"amfi_code": amfi_code, "tracking_error": tracking_error})
    return pd.DataFrame(rows)


def make_benchmark_chart(scorecard: pd.DataFrame, nav: pd.DataFrame, benchmark: pd.DataFrame) -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    top_codes = scorecard.nlargest(5, "fund_score")["amfi_code"].tolist()
    max_date = nav["date"].max()
    start_date = max_date - pd.DateOffset(years=3)
    top_nav = nav[nav["amfi_code"].isin(top_codes) & (nav["date"] >= start_date)].merge(
        scorecard[["amfi_code", "scheme_name"]], on="amfi_code", how="left"
    )
    fund_norm = top_nav.sort_values(["amfi_code", "date"]).copy()
    fund_norm["normalized"] = fund_norm.groupby("amfi_code")["nav"].transform(lambda s: s / s.iloc[0] * 100)

    bench_subset = benchmark[(benchmark["date"] >= start_date) & (benchmark["index_name"].str.contains("NIFTY50|NIFTY100|NIFTY 50|NIFTY 100", regex=True, case=False, na=False))].copy()
    if bench_subset.empty:
        bench_subset = benchmark[benchmark["date"] >= start_date].copy()
    bench_subset = bench_subset.sort_values(["index_name", "date"])
    bench_subset["normalized"] = bench_subset.groupby("index_name")["close_value"].transform(lambda s: s / s.iloc[0] * 100)

    plt.figure(figsize=(13, 7))
    sns.lineplot(data=fund_norm, x="date", y="normalized", hue="scheme_name", linewidth=1.7)
    sns.lineplot(data=bench_subset, x="date", y="normalized", hue="index_name", linestyle="--", linewidth=1.4, palette="dark")
    plt.title("Top 5 Funds vs Benchmarks, Last 3 Years")
    plt.ylabel("Growth of 100")
    plt.xlabel("Date")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    path = CHART_DIR / "benchmark_comparison_top5.png"
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Wrote {path}")


def make_notebook() -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell("# Performance Analytics\n\nComputes daily returns, CAGR, Sharpe, Sortino, alpha, beta, maximum drawdown, composite fund score, and benchmark comparison."),
        nbf.v4.new_code_cell("from pathlib import Path\nimport numpy as np\nimport pandas as pd\nimport seaborn as sns\nimport matplotlib.pyplot as plt\nfrom scipy.stats import linregress\n\nPROJECT_ROOT = Path('..').resolve()\nPROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'\nnav = pd.read_csv(PROCESSED_DIR / 'nav_history_cleaned.csv', parse_dates=['date'])\nfund = pd.read_csv(PROCESSED_DIR / 'fund_master_cleaned.csv')\nbenchmark = pd.read_csv(PROCESSED_DIR / 'benchmark_indices_cleaned.csv', parse_dates=['date'])\nscorecard = pd.read_csv(PROCESSED_DIR / 'fund_scorecard.csv')\nalpha_beta = pd.read_csv(PROCESSED_DIR / 'alpha_beta.csv')"),
        nbf.v4.new_markdown_cell("Daily returns are computed as `nav_t / nav_t-1 - 1` for each AMFI scheme and stored in `daily_returns.csv`."),
        nbf.v4.new_code_cell("daily_returns = pd.read_csv(PROCESSED_DIR / 'daily_returns.csv', parse_dates=['date'])\ndaily_returns['daily_return'].describe()"),
        nbf.v4.new_markdown_cell("CAGR is calculated over 1-year, 3-year, and 5-year windows using the latest NAV date as the endpoint."),
        nbf.v4.new_code_cell("scorecard[['scheme_name', 'cagr_1yr', 'cagr_3yr', 'cagr_5yr']].head(10)"),
        nbf.v4.new_markdown_cell("Sharpe and Sortino use a 6.5% annual risk-free rate proxy."),
        nbf.v4.new_code_cell("scorecard[['scheme_name', 'sharpe_ratio_calc', 'sortino_ratio_calc']].head(10)"),
        nbf.v4.new_markdown_cell("Alpha and beta are estimated by OLS regression of fund daily returns against Nifty 100 returns."),
        nbf.v4.new_code_cell("alpha_beta.sort_values('alpha', ascending=False).head(10)"),
        nbf.v4.new_markdown_cell("Maximum drawdown records the worst peak-to-trough decline and the corresponding start/trough dates."),
        nbf.v4.new_code_cell("scorecard[['scheme_name', 'max_drawdown', 'drawdown_start', 'drawdown_trough']].sort_values('max_drawdown').head(10)"),
        nbf.v4.new_markdown_cell("The 0-100 fund score combines 3-year CAGR, Sharpe, alpha, inverse expense ratio, and inverse drawdown rank."),
        nbf.v4.new_code_cell("scorecard[['scheme_name', 'fund_score', 'cagr_3yr', 'sharpe_ratio_calc', 'alpha', 'expense_ratio_pct', 'max_drawdown']].head(10)"),
        nbf.v4.new_markdown_cell("## Benchmark Comparison\n\n![Top 5 funds vs benchmarks](../reports/charts/performance/benchmark_comparison_top5.png)"),
    ]
    nbf.write(nb, NOTEBOOK_PATH)
    print(f"Wrote {NOTEBOOK_PATH}")


def main() -> None:
    fund = read_clean("fund_master", ["launch_date"])
    nav = read_clean("nav_history", ["date"])
    performance = read_clean("scheme_performance")
    benchmark = read_clean("benchmark_indices", ["date"])

    scorecard, alpha_beta, daily_returns = build_scorecard(fund, performance, nav, benchmark)
    make_benchmark_chart(scorecard, nav, benchmark)
    make_notebook()

    print(f"Wrote {SCORECARD_PATH} ({len(scorecard):,} rows)")
    print(f"Wrote {ALPHA_BETA_PATH} ({len(alpha_beta):,} rows)")
    print(f"Wrote {DAILY_RETURNS_PATH} ({len(daily_returns):,} rows)")


if __name__ == "__main__":
    main()
