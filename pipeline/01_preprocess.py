"""
PIPELINE STEP 01 - Preprocess Raw NCRB State-Level CSVs
=======================================================
Input : data/raw/*.csv  (14 state-level NCRB files)
Output: data/processed/master_state_data.csv

Run:
    python pipeline/01_preprocess.py
"""

import os
import sys
import csv
import pandas as pd
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
RAW_DIR  = ROOT / "data" / "raw"
PROC_DIR = ROOT / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

# ─── Dataset Configs ──────────────────────────────────────────────────────────
# Each entry: pattern to find the file, key columns, metric columns to extract
DATASET_CONFIGS = {
    "complaints": {
        "pattern": "25_Complaints_against_police",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "CPA_-_Complaints_Received/Alleged":                           "complaints_received",
            "CPA_-_Cases_Registered":                                       "complaints_cases_registered",
            "CPC_-_Police_Personnel_Disciplinary_Action_Initiated":         "disciplinary_actions",
            "CPC_-_Police_Personnel_Dismissal/Removal_from_Service":        "dismissals",
            "CPB_-_Police_Personnel_Convicted":                             "convictions_police",
            "CPA_-_Complaints/Cases_Declared_False/Unsubstantiated":        "false_complaints",
            "CPA_-_No_of_Departmental_Enquiries":                          "dept_enquiries",
            "CPA_-_No_of_Magisterial_Enquiries":                           "mag_enquiries",
        },
    },
    "rape_victims": {
        "pattern": "20_Victims_of_rape",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Victims_of_Rape_Total":        "rape_victims_total",
            "Victims_Upto_10_Yrs":          "rape_upto_10",
            "Victims_Between_10-14_Yrs":    "rape_10_14",
            "Victims_Between_14-18_Yrs":    "rape_14_18",
            "Victims_Between_18-30_Yrs":    "rape_18_30",
            "Victims_Between_30-50_Yrs":    "rape_30_50",
            "Victims_Above_50_Yrs":         "rape_above_50",
        },
    },
    "property": {
        "pattern": "10_Property_stolen_and_recovered",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Value_of_Property_Stolen":    "property_stolen_value",
            "Value_of_Property_Recovered": "property_recovered_value",
        },
    },
    "murder": {
        "pattern": "32_Murder_victim_age_sex",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Victims_Total":        "murder_total",
            "Victims_Above_50_Yrs": "murder_above_50",
        },
    },
    "auto_theft": {
        "pattern": "30_Auto_theft",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Auto_Theft_Stolen":    "auto_theft_stolen",
            "Auto_Theft_Recovered": "auto_theft_recovered",
        },
    },
    "fraud": {
        "pattern": "31_Serious_fraud",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Loss_of_Property_1_10_Crores":   "fraud_1_10cr",
            "Loss_of_Property_10_25_Crores":  "fraud_10_25cr",
            "Loss_of_Property_25_50_Crores":  "fraud_25_50cr",
            "Loss_of_Property_50_100_Crores": "fraud_50_100cr",
            "Loss_of_Property_Above_100_Crores": "fraud_above_100cr",
        },
    },
    "trials": {
        "pattern": "28_Trial_of_violent_crimes_by_courts",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Trial_of_Violent_Crimes_by_Courts_Total":          "trial_total",
            "Trial_of_Violent_Crimes_by_Courts_By_Confession":  "trial_confession",
            "Trial_of_Violent_Crimes_by_Courts_By_trial":       "trial_regular",
        },
    },
    "trial_periods": {
        "pattern": "29_Period_of_trials_by_courts",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Average_Period_of_Trial_Months": "avg_trial_months",
            "Pending_Trial_Cases":            "pending_trials",
        },
    },
    "hr_violations": {
        "pattern": "35_Human_rights_violation_by_police",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Human_Rights_Violations_Total":      "hr_violations_total",
            "Human_Rights_Violations_by_Police":  "hr_violations_police",
        },
    },
    "police_housing": {
        "pattern": "36_Police_housing",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "PH_Hous":              "housing_available",
            "PH_Hous_PH":           "housing_occupied",
            "PH_Sanctioned_Strength": "sanctioned_strength",
        },
    },
    "kidnapping": {
        "pattern": "39_Specific_purpose_of_kidnapping",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Kidnapping_Cases":          "kidnapping_cases",
            "Kidnapping_for_Ransom":     "kidnapping_ransom",
            "Kidnapping_for_Marriage":   "kidnapping_marriage",
        },
    },
    "custodial_deaths": {
        "pattern": "40_01_Custodial_death_person_remanded",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Custodial_Deaths_Remanded":     "custodial_deaths_remanded",
            "Custodial_Deaths_Not_Remanded": "custodial_deaths_not_remanded",
        },
    },
    "crimes_women": {
        "pattern": "42_Cases_under_crime_against_women",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Cases_Reported":                                               "women_cases_reported",
            "Cases_Chargesheeted":                                          "women_chargesheeted",
            "Cases_Convicted":                                              "women_convicted",
            "Cases_Acquitted_or_Discharged":                                "women_acquitted",
            "Cases_Pending_Investigation_at_Year_End":                      "women_pending_investigation",
            "Cases_Pending_Trial_at_Year_End":                              "women_pending_trial",
            "Cases_Declared_False_on_Account_of_Mistake_of_Fact_or_of_Law": "women_false_cases",
        },
    },
    "arrests_women": {
        "pattern": "43_Arrests_under_crime_against_women",
        "key_cols": ["Area_Name", "Year"],
        "rename": {
            "Persons_Arrested":     "women_arrests_persons",
            "Persons_Convicted":    "women_arrests_convicted",
            "Persons_Chargesheeted": "women_arrests_chargesheeted",
        },
    },
}


