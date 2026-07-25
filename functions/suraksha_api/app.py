"""api/app.py — SurakshaAI Flask REST API (10 endpoints)"""
import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.engine.loader import (
    get_district_data, get_risk_scores, get_forecast,
    get_anomalies, get_hotspots, get_network_json,
    get_districts, get_years, filter_district,
    get_socioeconomic, get_murder_motive, get_recidivism,
)
from api.engine.risk_engine import compute_risk, score_all

app = Flask(__name__)
CORS(app)


def ok(data): return jsonify({"status": "ok", "data": data})
def err(msg, code=400): return jsonify({"status": "error", "message": msg}), code


# ── 1. Health Check & Root ──────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return hello()

@app.route("/hello", methods=["GET"])
def hello():
    return ok({
        "name":      "SurakshaAI Crime Intelligence API",
        "version":   "2.0.0",
        "districts": get_districts()[:5],
        "years":     get_years()[-3:],
        "endpoints": [
            "/hello", "/districts", "/risk/<district>",
            "/trends/<district>", "/breakdown/<district>",
            "/top-risky", "/compare", "/hotspots",
            "/network", "/forecast/<district>",
            "/anomalies", "/socioeconomic/<district>",
        ]
    })


# ── 2. List Districts ──────────────────────────────────────────────────────────
@app.route("/districts", methods=["GET"])
def districts():
    return ok({"districts": get_districts(), "years": get_years()})


# ── 3. Risk Score for District ─────────────────────────────────────────────────
@app.route("/risk/<district>", methods=["GET"])
def risk(district):
    year = request.args.get("year", type=int)
    df   = filter_district(district, year)
    if df.empty:
        return err(f"District '{district}' not found. Try /districts for valid names.", 404)

    # Use latest year if not specified
    row    = df.sort_values("YEAR").iloc[-1]
    result = compute_risk(row)
    result["district"] = row.get("DISTRICT", district)
    result["year"]     = int(row.get("YEAR", 0))
    return ok(result)


# ── 4. Trends for District (year-by-year) ─────────────────────────────────────
@app.route("/trends/<district>", methods=["GET"])
def trends(district):
    df = filter_district(district)
    if df.empty:
        return err(f"District '{district}' not found.", 404)

    df   = df.sort_values("YEAR")
    rows = []
    for _, row in df.iterrows():
        r = compute_risk(row)
        rows.append({
            "year":  int(row["YEAR"]),
            "score": r["total_score"],
            "label": r["label"],
            **r["dimensions"],
            "total_crimes": float(row.get("TOTAL_CRIMES", row.get("TOTAL_IPC_CRIMES", 0)) or 0),
            "murder":  float(row.get("MURDER", 0) or 0),
            "rape":    float(row.get("RAPE", 0) or 0),
            "yoy":     float(row.get("CRIME_YOY_CHANGE", 0) or 0),
        })
    return ok({"district": district.upper(), "trends": rows})


# ── 5. Crime Type Breakdown ────────────────────────────────────────────────────
@app.route("/breakdown/<district>", methods=["GET"])
def breakdown(district):
    year = request.args.get("year", type=int)
    df   = filter_district(district, year)
    if df.empty:
        return err(f"District '{district}' not found.", 404)

    row  = df.sort_values("YEAR").iloc[-1]
    CRIME_COLS = [
        "MURDER", "RAPE", "KIDNAPPING_ABDUCTION", "DACOITY", "ROBBERY",
        "BURGLARY", "THEFT", "AUTO_THEFT", "CHEATING", "ARSON",
        "DOWRY_DEATHS", "ASSAULT_ON_WOMEN_WITH_INTENT_TO_OUTRAGE_HER_MODESTY",
        "CRUELTY_BY_HUSBAND_OR_HIS_RELATIVES", "RIOTS", "CRIMINAL_BREACH_OF_TRUST",
        "CAUSING_DEATH_BY_NEGLIGENCE", "COUNTERFIETING", "HURT_GREVIOUS_HURT",
    ]
    data = {c: float(row.get(c, 0) or 0) for c in CRIME_COLS if c in row.index}
    return ok({
        "district": row.get("DISTRICT", district),
        "year":     int(row.get("YEAR", 0)),
        "crimes":   dict(sorted(data.items(), key=lambda x: -x[1])),
        "total":    float(row.get("TOTAL_CRIMES", row.get("TOTAL_IPC_CRIMES", 0)) or 0),
    })


# ── 6. Top Risky Districts ─────────────────────────────────────────────────────
@app.route("/top-risky", methods=["GET"])
def top_risky():
    limit = request.args.get("limit", 10, type=int)
    year  = request.args.get("year", type=int)

    df = get_district_data()
    if df.empty:
        return err("No data available.", 500)

    if year:
        df = df[df["YEAR"] == year]
    else:
        df = df.sort_values("YEAR").groupby("DISTRICT").last().reset_index()

    scored = score_all(df)
    top    = scored.nlargest(limit, "RISK_SCORE")

    return ok({
        "year":      year or "latest",
        "top_risky": top[["DISTRICT","YEAR","RISK_SCORE","RISK_LABEL",
                           "D1_violent_crime","D2_property_crime","D3_women_safety"]].to_dict(orient="records")
    })


