from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib"))

import matplotlib.pyplot as plt
import nbformat as nbf
import pandas as pd
import seaborn as sns


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "EDA_Analysis.ipynb"
CHART_DIR = PROJECT_ROOT / "reports" / "charts" / "eda"

sns.set_theme(style="whitegrid")


def read_clean(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / f"{name}_cleaned.csv", parse_dates=parse_dates)


def savefig(name: str) -> None:
    path = CHART_DIR / f"{name}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"Wrote {path}")


def make_charts() -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    fund = read_clean("fund_master", ["launch_date"])
    nav = read_clean("nav_history", ["date"])
    aum = read_clean("aum_by_fund_house", ["date"])
    sip = read_clean("monthly_sip_inflows", ["month"])
    category = read_clean("category_inflows", ["month"])
    folios = read_clean("industry_folio_count", ["month"])
    performance = read_clean("scheme_performance")
    tx = read_clean("investor_transactions", ["transaction_date"])
    holdings = read_clean("portfolio_holdings", ["portfolio_date"])

    nav = nav.merge(fund[["amfi_code", "scheme_name", "fund_house"]], on="amfi_code", how="left")
    nav_2022_2026 = nav[(nav["date"] >= "2022-01-01") & (nav["date"] <= "2026-12-31")]

    plt.figure(figsize=(14, 7))
    sns.lineplot(data=nav_2022_2026, x="date", y="nav", hue="scheme_name", legend=False, linewidth=0.9)
    plt.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"), color="#2ca02c", alpha=0.12, label="2023 bull run")
    plt.axvspan(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-31"), color="#d62728", alpha=0.10, label="2024 corrections")
    plt.title("Daily NAV Trend for All Schemes, 2022-2026")
    plt.ylabel("NAV")
    plt.legend()
    savefig("01_nav_trend_all_schemes")

    aum["year"] = aum["date"].dt.year
    plt.figure(figsize=(13, 7))
    sns.barplot(data=aum[aum["year"].between(2022, 2025)], x="year", y="aum_lakh_crore", hue="fund_house")
    plt.axhline(12.5, color="#1f77b4", linestyle="--", linewidth=1.5, label="SBI 12.5 lakh crore marker")
    plt.title("AUM Growth by Fund House")
    plt.ylabel("AUM, lakh crore")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    savefig("02_aum_growth_by_fund_house")

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=sip, x="month", y="sip_inflow_crore", marker="o")
    high = sip.loc[sip["sip_inflow_crore"].idxmax()]
    plt.annotate(
        f"All-time high: {high['sip_inflow_crore']:,.0f} Cr",
        xy=(high["month"], high["sip_inflow_crore"]),
        xytext=(high["month"], high["sip_inflow_crore"] * 0.9),
        arrowprops={"arrowstyle": "->"},
    )
    plt.title("Monthly SIP Inflow Trend")
    plt.ylabel("SIP inflow, crore")
    savefig("03_sip_inflow_time_series")

    category["month_label"] = category["month"].dt.strftime("%Y-%m")
    heatmap_data = category.pivot_table(index="category", columns="month_label", values="net_inflow_crore", aggfunc="sum")
    plt.figure(figsize=(14, 5))
    sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=0.2)
    plt.title("Category Net Inflow Heatmap")
    plt.xlabel("Month")
    plt.ylabel("Category")
    savefig("04_category_inflow_heatmap")

    age_counts = tx["age_group"].value_counts().sort_index()
    plt.figure(figsize=(7, 7))
    plt.pie(age_counts, labels=age_counts.index, autopct="%1.1f%%", startangle=90)
    plt.title("Investor Age Group Distribution")
    savefig("05_age_group_distribution")

    plt.figure(figsize=(9, 6))
    sns.boxplot(data=tx[tx["transaction_type"] == "SIP"], x="age_group", y="amount_inr", order=sorted(tx["age_group"].dropna().unique()))
    plt.title("SIP Amount by Age Group")
    plt.ylabel("Amount, INR")
    savefig("06_sip_amount_by_age_group")

    plt.figure(figsize=(7, 5))
    sns.countplot(data=tx, x="gender", order=tx["gender"].value_counts().index)
    plt.title("Investor Gender Split")
    plt.ylabel("Transactions")
    savefig("07_gender_split")

    state_sip = tx[tx["transaction_type"] == "SIP"].groupby("state", as_index=False)["amount_inr"].sum().sort_values("amount_inr", ascending=False).head(15)
    plt.figure(figsize=(10, 7))
    sns.barplot(data=state_sip, y="state", x="amount_inr", color="#4c78a8")
    plt.title("SIP Amount by State")
    plt.xlabel("SIP amount, INR")
    savefig("08_sip_amount_by_state")

    tier_counts = tx.groupby("city_tier")["amount_inr"].sum()
    plt.figure(figsize=(7, 7))
    plt.pie(tier_counts, labels=tier_counts.index, autopct="%1.1f%%", startangle=90)
    plt.title("T30 vs B30 Amount Split")
    savefig("09_city_tier_split")

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=folios, x="month", y="total_folios_crore", marker="o")
    for _, row in folios.iloc[[0, -1]].iterrows():
        plt.annotate(f"{row['total_folios_crore']:.2f} Cr", xy=(row["month"], row["total_folios_crore"]), xytext=(row["month"], row["total_folios_crore"] + 0.5))
    plt.title("Folio Count Growth")
    plt.ylabel("Total folios, crore")
    savefig("10_folio_count_growth")

    selected_codes = performance.nlargest(10, "aum_crore")["amfi_code"].tolist()
    returns = (
        nav[nav["amfi_code"].isin(selected_codes)]
        .pivot(index="date", columns="scheme_name", values="nav")
        .pct_change(fill_method=None)
        .dropna(how="all")
    )
    plt.figure(figsize=(10, 8))
    sns.heatmap(returns.corr(), cmap="vlag", center=0, annot=False)
    plt.title("Daily Return Correlation Matrix: 10 Large Funds")
    savefig("11_nav_return_correlation")

    sector_weights = holdings.groupby("sector", as_index=False)["weight_pct"].sum().sort_values("weight_pct", ascending=False)
    plt.figure(figsize=(8, 8))
    wedges, _ = plt.pie(sector_weights["weight_pct"], startangle=90, wedgeprops={"width": 0.42})
    plt.legend(wedges, sector_weights["sector"], bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.title("Aggregate Sector Allocation")
    savefig("12_sector_allocation_donut")

    plt.figure(figsize=(10, 6))
    sns.barplot(data=performance.sort_values("return_3yr_pct", ascending=False).head(10), y="scheme_name", x="return_3yr_pct", color="#59a14f")
    plt.title("Top 10 Funds by 3-Year Return")
    plt.xlabel("3-year return, %")
    plt.ylabel("")
    savefig("13_top_3yr_returns")

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=performance, x="expense_ratio_pct", y="return_3yr_pct", hue="plan")
    plt.title("Expense Ratio vs 3-Year Return")
    savefig("14_expense_vs_return")

    tx_monthly = tx.assign(month=tx["transaction_date"].dt.to_period("M").dt.to_timestamp())
    tx_summary = tx_monthly.groupby(["month", "transaction_type"], as_index=False)["amount_inr"].sum()
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=tx_summary, x="month", y="amount_inr", hue="transaction_type", marker="o")
    plt.title("Monthly Transaction Amount by Type")
    plt.ylabel("Amount, INR")
    savefig("15_transaction_type_trends")


