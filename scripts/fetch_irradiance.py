"""
Fetch historical solar irradiance data from NASA POWER via AWS S3 Zarr store.

Data source:
  NASA Prediction Of Worldwide Energy Resources (POWER)
  Langley Research Center, power.larc.nasa.gov
  S3 bucket: s3://nasa-power (AWS Open Data Registry)
  Zarr store: nasa-power/syn1deg/temporal/power_syn1deg_daily_temporal_utc.zarr
  Grid: 1-degree resolution, UTC, CERES SYN1deg product

Variables fetched:
  ALLSKY_SFC_SW_DWN  - All-sky Global Horizontal Irradiance (GHI), W m-2 daily mean
  CLRSKY_SFC_SW_DWN  - Clear-sky GHI (theoretical max, no cloud), W m-2 daily mean
  ALLSKY_SFC_SW_DNI  - All-sky Direct Normal Irradiance (DNI), W m-2 daily mean
  ALLSKY_SFC_SW_DIFF - All-sky Diffuse Horizontal Irradiance, W m-2 daily mean

  *_Whm2day columns = raw_W_per_m2 * 24 h = daily total Wh/m2/day

Date range: August 22-29 for each of 2022, 2023, 2024
  (mirrors the official BWSC 2027 race window: 22-29 August 2027)

Usage:
  pip install zarr s3fs
  python3 scripts/fetch_irradiance.py
"""

import csv
import datetime
import os
import numpy as np
import zarr
import s3fs

ROUTE_CSV = os.path.join(os.path.dirname(__file__), "../data/route.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/irradiance")

ZARR_PATH = "nasa-power/syn1deg/temporal/power_syn1deg_daily_temporal_utc.zarr"
EPOCH = datetime.date(2000, 12, 31)   # time=0 corresponds to 2000-12-31
YEARS = [2022, 2023, 2024]
PARAMS = ["ALLSKY_SFC_SW_DWN", "CLRSKY_SFC_SW_DWN", "ALLSKY_SFC_SW_DNI", "ALLSKY_SFC_SW_DIFF"]
FIELD_NAMES = ["ghi_Wm2", "clrsky_ghi_Wm2", "dni_Wm2", "diff_Wm2"]


