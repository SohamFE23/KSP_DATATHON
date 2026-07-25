"""
PIPELINE STEP 00b - Enrich Districts with Census 2011 Socio-Economic Data
==========================================================================
Input : data/raw/india_census_2011.csv        (640 rows, 118 cols - all India)
        data/raw/karnataka_districts.geojson   (30 Karnataka district boundaries)
        data/processed/district_features.csv  (our crime data)

Output: data/processed/karnataka_socioeconomic.csv  (Census 2011 Karnataka data)
        data/processed/district_enriched.csv        (crime + census merged)
        data/processed/karnataka_districts.geojson  (cleaned GeoJSON copy)

Run:
    python pipeline/00b_enrich_census.py
"""

import pandas as pd
import numpy as np
import json
import re
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
RAW_DIR  = ROOT / "data" / "raw"
PROC_DIR = ROOT / "data" / "processed"
PROC_DIR.mkdir(exist_ok=True)

# ── District Name Mapping (Census names -> our NCRB names) ──────────────────
# Census 2011 uses different spellings than NCRB data
NAME_MAP = {
    "Belgaum":          "BELGAUM",
    "Bagalkot":         "BAGALKOT",
    "Bijapur":          "BIJAPUR",
    "Bidar":            "BIDAR",
    "Raichur":          "RAICHUR",
    "Koppal":           "KOPPAL",
    "Gadag":            "GADAG",
    "Dharwad":          "DHARWAD",
    "Uttara Kannada":   "UTTARA KANNADA",
    "Haveri":           "HAVERI",
    "Belagavi":         "BELGAUM",
    "Bagalkote":        "BAGALKOT",
    "Vijayapura":       "BIJAPUR",
    "Kalaburagi":       "GULBARGA",
    "Yadgir":           "YADGIR",
    "Mysore":           "MYSORE",
    "Mysuru":           "MYSORE",
    "Mandya":           "MANDYA",
    "Hassan":           "HASSAN",
    "Chikmagalur":      "CHIKMAGALUR",
    "Kodagu":           "KODAGU",
    "Dakshina Kannada": "DAKSHINA KANNADA",
    "Udupi":            "UDUPI",
    "Shimoga":          "SHIMOGA",
    "Shivamogga":       "SHIMOGA",
    "Tumkur":           "TUMKUR",
    "Tumakuru":         "TUMKUR",
    "Chitradurga":      "CHITRADURGA",
    "Davanagere":       "DAVANAGERE",
    "Davangere":        "DAVANAGERE",
    "Bellary":          "BELLARY",
    "Ballari":          "BELLARY",
    "Chamarajanagar":   "CHAMARAJNAGAR",
    "Chamarajnagar":    "CHAMARAJNAGAR",
    "Bangalore Urban":  "BANGALORE RURAL",    # closest match
    "Bangalore Rural":  "BANGALORE RURAL",
    "Chikkaballapur":   "CHIKKABALLAPURA",
    "Chikballapur":     "CHIKKABALLAPURA",
    "Kolar":            "KOLAR",
    "Ramanagara":       "RAMANAGARA",
    "Bangalore":        "BANGALORE RURAL",
}

# ── Census columns to extract ────────────────────────────────────────────────
CENSUS_COLS = {
    "Population":              "POPULATION",
    "Male":                    "POP_MALE",
    "Female":                  "POP_FEMALE",
    "Literate":                "LITERATE",
    "Male_Literate":           "LITERATE_MALE",
    "Female_Literate":         "LITERATE_FEMALE",
    "SC":                      "POP_SC",
    "ST":                      "POP_ST",
    "Workers":                 "WORKERS_TOTAL",
    "Non_Workers":             "NON_WORKERS",
    "Urban_population":        "POP_URBAN",
    "Rural_population":        "POP_RURAL",
}


def normalize_name(name: str) -> str:
    """Normalize district names for fuzzy matching."""
    return re.sub(r"[^a-z]", "", name.lower().strip())


