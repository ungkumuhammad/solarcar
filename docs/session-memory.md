# Session Memory — Solar Car BWSC 2027

> Read this file at the start of every session to restore project context.
> Most recent session at top. When the user says "compress", prepend a new entry.

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
