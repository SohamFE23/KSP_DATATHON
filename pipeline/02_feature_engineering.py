"""
PIPELINE STEP 02 — Feature Engineering
=======================================
Input : data/processed/master_state_data.csv   (from 01_preprocess.py)
        data/raw/district/karnataka_clean.csv   (district-level, already processed)
Output: data/processed/master_features.csv

Run:
    python pipeline/02_feature_engineering.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parent.parent
PROC_DIR  = ROOT / "data" / "processed"
RAW_DIR   = ROOT / "data" / "raw"

# ─── Load ─────────────────────────────────────────────────────────────────────

def load_state_master() -> pd.DataFrame:
    p = PROC_DIR / "master_state_data.csv"
    if not p.exists():
        raise FileNotFoundError(f"Run 01_preprocess.py first. Missing: {p}")
    return pd.read_csv(p, low_memory=False)


def load_district_data() -> pd.DataFrame:
    """Load district-level Karnataka IPC data (already cleaned)."""
    p = PROC_DIR / "karnataka_clean.csv"
    if not p.exists():
        raise FileNotFoundError(f"Missing: {p}. Copy karnataka_clean.csv to data/processed/")
    return pd.read_csv(p, low_memory=False)


# ─── Feature Engineering — State Level ────────────────────────────────────────

def engineer_state_features(df: pd.DataFrame) -> pd.DataFrame:
    print("  Engineering state-level features...")
    df = df.copy()

    # 1. Violent Crime Index
    df["violent_crime_index"] = (
        df.get("murder_total", 0) +
        df.get("rape_victims_total", 0) +
        df.get("kidnapping_cases", 0)
    )

    # 2. Property Crime Index
    df["property_crime_index"] = (
        df.get("auto_theft_stolen", 0) +
        df.get("fraud_total", 0)
    )

    # 3. Police Accountability Score
    df["accountability_score"] = (
        df.get("disciplinary_actions", 0) +
        df.get("dismissals", 0) * 3 +
        df.get("hr_violations_total", 0) +
        df.get("custodial_deaths_total", 0) * 5
    )

    # 4. Judicial Backlog Score
    df["judicial_backlog_score"] = (
        df.get("pending_trials", 0) +
        df.get("avg_trial_months", 0) * 10   # weight long trials
    )

    # 5. Women's Safety Score (higher = worse)
    df["women_safety_score"] = (
        df.get("women_cases_reported", 0) +
        df.get("women_arrests_persons", 0) -
        df.get("women_convicted", 0)
    ).clip(lower=0)

    # 6. Housing Gap (resource pressure)
    df["housing_gap"] = (
        df.get("sanctioned_strength", 0) - df.get("housing_available", 0)
    ).clip(lower=0)

    # 7. Total State Crime Proxy (sum of key counts)
    df["total_crime_proxy"] = (
        df["violent_crime_index"] +
        df["property_crime_index"] +
        df.get("women_cases_reported", 0) +
        df.get("complaints_received", 0)
    )

    # 8. Year-over-Year Change (%)
    df.sort_values(["Area_Name", "Year"], inplace=True)
    df["crime_yoy_pct"] = (
        df.groupby("Area_Name")["total_crime_proxy"]
          .pct_change() * 100
    ).fillna(0).round(2)

    # 9. 3-Year Rolling Average
    df["crime_3yr_avg"] = (
        df.groupby("Area_Name")["total_crime_proxy"]
          .transform(lambda x: x.rolling(3, min_periods=1).mean())
    ).round(2)

    # 10. Rape vulnerability: % of victims below 18
    rape_total = df.get("rape_victims_total", pd.Series(dtype=float)).replace(0, np.nan)
    df["rape_minor_pct"] = (df.get("rape_below_18", 0) / rape_total * 100).fillna(0).round(2)

    # 11. Property recovery efficiency
    df["property_recovery_rate"] = df.get("property_recovery_rate", 0)

    # 12. Complaint-to-registration ratio (accountability signal)
    cases_reg = df.get("complaints_cases_registered", pd.Series(dtype=float)).replace(0, np.nan)
    df["complaint_registration_ratio"] = (
        df.get("complaints_received", 0) / cases_reg
    ).fillna(0).clip(0, 100).round(2)

    return df


# ─── Feature Engineering — District Level ─────────────────────────────────────

def engineer_district_features(df: pd.DataFrame) -> pd.DataFrame:
    print("  Engineering district-level features...")
    df = df.copy()

    # YoY change (already exists as CRIME_YOY_CHANGE — keep it)
    if "CRIME_YOY_CHANGE" not in df.columns and "TOTAL_CRIMES" in df.columns:
        df.sort_values(["DISTRICT", "YEAR"], inplace=True)
        df["CRIME_YOY_CHANGE"] = (
            df.groupby("DISTRICT")["TOTAL_CRIMES"]
              .pct_change() * 100
        ).fillna(0).round(2)

    # 3-year rolling avg (already exists as CRIME_3YR_AVG — keep it)
    if "CRIME_3YR_AVG" not in df.columns and "TOTAL_CRIMES" in df.columns:
        df["CRIME_3YR_AVG"] = (
            df.groupby("DISTRICT")["TOTAL_CRIMES"]
              .transform(lambda x: x.rolling(3, min_periods=1).mean())
        ).round(2)

    # Violent crime sub-index
    violent_cols = ["MURDER", "RAPE", "KIDNAPPING_ABDUCTION", "DACOITY", "ROBBERY"]
    existing_v = [c for c in violent_cols if c in df.columns]
    if existing_v:
        df["VIOLENT_CRIME_INDEX"] = df[existing_v].sum(axis=1)

    # Women crime sub-index
    women_cols = ["DOWRY_DEATHS", "ASSAULT_ON_WOMEN_WITH_INTENT_TO_OUTRAGE_HER_MODESTY",
                  "CRUELTY_BY_HUSBAND_OR_HIS_RELATIVES", "RAPE"]
    existing_w = [c for c in women_cols if c in df.columns]
    if existing_w:
        df["WOMEN_CRIME_INDEX"] = df[existing_w].sum(axis=1)

    # Property crime sub-index
    prop_cols = ["THEFT", "AUTO_THEFT", "BURGLARY", "CHEATING", "CRIMINAL_BREACH_OF_TRUST"]
    existing_p = [c for c in prop_cols if c in df.columns]
    if existing_p:
        df["PROPERTY_CRIME_INDEX"] = df[existing_p].sum(axis=1)

    # Spike flag: crime > 1.5x 3yr avg
    if "TOTAL_CRIMES" in df.columns and "CRIME_3YR_AVG" in df.columns:
        df["IS_SPIKE"] = (
            (df["TOTAL_CRIMES"] > df["CRIME_3YR_AVG"] * 1.5) &
            (df["CRIME_3YR_AVG"] > 0)
        ).astype(int)

    return df


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  STEP 02 — Feature Engineering")
    print("="*60)

    # ── State-level ──────────────────────────────────────────────────────────
    try:
        state_df = load_state_master()
        print(f"\n  State data: {state_df.shape}")
        state_features = engineer_state_features(state_df)
        out_state = PROC_DIR / "master_features.csv"
        state_features.to_csv(out_state, index=False)
        print(f"  [OUT] {out_state}  ({state_features.shape})")
    except FileNotFoundError as e:
        print(f"  [SKIP] {e}")

    # ── District-level ───────────────────────────────────────────────────────
    try:
        dist_df = load_district_data()
        print(f"\n  District data: {dist_df.shape}")
        dist_features = engineer_district_features(dist_df)
        out_dist = PROC_DIR / "district_features.csv"
        dist_features.to_csv(out_dist, index=False)
        print(f"  [OUT] {out_dist}  ({dist_features.shape})")
    except FileNotFoundError as e:
        print(f"  [SKIP] {e}")

    print("\n  [DONE] Feature engineering complete.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
