"""Download supplementary datasets for SurakshaAI v2"""
import urllib.request
import json
import os
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW  = ROOT / "data" / "raw"

# ── 1. Karnataka GeoJSON (district boundaries) ────────────────────────────────
GEOJSON_URLS = [
    "https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/INDIAN_STATES/KARNATAKA/KARNATAKA_DISTRICTS.json",
    "https://raw.githubusercontent.com/udit-001/india-maps-data/main/data/states/karnataka/karnataka-districts.geojson",
    "https://raw.githubusercontent.com/adarshbiradar/maps-geojson/master/states/karnataka.json",
    "https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/karnataka",
]

print("\n=== Downloading Karnataka GeoJSON ===")
geojson_saved = False
for url in GEOJSON_URLS:
    try:
        out = RAW / "karnataka_districts.geojson"
        urllib.request.urlretrieve(url, out)
        with open(out) as f:
            g = json.load(f)
        feats = g.get("features", [])
        if feats:
            props = list(feats[0]["properties"].keys())
            print(f"  [OK] {len(feats)} district features")
            print(f"  Properties: {props}")
            geojson_saved = True
            break
        else:
            print(f"  [EMPTY] {url}")
    except Exception as e:
        print(f"  [FAIL] {url}: {e}")

if not geojson_saved:
    print("  [SKIP] All GeoJSON sources failed - creating fallback")


# ── 2. Census 2011 India District Data ────────────────────────────────────────
CENSUS_URLS = [
    "https://raw.githubusercontent.com/nishusharma1608/India-Census-2011-Analysis/master/india-districts-census-2011.csv",
    "https://raw.githubusercontent.com/rushilleo1998/India-Census-2011/main/india_census_2011.csv",
]

print("\n=== Downloading Census 2011 District Data ===")
census_saved = False
for url in CENSUS_URLS:
    try:
        out = RAW / "india_census_2011.csv"
        urllib.request.urlretrieve(url, out)
        df = pd.read_csv(out, nrows=5, encoding="latin-1")
        print(f"  [OK] {df.shape[1]} columns: {list(df.columns[:8])}")
        census_saved = True
        break
    except Exception as e:
        print(f"  [FAIL] {url}: {e}")

print(f"  Census data: {'SAVED' if census_saved else 'FAILED'}")


# ── 3. NCRB 2016-2020 (newer crime data) ─────────────────────────────────────
NCRB_NEWER_URLS = [
    "https://raw.githubusercontent.com/Robbinton/india-crime-data/main/district_wise_crime_2019.csv",
    "https://raw.githubusercontent.com/datasets/crime-in-india/main/data/crime-2019.csv",
]

print("\n=== Downloading Newer NCRB Crime Data ===")
for url in NCRB_NEWER_URLS:
    try:
        fname = url.split("/")[-1]
        out = RAW / fname
        urllib.request.urlretrieve(url, out)
        df = pd.read_csv(out, nrows=3, encoding="latin-1")
        print(f"  [OK] {fname}: {df.shape[1]} cols - {list(df.columns[:6])}")
    except Exception as e:
        print(f"  [FAIL] {url}: {e}")

print("\n=== Download Complete ===")
print(f"Files in data/raw/: {[f.name for f in RAW.glob('*.geojson') ] + [f.name for f in RAW.glob('*.csv') if 'census' in f.name.lower() or '2019' in f.name or '2020' in f.name]}")