def load_census() -> pd.DataFrame:
    p = RAW_DIR / "india_census_2011.csv"
    if not p.exists():
        raise FileNotFoundError(f"Run pipeline/00_download_datasets.py first. Missing: {p}")
    df = pd.read_csv(p, encoding="latin-1", low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]
    # Filter Karnataka
    karn = df[df["State name"].str.strip().str.upper().str.contains("KARNATAKA", na=False)].copy()
    print(f"  [CENSUS] Karnataka rows: {len(karn)}")
    return karn


def build_karnataka_socioeconomic(census_df: pd.DataFrame) -> pd.DataFrame:
    """Extract and compute key socio-economic indicators."""
    rows = []
    for _, row in census_df.iterrows():
        dist_raw = str(row.get("District name", "")).strip()

        # Map to NCRB name
        ncrb_name = NAME_MAP.get(dist_raw)
        if not ncrb_name:
            # Fuzzy match
            raw_norm = normalize_name(dist_raw)
            for k, v in NAME_MAP.items():
                if normalize_name(k) == raw_norm:
                    ncrb_name = v
                    break
            if not ncrb_name:
                ncrb_name = dist_raw.upper()

        pop    = pd.to_numeric(row.get("Population", 0), errors="coerce") or 1
        lit    = pd.to_numeric(row.get("Literate", 0), errors="coerce") or 0
        male   = pd.to_numeric(row.get("Male", 0), errors="coerce") or 0
        female = pd.to_numeric(row.get("Female", 0), errors="coerce") or 0
        sc     = pd.to_numeric(row.get("SC", 0), errors="coerce") or 0
        st     = pd.to_numeric(row.get("ST", 0), errors="coerce") or 0
        urban  = pd.to_numeric(row.get("Urban_population", 0), errors="coerce") or 0
        rural  = pd.to_numeric(row.get("Rural_population", 0), errors="coerce") or 0
        wrkrs  = pd.to_numeric(row.get("Workers", 0), errors="coerce") or 0

        rec = {
            "DISTRICT_CENSUS": dist_raw,
            "DISTRICT":        ncrb_name,
            # Raw counts
            "POPULATION":        int(pop),
            "POP_MALE":          int(male),
            "POP_FEMALE":        int(female),
            "POP_URBAN":         int(urban),
            "POP_RURAL":         int(rural),
            "POP_SC":            int(sc),
            "POP_ST":            int(st),
            "LITERATE":          int(lit),
            "WORKERS_TOTAL":     int(wrkrs),
            # Derived rates (%)
            "LITERACY_RATE":         round(lit / pop * 100, 2),
            "SEX_RATIO":             round(female / male * 1000, 1) if male > 0 else 0,
            "URBANIZATION_RATE":     round(urban / pop * 100, 2),
            "SC_PERCENTAGE":         round(sc / pop * 100, 2),
            "ST_PERCENTAGE":         round(st / pop * 100, 2),
            "WORKER_PARTICIPATION":  round(wrkrs / pop * 100, 2),
            # Vulnerability index (lower literacy + lower urbanization + higher SC/ST = more vulnerable)
            "VULNERABILITY_INDEX":   round(
                (100 - lit / pop * 100) * 0.4 +
                (100 - urban / pop * 100) * 0.3 +
                ((sc + st) / pop * 100) * 0.3,
                2
            ),
        }
        rows.append(rec)

    return pd.DataFrame(rows)


