"""
RUN ALL PIPELINE STEPS IN ORDER
================================
This script runs all 7 pipeline steps sequentially.
Each step's output feeds into the next.

Usage:
    python pipeline/run_all.py              # Run all steps
    python pipeline/run_all.py --from 3    # Resume from step 3
    python pipeline/run_all.py --only 4   # Run only step 4
"""

import sys
import time
import argparse
import subprocess
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
SCRIPTS = [
    (1, "01_preprocess.py",          "Load & clean 14 NCRB CSVs ??? master_state_data.csv"),
    (2, "02_feature_engineering.py", "Create 12 derived features ??? master_features.csv"),
    (3, "03_risk_classifier.py",     "Train XGBoost ??? risk_scores.csv + model"),
    (4, "04_hotspot_model.py",       "DBSCAN + Folium maps ??? hotspot_clusters.csv + HTML"),
    (5, "05_time_series_forecast.py","Prophet forecast ??? crime_forecast.csv"),
    (6, "06_anomaly_detection.py",   "IsolationForest ??? anomaly_flagged.csv"),
    (7, "07_network_builder.py",     "Crime network graph ??? crime_network.html + JSON"),
]

def run_step(step_num: int, script: str, desc: str) -> bool:
    script_path = Path(__file__).parent / script
    print(f"\n{'='*60}")
    print(f"  STEP {step_num}: {desc}")
    print(f"  Script: {script}")
    print(f"{'='*60}")
    t0 = time.time()
    result = subprocess.run([sys.executable, str(script_path)], capture_output=False)
    elapsed = round(time.time() - t0, 1)
    if result.returncode == 0:
        print(f"\n  ??? Step {step_num} completed in {elapsed}s")
        return True
    else:
        print(f"\n  ??? Step {step_num} FAILED (exit code {result.returncode})")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from",  dest="from_step", type=int, default=1, help="Start from step N")
    parser.add_argument("--only",  dest="only_step", type=int, default=None, help="Run only step N")
    args = parser.parse_args()

    steps_to_run = SCRIPTS
    if args.only_step:
        steps_to_run = [s for s in SCRIPTS if s[0] == args.only_step]
    elif args.from_step > 1:
        steps_to_run = [s for s in SCRIPTS if s[0] >= args.from_step]

    print(f"\n???????  SurakshaAI Pipeline Runner")
    print(f"   Running {len(steps_to_run)} step(s)\n")

    failed = []
    t_start = time.time()
    for step_num, script, desc in steps_to_run:
        ok = run_step(step_num, script, desc)
        if not ok:
            failed.append(step_num)
            print(f"  [WARN] Continuing despite step {step_num} failure...")

    total = round(time.time() - t_start, 1)
    print(f"\n{'='*60}")
    print(f"  Pipeline finished in {total}s")
    if failed:
        print(f"  ??????  Failed steps: {failed}")
    else:
        print(f"  ??? All steps completed successfully!")
    print(f"  Output files in: data/processed/")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

