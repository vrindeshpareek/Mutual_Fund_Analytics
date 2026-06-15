"""
recommender.py — Bluestock Fintech MF Capstone · Day 6
Simple rule-based fund recommender using Sharpe ratio and risk_grade.

Usage:
    python recommender.py --risk Low
    python recommender.py --risk Moderate
    python recommender.py --risk High
    python recommender.py  (interactive mode)
"""

import argparse
import pandas as pd
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
SCHEME_PERF = BASE / "data" / "processed" / "scheme_performance_cleaned.csv"
FUND_MASTER  = BASE / "data" / "processed" / "fund_master_cleaned.csv"

# ─── Risk-grade mapping ────────────────────────────────────────────────────────
RISK_MAP = {
    "Low":      ["Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High":     ["High", "Very High"],
}

# ─── Core recommender ─────────────────────────────────────────────────────────
def recommend(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """
    Return top_n funds ranked by Sharpe ratio within the risk bucket.

    Parameters
    ----------
    risk_appetite : str  — 'Low' | 'Moderate' | 'High'
    top_n         : int  — number of funds to return (default 3)

    Returns
    -------
    pd.DataFrame with columns:
        scheme_name, fund_house, category, risk_grade,
        sharpe_ratio, return_3yr_pct, expense_ratio_pct, aum_crore
    """
    risk_appetite = risk_appetite.strip().title()
    if risk_appetite not in RISK_MAP:
        raise ValueError(
            f"Invalid risk appetite '{risk_appetite}'. "
            f"Choose from: {list(RISK_MAP.keys())}"
        )

    scheme_perf = pd.read_csv(SCHEME_PERF)
    fund_master  = pd.read_csv(FUND_MASTER)

    grades = RISK_MAP[risk_appetite]
    filtered = scheme_perf[scheme_perf["risk_grade"].isin(grades)].copy()

    if filtered.empty:
        print(f"⚠  No funds found for risk appetite: {risk_appetite}")
        return pd.DataFrame()

    # Merge for extra context
    merged = filtered.merge(
        fund_master[["amfi_code", "min_sip_amount", "fund_manager"]],
        on="amfi_code",
        how="left",
    )

    cols = [
        "scheme_name", "fund_house", "category", "risk_grade",
        "sharpe_ratio", "return_3yr_pct", "expense_ratio_pct",
        "aum_crore", "min_sip_amount", "fund_manager",
    ]
    top = merged.nlargest(top_n, "sharpe_ratio")[cols].reset_index(drop=True)
    top.index += 1          # rank starts at 1
    top.index.name = "Rank"
    return top


# ─── Pretty printer ───────────────────────────────────────────────────────────
def print_recommendation(risk_appetite: str) -> None:
    print("\n" + "=" * 70)
    print(f"  🔍  Fund Recommendation  |  Risk Appetite: {risk_appetite.upper()}")
    print("=" * 70)

    result = recommend(risk_appetite)
    if result.empty:
        return

    for rank, row in result.iterrows():
        print(f"\n  #{rank}  {row['scheme_name']}")
        print(f"       Fund House   : {row['fund_house']}")
        print(f"       Category     : {row['category']}")
        print(f"       Risk Grade   : {row['risk_grade']}")
        print(f"       Sharpe Ratio : {row['sharpe_ratio']:.2f}")
        print(f"       3-Yr Return  : {row['return_3yr_pct']:.2f}%")
        print(f"       Expense Ratio: {row['expense_ratio_pct']:.2f}%")
        print(f"       AUM (₹ Cr)  : {row['aum_crore']:,.0f}")
        print(f"       Min SIP      : ₹{row['min_sip_amount']:,.0f}")
        print(f"       Fund Manager : {row['fund_manager']}")

    print("\n" + "-" * 70)
    print("  ⚠  Disclaimer: For educational/portfolio purposes only.")
    print("     Past performance is not indicative of future returns.")
    print("=" * 70 + "\n")


# ─── CLI entry point ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Bluestock MF Recommender — get top funds by risk appetite"
    )
    parser.add_argument(
        "--risk",
        choices=["Low", "Moderate", "High"],
        default=None,
        help="Risk appetite: Low | Moderate | High",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of funds to recommend (default: 3)",
    )
    args = parser.parse_args()

    if args.risk:
        result = recommend(args.risk, args.top)
        print_recommendation(args.risk)
    else:
        # Interactive mode
        print("\n🏦  Bluestock Fintech — MF Fund Recommender")
        print("    Risk Appetite Options: Low | Moderate | High")
        risk = input("    Enter your risk appetite: ").strip()
        print_recommendation(risk)


if __name__ == "__main__":
    main()
