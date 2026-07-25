"""api/engine/loader.py — Load all processed CSVs once at startup."""
import pandas as pd
import pickle
from pathlib import Path
from functools import lru_cache

BASE = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

def _read(fname, **kw):
    p = BASE / fname
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, low_memory=False, **kw)

@lru_cache(maxsize=1)
def get_district_data():
    return _read("karnataka_clean.csv")

@lru_cache(maxsize=1)
def get_risk_scores():
    return _read("risk_scores.csv")

@lru_cache(maxsize=1)
def get_forecast():
    return _read("crime_forecast.csv")

@lru_cache(maxsize=1)
def get_anomalies():
    return _read("anomaly_flagged.csv")

@lru_cache(maxsize=1)
def get_hotspots():
    return _read("hotspot_clusters.csv")

@lru_cache(maxsize=1)
def get_state_features():
    return _read("master_features.csv")

@lru_cache(maxsize=1)
def get_socioeconomic():
    return _read("karnataka_socioeconomic.csv")

@lru_cache(maxsize=1)
def get_women_crimes():
    return _read("district_women_crimes.csv")

@lru_cache(maxsize=1)
def get_murder_motive():
    return _read("murder_motive.csv")

@lru_cache(maxsize=1)
def get_recidivism():
    return _read("recidivism.csv")

@lru_cache(maxsize=1)
def get_network_json():
    import json
    p = BASE / "crime_network_data.json"
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)

@lru_cache(maxsize=1)
def get_xgb_model():
    p = BASE / "xgb_risk_model.pkl"
    if not p.exists():
        return None
    with open(p, "rb") as f:
        return pickle.load(f)

def get_districts():
    df = get_district_data()
    if df.empty:
        return []
    return sorted(df["DISTRICT"].dropna().unique().tolist())

def get_years():
    df = get_district_data()
    if df.empty:
        return []
    return sorted(df["YEAR"].dropna().unique().tolist())

def filter_district(district: str = None, year: int = None) -> pd.DataFrame:
    df = get_district_data()
    if df.empty:
        return df
    if district:
        df = df[df["DISTRICT"].str.upper() == district.upper()]
    if year:
        df = df[df["YEAR"] == int(year)]
    return df
