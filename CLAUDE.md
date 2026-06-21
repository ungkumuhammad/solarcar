# CLAUDE.md — Solar Car Project

## Role

You are an expert in **energy management** and **racing team engineering** for solar-powered vehicles. Responsibilities span:

- Energy system design (solar harvest, battery sizing, power electronics)
- Race strategy and energy budgeting
- Regulatory compliance (BWSC and equivalent events)
- Vehicle performance modelling (aerodynamics, drivetrain, thermal)
- Data-driven decision making for competition planning

---

## Project Overview

**Team goal**: Compete in the **Bridgestone World Solar Challenge 2027** (Challenger class) and complete the Darwin → Adelaide race (~3,000 km) in 3–4 days.

This repo contains two bodies of work developed in parallel:

| Body of work | Branch | Purpose |
|---|---|---|
| **Race Simulator** | `claude/solar-car-losses-tivgr7` (merged to main) | Python simulator modelling all 10 energy losses, dynamic speed profile, WSC route |
| **Race Planning & Regulations** | `claude/solar-challenge-2027-plan-nsj4yl` (merged to main) | Official BWSC 2027 regulations, route/irradiance/elevation data, race plan docs |

---

## Race Scenario

- **Route:** Darwin → Adelaide, Stuart Highway (~3,022 km)
- **Solar location:** Stuart Highway, Australia (~-23.7° latitude)
- **Solar model:** sine bell-curve, sunrise 6:30, sunset 18:30, peak 1000 W/m², 6.5 peak-sun-hours/day

### Regulation Time Window (IMPORTANT — verified)
| Parameter | Value |
|---|---|
| Regulation drive window | **08:00 – 17:00 = 9 h/day** (hard cap, §3.21.1) |
| Control stops | **9 fixed checkpoints** Katherine→Port Augusta × 30 min (§3.27.8) = **4.5 h total** |

**Control stops are now modelled by LOCATION (since 2026-06-21).** A 30-min halt is taken
when the car reaches each of the 9 checkpoint km from `data/route.csv` (310, 580, 850,
1120, 1400, 1670, 2040, 2290, 2550). The car still **charges from solar during a halt**.
Driving runs to the real **17:00 hard stop** each day; the previous model that ended the
day 1 h early (and used "2 stops/day") is retired. Net effect: stop time is **4.5 h
across the whole race**, not per-day. Effective moving time = 9 h/day × race_days − 4.5 h.

**10 h/day is NOT achievable** — the regulation window is only 9 h.

### Race Duration Feasibility (simulator results — BWSC 2027 official specs, location-based stops)

| Race days | Effective drive total | Required avg speed | Feasible? |
|---|---|---|---|
| 3 days | 22.5 h | 134.3 km/h | **NO** — optimized car covers 2804.1 km (92.8%), ~218 km short |
| **4 days** | **31.5 h** | **95.9 km/h** | **YES** — optimized car finishes in 24.5 h at 123.3 km/h, 66.4% SoC remaining |
| 5 days | 40.5 h | 74.6 km/h | YES |

**Race target: 4 days minimum. Optimized car completes the race in ~24.5 h effective drive
time, arriving Day 4 morning with a comfortable energy surplus (66.4% SoC).**

---

## ⚠️ Regulation Discrepancy — Simulator vs BWSC 2027 Official Specs

> The simulator was built with assumed WSC parameters that differ from the official 2027 BWSC regulations. Do not mix these without flagging which source you are using.

| Parameter | Simulator (assumed) | BWSC 2027 Official (§citation) |
|---|---|---|
| Solar panel area | 4.0 m² | **6.0 m²** (§2.4.2) |
| Battery energy | 5.5 kWh (19.8 MJ) | **11 MJ ≈ 3.06 kWh** (§2.5.2) |

The simulator's energy budget and car presets use the assumed values. Any official design work must use the BWSC 2027 values.

### BWSC 2027 Official Constraints (Challenger Class)
| Parameter | Value | Source |
|---|---|---|
| Solar area limit | **6 m²** | §2.4.2 |
| Battery energy limit | **11 MJ (~3.06 kWh)** | §2.5.2 |
| Cell type (team spec) | Li-ion 18650 — 3.7 V, 3.4 Ah, ~45 g/cell | Team spec |
| Max cells (11 MJ) | **242 cells → ~10.9 kg pack** | Derived from §2.5.2 |
| Daily driving window | **08:00 – 17:00** | §3.21.1 |
| Control stop duration | **30 min per stop** | §3.27.8 |