# ── 7. Compare Districts ───────────────────────────────────────────────────────
@app.route("/compare", methods=["GET"])
def compare():
    dists_raw = request.args.get("districts", "")
    dists = [d.strip().upper() for d in dists_raw.split(",") if d.strip()]
    if len(dists) < 2:
        return err("Provide at least 2 districts: /compare?districts=BAGALKOT,BELGAUM")

    year = request.args.get("year", type=int)
    results = []
    for dist in dists:
        df_d = filter_district(dist, year)
        if df_d.empty:
            results.append({"district": dist, "error": "not found"})
            continue
        row = df_d.sort_values("YEAR").iloc[-1]
        r   = compute_risk(row)
        results.append({
            "district": row.get("DISTRICT", dist),
            "year":     int(row.get("YEAR", 0)),
            **r,
        })
    return ok({"comparison": results})


# ── 8. Hotspot Clusters ────────────────────────────────────────────────────────
@app.route("/hotspots", methods=["GET"])
def hotspots():
    df = get_hotspots()
    if df.empty:
        df = get_district_data()
        df = df.sort_values("YEAR").groupby("DISTRICT").last().reset_index()

    cols = ["DISTRICT", "LAT", "LON", "CLUSTER", "TOTAL_CRIMES",
            "PREDICTED_RISK_LABEL", "RISK_LABEL"]
    out_cols = [c for c in cols if c in df.columns]
    data = df[out_cols].fillna(0).to_dict(orient="records")
    return ok({"hotspots": data, "count": len(data)})


# ── 9. Crime Network Graph ─────────────────────────────────────────────────────
@app.route("/network", methods=["GET"])
def network():
    graph = get_network_json()
    if not graph:
        return err("Network graph not yet built. Run pipeline/07_network_builder.py", 503)
    return ok(graph)


# ── 10. Crime Forecast ────────────────────────────────────────────────────────
@app.route("/forecast/<district>", methods=["GET"])
def forecast(district):
    df = get_forecast()
    if df.empty:
        return err("Forecast not available. Run pipeline/05_time_series_forecast.py", 503)

    df_d = df[df["DISTRICT"].str.upper() == district.upper()]
    if df_d.empty:
        avail = sorted(df["DISTRICT"].unique().tolist())
        return err(f"District '{district}' not in forecast. Available: {avail[:5]}...", 404)

    rows = df_d[["year","yhat","yhat_lower","yhat_upper","is_forecast","TREND"]].to_dict(orient="records")
    trend = str(df_d[df_d["is_forecast"]]["TREND"].iloc[0]) if len(df_d[df_d["is_forecast"]]) else "STABLE"
    return ok({"district": district.upper(), "forecast": rows, "trend": trend})


# ── 11. Anomaly Alerts ────────────────────────────────────────────────────────
@app.route("/anomalies", methods=["GET"])
def anomalies():
    df = get_anomalies()
    if df.empty:
        return err("Anomaly data not available. Run pipeline/06_anomaly_detection.py", 503)

    district = request.args.get("district", "")
    severity = request.args.get("severity", "")

    if district:
        df = df[df["DISTRICT"].str.upper() == district.upper()]
    if severity:
        df = df[df["ANOMALY_SEVERITY"].str.upper() == severity.upper()]

    anomaly_df = df[df["IS_ANOMALY"] == 1] if "IS_ANOMALY" in df.columns else df
    cols = ["DISTRICT","YEAR","ANOMALY_SCORE","ANOMALY_SEVERITY","TOTAL_CRIMES","PREDICTED_RISK_LABEL"]
    out_cols = [c for c in cols if c in anomaly_df.columns]
    data = anomaly_df[out_cols].sort_values("ANOMALY_SCORE", ascending=False).head(50).to_dict(orient="records")
    return ok({"anomalies": data, "total_flagged": len(anomaly_df), "count_returned": len(data)})


# ── 12. Socio-Economic Data ────────────────────────────────────────────────────
@app.route("/socioeconomic", methods=["GET"])
@app.route("/socioeconomic/<district>", methods=["GET"])
def socioeconomic(district=None):
    df = get_socioeconomic()
    if df.empty:
        return err("Socio-economic data not available. Run pipeline/00b_enrich_census.py", 503)
    if district:
        df = df[df["DISTRICT"].str.upper() == district.upper()]
    return ok(df.fillna(0).to_dict(orient="records"))


# ── 13. Murder Motives ────────────────────────────────────────────────────────
@app.route("/murder-motives", methods=["GET"])
def murder_motives():
    df = get_murder_motive()
    if df.empty:
        return err("Murder motive data not available.", 503)
    return ok(df.fillna(0).to_dict(orient="records"))


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n  SurakshaAI API starting on http://127.0.0.1:5000")
    print("  Try: http://127.0.0.1:5000/hello\n")
    app.run(debug=True, port=5000, host="0.0.0.0")
