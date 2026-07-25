"""dashboard/app.py — SurakshaAI main entry point."""
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(
    page_title="SurakshaAI — KSP Crime Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global Dark Theme CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background: #0d1117 !important;
    color: #e6edf3 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d !important;
}
section[data-testid="stSidebar"] * { color: #e6edf3 !important; }

/* Selectbox / inputs */
.stSelectbox > div > div, .stTextInput > div > div {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #161b22; border-bottom: 1px solid #30363d; gap: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #8b949e; border-radius: 6px 6px 0 0; }
.stTabs [aria-selected="true"] { background: #21262d; color: #e6edf3; border-bottom: 2px solid #58a6ff; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: white; border: none; border-radius: 8px;
    padding: 8px 20px; font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(35,134,54,0.4); }

/* Dataframes */
.stDataFrame { border: 1px solid #30363d !important; border-radius: 8px !important; }

/* Sliders */
.stSlider [data-baseweb="slider"] div { background: #58a6ff !important; }

/* Metric */
[data-testid="metric-container"] {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 16px;
}
[data-testid="stMetricValue"] { color: #e6edf3 !important; }
[data-testid="stMetricLabel"] { color: #8b949e !important; }

/* HR */
hr { border-color: #30363d !important; }

/* Expander */
.streamlit-expanderHeader { background: #161b22 !important; border: 1px solid #30363d !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px 0;">
      <div style="font-size:40px;">🛡️</div>
      <div style="color:#e6edf3;font-size:20px;font-weight:700;">SurakshaAI</div>
      <div style="color:#58a6ff;font-size:12px;letter-spacing:2px;">CRIME INTELLIGENCE v2.0</div>
    </div>
    <hr style="border-color:#30363d;margin:10px 0;">
    """, unsafe_allow_html=True)

    st.markdown("### Navigation")
    st.page_link("app.py",                         label="🏠 Home",             icon=None)
    st.page_link("pages/1_Overview.py",             label="📊 Overview",         icon=None)
    st.page_link("pages/2_Hotspot_Map.py",          label="🗺️ Hotspot Maps",     icon=None)
    st.page_link("pages/3_Risk_Predictor.py",       label="⚠️ Risk Predictor",   icon=None)
    st.page_link("pages/4_Crime_Forecast.py",       label="📈 Crime Forecast",   icon=None)
    st.page_link("pages/5_Anomaly_Alerts.py",       label="🔴 Anomaly Alerts",   icon=None)
    st.page_link("pages/6_Network_Analysis.py",     label="🔗 Network Analysis", icon=None)
    st.page_link("pages/7_Raw_Data.py",             label="📋 Raw Data",         icon=None)

    st.markdown("<hr style='border-color:#30363d;margin:16px 0;'>", unsafe_allow_html=True)
    st.caption("Karnataka State Police | SCRB | Datathon 2026")

# ── Home Page ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:60px 0 40px 0;">
  <div style="font-size:64px;margin-bottom:16px;">🛡️</div>
  <h1 style="color:#e6edf3;font-size:42px;font-weight:700;margin:0;">
    SurakshaAI
  </h1>
  <p style="color:#58a6ff;font-size:18px;letter-spacing:3px;margin:8px 0 24px 0;">
    CRIME INTELLIGENCE PLATFORM
  </p>
  <p style="color:#8b949e;font-size:16px;max-width:600px;margin:0 auto;">
    AI-driven crime analytics for Karnataka State Police.<br>
    Predict · Analyze · Prevent
  </p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("""<div style="background:#161b22;border:1px solid #30363d;border-left:4px solid #58a6ff;
        border-radius:10px;padding:20px;text-align:center;">
      <div style="font-size:32px;">🗺️</div>
      <div style="color:#e6edf3;font-weight:700;margin-top:8px;">Interactive Maps</div>
      <div style="color:#8b949e;font-size:13px;">Hotspot clusters & heatmaps</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""<div style="background:#161b22;border:1px solid #30363d;border-left:4px solid #f85149;
        border-radius:10px;padding:20px;text-align:center;">
      <div style="font-size:32px;">🤖</div>
      <div style="color:#e6edf3;font-weight:700;margin-top:8px;">AI Risk Scoring</div>
      <div style="color:#8b949e;font-size:13px;">XGBoost predictions</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown("""<div style="background:#161b22;border:1px solid #30363d;border-left:4px solid #e3b341;
        border-radius:10px;padding:20px;text-align:center;">
      <div style="font-size:32px;">📈</div>
      <div style="color:#e6edf3;font-weight:700;margin-top:8px;">Crime Forecast</div>
      <div style="color:#8b949e;font-size:13px;">3-year projections</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown("""<div style="background:#161b22;border:1px solid #30363d;border-left:4px solid #3fb950;
        border-radius:10px;padding:20px;text-align:center;">
      <div style="font-size:32px;">🔗</div>
      <div style="color:#e6edf3;font-weight:700;margin-top:8px;">Network Analysis</div>
      <div style="color:#8b949e;font-size:13px;">Crime co-occurrence graphs</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 Use the sidebar to navigate to any page, or click the links above.")