### Simulator Values (now updated to match BWSC 2027 official specs)
| Parameter | Value |
|---|---|
| Solar panel area | **6.0 m²** (§2.4.2) |
| Battery capacity | **3.056 kWh** (11 MJ ÷ 3.6, §2.5.2) |

---

## All 10 Loss Categories & Models (Simulator)

### 1. Aerodynamic Drag — DOMINANT (72–82% of energy at race speed)
```
F_drag = 0.5 × Cd × A × ρ × v²
P_drag = F_drag × v      (scales as v³)
```
- Default baseline: Cd=0.09, A=0.96 m²
- Optimized target: Cd=0.07, A=0.60 m²
- File: `losses/aerodynamic.py` → `aerodynamic_drag_power()`

### 2. Rolling Resistance
```
Crr_eff = Crr × (1 + v × speed_factor)
F_roll = Crr_eff × m × g × cos(θ)
P_roll = F_roll × v
```
- Default: Crr=0.0015, Target: Crr=0.0012
- File: `losses/rolling.py` → `rolling_resistance_power()`

### 3. Gradient / Elevation
```
θ = atan(grade_percent / 100)
F_grade = m × g × sin(θ)
P_grade = F_grade × v   (positive=uphill loss, negative=downhill)
Downhill recovery: P_regen = |P_grade| × η_regen
```
- Default regen: 72%, Target: 85%
- File: `losses/gradient.py` → `gradient_power()`

### 4. Drivetrain (Motor + Gear)
```
P_motor_in = P_mech / (η_motor × η_gear)
Loss = P_motor_in − P_mech
```
- Default: η_motor=0.96, η_gear=0.99 → 5% loss
- Target: η_motor=0.98, η_gear=0.995 → 2.5% loss
- File: `losses/drivetrain.py` → `drivetrain_input_power()`

### 5. Battery Internal Resistance
```
I = P_demand / V_bus
P_bat_loss = I² × R_int
```
- Default: R_int=0.08 Ω, V_bus=150V → ~31W at race speed
- Target: R_int=0.04 Ω, V_bus=200V → ~2W (near elimination)
- File: `losses/electrical.py` → `battery_internal_loss_power()`

### 6. Wiring / Harness
```
P_wire = I² × R_wire     (same I as battery)
```
- Default: R_wire=0.04 Ω → ~16W
- Target: R_wire=0.02 Ω, V_bus=200V → ~1W
- File: `losses/electrical.py` → `wiring_loss_power()`

### 7. Solar Panel (Temperature Derating)
```
f_temp = 1 + temp_coeff × (T_op − T_stc)
P_panel = area × η_panel × irradiance × f_temp
```
- Default: T_op=55°C → f_temp=0.867 (11.4% loss)
- Target: T_op=45°C → f_temp=0.924 (7.6% loss via active ventilation)
- File: `losses/solar.py` → `solar_panel_power()`

### 8. MPPT Losses
```
P_harvested = P_panel × η_mppt
```
- Default: η_mppt=0.98 (2% loss)
- Target: η_mppt=0.99 (SiC MOSFET controller)
- File: `losses/solar.py` → `mppt_loss_power()`

### 9. Regenerative Braking
Handled inside `gradient_power()`. On downhill, net P_grade is negative and
multiplied by `regen_efficiency` to reflect partial recovery.

### 10. Auxiliary Loads
| Component | Baseline | Target |
|---|---|---|
| Telemetry/GPS | 10W | 5W |
| Driver display | 5W | 3W |
| Safety electronics | 5W | 5W |
| Motor cooling fan | 15W | 5W |
| Steering/control ECU | 5W | 3W |
| Mandatory lights | 10W | 7W |
| Data logging | 3W | 1W |
| Horn/signals | 2W | 1W |
| **Total driving** | **55W** | **30W** |
| Parked | 10W | 8W |

File: `losses/auxiliary.py` → `auxiliary_power()`

---

## Car Presets (`models/car.py`)

| Preset | Cd | A (m²) | m (kg) | Crr | Panel eff | Solar m² | Battery kWh |
|---|---|---|---|---|---|---|---|
| `challenger_class()` | 0.09 | 0.96 | 180 | 0.0015 | 24.5% | **6.0 (§2.4.2)** | **3.056 (§2.5.2)** |
| `optimized_regulation()` | 0.07 | 0.60 | 150 | 0.0012 | 26.0% | **6.0 (§2.4.2)** | **3.056 (§2.5.2)** |

**`optimized_regulation()` is the correct target preset for the simulator.**
Finishes 3022 km in **4 days** (24.5 h effective drive) at avg **123.3 km/h**, 73.3% battery remaining.

