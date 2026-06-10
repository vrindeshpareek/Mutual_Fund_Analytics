# Mutual Fund Analytics Data Dictionary

Source files live in `data/raw/`; cleaned files live in `data/processed/`.

## fund_master_cleaned
Source: `01_fund_master.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `amfi_code` | `int64` | AMFI scheme identifier used as the fund key. |
| `fund_house` | `str` | Fund House from `01_fund_master.csv`. |
| `scheme_name` | `str` | Scheme Name from `01_fund_master.csv`. |
| `category` | `str` | Category from `01_fund_master.csv`. |
| `sub_category` | `str` | Sub Category from `01_fund_master.csv`. |
| `plan` | `str` | Plan from `01_fund_master.csv`. |
| `launch_date` | `datetime64[us]` | Launch Date from `01_fund_master.csv`. |
| `benchmark` | `str` | Benchmark from `01_fund_master.csv`. |
| `expense_ratio_pct` | `float64` | Annual expense ratio percentage. |
| `exit_load_pct` | `float64` | Exit Load Pct from `01_fund_master.csv`. |
| `min_sip_amount` | `int64` | Min Sip Amount from `01_fund_master.csv`. |
| `min_lumpsum_amount` | `int64` | Min Lumpsum Amount from `01_fund_master.csv`. |
| `fund_manager` | `str` | Fund Manager from `01_fund_master.csv`. |
| `risk_category` | `str` | Risk Category from `01_fund_master.csv`. |
| `sebi_category_code` | `str` | Sebi Category Code from `01_fund_master.csv`. |

## nav_history_cleaned
Source: `02_nav_history.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `amfi_code` | `int64` | AMFI scheme identifier used as the fund key. |
| `date` | `datetime64[us]` | Date from `02_nav_history.csv`. |
| `nav` | `float64` | Net asset value for a scheme on a date. |

## aum_by_fund_house_cleaned
Source: `03_aum_by_fund_house.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `date` | `datetime64[us]` | Date from `03_aum_by_fund_house.csv`. |
| `fund_house` | `str` | Fund House from `03_aum_by_fund_house.csv`. |
| `aum_lakh_crore` | `float64` | Aum Lakh Crore from `03_aum_by_fund_house.csv`. |
| `aum_crore` | `int64` | Assets under management in INR crore. |
| `num_schemes` | `int64` | Num Schemes from `03_aum_by_fund_house.csv`. |

## monthly_sip_inflows_cleaned
Source: `04_monthly_sip_inflows.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `month` | `datetime64[us]` | Month from `04_monthly_sip_inflows.csv`. |
| `sip_inflow_crore` | `int64` | Sip Inflow Crore from `04_monthly_sip_inflows.csv`. |
| `active_sip_accounts_crore` | `float64` | Active Sip Accounts Crore from `04_monthly_sip_inflows.csv`. |
| `new_sip_accounts_lakh` | `float64` | New Sip Accounts Lakh from `04_monthly_sip_inflows.csv`. |
| `sip_aum_lakh_crore` | `float64` | Sip Aum Lakh Crore from `04_monthly_sip_inflows.csv`. |
| `yoy_growth_pct` | `float64` | Yoy Growth Pct from `04_monthly_sip_inflows.csv`. |

## category_inflows_cleaned
Source: `05_category_inflows.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `month` | `datetime64[us]` | Month from `05_category_inflows.csv`. |
| `category` | `str` | Category from `05_category_inflows.csv`. |
| `net_inflow_crore` | `float64` | Net category inflow in INR crore. |

## industry_folio_count_cleaned
Source: `06_industry_folio_count.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `month` | `datetime64[us]` | Month from `06_industry_folio_count.csv`. |
| `total_folios_crore` | `float64` | Total Folios Crore from `06_industry_folio_count.csv`. |
| `equity_folios_crore` | `float64` | Equity Folios Crore from `06_industry_folio_count.csv`. |
| `debt_folios_crore` | `float64` | Debt Folios Crore from `06_industry_folio_count.csv`. |
| `hybrid_folios_crore` | `float64` | Hybrid Folios Crore from `06_industry_folio_count.csv`. |
| `others_folios_crore` | `float64` | Others Folios Crore from `06_industry_folio_count.csv`. |

