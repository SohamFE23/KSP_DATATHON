"""Page 1 — Overview: KPI cards, trends, top districts, risk distribution."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.components.cards import metric_card, section_header, risk_badge

PROC = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

@st.cache_data
def load():
    df = pd.read_csv(PROC / "karnataka_clean.csv", low_memory=False)
    rs = pd.read_csv(PROC / "risk_scores.csv",     low_memory=False)
    an = pd.read_csv(PROC / "anomaly_flagged.csv", low_memory=False)
    return df, rs, an

DARK = {
    "paper_bgcolor": "#0d1117",
    "plot_bgcolor": "#161b22",
    "font": {"color": "#e6edf3"},
    "xaxis": {"gridcolor": "#30363d", "color": "#8b949e"},
    "yaxis": {"gridcolor": "#30363d", "color": "#8b949e"}
}

st.markdown("## 📊 Overview Dashboard")
st.markdown("<hr style='border-color:#30363d;'>", unsafe_allow_html=True)

try:
    df, rs, an = load()
except Exception as e:
    st.error(f"Data load failed: {e}")
    st.stop()

# ── KPI Row ────────────────────────────────────────────────────────────────────
total_crimes  = int(df["TOTAL_CRIMES"].sum() if "TOTAL_CRIMES" in df else 0)
districts_n   = df["DISTRICT"].nunique()
years_n       = df["YEAR"].nunique()
high_risk_n   = int((rs["PREDICTED_RISK_LABEL"] == "HIGH").sum()) if "PREDICTED_RISK_LABEL" in rs.columns else 0
anomaly_n     = int(an["IS_ANOMALY"].sum()) if "IS_ANOMALY" in an.columns else 0

c1,c2,c3,c4,c5 = st.columns(5)
with c1: metric_card("Total Crimes", f"{total_crimes:,}", icon="🔴", color="#f85149")
with c2: metric_card("Districts",    districts_n,          icon="🗺️", color="#58a6ff")
with c3: metric_card("Years of Data",years_n,              icon="📅", color="#8b949e")
with c4: metric_card("High-Risk Rows",high_risk_n,         icon="⚠️", color="#e3b341")
with c5: metric_card("Anomalies",    anomaly_n,            icon="🔍", color="#bc8cff")

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Crime Trend + Top Districts ────────────────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    section_header("Crime Trend Over Years", "Total IPC crimes across all Karnataka districts")
    yt = df.groupby("YEAR")["TOTAL_CRIMES"].sum().reset_index() if "TOTAL_CRIMES" in df else pd.DataFrame()
    if not yt.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=yt["YEAR"], y=yt["TOTAL_CRIMES"],
            mode="lines+markers",
            line=dict(color="#58a6ff", width=3),
            marker=dict(size=7, color="#58a6ff"),
            fill="tozeroy", fillcolor="rgba(88,166,255,0.1)",
            name="Total Crimes",
        ))
        fig.update_layout(
            paper_bgcolor="#0d1117",
            plot_bgcolor="#161b22",
            font=dict(color="#e6edf3"),
            xaxis=dict(gridcolor="#30363d", color="#8b949e"),
            yaxis=dict(gridcolor="#30363d", color="#8b949e"),
            height=300,
            margin=dict(l=10,r=10,t=10,b=10),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    section_header("Top 10 Districts", "By total crime volume (all years)")
    crime_col = "TOTAL_CRIMES" if "TOTAL_CRIMES" in df.columns else None
    if crime_col:
        top10 = df.groupby("DISTRICT")[crime_col].sum().nlargest(10).reset_index()
        fig2 = go.Figure(go.Bar(
            x=top10[crime_col], y=top10["DISTRICT"],
            orientation="h",
            marker_color=[f"hsl({220-i*15},70%,55%)" for i in range(10)],
        ))
        fig2.update_layout(
            paper_bgcolor="#0d1117",
            plot_bgcolor="#161b22",
            font=dict(color="#e6edf3"),
            xaxis=dict(gridcolor="#30363d", color="#8b949e"),
            yaxis=dict(gridcolor="#30363d", color="#8b949e", autorange="reversed"),
            height=300,
            margin=dict(l=10,r=10,t=10,b=10),
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Risk Distribution + Crime Category Mix ──────────────────────────────
col3, col4 = st.columns([1, 2])

with col3:
    section_header("Risk Distribution")
    risk_col = "PREDICTED_RISK_LABEL" if "PREDICTED_RISK_LABEL" in rs.columns else "RISK_LABEL"
    if risk_col in rs.columns:
        dist = rs[risk_col].value_counts().reset_index()
        dist.columns = ["Risk", "Count"]
        fig3 = go.Figure(go.Pie(
            labels=dist["Risk"], values=dist["Count"],
            hole=0.55,
            marker_colors=["#f85149","#e3b341","#3fb950"],
        ))
        fig3.update_layout(
            paper_bgcolor="#0d1117",
            plot_bgcolor="#161b22",
            font=dict(color="#e6edf3"),
            height=280,
            margin=dict(l=10,r=10,t=10,b=10),
            showlegend=True,
            legend=dict(bgcolor="#161b22", bordercolor="#30363d")
        )
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    section_header("Crime Category Breakdown", "Summed across all districts & years")
    CATS = {"MURDER":"#f85149","RAPE":"#ff7b72","KIDNAPPING_ABDUCTION":"#ffa657",
            "DACOITY":"#e3b341","ROBBERY":"#d2a8ff","BURGLARY":"#79c0ff",
            "THEFT":"#58a6ff","AUTO_THEFT":"#3fb950","DOWRY_DEATHS":"#bc8cff",
            "RIOTS":"#8b949e","CHEATING":"#39d353","ARSON":"#f0883e"}
    totals = {k: float(df[k].sum()) for k in CATS if k in df.columns}
    totals = dict(sorted(totals.items(), key=lambda x: -x[1]))
    fig4 = go.Figure(go.Bar(
        x=list(totals.keys()), y=list(totals.values()),
        marker_color=list(CATS.values())[:len(totals)],
    ))
    fig4.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3"),
        xaxis=dict(gridcolor="#30363d", color="#8b949e", tickangle=-35, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#30363d", color="#8b949e"),
        height=280,
        margin=dict(l=10,r=10,t=10,b=10),
        showlegend=False
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: YoY Spike Map ──────────────────────────────────────────────────────
section_header("Year-over-Year Crime Change by District", "Percentage change from previous year")
if "CRIME_YOY_CHANGE" in df.columns and "LAT" in df.columns:
    latest = df.sort_values("YEAR").groupby("DISTRICT").last().reset_index()
    fig5 = px.scatter(
        latest, x="LON", y="LAT",
        size=latest["TOTAL_CRIMES"].clip(100, None) if "TOTAL_CRIMES" in latest.columns else None,
        color="CRIME_YOY_CHANGE",
        color_continuous_scale=["#3fb950","#e3b341","#f85149"],
        hover_name="DISTRICT",
        text="DISTRICT",
        size_max=35,
    )
    fig5.update_traces(textposition="top center", textfont=dict(size=9, color="#e6edf3"))
    fig5.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3"),
        xaxis=dict(gridcolor="#30363d", color="#8b949e"),
        yaxis=dict(gridcolor="#30363d", color="#8b949e"),
        height=420,
        coloraxis_colorbar=dict(title="YoY %"),
        margin=dict(l=10,r=10,t=10,b=10)
    )
    st.plotly_chart(fig5, use_container_width=True)
