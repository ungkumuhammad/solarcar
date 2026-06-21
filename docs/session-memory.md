# Session Memory — Solar Car BWSC 2027

> Read this file at the start of every session to restore project context.
> Most recent session at top. When the user says "compress", prepend a new entry.

---

## 2026-06-21 — Speed-profile visualization + location-based control stops

### Accomplished
- Added matplotlib visualization: `--plot` produces `output/dashboard.png` (5 panels:
  speed, SoC, stacked power breakdown, elevation, irradiance over elapsed race time)
  and `output/power_by_day.png` (stacked energy-Wh bar per race day).
- Added `--table` (one row per ≥5 km/h speed change, + day starts, control stops, finish)
  and `--csv` (exports `speed_table.csv` + full per-timestep `full_trace.csv`).
- Extended `EnergyBudget` with aligned per-timestep traces (distance, day, irradiance,
  grade, altitude, driving/control-stop flags, and per-loss power) recorded for BOTH
  driving and parked/charging daylight steps — so evening/morning solar charging and
  cross-day SoC carryover are visible.
- **Model change — control stops are now location-based** (user-requested): a 30-min halt
  is taken when the car reaches each of the 9 official checkpoint km
  (310/580/850/1120/1400/1670/2040/2290/2550 from `data/route.csv`), car keeps charging
  from solar during the halt, and driving runs to the real **17:00 hard stop** (retired
  the old "end day 1 h early / 2 stops per day" abstraction).

### Key Decisions / Findings
- New results (location-based stops): optimized 4-day **finishes 3022 km, 66.4% SoC**
  (was 73.3%); 3-day now **2804 km / 92.8% (DNF)** because all 9 stops = 4.5 h apply
  regardless of race length; baseline 4-day **2925 km, 16.4% SoC (DNF)**.
- `RaceConfig`: `control_stops_per_day` → `num_control_stops` (default 9);
  `drive_end_hour` now returns the real 17:00; `total_drive_hours = 9h×days − 4.5h`.
- Confirmed three current modeling caveats the charts faithfully show (not fixed this
  session): regen is capped at zero (no surplus to battery, `simulator.py`), battery
  strategy is greedy per-day, irradiance is time-based not location-based.
- matplotlib/numpy installed via new `requirements.txt`; `output/` is git-ignored.

### Files Created / Modified
- New: `simulation/plots.py`, `simulation/tables.py`, `requirements.txt`
- Modified: `simulation/energy_budget.py` (traces + `record_step`), `simulation/simulator.py`
  (location-based stops, full trace recording), `models/race.py` (stop accounting),
  `environment/route.py` (`load_control_stops_km`, `OFFICIAL_CONTROL_STOPS_KM`),
  `main.py` (CLI flags + control-stop wiring), `.gitignore`, `CLAUDE.md` (results updated)

### Project Status
- Visualization (plots + table + CSV): **Complete**
- Control-stop model: **upgraded to location-based**

### Next Steps (waiting for instruction)
- **Whole-race battery strategy** (user-selected next): make speed planning ensure charge
  lasts to Adelaide, not just end of day (replaces greedy per-day budget).
- Optional follow-ups: regen→battery charging, location-based irradiance.

---

## 2026-06-21 — Data scripts and environmental datasets

### Accomplished
- Fetched 3-year solar irradiance data (Aug 22–29, 2022/2023/2024) at 11 route checkpoints
- Fetched elevation profile (58 points, ~50 km spacing) Darwin → Adelaide
- Wrote and committed fetch scripts documenting the actual data sources used
- Pushed all 7 files to branch claude/solar-challenge-2027-plan-nsj4yl

### Key Decisions / Findings
- NASA POWER REST API blocked from environment; used AWS S3 Zarr store instead:
  `s3://nasa-power/syn1deg/temporal/power_syn1deg_daily_temporal_utc.zarr`
  Access: anonymous via s3fs + zarr; time epoch = 2000-12-31; units = W m-2 daily mean × 24 = Wh/m²/day
- OpenTopoData API blocked; used AWS elevation-tiles-prod instead:
  `s3://elevation-tiles-prod/geotiff/{zoom}/{x}/{y}.tif` (zoom=9)
  Requires pyproj reproject WGS84→EPSG:3857 before rasterio sampling
