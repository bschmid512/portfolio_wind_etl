#!/usr/bin/env python3
"""
Pull monthly U.S. generation by source from EIA API v2.
Writes: data/raw/monthly_generation.csv
Columns: period, GWh, source
"""
import sys, requests, pandas as pd, numpy as np
from pathlib import Path

API_KEY = "GSkHA1tBQdn3zaajqwcF3jRxHTSZwJIt3g7xxpgX"          #  ← paste your key

SERIES = {
    "Coal":    "ELEC.GEN.COW-US-99.M",
    "Gas":     "ELEC.GEN.NG-US-99.M",
    "Nuclear": "ELEC.GEN.NUC-US-99.M",
    "Hydro":   "ELEC.GEN.HYC-US-99.M",
    "Wind":    "ELEC.GEN.WND-US-99.M",
    "Solar":   "ELEC.GEN.SUN-US-99.M",
}

def _detect_columns(df: pd.DataFrame, src: str) -> pd.DataFrame:
    """Rename timestamp ➜ period  •  numeric ➜ GWh."""
    # 1. timestamp column
    ts_candidates = [c for c in df.columns if c.lower() in {"period", "date", "yyyymm"}]
    if not ts_candidates:
        sys.exit(f"[{src}] No period/date column found in API payload: {df.columns.tolist()}")
    df = df.rename(columns={ts_candidates[0]: "period"})

    # 2. numeric column
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    if "value" in num_cols:
        num = "value"
    elif "generation" in num_cols:
        num = "generation"
    elif len(num_cols) == 1:
        num = num_cols[0]
    else:
        sys.exit(f"[{src}] Cannot unambiguously pick numeric column: {num_cols}")

    df = df.rename(columns={num: "GWh"})
    return df[["period", "GWh"]]

def fetch_series(name: str, sid: str) -> pd.DataFrame:
    url = f"https://api.eia.gov/v2/seriesid/{sid}?api_key={API_KEY}"
    j   = requests.get(url, timeout=30).json()

    if "response" in j and "data" in j["response"]:
        df = pd.DataFrame(j["response"]["data"])
    elif "series" in j and j["series"]:
        df = pd.DataFrame(j["series"][0]["data"], columns=["period", "GWh"])
    else:
        sys.exit(f"[{name}] Unrecognized JSON:\n{j}")

    df = _detect_columns(df, name)
    df.insert(0, "source", name)
    return df

def main():
    dfs = []
    for name, sid in SERIES.items():
        print(f"Fetching {name} …", end=" ", flush=True)
        dfs.append(fetch_series(name, sid))
        print("OK")

    all_df = pd.concat(dfs, ignore_index=True)
    out_dir = Path(__file__).parent.parent / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_fp  = out_dir / "monthly_generation.csv"
    all_df.to_csv(out_fp, index=False)
    print(f"\nWrote {len(all_df):,} rows ➜ {out_fp}")

if __name__ == "__main__":
    main()
