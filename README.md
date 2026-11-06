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

## What to explain in an interview

- **Data quality:** completeness, uniqueness, validity and date checks.
- **Reconciliation:** compares the same company/metric/period across providers. A discrepancy is a review signal, not automatic proof of an error.
- **Anomaly screening:** Isolation Forest runs separately for each metric to avoid mixing unlike units.
- **Limitations:** the demo score uses transparent heuristic penalties; a production score should have business-approved rules, severity weights, lineage and human review.

## Suggested extensions

1. Add a PostgreSQL database and retain raw, standardized and curated layers.
2. Add currency/unit normalization before comparing sources.
3. Add an immutable correction/audit table and reviewer workflow.
4. Add scheduled ingestion, retries, monitoring and unit tests.

**Data note:** the included CSV is synthetic demonstration data, not real Bloomberg or issuer data.