def enrich_crime_data(socio_df: pd.DataFrame) -> pd.DataFrame:
    """Merge Census socio-economic data with district crime features."""
    crime_p = PROC_DIR / "district_features.csv"
    if not crime_p.exists():
        print("  [SKIP] district_features.csv not found - run pipeline steps 01-02 first")
        return pd.DataFrame()

    crime_df = pd.read_csv(crime_p, low_memory=False)

    # Normalize district names for merge
    crime_df["DISTRICT_NORM"] = crime_df["DISTRICT"].str.strip().str.upper()
    socio_df["DISTRICT_NORM"] = socio_df["DISTRICT"].str.strip().str.upper()

    merged = pd.merge(
        crime_df,
        socio_df.drop(columns=["DISTRICT_CENSUS"], errors="ignore"),
        on="DISTRICT_NORM",
        how="left",
        suffixes=("", "_CENSUS"),
    )

    # Per-capita crime rates (crimes per 1 lakh population)
    if "POPULATION" in merged.columns:
        pop = merged["POPULATION"].replace(0, np.nan)
        crime_cols_to_normalize = [
            "MURDER", "RAPE", "KIDNAPPING_ABDUCTION", "TOTAL_CRIMES",
            "THEFT", "BURGLARY", "DOWRY_DEATHS", "VIOLENT_CRIME_INDEX",
            "WOMEN_CRIME_INDEX", "PROPERTY_CRIME_INDEX",
        ]
        for col in crime_cols_to_normalize:
            if col in merged.columns:
                merged[f"{col}_PER_LAKH"] = (
                    merged[col] / pop * 100000
                ).round(2)
        print(f"  [ENRICHED] Added per-capita rates for {len(crime_cols_to_normalize)} crime types")

    matched = merged["POPULATION"].notna().sum()
    total   = len(merged)
    print(f"  [MERGE] {matched}/{total} district-year rows matched with Census data")

    return merged


def copy_geojson():
    """Copy and validate GeoJSON to processed folder."""
    src = RAW_DIR / "karnataka_districts.geojson"
    dst = PROC_DIR / "karnataka_districts.geojson"
    if not src.exists():
        print("  [SKIP] GeoJSON not found")
        return
    with open(src) as f:
        g = json.load(f)

    # Normalize district names in GeoJSON properties for dashboard use
    for feat in g["features"]:
        props = feat["properties"]
        raw_name = props.get("district", props.get("DISTRICT", ""))
        props["DISTRICT_NCRB"] = NAME_MAP.get(raw_name, raw_name.upper())
        props["district_display"] = raw_name

    with open(dst, "w") as f:
        json.dump(g, f)
    print(f"  [GEOJSON] {len(g['features'])} district boundaries saved to processed/")


def main():
    print("\n" + "="*60)
    print("  STEP 00b - Census 2011 Socio-Economic Enrichment")
    print("="*60)

    # 1. Load and build Karnataka socioeconomic dataset
    census_raw = load_census()
    socio_df   = build_karnataka_socioeconomic(census_raw)
    print(f"  [SOCIO] {len(socio_df)} districts | Columns: {list(socio_df.columns)}")

    # 2. Save standalone socioeconomic CSV
    out_socio = PROC_DIR / "karnataka_socioeconomic.csv"
    socio_df.to_csv(out_socio, index=False)
    print(f"  [OUT] {out_socio}")

    # 3. Merge with crime data
    enriched = enrich_crime_data(socio_df)
    if not enriched.empty:
        out_enriched = PROC_DIR / "district_enriched.csv"
        enriched.to_csv(out_enriched, index=False)
        print(f"  [OUT] {out_enriched}  ({enriched.shape})")

    # 4. Copy and clean GeoJSON
    copy_geojson()

    # 5. Print summary
    print("\n  Top 5 Most Vulnerable Districts (Census 2011):")
    top = socio_df.nlargest(5, "VULNERABILITY_INDEX")[
        ["DISTRICT", "POPULATION", "LITERACY_RATE", "URBANIZATION_RATE", "VULNERABILITY_INDEX"]
    ]
    print(top.to_string(index=False))

    print("\n  Top 5 Most Literate Districts:")
    lit = socio_df.nlargest(5, "LITERACY_RATE")[["DISTRICT", "LITERACY_RATE", "URBANIZATION_RATE"]]
    print(lit.to_string(index=False))

    print("\n  [DONE] Census enrichment complete.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