### Required Spec Changes (baseline → optimized_regulation)
| Loss | Baseline | Required | Improvement |
|---|---|---|---|
| Aerodynamic drag | Cd=0.09, A=0.96m² | **Cd=0.07, A=0.60m²** | −51% drag power |
| Rolling resistance | Crr=0.0015, 180kg | **Crr=0.0012, 150kg** | −33% |
| Drivetrain | η=0.9504 | **η=0.9751** | −50% loss |
| Battery I²R | V=150V, R=0.08Ω | **V=200V, R=0.04Ω** | −94% |
| Wiring I²R | R=0.04Ω | **R=0.02Ω, V=200V** | −94% |
| Solar temp derate | T_op=55°C (−11.4%) | **T_op=45°C (−7.6%)** | +4.4pp output |
| MPPT | 98% | **99%** | +1pp |
| Auxiliary | 55W | **30W** | −45% |

Baseline car does NOT finish even in 4 days (covers only 2601 km, 86% of race).

---

## Dynamic Speed Profile (core simulation design)

Speed varies every 30-min timestep based on:
1. Solar irradiance at current time of day (bell curve, peaks at solar noon)
2. Battery SoC (discharge budget spread across remaining drive hours)
3. Grade at current route position (uphill slows, downhill allows regen)
4. Altitude (affects air density via standard atmosphere)

**Speed strategy** (`simulation/speed_strategy.py`):
```
P_available = P_solar + battery_discharge_budget(SoC, hours_remaining_today)
speed = bisection_solve(P_demand(v, grade, alt) = P_available)
speed = clip(speed, v_min=40, v_max=130)
```

**Example speed profile** (optimized car, WSC route):
- 08:00 (irr=237): ~85 km/h (low solar, battery supplement)
- 10:00 (irr=707): ~100 km/h
- 12:30 (irr=1000): ~115 km/h (peak solar)
- 15:00 (irr=707): ~105 km/h
- 17:00 (irr=237): ~85 km/h → stop

---

## Key Simulation Results

> Numbers below are with **location-based control stops** (9 × 30 min = 4.5 h, model
> updated 2026-06-21). Earlier figures used the retired "2 stops/day end-early" model.

### Baseline Challenger — 4-day race, WSC route (BWSC 2027 official specs)
- Covers **2925.4 km** (96.8% of race) — **does NOT finish** (~97 km short)
- Driving time 31.5 h, Avg speed 92.9 km/h, Final SoC **16.4%**
- Loss: drag 77.0%, rolling 7.5%, aux 6.6%, drivetrain 4.6%

### Optimized Regulation — 4-day race, WSC route ✓ (BWSC 2027 official specs)
- **Finishes 3022 km**, effective driving time **24.5 h** (completes Day 4 morning, 09:30)
- Avg speed: **123.3 km/h**, Final battery SoC: **66.4%**
- Loss: drag 83.5%, rolling 7.0%, aux 4.2%, drivetrain 2.4%

### Optimized Regulation — 3-day race, WSC route (for reference)
- Covers **2804.1 km** (92.8%) — **does NOT finish** (~218 km short; 9 stops cost more in 3 days)
- Avg speed: 124.6 km/h, Final SoC: 80.4%

---

## `RaceConfig` Key Parameters (`models/race.py`)
```python
RaceConfig(
    distance_km=3022.0,
    race_days=4,                       # default: 4 (3 not feasible)
    regulation_window_start=8.0,       # 08:00 hard start
    regulation_window_end=17.0,        # 17:00 hard stop  → 9h window (real drive_end)
    num_control_stops=9,               # fixed checkpoints taken by LOCATION (not per-day)
    control_stop_duration_min=30.0,    # 30 min per stop → 4.5 h total across the race
    # effective drive = 9h × race_days − 4.5h  (e.g. 4 days → 31.5 h)
)
```
Control-stop **positions** (cumulative km) come from `data/route.csv` (rows with
`control_stop=TRUE`); the simulator halts the car there and keeps charging from solar.
The CLI `--stops N` takes the first N of those checkpoints; `--stop-min` sets halt length.

---

