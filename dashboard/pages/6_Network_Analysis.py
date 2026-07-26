"""Page 6 — Network Analysis: Pyvis Crime Linkage Graph & Correlation Heatmap."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from dashboard.components.cards import section_header, info_box

PROC = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

st.markdown("## 🔗 Crime Network & Co-occurrence Graph")
st.markdown("<p style='color:#8b949e;'>NetworkX & Pyvis Graph Analytics for Modus Operandi & Crime Category Linkages</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color:#30363d;'>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🌐 Interactive Pyvis Network Graph", "🔥 Crime Correlation Heatmap"])

with tab1:
    section_header("Crime Co-Occurrence Network Graph", "Nodes represent crime categories, edges show statistical correlation (co-occurrence in districts)")
    net_html = PROC / "crime_network.html"
    if net_html.exists():
        with open(net_html, "r", encoding="utf-8") as f:
            html_data = f.read()
        components.html(html_data, height=650, scrolling=True)
    else:
        info_box("Network graph HTML not found. Run `python pipeline/07_network_builder.py`", "warn")

with tab2:
    section_header("Crime Type Correlation Matrix", "Pairwise Pearson correlation coefficients between crime types")
    corr_img = PROC / "crime_correlation.png"
    if corr_img.exists():
        st.image(str(corr_img), use_container_width=True)
    else:
        info_box("Correlation image not found. Run `python pipeline/07_network_builder.py`", "warn")
