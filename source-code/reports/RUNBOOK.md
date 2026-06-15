# Mutual Fund Analytics Runbook

Run these commands from the project root:

```powershell
python -m pip install -r requirements.txt
python data_ingestion.py
python live_nav_fetch.py
python data_cleaning_sql.py
python generate_eda.py
python generate_performance.py
```

Open the notebooks:

```powershell
python -m jupyter lab notebooks
```

Optional notebook execution checks:

```powershell
python -m jupyter nbconvert --to notebook --execute notebooks/EDA_Analysis.ipynb --output EDA_Analysis.executed.ipynb --ExecutePreprocessor.timeout=300
python -m jupyter nbconvert --to notebook --execute notebooks/Performance_Analytics.ipynb --output Performance_Analytics.executed.ipynb --ExecutePreprocessor.timeout=300
```

Key outputs:

- `data/processed/`: 10 cleaned datasets, daily returns, fund scorecard, and alpha/beta.
- `bluestock_mf.db`: SQLite analytics database.
- `schema.sql`: star-schema DDL.
- `queries.sql`: 10 analytical SQL queries.
- `data_dictionary.md`: column definitions and source references.
- `reports/charts/eda/`: 15 EDA PNG charts.
- `reports/charts/performance/benchmark_comparison_top5.png`: benchmark comparison.
