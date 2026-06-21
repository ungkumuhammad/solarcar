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
| Typical control stops | 2 stops × 30 min/day = **60 min lost/day** (§3.27.8) |
| **Effective driving/day** | **9 – 1 = 8.0 h/day** |

**10 h/day is NOT achievable** — the regulation window is only 9 h, and control stops reduce effective driving to ~8 h/day.

### Race Duration Feasibility (simulator results)

| Race days | Effective drive total | Required avg speed | Feasible (regulation energy)? |
|---|---|---|---|
| 3 days | 24 h | 125.9 km/h | **NO** — energy cap is ~111 km/h max |
| **4 days** | **32 h** | **94.4 km/h** | **YES** — optimized car finishes with 16% SOC |
| 5 days | 40 h | 75.5 km/h | YES — baseline car can also finish |

**Correct race target: 4 days, 8 h/day effective, 94.4 km/h required.**

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

### Simulator Assumed Constraints (used in Python code)
| Parameter | Fixed Value |
|---|---|
| Solar panel area | **4.0 m²** (hard cap in simulator) |
| Battery capacity | **5.5 kWh** (hard cap in simulator) |

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
| `challenger_class()` | 0.09 | 0.96 | 180 | 0.0015 | 24.5% | **4.0 (sim)** | **5.5 (sim)** |
| `optimized_regulation()` | 0.07 | 0.60 | 150 | 0.0012 | 26.0% | **4.0 (sim)** | **5.5 (sim)** |

**`optimized_regulation()` is the correct target preset for the simulator.**
Finishes 3022 km in **4 days** (8h/day effective) at avg **111.9 km/h**, 16.3% battery remaining.

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

### Baseline Challenger — 4-day race, WSC route
- Solar-neutral speed: **84.7 km/h**
- Covers **2601 km** (86% of race) — **does NOT finish**
- Avg speed: 81.3 km/h, Loss: drag 72%, rolling 9%, aux 9%, drivetrain 4.5%

### Optimized Regulation — 4-day race, WSC route ✓
- **Finishes 3022 km**, driving time 27h, avg **111.9 km/h**
- Final battery SoC: 16.3%
- Loss: drag 82%, rolling 8%, aux 5%, drivetrain 2.4%

---

## `RaceConfig` Key Parameters (`models/race.py`)
```python
RaceConfig(
    distance_km=3022.0,
    race_days=4,                       # default: 4 (3 not feasible)
    regulation_window_start=8.0,       # 08:00 hard start
    regulation_window_end=17.0,        # 17:00 hard stop  → 9h window
    control_stops_per_day=2,           # mandatory checkpoint halts
    control_stop_duration_min=30.0,    # → 60 min/day lost
    # effective drive = 9h - 1h = 8.0 h/day
)
```

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
│   └── route.py                 ← RouteSegment, RouteProfile (flat / wsc / csv)
├── simulation/
│   ├── speed_strategy.py        ← SpeedStrategy (dynamic speed per timestep)
│   ├── simulator.py             ← RaceSimulator.run() (main time-step loop)
│   └── energy_budget.py         ← EnergyBudget (result aggregation + print_summary)
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

# Change control stop assumptions
python main.py --preset optimized_regulation --stops 3 --stop-min 20 --route wsc

# Override individual car params
python main.py --cd 0.07 --mass 155 --route wsc
```

---

## Verified Simulation Output (2026-06-21)

### `python main.py --preset optimized_regulation --route wsc`
```
Distance covered:  3022.0 km  ← FINISHES
Driving time:        27.0 h
Average speed:      111.9 km/h
Final battery SoC:   16.3%
Energy in:         24835.5 Wh  (solar 20781 + battery 4054)
Loss breakdown:    drag 81.8%, rolling 7.9%, aux 5.1%, drivetrain 2.4%
```

### `python main.py --route wsc`  (baseline challenger)
```
Distance covered:  2601.1 km  ← DOES NOT FINISH (86%)
Driving time:        32.0 h
Average speed:       81.3 km/h
Final battery SoC:   18.2%
Energy in:         26122.9 Wh  (solar 22722 + battery 3401)
Loss breakdown:    drag 72.3%, rolling 9.0%, aux 9.2%, drivetrain 4.5%
```

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
| Simulator updated for BWSC 2027 official specs | **Not started** — solar area/battery differ from official |
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
1. **Reconcile simulator with BWSC 2027 official specs** — update solar area (4→6 m²) and battery (5.5→3.06 kWh) and re-run feasibility
2. **Matplotlib plots** — speed profile, SoC trace, power breakdown per day
3. **CSV export** — time-series trace for external analysis
4. **Sensitivity analysis** — rank which parameter has most impact on finish time
5. **Wind model** — headwind/tailwind (Stuart Highway avg ~10 km/h headwind northbound)
6. **Cloud/weather model** — stochastic irradiance variation day-to-day
7. **Race strategy optimizer** — find optimal speed per segment to minimize total time
8. **Web dashboard** — interactive sliders for real-time car parameter exploration
