# FinTrust — Financial Data Quality & Reconciliation

A portfolio project for a Bloomberg-style Data Management role. It demonstrates ingestion of financial observations, field-level validation, cross-source reconciliation, statistical anomaly screening, and downloadable reports.

## Run locally

```bash
cd fintrust
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app starts with `data/financial_observations.csv`. Upload another CSV from the sidebar to test your own data. Required columns: `company, metric, period, value, unit, currency, source`.

