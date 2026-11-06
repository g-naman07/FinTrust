import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

KEY_COLUMNS = ["company", "metric", "period", "source"]
REQUIRED = ["company", "metric", "period", "value", "unit", "currency", "source"]


def _safe_series(df, column):
    if column not in df.columns:
        return pd.Series(index=df.index, dtype="object")
    return df[column]


def run_quality_checks(data):
    """Return field-level checks and a row-level annotated copy."""
    df = data.copy()
    for col in REQUIRED:
        if col not in df.columns:
            df[col] = np.nan
    df["value_numeric"] = pd.to_numeric(df["value"], errors="coerce")
    df["period_parsed"] = pd.to_datetime(df["period"], errors="coerce")

    missing_cells = int(df[REQUIRED].isna().sum().sum())
    total_cells = max(len(df) * len(REQUIRED), 1)
    completeness = 100.0 * (1 - missing_cells / total_cells)

    duplicate_mask = df.duplicated(subset=KEY_COLUMNS, keep=False)
    duplicate_count = int(duplicate_mask.sum())
    invalid_value_count = int(df["value_numeric"].isna().sum())
    invalid_period_count = int(df["period_parsed"].isna().sum())
    invalid_currency_count = int((df["currency"].notna() & (df["currency"].astype(str).str.len() != 3)).sum())

    df["is_duplicate_key"] = duplicate_mask
    df["is_valid_value"] = df["value_numeric"].notna()
    df["is_valid_period"] = df["period_parsed"].notna()

    checks = [
        {"check": "Completeness", "failed_rows_or_cells": missing_cells, "description": f"{completeness:.1f}% of required cells are populated"},
        {"check": "Duplicate key", "failed_rows_or_cells": duplicate_count, "description": "Duplicate company + metric + period + source combinations"},
        {"check": "Numeric value", "failed_rows_or_cells": invalid_value_count, "description": "Values that cannot be parsed as numbers"},
        {"check": "Reporting period", "failed_rows_or_cells": invalid_period_count, "description": "Periods that cannot be parsed as dates"},
        {"check": "Currency format", "failed_rows_or_cells": invalid_currency_count, "description": "Non-empty currency codes that are not three characters"},
    ]
    # Transparent, simple score for this demo; weights are configurable in a production system.
    penalties = min(30, duplicate_count / max(len(df), 1) * 100)
    penalties += min(25, invalid_value_count / max(len(df), 1) * 100)
    penalties += min(15, invalid_period_count / max(len(df), 1) * 100)
    penalties += min(10, invalid_currency_count / max(len(df), 1) * 100)
    quality_score = max(0.0, min(100.0, completeness - penalties))
    return {
        "checks": checks,
        "completeness": completeness,
        "duplicate_count": duplicate_count,
        "quality_score": quality_score,
        "annotated": df,
    }


def reconcile_sources(data):
    """Compare values for the same company, metric and period across sources."""
    df = data.copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["company", "metric", "period", "value"])
    if df.empty:
        return pd.DataFrame(columns=["company", "metric", "period", "source_count", "min_value", "max_value", "spread_pct", "sources"])
    grouped = df.groupby(["company", "metric", "period"], dropna=False)
    rows = []
    for (company, metric, period), group in grouped:
        if group["source"].nunique() < 2:
            continue
        low = float(group["value"].min())
        high = float(group["value"].max())
        denominator = max(abs(float(group["value"].mean())), 1e-9)
        rows.append({
            "company": company,
            "metric": metric,
            "period": period,
            "source_count": int(group["source"].nunique()),
            "min_value": low,
            "max_value": high,
            "spread_pct": round((high - low) / denominator * 100, 2),
            "sources": ", ".join(sorted(group["source"].astype(str).unique())),
        })
    return pd.DataFrame(rows)


def detect_anomalies(data, contamination=0.08):
    """Screen each metric independently with Isolation Forest."""
    df = data.copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["metric", "value"])
    results = []
    for metric, group in df.groupby("metric"):
        if len(group) < 6 or group["value"].nunique() < 3:
            continue
        model = IsolationForest(contamination=contamination, random_state=42)
        prediction = model.fit_predict(group[["value"]])
        score = model.decision_function(group[["value"]])
        flagged = group.copy()
        flagged["anomaly"] = prediction == -1
        flagged["anomaly_score"] = score
        flagged = flagged[flagged["anomaly"]]
        for _, row in flagged.iterrows():
            results.append({
                "company": row.get("company", ""),
                "metric": metric,
                "period": row.get("period", ""),
                "value": row["value"],
                "source": row.get("source", ""),
                "anomaly_score": round(float(row["anomaly_score"]), 4),
            })
    return pd.DataFrame(results, columns=["company", "metric", "period", "value", "source", "anomaly_score"])