def load_checkpoints(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def time_indices(year):
    start = (datetime.date(year, 8, 22) - EPOCH).days
    return list(range(start, start + 8))


def main():
    access_date = datetime.date.today().isoformat()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    checkpoints = load_checkpoints(ROUTE_CSV)
    print(f"Loaded {len(checkpoints)} checkpoints")

    print("Opening NASA POWER S3 Zarr store (anonymous access)...")
    fs = s3fs.S3FileSystem(anon=True)
    store = s3fs.S3Map(ZARR_PATH, s3=fs)
    z = zarr.open(store, mode="r")

    lat_arr = z["lat"][:]  # 1-deg grid, -89.5 to 89.5
    lon_arr = z["lon"][:]  # 1-deg grid, -179.5 to 179.5

    # Assign nearest grid cell to each checkpoint
    for cp in checkpoints:
        lat = float(cp["latitude"]); lon = float(cp["longitude"])
        cp["lat_idx"] = int(np.argmin(np.abs(lat_arr - lat)))
        cp["lon_idx"] = int(np.argmin(np.abs(lon_arr - lon)))
        cp["lat_grid"] = float(lat_arr[cp["lat_idx"]])
        cp["lon_grid"] = float(lon_arr[cp["lon_idx"]])

    # Compute time index range across all years
    all_t = [t for yr in YEARS for t in time_indices(yr)]
    t_min, t_max = min(all_t), max(all_t)
    lat_indices = sorted({cp["lat_idx"] for cp in checkpoints})
    lon_indices = sorted({cp["lon_idx"] for cp in checkpoints})
    lat_min = min(lat_indices); lon_min = min(lon_indices)
    lat_max = max(lat_indices); lon_max = max(lon_indices)

    print(f"Fetching Zarr slices (t={t_min}..{t_max}, lat[{lat_min}..{lat_max}], lon[{lon_min}..{lon_max}])...")
    data = {}
    for param in PARAMS:
        print(f"  {param}...", end=" ", flush=True)
        data[param] = z[param][t_min:t_max+1, lat_min:lat_max+1, lon_min:lon_max+1]
        print(f"shape {data[param].shape}")

    CSV_FIELDS = [
        "location", "cumulative_km", "lat_grid", "lon_grid", "date",
        "ghi_Wm2", "clrsky_ghi_Wm2", "dni_Wm2", "diff_Wm2",
        "ghi_Whm2day", "clrsky_ghi_Whm2day", "dni_Whm2day", "diff_Whm2day",
    ]
    all_records = []

    for year in YEARS:
        t_indices = time_indices(year)
        year_records = []
        for cp in checkpoints:
            for t_idx in t_indices:
                day = (EPOCH + datetime.timedelta(days=t_idx)).isoformat()
                t_rel = t_idx - t_min
                lat_rel = cp["lat_idx"] - lat_min
                lon_rel = cp["lon_idx"] - lon_min
                row = {
                    "location": cp["location"],
                    "cumulative_km": int(cp["cumulative_km"]),
                    "lat_grid": cp["lat_grid"],
                    "lon_grid": cp["lon_grid"],
                    "date": day,
                }
                for param, field in zip(PARAMS, FIELD_NAMES):
                    v = float(data[param][t_rel, lat_rel, lon_rel])
                    row[field] = round(v, 2)
                # Daily total = daily mean W/m2 * 24 h
                row["ghi_Whm2day"]        = round(row["ghi_Wm2"]        * 24, 1)
                row["clrsky_ghi_Whm2day"] = round(row["clrsky_ghi_Wm2"] * 24, 1)
                row["dni_Whm2day"]        = round(row["dni_Wm2"]        * 24, 1)
                row["diff_Whm2day"]       = round(row["diff_Wm2"]       * 24, 1)
                year_records.append(row)
                all_records.append(row)

        path = os.path.join(OUTPUT_DIR, f"irradiance_aug_{year}.csv")
        with open(path, "w", newline="") as f:
            f.write(f"# Source: NASA POWER, s3://nasa-power (AWS Open Data), {ZARR_PATH}\n")
            f.write(f"# Variables: {', '.join(PARAMS)}\n")
            f.write(f"# Grid: 1-degree nearest-cell; units raw = W m-2 daily mean; *_Whm2day = raw*24\n")
            f.write(f"# Date range: {year}-08-22 to {year}-08-29 (BWSC 2027 race window reference)\n")
            f.write(f"# Retrieved: {access_date}\n")
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            w.writerows(year_records)
        print(f"Written: {path} ({len(year_records)} rows)")

    # 3-year summary
    from collections import defaultdict
    groups = defaultdict(list)
    for rec in all_records:
        groups[(rec["location"], rec["cumulative_km"], rec["lat_grid"],
                rec["lon_grid"], rec["date"][5:])].append(rec)

    SUM_FIELDS = [
        "location", "cumulative_km", "lat_grid", "lon_grid", "calendar_mmdd", "years_averaged",
        "ghi_Wm2_avg", "clrsky_ghi_Wm2_avg", "dni_Wm2_avg", "diff_Wm2_avg",
        "ghi_Whm2day_avg", "clrsky_ghi_Whm2day_avg", "dni_Whm2day_avg", "diff_Whm2day_avg",
    ]
    summary = []
    for (loc, cum, lat_g, lon_g, mmdd), recs in sorted(groups.items()):
        def avg(f): return round(sum(r[f] for r in recs) / len(recs), 2)
        summary.append({
            "location": loc, "cumulative_km": cum,
            "lat_grid": lat_g, "lon_grid": lon_g,
            "calendar_mmdd": mmdd, "years_averaged": len(recs),
            "ghi_Wm2_avg": avg("ghi_Wm2"), "clrsky_ghi_Wm2_avg": avg("clrsky_ghi_Wm2"),
            "dni_Wm2_avg": avg("dni_Wm2"),  "diff_Wm2_avg": avg("diff_Wm2"),
            "ghi_Whm2day_avg": avg("ghi_Whm2day"), "clrsky_ghi_Whm2day_avg": avg("clrsky_ghi_Whm2day"),
            "dni_Whm2day_avg": avg("dni_Whm2day"),  "diff_Whm2day_avg": avg("diff_Whm2day"),
        })

    sum_path = os.path.join(OUTPUT_DIR, "irradiance_3yr_summary.csv")
    with open(sum_path, "w", newline="") as f:
        f.write(f"# Source: NASA POWER S3 Zarr — 3-year average (2022, 2023, 2024) for Aug 22-29\n")
        f.write(f"# Retrieved: {access_date}\n")
        w = csv.DictWriter(f, fieldnames=SUM_FIELDS)
        w.writeheader()
        w.writerows(summary)
    print(f"Written: {sum_path} ({len(summary)} rows)")
    print("\nDone.")


if __name__ == "__main__":
    main()
