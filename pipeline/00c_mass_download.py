"""
PIPELINE STEP 00c - Mass Dataset Downloader + Extract Unused Local CSVs
========================================================================
Downloads additional datasets from online sources AND
processes the 57 unused district CSVs already in data/raw/district/

Outputs in data/processed/:
  police_strength.csv          <- #12: district police strength (actual vs sanctioned)
  sc_crimes.csv                <- #02_01: crimes against SC communities
  st_crimes.csv                <- #02: crimes against ST communities
  crimes_children.csv          <- #03: crimes against children
  arrests_by_age_sex.csv       <- #07_01: arrests by sex and age
  juvenile_ipc.csv             <- #08_01: juveniles apprehended IPC
  anti_corruption.csv          <- #23+24: anti-corruption cases + arrests
  murder_motive.csv            <- #19: motive/cause of murder
  recidivism.csv               <- #22: persons arrested under recidivism
  offenders_victim_relation.csv<- #21: offenders known to victim
  crime_by_place.csv           <- #17: crime by place of occurrence
  police_casualties.csv        <- #13+15+16: police killed, suicide, firing
  property_by_nature.csv       <- #11: property stolen by type
  firearms_murder.csv          <- #34: firearms used in murder
  custody_escapes.csv          <- #41: escapes from police custody
  district_women_crimes.csv    <- #42 district: district-wise women crimes 2001-2014

Run:
    python pipeline/00c_mass_download.py
"""

import sys
import urllib.request
import pandas as pd
import numpy as np
import json
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
RAW_DIR  = ROOT / "data" / "raw"
DIST_DIR = RAW_DIR / "district"
PROC_DIR = ROOT / "data" / "processed"
PROC_DIR.mkdir(exist_ok=True)

KARNATAKA_ALIASES = [
    "KARNATAKA", "Karnataka", "karnataka", "KA", "Karnata"
]

# ============================================================
# PART A: Download from Online Sources
# ============================================================

ONLINE_DATASETS = [
    # India roads / infrastructure (for crime context)
    {
        "name": "india_hdi_states",
        "url": "https://raw.githubusercontent.com/datameet/india-district-boundaries/master/states.geojson",
        "type": "geojson",
        "desc": "India state boundaries with HDI data",
    },
    # Socio-economic proxy: India nighttime lights (urbanization proxy)
    {
        "name": "india_election_2014",
        "url": "https://raw.githubusercontent.com/datameet/india-election-data/master/assembly-constituencies/2014/GE2014.csv",
        "type": "csv",
        "desc": "India 2014 election results - constituency level data",
    },
    # Karnataka HDR / development
    {
        "name": "india_districts_census_clean",
        "url": "https://raw.githubusercontent.com/nshiddqui/india-census-2011/main/india-districts-census-2011.csv",
        "type": "csv",
        "desc": "India Census 2011 cleaned district data",
    },
    # Crime against women trend
    {
        "name": "crime_women_state",
        "url": "https://raw.githubusercontent.com/nicholasgasior/india-crime-stats/main/crime_against_women_statewise.csv",
        "type": "csv",
        "desc": "State-wise crimes against women trend",
    },
    # District population estimate
    {
        "name": "india_districts_pop",
        "url": "https://raw.githubusercontent.com/saikumarsuvanam/India-Population-By-Districts/main/India_Population_By_Districts_2011.csv",
        "type": "csv",
        "desc": "India 2011 population by district",
    },
]


def try_download(entry: dict) -> bool:
    url  = entry["url"]
    name = entry["name"]
    dtype = entry["type"]
    ext  = ".geojson" if dtype == "geojson" else ".csv"
    out  = RAW_DIR / f"{name}{ext}"

    try:
        urllib.request.urlretrieve(url, out)
        if dtype == "csv":
            df = pd.read_csv(out, nrows=3, encoding="latin-1", on_bad_lines="skip")
            print(f"    [OK] {name}.csv - {df.shape[1]} cols | {list(df.columns[:5])}")
        elif dtype == "geojson":
            with open(out) as f:
                g = json.load(f)
            print(f"    [OK] {name}.geojson - {len(g.get('features', []))} features")
        return True
    except Exception as e:
        if out.exists():
            out.unlink()
        print(f"    [FAIL] {name}: {str(e)[:60]}")
        return False


# ============================================================
# PART B: Process Already-Downloaded District CSVs
# ============================================================

def read_district_csv(path: Path, encodings=("utf-8-sig", "latin-1", "cp1252")) -> pd.DataFrame:
    """Read a district CSV, trying multiple encodings, skipping bad lines."""
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc, low_memory=False, on_bad_lines="skip")
            df.columns = [str(c).strip().replace("\ufeff", "") for c in df.columns]
            return df
        except Exception:
            continue
    return pd.DataFrame()


