from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

from quality_engine import run_quality_checks, reconcile_sources, detect_anomalies

st.set_page_config(page_title="FinTrust | Data Quality", page_icon="📊", layout="wide")
ROOT = Path(__file__).parent
DATA = ROOT / "data" / "financial_observations.csv"
REQUIRED = ["company", "metric", "period", "value", "unit", "currency", "source"]

st.title("FinTrust — Financial Data Quality & Reconciliation")
st.caption("A demonstration data-management workflow: ingest → validate → reconcile → investigate.")

with st.sidebar:
    st.header("Data input")
    uploaded = st.file_uploader("Upload financial observations (CSV)", type=["csv"])
    tolerance = st.slider("Source discrepancy threshold (%)", 0.0, 50.0, 5.0, 0.5)
    st.caption("Expected columns: " + ", ".join(REQUIRED))

try:
    df = pd.read_csv(uploaded) if uploaded is not None else pd.read_csv(DATA)
except Exception as exc:
    st.error(f"Could not read the CSV: {exc}")
    st.stop()

missing_columns = [c for c in REQUIRED if c not in df.columns]
if missing_columns:
    st.error(f"Missing required columns: {', '.join(missing_columns)}")
    st.stop()

checks = run_quality_checks(df)
recon = reconcile_sources(df)
anomalies = detect_anomalies(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows ingested", f"{len(df):,}")
c2.metric("Completeness", f"{checks['completeness']:.1f}%")
c3.metric("Duplicate keys", f"{checks['duplicate_count']:,}")
c4.metric("Quality score", f"{checks['quality_score']:.1f}/100")

st.subheader("1. Data quality checks")
quality_view = pd.DataFrame(checks["checks"])
st.dataframe(quality_view, use_container_width=True, hide_index=True)

left, right = st.columns(2)
with left:
    st.subheader("Missing values by field")
    missing = df[REQUIRED].isna().sum().rename("missing_rows").reset_index()
    missing.columns = ["field", "missing_rows"]
    st.plotly_chart(px.bar(missing, x="field", y="missing_rows", title="Missing values"), use_container_width=True)
with right:
    st.subheader("Records by source")
    source_counts = df.groupby("source").size().reset_index(name="records")
    st.plotly_chart(px.bar(source_counts, x="source", y="records", title="Source coverage"), use_container_width=True)

st.subheader("2. Cross-source reconciliation")
st.caption(f"Groups with a relative spread above {tolerance:.1f}% are flagged for investigation. Differences are not automatically errors: units, definitions and reporting periods must be checked.")
if recon.empty:
    st.info("No comparable records from multiple sources were found.")
else:
    flagged = recon[recon["spread_pct"] > tolerance]
    st.metric("Groups requiring review", len(flagged))
    st.dataframe(recon.sort_values("spread_pct", ascending=False), use_container_width=True, hide_index=True)

st.subheader("3. Statistical anomaly screening")
if anomalies.empty:
    st.info("Not enough numeric observations per metric for anomaly screening. Add more rows to enable it.")
else:
    st.caption("Isolation Forest is applied separately within each metric so values with different units are not mixed. Review flagged records; a statistical outlier is not necessarily incorrect.")
    st.dataframe(anomalies, use_container_width=True, hide_index=True)

st.subheader("4. Source records")
st.dataframe(df, use_container_width=True, hide_index=True)

st.download_button("Download reconciliation report", recon.to_csv(index=False).encode("utf-8"), "reconciliation_report.csv", "text/csv")
st.download_button("Download quality-annotated data", checks["annotated"].to_csv(index=False).encode("utf-8"), "quality_annotated_data.csv", "text/csv")
