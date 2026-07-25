"""Page 2 — Hotspot Map: Interactive Folium Maps & Spatial Clusters."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from dashboard.components.cards import section_header, info_box

st.set_page_config(page_title="Hotspot Maps — SurakshaAI", page_icon="🗺️", layout="wide")

PROC = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

st.markdown("## 🗺️ Geospatial Crime Hotspot Analytics")
st.markdown("<p style='color:#8b949e;'>DBSCAN Clustering & Folium Interactive Spatial Analysis</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color:#30363d;'>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔴 Cluster Hotspot Map", "🔥 Density Heatmap", "🗺️ Risk Choropleth"])

def render_html_file(file_path: Path, height=600):
    if not file_path.exists():
        info_box(f"Map file `{file_path.name}` not found. Please run `python pipeline/04_hotspot_model.py` first.", "warn")
        return
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    components.html(html_content, height=height, scrolling=True)

with tab1:
    section_header("DBSCAN Spatial Cluster Map", "Districts grouped into spatiotemporal crime clusters")
    render_html_file(PROC / "karnataka_hotspot_map.html")

with tab2:
    section_header("Crime Density Heatmap", "Intensity overlay of total crime distribution")
    render_html_file(PROC / "karnataka_heatmap.html")

with tab3:
    section_header("Risk Classification Choropleth", "District-level risk boundary visualization")
    render_html_file(PROC / "karnataka_choropleth.html")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📊 District Spatial Clusters Summary")
if (PROC / "hotspot_clusters.csv").exists():
    df_clusters = pd.read_csv(PROC / "hotspot_clusters.csv")
    cols = ["DISTRICT", "CLUSTER", "TOTAL_CRIMES", "RISK_LABEL", "LAT", "LON"]
    avail = [c for c in cols if c in df_clusters.columns]
    st.dataframe(df_clusters[avail], use_container_width=True)
