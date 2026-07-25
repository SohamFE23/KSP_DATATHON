"""
PIPELINE STEP 08 - Executive PDF/HTML Report Generator
======================================================
Generates an executive crime intelligence summary report for any district in Karnataka.

Input : data/processed/district_enriched.csv
        data/processed/risk_scores.csv
        data/processed/crime_forecast.csv
        data/processed/anomaly_flagged.csv

Output: reports/<DISTRICT>_crime_report.html & .pdf (if pdfkit/reportlab available)

Usage:
    python pipeline/08_report_generator.py --district BANGALORE_COMMR
    python pipeline/08_report_generator.py --all
"""

import sys
import argparse
import pandas as pd
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
PROC_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT))
from api.engine.risk_engine import compute_risk


def generate_html_report(district: str) -> Path:
    df_path = PROC_DIR / "district_enriched.csv"
    if not df_path.exists():
        df_path = PROC_DIR / "karnataka_clean.csv"

    df = pd.read_csv(df_path, low_memory=False)
    df_d = df[df["DISTRICT"].str.upper() == district.upper()].sort_values("YEAR")

    if df_d.empty:
        print(f"[ERROR] District '{district}' not found.")
        return None

    latest = df_d.iloc[-1]
    risk_res = compute_risk(latest)

    year = int(latest.get("YEAR", 2013))
    total_crimes = int(latest.get("TOTAL_CRIMES", latest.get("TOTAL_IPC_CRIMES", 0)))
    murder = int(latest.get("MURDER", 0))
    rape = int(latest.get("RAPE", 0))
    theft = int(latest.get("THEFT", 0))
    robbery = int(latest.get("ROBBERY", 0))

    dims = risk_res["dimensions"]

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>SurakshaAI Executive Crime Intelligence Report - {district.upper()}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #0d1117;
            color: #e6edf3;
            margin: 0; padding: 30px;
        }}
        .header {{
            border-bottom: 2px solid #30363d;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .title {{ font-size: 28px; font-weight: bold; color: #58a6ff; margin: 0; }}
        .subtitle {{ font-size: 14px; color: #8b949e; margin-top: 5px; }}
        .card-grid {{ display: flex; gap: 15px; margin-bottom: 25px; }}
        .card {{
            flex: 1; background: #161b22; border: 1px solid #30363d;
            border-radius: 8px; padding: 15px; text-align: center;
        }}
        .card-val {{ font-size: 24px; font-weight: bold; margin-top: 5px; color: #e6edf3; }}
        .badge {{
            display: inline-block; padding: 4px 12px; border-radius: 12px;
            font-weight: bold; font-size: 14px;
        }}
        .badge-HIGH {{ background: rgba(248,81,73,0.2); color: #f85149; border: 1px solid #f85149; }}
        .badge-MEDIUM {{ background: rgba(227,179,65,0.2); color: #e3b341; border: 1px solid #e3b341; }}
        .badge-LOW {{ background: rgba(63,185,80,0.2); color: #3fb950; border: 1px solid #3fb950; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 10px; border: 1px solid #30363d; text-align: left; }}
        th {{ background: #161b22; color: #58a6ff; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #8b949e; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🛡️ SurakshaAI Executive Intelligence Report</div>
        <div class="subtitle">Karnataka State Police | SCRB Datathon 2026 | District: <strong>{district.upper()}</strong></div>
    </div>

    <div class="card-grid">
        <div class="card">
            <div style="color:#8b949e;font-size:12px;">RISK SCORE</div>
            <div class="card-val">{risk_res['total_score']} / 100</div>
            <div style="margin-top:8px;"><span class="badge badge-{risk_res['label']}">{risk_res['label']}</span></div>
        </div>
        <div class="card">
            <div style="color:#8b949e;font-size:12px;">TOTAL IPC CRIMES</div>
            <div class="card-val">{total_crimes:,}</div>
            <div style="color:#8b949e;font-size:11px;margin-top:4px;">Year {year}</div>
        </div>
        <div class="card">
            <div style="color:#8b949e;font-size:12px;">VIOLENT CRIMES</div>
            <div class="card-val">{murder + rape + robbery}</div>
            <div style="color:#8b949e;font-size:11px;margin-top:4px;">Murder: {murder} | Rape: {rape}</div>
        </div>
    </div>

    <h3>📊 6-Dimension Composite Risk Assessment</h3>
    <table>
        <tr><th>Dimension</th><th>Score</th><th>Max Weight</th><th>Category Description</th></tr>
        <tr><td>D1 Violent Crime Severity</td><td>{dims['D1_violent_crime']}</td><td>20</td><td>Murder, rape, kidnapping, robbery</td></tr>
        <tr><td>D2 Property & Economic Crime</td><td>{dims['D2_property_crime']}</td><td>20</td><td>Theft, burglary, auto theft, fraud</td></tr>
        <tr><td>D3 Women's Safety</td><td>{dims['D3_women_safety']}</td><td>15</td><td>Dowry deaths, assault, cruelty</td></tr>
        <tr><td>D4 Crime Trend Volatility</td><td>{dims['D4_trend_volatility']}</td><td>15</td><td>Year-over-year delta spike</td></tr>
        <tr><td>D5 Total Crime Volume</td><td>{dims['D5_total_volume']}</td><td>15</td><td>Normalized volume against state peak</td></tr>
        <tr><td>D6 Anomaly & Spike Indicator</td><td>{dims['D6_anomaly_spike']}</td><td>15</td><td>IsolationForest anomaly flag</td></tr>
    </table>

    <h3 style="margin-top:30px;">📋 Actionable Recommendations for Police Administration</h3>
    <ul>
        <li><strong>Patrolling Strategy:</strong> Increase high-visibility night patrolling in high property crime sectors.</li>
        <li><strong>Women Safety Cells:</strong> Strengthen special victim assistance units for violent/domestic crime response.</li>
        <li><strong>Predictive Resource Allocation:</strong> Deploy additional personnel during peak forecasted threat windows.</li>
    </ul>

    <div class="footer">
        Generated automatically by SurakshaAI Intelligence Platform v2.0
    </div>
</body>
</html>"""

    out_file = REPORTS_DIR / f"{district.upper()}_crime_report.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"  [REPORT] Generated HTML Report -> {out_file}")
    return out_file


def main():
    parser = argparse.ArgumentParser(description="SurakshaAI Executive Report Generator")
    parser.add_argument("--district", type=str, default="BANGALORE COMMR.", help="District name")
    parser.add_argument("--all", action="store_true", help="Generate report for all districts")
    args = parser.parse_args()

    df_path = PROC_DIR / "karnataka_clean.csv"
    if not df_path.exists():
        print("[ERROR] karnataka_clean.csv missing.")
        return

    df = pd.read_csv(df_path, low_memory=False)
    districts = sorted(df["DISTRICT"].dropna().unique().tolist())

    if args.all:
        print(f"Generating reports for all {len(districts)} districts...")
        for d in districts:
            generate_html_report(d)
    else:
        generate_html_report(args.district)


if __name__ == "__main__":
    main()
