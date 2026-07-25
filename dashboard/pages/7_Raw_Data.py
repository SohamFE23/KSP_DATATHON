"""Page 7 — Raw Data: Filterable Data Table & CSV Exporter."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from dashboard.components.cards import section_header, info_box

st.set_page_config(page_title="Raw Data — SurakshaAI", page_icon="📋", layout="wide")

PROC = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

st.markdown("## 📋 Processed Datasets & Raw Data Explorer")
st.markdown("<p style='color:#8b949e;'>Inspect, Filter, and Export Clean Data Products</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color:#30363d;'>", unsafe_allow_html=True)

dataset_options = {
    "District Enriched (Crime + Census 2011)": "district_enriched.csv",
    "Karnataka Clean Crime Data": "karnataka_clean.csv",
    "District Risk Scores & Predictions": "risk_scores.csv",
    "Hotspot Clusters": "hotspot_clusters.csv",
    "Crime Forecast": "crime_forecast.csv",
    "Anomaly Flagged": "anomaly_flagged.csv",
    "Socio-Economic Data (Census 2011)": "karnataka_socioeconomic.csv",
    "Full IPC 2014 Crimes": "ipc_2014.csv",
    "District Women Crimes": "district_women_crimes.csv",
    "SC Crimes": "sc_crimes.csv",
    "ST Crimes": "st_crimes.csv",
    "Police Strength": "police_strength.csv",
}

selected_label = st.selectbox("Select Dataset to Explore", list(dataset_options.keys()))
fname = dataset_options[selected_label]
fpath = PROC / fname

if not fpath.exists():
    info_box(f"File `{fname}` does not exist in `data/processed/`.", "error")
    st.stop()

@st.cache_data
def load_csv(path):
    return pd.read_csv(path, low_memory=False)

df = load_csv(fpath)

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(f"**Shape:** `{df.shape[0]}` rows × `{df.shape[1]}` columns")
with col2:
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download {fname}",
        data=csv_bytes,
        file_name=fname,
        mime="text/csv"
    )

search_term = st.text_input("🔍 Quick Search Filter across all text fields")
if search_term:
    mask = df.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)
    df = df[mask]
    st.caption(f"Showing {len(df)} matching rows")

st.dataframe(df, use_container_width=True, height=500)