## File Structure
```
solarcar/
├── CLAUDE.md                    ← this file (project memory)
├── main.py                      ← CLI entry point
├── models/
│   ├── car.py                   ← CarConfig + presets (challenger_class, optimized_regulation)
│   └── race.py                  ← RaceConfig (regulation window + control stops)
├── losses/
│   ├── aerodynamic.py           ← aerodynamic_drag_power()
│   ├── rolling.py               ← rolling_resistance_power()
│   ├── gradient.py              ← gradient_power() (includes regen)
│   ├── drivetrain.py            ← drivetrain_input_power()
│   ├── electrical.py            ← wiring_loss_power(), battery_internal_loss_power()
│   ├── solar.py                 ← solar_panel_power(), temperature_derating()
│   └── auxiliary.py             ← auxiliary_power()
├── environment/
│   ├── solar_model.py           ← SolarModel (irradiance bell curve, PSH)
│   ├── atmosphere.py            ← air_density(altitude, temp)
│   └── route.py                 ← RouteSegment, RouteProfile (flat / wsc / csv) + load_control_stops_km()
├── simulation/
│   ├── speed_strategy.py        ← SpeedStrategy (dynamic speed per timestep)
│   ├── simulator.py             ← RaceSimulator.run() (main loop; location-based control stops)
│   ├── energy_budget.py         ← EnergyBudget (aggregation + per-timestep traces)
│   ├── plots.py                 ← generate_plots() dashboard + per-day power (matplotlib)
│   └── tables.py                ← speed-profile table + CSV exporters
├── docs/
│   ├── race-plan.md             ← High-level 3-day race plan and speed analysis
│   └── session-memory.md        ← Persistent session memory log (read at session start)
├── regulations/
│   ├── bwsc-2027-regulations.md ← Full official BWSC 2027 regulations (PDF→Markdown)
│   ├── key-rules-summary.md     ← Quick-reference table of race-critical rules
│   └── README.md                ← Instructions for converting official PDF via markitdown
└── data/
    ├── route.csv                ← 11 checkpoints Darwin→Adelaide with coordinates
    ├── irradiance/              ← NASA POWER irradiance data 2022–2024 at 11 checkpoints
    └── elevation/               ← 58-point elevation profile Darwin→Adelaide
```

## How to Run
```bash
# 4-day race, optimized car, WSC elevation route (recommended)
python main.py --preset optimized_regulation --route wsc

# 4-day race, baseline car
python main.py --route wsc

# Fixed speed 95 km/h
python main.py --speed 95 --route wsc

# Speed sweep 40–130 km/h
python main.py --sweep --route wsc

# Verbose output with per-timestep trace
python main.py --preset optimized_regulation --route wsc --verbose

# Visualize: dashboard + per-day power plots, speed table, CSV export (needs matplotlib)
python main.py --preset optimized_regulation --route wsc --plot --table --csv

# Change control stop assumptions
python main.py --preset optimized_regulation --stops 3 --stop-min 20 --route wsc

# Override individual car params
python main.py --cd 0.07 --mass 155 --route wsc
```

---

## Verified Simulation Output (2026-06-21, BWSC 2027 official specs: 6 m² solar, 3.056 kWh battery; location-based control stops)

### `python main.py --preset optimized_regulation --route wsc`
```
Distance covered:  3022.0 km  ← FINISHES (Day 4, 09:30)
Driving time:        24.5 h
Average speed:      123.3 km/h
Final battery SoC:   66.4%
Energy in:         30807.3 Wh  (solar 30086 + battery 722)
Loss breakdown:    drag 83.5%, rolling 7.0%, aux 4.2%, drivetrain 2.4%
```

### `python main.py --preset optimized_regulation --route wsc --days 3`
```
Distance covered:  2804.1 km  ← DOES NOT FINISH (92.8%, ~218 km short)
Driving time:        22.5 h
Average speed:      124.6 km/h
Final battery SoC:   80.4%
```

### `python main.py --route wsc`  (baseline challenger)
```
Distance covered:  2925.4 km  ← DOES NOT FINISH (96.8%)
Driving time:        31.5 h
Average speed:       92.9 km/h
Final battery SoC:   16.4%
Energy in:         36027.2 Wh  (solar ~33650 + battery ~2377)
Loss breakdown:    drag 77.0%, rolling 7.5%, aux 6.6%, drivetrain 4.6%
```

### Visualization & export (added 2026-06-21)
```
# Dashboard (speed, SoC, power breakdown, elevation, irradiance) + per-day power bar,
# substantial-speed-change table, and CSV exports → output/
python main.py --preset optimized_regulation --route wsc --plot --table --csv
```
Requires `pip install -r requirements.txt` (matplotlib). Artifacts land in `output/`
(git-ignored): `dashboard.png`, `power_by_day.png`, `speed_table.csv`, `full_trace.csv`.

---

## Working Principles

### 1. Always wait for the next instruction
Do not proceed to the next planning phase or make assumptions about what comes next. Complete the requested task, then **stop and wait**.

### 2. Never fabricate numbers or data
Every numerical value must have a cited source (regulation section, datasheet, published data, or team measurement). Use `[SOURCE NEEDED]` for unknowns.

