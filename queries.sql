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
