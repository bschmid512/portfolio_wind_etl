#!/usr/bin/env python3
"""
Clean data/raw/monthly_generation.csv  ->  data/processed/monthly_gen_clean.csv
Columns written: date, source, GWh, TWh, total_GWh, share
"""
import pandas as pd
from pathlib import Path

base   = Path(__file__).parent.parent
raw_fp = base / "data" / "raw" / "monthly_generation.csv"
out_fp = base / "data" / "processed" / "monthly_gen_clean.csv"
out_fp.parent.mkdir(parents=True, exist_ok=True)

# 1  Load raw: columns are period, GWh, source
raw = pd.read_csv(raw_fp)

if not {"period", "GWh", "source"}.issubset(raw.columns):
    raise ValueError(f"Unexpected columns in {raw_fp}: {raw.columns.tolist()}")

# 2  Parse period ➜ pandas Timestamp
p = raw["period"].astype(str)

# a) “YYYY-MM” → simply append “-01” then parse
mask_dash = p.str.contains("-")
raw.loc[mask_dash, "date"] = pd.to_datetime(p[mask_dash] + "-01", format="%Y-%m-%d")

# b) “YYYYMM” → parse with %Y%m
mask_nodash = ~mask_dash
raw.loc[mask_nodash, "date"] = pd.to_datetime(p[mask_nodash], format="%Y%m")

# drop rows where date could not be parsed
clean = raw.dropna(subset=["date"]).copy()

# 3  Aggregate duplicates (sum GWh for same date+source)
clean = (
    clean.groupby(["date", "source"], as_index=False)
          .agg(GWh=("GWh", "sum"))
)

# 4  Add helper columns
clean["TWh"]       = clean["GWh"] / 1_000
clean["total_GWh"] = clean.groupby("date")["GWh"].transform("sum")
clean["share"]     = clean["GWh"] / clean["total_GWh"]

# 5  Save
clean.to_csv(out_fp, index=False)
print(f"Wrote {len(clean):,} rows ➜ {out_fp}")
