"""Page 4 — Crime Forecast: Prophet Time-Series & Emerging Threats."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dashboard.components.cards import section_header, metric_card, trend_badge, info_box

PROC = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

st.markdown("## 📈 Time Series Crime Forecasting")
st.markdown("<p style='color:#8b949e;'>Prophet & Linear Trend Extrapolation for Emerging Crime Threat Detection</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color:#30363d;'>", unsafe_allow_html=True)

@st.cache_data
def load_forecast():
    if (PROC / "crime_forecast.csv").exists():
        return pd.read_csv(PROC / "crime_forecast.csv")
    return pd.DataFrame()

df_forecast = load_forecast()

if df_forecast.empty:
    info_box("Forecast data unavailable. Run `python pipeline/05_time_series_forecast.py`", "error")
    st.stop()

districts = sorted(df_forecast["DISTRICT"].dropna().unique().tolist())

col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### 🎯 Select District")
    selected_dist = st.selectbox("District", districts)
    
    df_d = df_forecast[df_forecast["DISTRICT"] == selected_dist].sort_values("year")
    trend = df_d["TREND"].iloc[-1] if "TREND" in df_d.columns else "STABLE"
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🚦 Trend Status")
    trend_badge(trend)

with col2:
    section_header(f"Crime Forecast Projection: {selected_dist}", "Historical data + 3-year projection with confidence bands")
    
    fig = go.Figure()
    
    hist_df = df_d[df_d["is_forecast"] == False]
    fc_df   = df_d[df_d["is_forecast"] == True]
    
    # Upper & Lower confidence bands
    if "yhat_upper" in df_d.columns and "yhat_lower" in df_d.columns:
        fig.add_trace(go.Scatter(
            x=list(df_d["year"]) + list(df_d["year"])[::-1],
            y=list(df_d["yhat_upper"]) + list(df_d["yhat_lower"])[::-1],
            fill='toself',
            fillcolor='rgba(88,166,255,0.15)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=False,
            name="Confidence Interval"
        ))

    # Historical
    fig.add_trace(go.Scatter(
        x=hist_df["year"], y=hist_df["yhat"],
        mode="lines+markers",
        name="Historical",
        line=dict(color="#58a6ff", width=3),
        marker=dict(size=7)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=fc_df["year"], y=fc_df["yhat"],
        mode="lines+markers",
        name="Forecast",
        line=dict(color="#f85149", width=3, dash="dash"),
        marker=dict(size=8, symbol="diamond")
    ))

    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3"),
        xaxis=dict(gridcolor="#30363d"),
        yaxis=dict(gridcolor="#30363d"),
        height=380,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
section_header("🚨 Top Emerging Threat Districts")
if (PROC / "forecast_top5_districts.png").exists():
    st.image(str(PROC / "forecast_top5_districts.png"), use_container_width=True)