- Confirmed elevation values: Darwin 28 m, Alice Springs 581 m, Port Augusta 13 m, Adelaide 44 m
- 3yr avg irradiance (Aug 22): Alice Springs GHI 5,916 Wh/m²/day; Adelaide GHI 3,632 Wh/m²/day

### Files Created / Modified
- `scripts/fetch_irradiance.py` — NASA POWER S3 Zarr fetch; nearest-cell lookup; per-year CSV + 3yr summary
- `scripts/fetch_elevation.py` — AWS elevation-tiles-prod GeoTIFF fetch; EPSG:3857 reproject; 58-point profile
- `data/irradiance/irradiance_aug_2022.csv` — 88 rows (11 checkpoints × 8 days Aug 22–29)
- `data/irradiance/irradiance_aug_2023.csv` — same structure, 2023
- `data/irradiance/irradiance_aug_2024.csv` — same structure, 2024
- `data/irradiance/irradiance_3yr_summary.csv` — 88 rows, 3-year averages per checkpoint per calendar day
- `data/elevation/elevation_profile.csv` — 58 rows: 11 checkpoints + 47 interpolated points

### Project Status
| Phase | Status |
|---|---|
| High-level race plan | Complete (`docs/race-plan.md`) |
| Regulation folder | Complete (`regulations/`) |
| Key rules summary | Complete (`regulations/key-rules-summary.md`) |
| Route data | Approximate — pending official BWSC 2027 route notes |
| Irradiance data | Complete (`data/irradiance/`) |
| Elevation data | Complete (`data/elevation/`) |
| Solar power budget | Not started |
| Power-speed model | Not started |
| Battery design | Not started |
| Energy balance | Not started |
| Strategy model | Not started |

### Next Steps (waiting for instruction)
- Solar power budget: model daily Wh harvest from 6 m² array using `irradiance_3yr_summary.csv`
- Power-speed curve: aero drag + rolling resistance model → efficient cruise speed
- Energy balance: confirm solar-in vs drive-out allows 3-day plan at legal speeds

---

## 2026-06-21 — Foundation: race plan, regulations, route data

### Accomplished
- Created `docs/race-plan.md` with required average speed analysis (Scenario A & B)
- Converted official BWSC 2027 PDF to Markdown via markitdown (2,297 lines)
- Created `regulations/key-rules-summary.md` with all rules cited by § number
- Created `CLAUDE.md` at repo root with expert role and working principles
- Corrected user-provided specs to match official regulations (see Key Decisions below)
- Committed and pushed to branch `claude/solar-challenge-2027-plan-nsj4yl`

### Key Decisions / Findings
- User stated 4 m² solar → official limit is 6 m² (§2.4.2); corrected throughout
- User stated 20 kg battery → regulation defines energy limit 11 MJ (§2.5.2);
  18650 cell (3.7 V, 3.4 Ah, 45 g) → 45,288 J/cell → max 242 cells → ~10.9 kg; corrected throughout
- Daily start time is 08:00 ALL days including Day 1 (§3.21.1) — earlier web research incorrectly said 08:30
- Required average speed: 3,000 km ÷ 22.5 h effective (27 h − 9 stops × 0.5 h) ≈ 133 km/h
- 133 km/h exceeds weighted legal ceiling (~121 km/h): NT 130 km/h, SA 110 km/h
- Strict 3-day finish not achievable within road speed limits; practical minimum ~3.5 days
- markitdown command: `markitdown "<pdf_path>" 2>/dev/null > regulations/bwsc-2027-regulations.md`

### Files Created / Modified
- `docs/race-plan.md` — 3-day plan, speed scenarios, speed-limit analysis, daily distance targets
- `regulations/bwsc-2027-regulations.md` — full official 2027 BWSC Event Regulations V1.0 (07 May 2026)
- `regulations/key-rules-summary.md` — quick-reference: hard limits, late-finish penalty, control stop procedure
- `data/route.csv` — 11 checkpoints with lat/lon, cumulative km, territory, speed limit, control_stop flag
- `CLAUDE.md` — expert role definition, project brief, working principles

### Project Status
| Phase | Status |
|---|---|
| High-level race plan | Complete |
| Regulation folder | Complete |
| Key rules summary | Complete |
| Route data | Approximate — pending official BWSC 2027 route notes |
| All other phases | Not started |

### Next Steps (waiting for instruction)
- Fetch historical irradiance and elevation data *(completed in session above)*