def filter_karnataka(df: pd.DataFrame, state_col: str = None) -> pd.DataFrame:
    """Filter rows for Karnataka only."""
    if state_col and state_col in df.columns:
        mask = df[state_col].astype(str).str.strip().str.upper().str.contains("KARNATAKA|KARNATA", na=False)
        return df[mask].copy()
    # Try common state column names
    for col in ["State_UT", "STATE_UT", "State/UT", "State", "Area_Name", "state", "ST_NAME"]:
        if col in df.columns:
            mask = df[col].astype(str).str.upper().str.contains("KARNATAKA", na=False)
            filtered = df[mask].copy()
            if len(filtered) > 0:
                return filtered
    return df  # return all if can't filter


def numeric_cols(df: pd.DataFrame, skip_cols: list) -> pd.DataFrame:
    """Convert all non-skip columns to numeric."""
    for col in df.columns:
        if col not in skip_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


LOCAL_TASKS = [

    # ── Police Strength ──────────────────────────────────────────────────────
    {
        "name": "police_strength",
        "file": "12_Police_strength_actual_and_sanctioned.csv",
        "desc": "District police strength: actual vs sanctioned",
        "key_cols": ["State_UT", "District", "Year"],
        "rename": {},
    },

    # ── Crimes Against SC ─────────────────────────────────────────────────────
    {
        "name": "sc_crimes",
        "file": "02_01_District_wise_crimes_committed_against_SC_2014.csv",
        "desc": "Crimes against Scheduled Castes by district",
        "key_cols": ["State_UT", "District", "Year"],
        "rename": {},
    },

    # ── Crimes Against ST ─────────────────────────────────────────────────────
    {
        "name": "st_crimes",
        "file": "02_District_wise_crimes_committed_against_ST_2014.csv",
        "desc": "Crimes against Scheduled Tribes by district",
        "key_cols": ["State_UT", "District", "Year"],
        "rename": {},
    },

    # ── Crimes Against Children ───────────────────────────────────────────────
    {
        "name": "crimes_children",
        "file": "03_District_wise_crimes_committed_against_children_2001_2012.csv",
        "desc": "District-wise crimes against children",
        "key_cols": ["State_UT", "District", "Year"],
        "rename": {},
    },

    # ── Arrests by Age & Sex ──────────────────────────────────────────────────
    {
        "name": "arrests_by_age_sex",
        "file": "07_01_Persons_arrested_by_sex_and_age_group_IPC_2014.csv",
        "desc": "Arrests breakdown by sex and age group",
        "key_cols": ["State_UT", "District", "Year"],
        "rename": {},
    },

    # ── Juvenile IPC ──────────────────────────────────────────────────────────
    {
        "name": "juvenile_ipc",
        "file": "08_01_Juvenile_apprehended_state_IPC.csv",
        "desc": "Juveniles apprehended under IPC by state",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Murder Motive ─────────────────────────────────────────────────────────
    {
        "name": "murder_motive",
        "file": "19_Motive_or_cause_of_murder_and_culpable_homicide_not_amounting_to_murder.csv",
        "desc": "Motive/cause of murder: dispute, property, love, etc.",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Recidivism ────────────────────────────────────────────────────────────
    {
        "name": "recidivism",
        "file": "22_Persons_arrested_under_recidivism.csv",
        "desc": "Repeat offenders: persons arrested for recidivism",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Offender-Victim Relationship ──────────────────────────────────────────
    {
        "name": "offender_victim_relation",
        "file": "21_Offenders_known_to_the_victim.csv",
        "desc": "Were offenders known to rape victims? Family/neighbour/stranger",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Anti-Corruption Cases ─────────────────────────────────────────────────
    {
        "name": "anti_corruption_cases",
        "file": "23_Anti_corruprion_cases.csv",
        "desc": "Anti-corruption cases: Prevention of Corruption Act",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Anti-Corruption Arrests ───────────────────────────────────────────────
    {
        "name": "anti_corruption_arrests",
        "file": "24_Anti_corruption_arrests.csv",
        "desc": "Anti-corruption arrests by state",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Crime by Place ────────────────────────────────────────────────────────
    {
        "name": "crime_by_place",
        "file": "17_Crime_by_place_of_occurrence_2001_2012.csv",
        "desc": "Crime by place: road, house, public place, etc.",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Police Casualties ─────────────────────────────────────────────────────
    {
        "name": "police_killed_injured",
        "file": "13_Police_killed_or_injured_on_duty.csv",
        "desc": "Police personnel killed or injured on duty",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Property Stolen by Nature ─────────────────────────────────────────────
    {
        "name": "property_by_nature",
        "file": "11_Property_stolen_and_recovered_nature_of_property.csv",
        "desc": "Property stolen: cash, jewellery, vehicles, livestock",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Firearms in Murder ────────────────────────────────────────────────────
    {
        "name": "firearms_murder",
        "file": "34_Use_of_fire_arms_in_murder_cases.csv",
        "desc": "Use of firearms in murder cases by state",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Police Custody Escapes ────────────────────────────────────────────────
    {
        "name": "custody_escapes",
        "file": "41_Escapes_from_police_custody.csv",
        "desc": "Escapes from police custody by state",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── Unidentified Dead Bodies ──────────────────────────────────────────────
    {
        "name": "unidentified_bodies",
        "file": "38_Unidentified_dead_bodies_recovered_and_inquest_conducted.csv",
        "desc": "Unidentified dead bodies recovered + inquests",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },

    # ── District Women Crimes 2001-2014 ───────────────────────────────────────
    {
        "name": "district_women_crimes",
        "file": "42_District_wise_crimes_committed_against_women_2014.csv",
        "desc": "District-level women crimes: rape, dowry, assault, trafficking",
        "key_cols": ["State_UT", "District", "Year"],
        "rename": {},
    },

    # ── IPC 2014 ──────────────────────────────────────────────────────────────
    {
        "name": "ipc_2014",
        "file": "01_District_wise_crimes_committed_IPC_2014.csv",
        "desc": "Full IPC crimes by district 2014 (91 crime categories!)",
        "key_cols": ["State_UT", "District", "Year"],
        "rename": {},
    },

    # ── Juvenile Education / Family Background ────────────────────────────────
    {
        "name": "juvenile_education",
        "file": "18_01_Juveniles_arrested_Education.csv",
        "desc": "Education level of arrested juveniles",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },
    {
        "name": "juvenile_family",
        "file": "18_03_Juveniles_arrested_Family_background.csv",
        "desc": "Family background of arrested juveniles",
        "key_cols": ["Area_Name", "Year"],
        "rename": {},
    },
]


def process_local_task(task: dict) -> dict:
    fpath = DIST_DIR / task["file"]
    if not fpath.exists():
        # Also check raw root
        fpath = RAW_DIR / task["file"]
    if not fpath.exists():
        return {"name": task["name"], "status": "MISSING", "rows": 0}

    df = read_district_csv(fpath)
    if df.empty:
        return {"name": task["name"], "status": "UNREADABLE", "rows": 0}

    # Try to filter Karnataka where possible
    df_karn = filter_karnataka(df)

    # Convert metrics to numeric
    key_cols = [c for c in task["key_cols"] if c in df_karn.columns]
    df_karn = numeric_cols(df_karn, skip_cols=key_cols + ["Group_Name", "Sub_Group_Name", "Subgroup"])

    # Save full (all states) and Karnataka subset
    out_full = PROC_DIR / f"{task['name']}_all_states.csv"
    out_karn = PROC_DIR / f"{task['name']}.csv"

    df.to_csv(out_full, index=False)
    df_karn.to_csv(out_karn, index=False)

    return {
        "name":   task["name"],
        "status": "OK",
        "rows_all":  len(df),
        "rows_karn": len(df_karn),
        "cols":   df.shape[1],
        "desc":   task["desc"],
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 65)
    print("  STEP 00c - Mass Dataset Download + Extract Local CSVs")
    print("=" * 65)

    # PART A: Online downloads
    print(f"\n--- PART A: Downloading {len(ONLINE_DATASETS)} Online Datasets ---")
    downloaded = 0
    for entry in ONLINE_DATASETS:
        print(f"  Trying: {entry['name']} ({entry['desc'][:45]}...)")
        if try_download(entry):
            downloaded += 1
    print(f"\n  Online: {downloaded}/{len(ONLINE_DATASETS)} downloaded")

    # PART B: Process local CSVs
    print(f"\n--- PART B: Processing {len(LOCAL_TASKS)} Local District CSVs ---")
    results = []
    for task in LOCAL_TASKS:
        r = process_local_task(task)
        results.append(r)
        status = r["status"]
        if status == "OK":
            print(f"  [OK]      {r['name']:35s} | all:{r['rows_all']:4d} | karn:{r['rows_karn']:3d} | {r['cols']}cols")
        else:
            print(f"  [{status}] {r['name']}")

    ok_tasks = [r for r in results if r["status"] == "OK"]
    print(f"\n  Local CSVs processed: {len(ok_tasks)}/{len(LOCAL_TASKS)}")

    # Summary table
    print("\n" + "=" * 65)
    print("  PROCESSED FILES SUMMARY")
    print("=" * 65)
    for r in ok_tasks:
        print(f"  {r['name']:35s} -> {r['rows_karn']:3d} Karnataka rows | {r['cols']} cols")
        print(f"    {r['desc']}")

    print("\n  All outputs in: data/processed/")
    print(f"  Total new files: {len(ok_tasks) * 2} (Karnataka + all-states versions)")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
