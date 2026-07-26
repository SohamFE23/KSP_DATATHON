"""engine/risk_engine.py — 6-Dimension composite risk formula."""
import pandas as pd
import numpy as np

WEIGHTS = {"D1": 20, "D2": 20, "D3": 15, "D4": 15, "D5": 15, "D6": 15}
RISK_BANDS = {"LOW": (0, 35), "MEDIUM": (35, 60), "HIGH": (60, 100)}

def _safe(val, default=0.0):
    try:
        v = float(val)
        return v if not np.isnan(v) else default
    except Exception:
        return default

def compute_risk(row: pd.Series) -> dict:
    murder   = _safe(row.get("MURDER", 0))
    rape     = _safe(row.get("RAPE", 0))
    kidnap   = _safe(row.get("KIDNAPPING_ABDUCTION", 0))
    dacoity  = _safe(row.get("DACOITY", 0))
    robbery  = _safe(row.get("ROBBERY", 0))
    D1 = min(WEIGHTS["D1"], (murder * 3 + rape * 2 + kidnap + dacoity * 2 + robbery) / 50)

    theft    = _safe(row.get("THEFT", 0))
    burglary = _safe(row.get("BURGLARY", 0))
    auto     = _safe(row.get("AUTO_THEFT", 0))
    cheating = _safe(row.get("CHEATING", 0))
    D2 = min(WEIGHTS["D2"], (theft + burglary * 2 + auto + cheating) / 300)

    dowry    = _safe(row.get("DOWRY_DEATHS", 0))
    assault  = _safe(row.get("ASSAULT_ON_WOMEN_WITH_INTENT_TO_OUTRAGE_HER_MODESTY", 0))
    cruelty  = _safe(row.get("CRUELTY_BY_HUSBAND_OR_HIS_RELATIVES", 0))
    D3 = min(WEIGHTS["D3"], (dowry * 3 + assault + cruelty + rape) / 100)

    yoy = abs(_safe(row.get("CRIME_YOY_CHANGE", 0)))
    D4  = min(WEIGHTS["D4"], yoy / 10)

    total = _safe(row.get("TOTAL_CRIMES", row.get("TOTAL_IPC_CRIMES", 0)))
    D5    = min(WEIGHTS["D5"], total / 2000)

    spike   = _safe(row.get("IS_SPIKE", 0))
    yoy_abs = _safe(row.get("CRIME_YOY_CHANGE", 0))
    D6 = min(WEIGHTS["D6"], spike * 10 + max(0, yoy_abs) / 20)

    score = round(D1 + D2 + D3 + D4 + D5 + D6, 2)

    label = "LOW"
    for band, (lo, hi) in RISK_BANDS.items():
        if lo <= score < hi:
            label = band
            break
    if score >= 60:
        label = "HIGH"

    return {
        "total_score": score,
        "label":       label,
        "dimensions": {
            "D1_violent_crime":     round(D1, 2),
            "D2_property_crime":    round(D2, 2),
            "D3_women_safety":      round(D3, 2),
            "D4_trend_volatility":  round(D4, 2),
            "D5_total_volume":      round(D5, 2),
            "D6_anomaly_spike":     round(D6, 2),
        },
        "weights": WEIGHTS,
    }

def score_all(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for _, row in df.iterrows():
        r = compute_risk(row)
        results.append({
            "DISTRICT":    row.get("DISTRICT", ""),
            "YEAR":        row.get("YEAR", 0),
            "RISK_SCORE":  r["total_score"],
            "RISK_LABEL":  r["label"],
            **r["dimensions"],
        })
    return pd.DataFrame(results)