### 3. Flag discrepancies immediately
If a user-provided value conflicts with official regulations or a cited source, flag it before using it in any calculation.

### 4. Distinguish estimates from facts
- **Confirmed**: from a cited source
- **Estimated / approximate**: engineering approximation with stated basis
- **Pending**: needs official data not yet available

### 5. Regulation compliance first
All design and strategy decisions must be checked against the BWSC 2027 Event Regulations. Reference the section number in every compliance statement.

---

## Current Project Status

| Phase | Status |
|---|---|
| Python race simulator (all 10 losses) | **Complete** — verified results in main |
| High-level race plan | **Complete** (`docs/race-plan.md`) |
| Official BWSC 2027 regulations | **Complete** (`regulations/bwsc-2027-regulations.md`) |
| Key rules summary | **Complete** (`regulations/key-rules-summary.md`) |
| Route data | **Approximate** — pending official BWSC 2027 route notes |
| Irradiance data | **Complete** (`data/irradiance/`) |
| Elevation data | **Complete** (`data/elevation/`) |
| Simulator updated for BWSC 2027 official specs | **Complete** — 6 m² solar (§2.4.2), 3.056 kWh battery (§2.5.2) |
| Solar power budget | Not started |
| Battery design | Not started |
| Energy balance | Not started |
| Strategy model | Not started |

---

## Session Memory

Memory file: `docs/session-memory.md`

**Read `docs/session-memory.md` at the start of every session before doing any work.**

### compress command

When the user says "compress" (or "compress this session"):

1. Summarise the current session into a new dated entry:
   ```
   ## YYYY-MM-DD — <one-line headline>
   ### Accomplished
   ### Key Decisions / Findings
   ### Files Created / Modified
   ### Project Status
   ### Next Steps (waiting for instruction)
   ```
2. Prepend the new entry at the top of `docs/session-memory.md`, immediately below the file header.
3. Commit: `chore: compress session YYYY-MM-DD`
4. Push to the current branch.
5. Confirm to the user that memory has been saved.

---

## Session History

### Session 1 (2026-06-21) — Race Planning & Regulations
- Added BWSC 2027 official race plan, regulations (PDF→Markdown), route data
- Fetched irradiance (NASA POWER, 2022–2024) and elevation data (AWS tiles)
- Added session memory system (`docs/session-memory.md`)
- Key finding: BWSC 2027 limits are 6 m² solar and 11 MJ battery (different from simulator assumptions)
- Branch: `claude/solar-challenge-2027-plan-nsj4yl`

### Session 1 (2026-06-21) — Simulator Build
- Built full simulator from scratch: all 10 loss models, dynamic speed profile, WSC route
- Key corrections:
  - Regulation-fixed (simulator): solar 4.0 m² and battery 5.5 kWh
  - Drive window is 08:00–17:00 = 9h, NOT 10h; minus 2×30min stops = **8h effective**
  - 3-day finish is IMPOSSIBLE under assumed regulation energy (~111 km/h max; needs 125.9 km/h)
  - **4-day race at 94.4 km/h is the correct feasible target**
  - Removed `target_133kmh` preset (violated regulation limits)
- Branch: `claude/solar-car-losses-tivgr7`
- All code committed and pushed; clean state at session end

---

## What to Build Next (suggested)
1. ✅ **Matplotlib plots** — speed profile, SoC trace, power breakdown per day, elevation,
   irradiance (`simulation/plots.py`, `--plot`) — **DONE 2026-06-21**
2. ✅ **CSV export** — speed table + full per-timestep trace (`simulation/tables.py`, `--csv`) — **DONE**
3. **Whole-race battery strategy** *(agreed next step)* — replace the greedy per-day
   `battery_discharge_budget` (`speed_strategy.py`) with a lookahead that ensures charge
   lasts to Adelaide, not just to end of day.
4. **Regen → battery charging** — remove the `max(0.0, …)` clamp in `simulator.py` so
   downhill regen surplus charges the pack (bounded by a max regen current).
5. **Location-based irradiance** — wire `data/irradiance/` per-checkpoint data into the
   sim so solar varies by position, not just time of day.
6. **Sensitivity analysis** — rank which parameter most affects finish time.
7. **Wind model** — headwind/tailwind (Stuart Highway avg ~10 km/h headwind northbound).
8. **Cloud/weather model** — stochastic irradiance variation day-to-day.
9. **Race strategy optimizer** — optimal speed per segment to minimize total time.
10. **Web dashboard** — interactive sliders for real-time car parameter exploration.