def make_notebook() -> None:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell("# EDA Analysis\n\nExploratory analysis for mutual fund NAV, AUM, SIP, investor, geography, folio, correlation, and portfolio allocation trends."),
        nbf.v4.new_code_cell("from pathlib import Path\nimport pandas as pd\nimport seaborn as sns\nimport matplotlib.pyplot as plt\nimport plotly.express as px\n\nPROJECT_ROOT = Path('..').resolve()\nPROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'\nCHART_DIR = PROJECT_ROOT / 'reports' / 'charts' / 'eda'\nsns.set_theme(style='whitegrid')"),
        nbf.v4.new_code_cell("fund = pd.read_csv(PROCESSED_DIR / 'fund_master_cleaned.csv', parse_dates=['launch_date'])\nnav = pd.read_csv(PROCESSED_DIR / 'nav_history_cleaned.csv', parse_dates=['date'])\naum = pd.read_csv(PROCESSED_DIR / 'aum_by_fund_house_cleaned.csv', parse_dates=['date'])\nsip = pd.read_csv(PROCESSED_DIR / 'monthly_sip_inflows_cleaned.csv', parse_dates=['month'])\ncategory = pd.read_csv(PROCESSED_DIR / 'category_inflows_cleaned.csv', parse_dates=['month'])\nfolios = pd.read_csv(PROCESSED_DIR / 'industry_folio_count_cleaned.csv', parse_dates=['month'])\nperformance = pd.read_csv(PROCESSED_DIR / 'scheme_performance_cleaned.csv')\ntx = pd.read_csv(PROCESSED_DIR / 'investor_transactions_cleaned.csv', parse_dates=['transaction_date'])\nholdings = pd.read_csv(PROCESSED_DIR / 'portfolio_holdings_cleaned.csv', parse_dates=['portfolio_date'])\nnav = nav.merge(fund[['amfi_code', 'scheme_name', 'fund_house']], on='amfi_code', how='left')"),
        nbf.v4.new_markdown_cell("Insight 1: Chart 01 shows broad NAV participation across schemes, with the 2023 rally and 2024 correction windows visible as market-wide regimes."),
        nbf.v4.new_code_cell("fig = px.line(nav, x='date', y='nav', color='scheme_name', title='Daily NAV Trend for All Schemes')\nfig.add_vrect(x0='2023-01-01', x1='2023-12-31', fillcolor='green', opacity=0.12, line_width=0)\nfig.add_vrect(x0='2024-01-01', x1='2024-12-31', fillcolor='red', opacity=0.10, line_width=0)\nfig.show()"),
        nbf.v4.new_markdown_cell("Insight 2: Chart 02 highlights that large fund houses dominate AUM, with SBI marked against the 12.5 lakh crore reference level."),
        nbf.v4.new_code_cell("aum.assign(year=aum['date'].dt.year).pivot_table(index='year', columns='fund_house', values='aum_lakh_crore').plot(kind='bar', figsize=(14, 6)); plt.title('AUM Growth by Fund House'); plt.ylabel('AUM, lakh crore');"),
        nbf.v4.new_markdown_cell("Insight 3: Chart 03 shows SIP inflows compounding strongly into the late-2025 peak."),
        nbf.v4.new_code_cell("px.line(sip, x='month', y='sip_inflow_crore', markers=True, title='Monthly SIP Inflows').show()"),
        nbf.v4.new_markdown_cell("Insight 4: Chart 04 reveals category-level rotation through varying net inflow intensity by month."),
        nbf.v4.new_code_cell("category.assign(month_label=category['month'].dt.strftime('%Y-%m')).pivot_table(index='category', columns='month_label', values='net_inflow_crore').pipe(lambda x: sns.heatmap(x, cmap='YlGnBu')); plt.title('Category Inflow Heatmap');"),
        nbf.v4.new_markdown_cell("Insight 5: Charts 05-07 show investor mix across age, SIP ticket size, and gender."),
        nbf.v4.new_code_cell("tx['age_group'].value_counts().sort_index().plot(kind='pie', autopct='%1.1f%%', figsize=(6, 6)); plt.title('Age Group Distribution');"),
        nbf.v4.new_markdown_cell("Insight 6: Charts 08-09 show geographic contribution, separating state-level SIP amount from T30/B30 city-tier concentration."),
        nbf.v4.new_code_cell("tx[tx.transaction_type == 'SIP'].groupby('state')['amount_inr'].sum().sort_values().tail(15).plot(kind='barh', figsize=(9, 6)); plt.title('SIP Amount by State');"),
        nbf.v4.new_markdown_cell("Insight 7: Chart 10 tracks industry folio growth from the January 2022 base to the December 2025 endpoint."),
        nbf.v4.new_code_cell("sns.lineplot(data=folios, x='month', y='total_folios_crore', marker='o'); plt.title('Folio Count Growth');"),
        nbf.v4.new_markdown_cell("Insight 8: Chart 11 shows that large equity funds have mostly positive return correlations, supporting common market-factor exposure."),
        nbf.v4.new_code_cell("selected = performance.nlargest(10, 'aum_crore')['amfi_code']; corr = nav[nav.amfi_code.isin(selected)].pivot(index='date', columns='scheme_name', values='nav').pct_change(fill_method=None).corr(); sns.heatmap(corr, cmap='vlag', center=0); plt.title('Return Correlation Matrix');"),
        nbf.v4.new_markdown_cell("Insight 9: Chart 12 summarizes aggregate sector exposure across equity portfolio holdings."),
        nbf.v4.new_code_cell("holdings.groupby('sector')['weight_pct'].sum().sort_values(ascending=False).plot(kind='pie', wedgeprops={'width': .42}, figsize=(7, 7)); plt.title('Sector Allocation Donut');"),
        nbf.v4.new_markdown_cell("Insight 10: Charts 13-15 connect performance, cost, and transaction behavior for fund comparison and investor activity review."),
        nbf.v4.new_code_cell("performance.sort_values('return_3yr_pct').tail(10).plot(kind='barh', x='scheme_name', y='return_3yr_pct', legend=False, figsize=(9, 6)); plt.title('Top 10 Funds by 3-Year Return');"),
        nbf.v4.new_markdown_cell(
            "## Final Report Chart Gallery\n\n"
            "![01 NAV trend](../reports/charts/eda/01_nav_trend_all_schemes.png)\n\n"
            "![02 AUM growth](../reports/charts/eda/02_aum_growth_by_fund_house.png)\n\n"
            "![03 SIP inflow](../reports/charts/eda/03_sip_inflow_time_series.png)\n\n"
            "![04 Category heatmap](../reports/charts/eda/04_category_inflow_heatmap.png)\n\n"
            "![05 Age distribution](../reports/charts/eda/05_age_group_distribution.png)\n\n"
            "![06 SIP by age](../reports/charts/eda/06_sip_amount_by_age_group.png)\n\n"
            "![07 Gender split](../reports/charts/eda/07_gender_split.png)\n\n"
            "![08 SIP by state](../reports/charts/eda/08_sip_amount_by_state.png)\n\n"
            "![09 City tier](../reports/charts/eda/09_city_tier_split.png)\n\n"
            "![10 Folio growth](../reports/charts/eda/10_folio_count_growth.png)\n\n"
            "![11 Return correlation](../reports/charts/eda/11_nav_return_correlation.png)\n\n"
            "![12 Sector allocation](../reports/charts/eda/12_sector_allocation_donut.png)\n\n"
            "![13 Top returns](../reports/charts/eda/13_top_3yr_returns.png)\n\n"
            "![14 Expense vs return](../reports/charts/eda/14_expense_vs_return.png)\n\n"
            "![15 Transaction trends](../reports/charts/eda/15_transaction_type_trends.png)"
        ),
    ]
    nbf.write(nb, NOTEBOOK_PATH)
    print(f"Wrote {NOTEBOOK_PATH}")


def main() -> None:
    make_charts()
    make_notebook()


if __name__ == "__main__":
    main()
