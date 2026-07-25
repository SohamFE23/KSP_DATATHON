"""dashboard/components/cards.py — Metric cards and alert cards."""
import streamlit as st

def metric_card(title: str, value, delta=None, icon: str = "", color: str = "#58a6ff"):
    delta_html = ""
    if delta is not None:
        arrow = "▲" if float(str(delta).replace("%","")) > 0 else "▼"
        clr   = "#f85149" if float(str(delta).replace("%","")) > 0 else "#3fb950"
        delta_html = f'<span style="color:{clr};font-size:13px;">{arrow} {delta}</span>'

    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,#161b22,#1c2128);
        border:1px solid #30363d; border-left:4px solid {color};
        border-radius:10px; padding:18px 20px; margin-bottom:8px;
        box-shadow:0 4px 15px rgba(0,0,0,0.3);">
      <div style="color:#8b949e;font-size:12px;letter-spacing:1px;text-transform:uppercase;">{icon} {title}</div>
      <div style="color:#e6edf3;font-size:28px;font-weight:700;margin:6px 0;">{value}</div>
      {delta_html}
    </div>""", unsafe_allow_html=True)


def risk_badge(label: str):
    colors = {"HIGH": "#f85149", "MEDIUM": "#e3b341", "LOW": "#3fb950"}
    bg     = {"HIGH": "rgba(248,81,73,0.15)", "MEDIUM": "rgba(227,179,65,0.15)", "LOW": "rgba(63,185,80,0.15)"}
    c = colors.get(label.upper(), "#8b949e")
    b = bg.get(label.upper(), "rgba(139,148,158,0.15)")
    st.markdown(f"""
    <div style="display:inline-block;background:{b};border:1px solid {c};
        border-radius:20px;padding:5px 18px;color:{c};
        font-weight:700;font-size:16px;letter-spacing:1px;">
      {label.upper()}
    </div>""", unsafe_allow_html=True)


def anomaly_card(district: str, year: int, score: float, severity: str, total: float = 0):
    colors = {"CRITICAL": "#f85149", "HIGH": "#e3b341", "NORMAL": "#3fb950"}
    c = colors.get(severity.upper(), "#8b949e")
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,#161b22,#1c2128);
        border:1px solid {c}44; border-left:4px solid {c};
        border-radius:10px; padding:14px 18px; margin:6px 0;
        box-shadow:0 2px 10px rgba(0,0,0,0.3);">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <span style="color:#e6edf3;font-weight:700;font-size:16px;">{district}</span>
          <span style="color:#8b949e;margin-left:10px;">Year {year}</span>
        </div>
        <span style="background:{c}22;color:{c};border:1px solid {c};
            border-radius:12px;padding:3px 12px;font-size:12px;font-weight:700;">
          {severity}
        </span>
      </div>
      <div style="margin-top:8px;color:#8b949e;font-size:13px;">
        Anomaly Score: <span style="color:{c};font-weight:700;">{score:.3f}</span>
        {"&nbsp;&nbsp;|&nbsp;&nbsp;Crimes: <span style='color:#e6edf3;'>" + f"{int(total):,}" + "</span>" if total else ""}
      </div>
    </div>""", unsafe_allow_html=True)


def trend_badge(trend: str):
    cfg = {
        "INCREASING": ("▲ INCREASING", "#f85149", "rgba(248,81,73,0.15)"),
        "STABLE":     ("→ STABLE",     "#e3b341", "rgba(227,179,65,0.15)"),
        "DECREASING": ("▼ DECREASING", "#3fb950", "rgba(63,185,80,0.15)"),
    }
    label, c, bg = cfg.get(trend.upper(), ("? UNKNOWN", "#8b949e", "rgba(139,148,158,0.1)"))
    st.markdown(f"""
    <span style="background:{bg};border:1px solid {c};border-radius:20px;
        padding:5px 16px;color:{c};font-weight:700;font-size:14px;">
      {label}
    </span>""", unsafe_allow_html=True)


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin:24px 0 16px 0;padding-bottom:12px;border-bottom:1px solid #30363d;">
      <h2 style="color:#e6edf3;margin:0;font-size:22px;">{title}</h2>
      {"<p style='color:#8b949e;margin:4px 0 0 0;font-size:14px;'>" + subtitle + "</p>" if subtitle else ""}
    </div>""", unsafe_allow_html=True)


def info_box(msg: str, kind: str = "info"):
    colors = {"info": "#58a6ff", "warn": "#e3b341", "error": "#f85149", "success": "#3fb950"}
    icons  = {"info": "ℹ️", "warn": "⚠️", "error": "❌", "success": "✅"}
    c = colors.get(kind, "#58a6ff")
    i = icons.get(kind, "ℹ️")
    st.markdown(f"""
    <div style="background:{c}11;border:1px solid {c}44;border-radius:8px;
        padding:12px 16px;color:{c};font-size:14px;margin:8px 0;">
      {i} {msg}
    </div>""", unsafe_allow_html=True)
