# Day 1 Data Quality Summary

## Dataset Anomalies

### 01_fund_master.csv
- no immediate anomalies detected

### 02_nav_history.csv
- no immediate anomalies detected

### 03_aum_by_fund_house.csv
- no immediate anomalies detected

### 04_monthly_sip_inflows.csv
- missing values in 1 columns (yoy_growth_pct: 12)

### 05_category_inflows.csv
- no immediate anomalies detected

### 06_industry_folio_count.csv
- no immediate anomalies detected

### 07_scheme_performance.csv
- no immediate anomalies detected

### 08_investor_transactions.csv
- no immediate anomalies detected

### 09_portfolio_holdings.csv
- no immediate anomalies detected

### 10_benchmark_indices.csv
- no immediate anomalies detected

### live_nav_latest.csv
- no immediate anomalies detected

### mfapi_nav_history_key_schemes.csv
- no immediate anomalies detected

## Fund Master Exploration
- fund houses: matching column not found
- sub-categories: matching column not found
- AMFI scheme code structure: column 'amfi_code' is 100.0% numeric-convertible; codes are treated as stable scheme identifiers.

## AMFI Code Validation
- AMFI validation passed: all 40 fund_master scheme codes exist in nav_history.
