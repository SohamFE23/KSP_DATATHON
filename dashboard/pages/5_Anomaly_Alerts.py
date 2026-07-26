"""Page 5 — Anomaly Alerts: IsolationForest Outlier Detection & Critical Cards."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
from dashboard.components.cards import section_header, anomaly_card, metric_card, info_box

PROC = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

st.markdown("## 🔴 AI Anomaly & Incident Detection")
st.markdown("<p style='color:#8b949e;'>IsolationForest Machine Learning Flags Deviances & Spikes in Crime Patterns</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color:#30363d;'>", unsafe_allow_html=True)

@st.cache_data
def load_anomalies():
    if (PROC / "anomaly_flagged.csv").exists():
        return pd.read_csv(PROC / "anomaly_flagged.csv")
    return pd.DataFrame()

df_anom = load_anomalies()

if df_anom.empty:
    info_box("Anomaly data unavailable. Run `python pipeline/06_anomaly_detection.py`", "error")
    st.stop()

# Filter anomalies
anomalies_only = df_anom[df_anom["IS_ANOMALY"] == 1] if "IS_ANOMALY" in df_anom.columns else df_anom

col1, col2, col3 = st.columns(3)
with col1:
    metric_card("Total Flagged Anomalies", len(anomalies_only), icon="🔴", color="#f85149")
with col2:
    crit_count = len(anomalies_only[anomalies_only["ANOMALY_SEVERITY"] == "CRITICAL"]) if "ANOMALY_SEVERITY" in anomalies_only.columns else 0
    metric_card("Critical Severity Anomalies", crit_count, icon="⚠️", color="#e3b341")
with col3:
    total_records = len(df_anom)
    rate = (len(anomalies_only) / total_records * 100) if total_records else 0
    metric_card("Anomaly Detection Rate", f"{rate:.1f}%", icon="📊", color="#58a6ff")

st.markdown("<br>", unsafe_allow_html=True)

f1, f2 = st.columns([1, 1])
with f1:
    dist_filter = st.multiselect("Filter by District", sorted(df_anom["DISTRICT"].dropna().unique().tolist()))
with f2:
    sev_filter = st.multiselect("Filter by Severity", ["CRITICAL", "HIGH", "NORMAL"])

filtered_df = anomalies_only.copy()
if dist_filter:
    filtered_df = filtered_df[filtered_df["DISTRICT"].isin(dist_filter)]
if sev_filter and "ANOMALY_SEVERITY" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["ANOMALY_SEVERITY"].isin(sev_filter)]

section_header(f"Flagged Anomaly Incident Feed ({len(filtered_df)} records)")

if filtered_df.empty:
    info_box("No anomaly records match the selected filters.", "info")
else:
    for _, row in filtered_df.sort_values("ANOMALY_SCORE", ascending=False).iterrows():
        dist = row.get("DISTRICT", "Unknown")
        yr   = int(row.get("YEAR", 0))
        score= float(row.get("ANOMALY_SCORE", 0))
        sev  = str(row.get("ANOMALY_SEVERITY", "HIGH"))
        tot  = float(row.get("TOTAL_CRIMES", 0))
        anomaly_card(dist, yr, score, sev, tot)

st.markdown("<br>", unsafe_allow_html=True)
section_header("📊 Anomaly Feature Distribution Visualization")
if (PROC / "anomaly_results.png").exists():
    st.image(str(PROC / "anomaly_results.png"), use_container_width=True)