# ─── Helper Functions ─────────────────────────────────────────────────────────

def find_csv(pattern: str) -> Path | None:
    """Find a CSV file in data/raw/ by partial name match."""
    for f in RAW_DIR.rglob("*.csv"):
        if pattern.lower() in f.name.lower():
            return f
    return None


def load_clean_csv(filepath: Path, key_cols: list, rename: dict) -> pd.DataFrame:
    """Load a CSV, strip BOM, normalize col names, extract only needed columns."""
    # Try multiple encodings; skip bad lines for malformed CSVs
    for enc in ["utf-8-sig", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(
                filepath, encoding=enc, low_memory=False,
                on_bad_lines="skip",   # skip malformed rows
            )
            break
        except Exception:
            continue
    else:
        raise ValueError(f"Cannot read {filepath.name} with any known encoding")

    # Strip whitespace and BOM from column names
    df.columns = [str(c).strip().replace("\ufeff", "").replace("\u2192", "->") for c in df.columns]

    # ---- Fuzzy column matching: find closest match for each rename key ------
    actual_cols = set(df.columns)
    fuzzy_rename = {}
    for src, dst in rename.items():
        if src in actual_cols:
            fuzzy_rename[src] = dst
        else:
            # Try case-insensitive partial match
            src_lower = src.lower().replace(" ", "_")
            for col in actual_cols:
                if src_lower in col.lower().replace(" ", "_") or col.lower().replace(" ", "_") in src_lower:
                    fuzzy_rename[col] = dst
                    break

    missing = set(rename.values()) - set(fuzzy_rename.values())
    if missing:
        print(f"    [WARN] {filepath.name}: could not map {list(missing)[:2]}")

    # Keep only key cols + matched rename sources
    keep = key_cols + list(fuzzy_rename.keys())
    df = df[[c for c in keep if c in df.columns]].copy()
    df.rename(columns=fuzzy_rename, inplace=True)

    # Normalize key columns
    if "Area_Name" in df.columns:
        df["Area_Name"] = df["Area_Name"].astype(str).str.strip().str.title()
    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        df.dropna(subset=["Year"], inplace=True)
        df["Year"] = df["Year"].astype(int)

    # Convert all non-key columns to numeric
    metric_cols = [c for c in df.columns if c not in ("Area_Name", "Year")]
    for col in metric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Drop rows without state/year
    df.dropna(subset=["Area_Name", "Year"], inplace=True)
    df = df[df["Area_Name"].str.strip().str.len() > 0]

    if df.empty:
        raise ValueError(f"No valid rows after cleaning {filepath.name}")

    # Group by (state, year) — some files have multiple rows per state/year
    agg = {c: "sum" for c in df.columns if c not in ("Area_Name", "Year")}
    df = df.groupby(["Area_Name", "Year"], as_index=False).agg(agg)

    return df


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  STEP 01 - Preprocess State-Level NCRB Datasets")
    print("="*60)

    master = None
    loaded = 0

    for name, cfg in DATASET_CONFIGS.items():
        filepath = find_csv(cfg["pattern"])
        if filepath is None:
            print(f"  [MISSING] {cfg['pattern']}")
            continue

        try:
            df = load_clean_csv(filepath, cfg["key_cols"], cfg["rename"])
            print(f"  [OK] {name:20s} → {len(df):4d} rows  |  {filepath.name}")

            if master is None:
                master = df
            else:
                master = pd.merge(master, df, on=["Area_Name", "Year"], how="outer")

            loaded += 1
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")

    if master is None:
        print("\n[FATAL] No datasets loaded. Check data/raw/ folder.")
        print("Ensure the 19 CSV files are in:", RAW_DIR)
        return

    # ── Derived columns ──────────────────────────────────────────────────────
    master["fraud_total"] = (
        master.get("fraud_1_10cr", 0) +
        master.get("fraud_10_25cr", 0) +
        master.get("fraud_25_50cr", 0) +
        master.get("fraud_50_100cr", 0) +
        master.get("fraud_above_100cr", 0)
    )
    master["rape_below_18"] = (
        master.get("rape_upto_10", 0) +
        master.get("rape_10_14", 0) +
        master.get("rape_14_18", 0)
    )
    master["custodial_deaths_total"] = (
        master.get("custodial_deaths_remanded", 0) +
        master.get("custodial_deaths_not_remanded", 0)
    )
    master["property_recovery_rate"] = (
        master.get("property_recovered_value", 0) /
        master.get("property_stolen_value", 1).replace(0, 1) * 100
    ).clip(0, 100)

    # ── Fillna & sort ────────────────────────────────────────────────────────
    master.fillna(0, inplace=True)
    master.sort_values(["Area_Name", "Year"], inplace=True)
    master.reset_index(drop=True, inplace=True)

    # ── Save ─────────────────────────────────────────────────────────────────
    out = PROC_DIR / "master_state_data.csv"
    master.to_csv(out, index=False)

    print(f"\n  [DONE] Loaded {loaded}/{len(DATASET_CONFIGS)} datasets")
    print(f"  [OUT]  {out}")
    print(f"  [SHAPE] {master.shape[0]} rows × {master.shape[1]} columns")
    print(f"  [STATES] {master['Area_Name'].nunique()} unique states")
    print(f"  [YEARS]  {sorted(master['Year'].unique())}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
