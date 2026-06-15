# Bluestock Mutual Fund Analytics Capstone

## Project Overview

This project builds an end-to-end Mutual Fund Analytics Platform using Python, SQLite, Power BI, and financial analytics techniques. The solution ingests mutual fund, NAV, SIP, investor, and portfolio datasets, performs data cleaning and validation, computes performance and risk metrics, and delivers an interactive Power BI dashboard for decision-making.

## Objectives

* Build a complete ETL pipeline for mutual fund data.
* Analyze fund performance using financial metrics.
* Generate investor and SIP insights.
* Compute advanced risk measures such as VaR, CVaR, and rolling Sharpe ratio.
* Develop an interactive Power BI dashboard.
* Create a simple fund recommendation system.

## Tech Stack

* Python (Pandas, NumPy, Matplotlib)
* SQLite
* Power BI
* Git & GitHub

## Dataset Description

The project uses mutual fund master data, NAV history, benchmark indices, SIP inflows, investor transactions, category inflows, and portfolio holdings datasets.

## Key Analytics

* CAGR, Alpha, Beta, Sharpe Ratio
* Historical VaR and CVaR
* Rolling 90-Day Sharpe Ratio
* Investor Cohort Analysis
* SIP Continuity Analysis
* Sector Concentration (HHI)
* Fund Recommendation Engine

## Dashboard Pages

1. Industry Overview
2. Fund Performance
3. Investor Analytics
4. SIP & Market Trends

## How to Run

1. Clone the repository.
2. Install dependencies:
   pip install -r requirements.txt
3. Run:
   python run_pipeline.py
4. Open Power BI dashboard:
   bluestock_mf_dashboard.pbix

## Deliverables

* Advanced_Analytics.ipynb
* bluestock_mf_dashboard.pbix
* Dashboard.pdf
* var_cvar_report.csv
* recommender.py
* rolling_sharpe_chart.png

## Author

Vrindesh Pareek