## scheme_performance_cleaned
Source: `07_scheme_performance.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `amfi_code` | `int64` | AMFI scheme identifier used as the fund key. |
| `scheme_name` | `str` | Scheme Name from `07_scheme_performance.csv`. |
| `fund_house` | `str` | Fund House from `07_scheme_performance.csv`. |
| `category` | `str` | Category from `07_scheme_performance.csv`. |
| `plan` | `str` | Plan from `07_scheme_performance.csv`. |
| `return_1yr_pct` | `float64` | Return 1Yr Pct from `07_scheme_performance.csv`. |
| `return_3yr_pct` | `float64` | Return 3Yr Pct from `07_scheme_performance.csv`. |
| `return_5yr_pct` | `float64` | Return 5Yr Pct from `07_scheme_performance.csv`. |
| `benchmark_3yr_pct` | `float64` | Benchmark 3Yr Pct from `07_scheme_performance.csv`. |
| `alpha` | `float64` | Alpha from `07_scheme_performance.csv`. |
| `beta` | `float64` | Beta from `07_scheme_performance.csv`. |
| `sharpe_ratio` | `float64` | Sharpe Ratio from `07_scheme_performance.csv`. |
| `sortino_ratio` | `float64` | Sortino Ratio from `07_scheme_performance.csv`. |
| `std_dev_ann_pct` | `float64` | Std Dev Ann Pct from `07_scheme_performance.csv`. |
| `max_drawdown_pct` | `float64` | Max Drawdown Pct from `07_scheme_performance.csv`. |
| `aum_crore` | `int64` | Assets under management in INR crore. |
| `expense_ratio_pct` | `float64` | Annual expense ratio percentage. |
| `morningstar_rating` | `int64` | Morningstar Rating from `07_scheme_performance.csv`. |
| `risk_grade` | `str` | Risk Grade from `07_scheme_performance.csv`. |
| `performance_anomaly_flag` | `bool` | Performance Anomaly Flag from `07_scheme_performance.csv`. |

## investor_transactions_cleaned
Source: `08_investor_transactions.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `investor_id` | `str` | Investor Id from `08_investor_transactions.csv`. |
| `transaction_date` | `datetime64[us]` | Transaction Date from `08_investor_transactions.csv`. |
| `amfi_code` | `int64` | AMFI scheme identifier used as the fund key. |
| `transaction_type` | `str` | Standardized investor transaction category: SIP, Lumpsum, or Redemption. |
| `amount_inr` | `int64` | Amount Inr from `08_investor_transactions.csv`. |
| `state` | `str` | State from `08_investor_transactions.csv`. |
| `city` | `str` | City from `08_investor_transactions.csv`. |
| `city_tier` | `str` | City Tier from `08_investor_transactions.csv`. |
| `age_group` | `str` | Age Group from `08_investor_transactions.csv`. |
| `gender` | `str` | Gender from `08_investor_transactions.csv`. |
| `annual_income_lakh` | `float64` | Annual Income Lakh from `08_investor_transactions.csv`. |
| `payment_mode` | `str` | Payment Mode from `08_investor_transactions.csv`. |
| `kyc_status` | `str` | Investor KYC status enum after cleaning. |
| `transaction_quality_flag` | `str` | Transaction Quality Flag from `08_investor_transactions.csv`. |

## portfolio_holdings_cleaned
Source: `09_portfolio_holdings.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `amfi_code` | `int64` | AMFI scheme identifier used as the fund key. |
| `stock_symbol` | `str` | Stock Symbol from `09_portfolio_holdings.csv`. |
| `stock_name` | `str` | Stock Name from `09_portfolio_holdings.csv`. |
| `sector` | `str` | Sector from `09_portfolio_holdings.csv`. |
| `weight_pct` | `float64` | Portfolio holding weight percentage. |
| `market_value_cr` | `float64` | Market Value Cr from `09_portfolio_holdings.csv`. |
| `current_price_inr` | `float64` | Current Price Inr from `09_portfolio_holdings.csv`. |
| `portfolio_date` | `datetime64[us]` | Portfolio Date from `09_portfolio_holdings.csv`. |

## benchmark_indices_cleaned
Source: `10_benchmark_indices.csv`

| Column | Data type | Business definition |
|---|---:|---|
| `date` | `datetime64[us]` | Date from `10_benchmark_indices.csv`. |
| `index_name` | `str` | Index Name from `10_benchmark_indices.csv`. |
| `close_value` | `float64` | Benchmark index closing level. |
