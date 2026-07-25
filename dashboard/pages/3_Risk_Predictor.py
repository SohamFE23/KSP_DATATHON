"""Page 3 — Risk Predictor: XGBoost Risk Classification & 6D Dimension Scores."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dashboard.components.cards import section_header, risk_badge, metric_card, info_box
from api.engine.risk_engine import compute_risk

st.set_page_config(page_title="Risk Predictor — SurakshaAI", page_icon="⚠️", layout="wide")

PROC = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

st.markdown("## ⚠️ AI District Risk Predictor")
st.markdown("<p style='color:#8b949e;'>XGBoost Machine Learning & 6-Dimension Composite Risk Assessment</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color:#30363d;'>", unsafe_allow_html=True)

@st.cache_data
def load_data():
    if (PROC / "district_features.csv").exists():
        return pd.read_csv(PROC / "district_features.csv", low_memory=False)
    return pd.read_csv(PROC / "karnataka_clean.csv", low_memory=False)

try:
    df = load_data()
except Exception as e:
    info_box(f"Data load error: {e}", "error")
    st.stop()

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Select District & Year")
    districts = sorted(df["DISTRICT"].dropna().unique().tolist())
    selected_dist = st.selectbox("District", districts)
    
    df_dist = df[df["DISTRICT"] == selected_dist].sort_values("YEAR")
    years = sorted(df_dist["YEAR"].dropna().unique().tolist())
    selected_year = st.selectbox("Year", years, index=len(years)-1)
    
    row = df_dist[df_dist["YEAR"] == selected_year].iloc[0]
    risk_res = compute_risk(row)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏆 Prediction Output")
    risk_badge(risk_res["label"])
    st.markdown(f"<h1 style='color:#58a6ff;margin-top:10px;'>{risk_res['total_score']} <span style='font-size:18px;color:#8b949e;'>/ 100</span></h1>", unsafe_allow_html=True)

with col2:
    section_header(f"Risk Breakdown: {selected_dist} ({selected_year})")
    dims = risk_res["dimensions"]
    weights = risk_res["weights"]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(dims.values()),
        y=[k.replace("_", " ").title() for k in dims.keys()],
        orientation="h",
        marker_color=["#f85149", "#ffa657", "#e3b341", "#79c0ff", "#58a6ff", "#bc8cff"],
        text=[f"{v:.1f} / {weights['D'+str(i+1)]}" for i, v in enumerate(dims.values())],
        textposition="auto"
    ))
    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3"),
        xaxis=dict(gridcolor="#30363d", range=[0, 25]),
        yaxis=dict(gridcolor="#30363d", autorange="reversed"),
        height=320,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
section_header("🤖 XGBoost Feature Importance & Model Accuracy")
if (PROC / "xgb_results.png").exists():
    st.image(str(PROC / "xgb_results.png"), use_column_width=True)
else:
    info_box("XGBoost results visualization model png not generated yet.", "info")
