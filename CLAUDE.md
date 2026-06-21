# Solar Car Race Simulator — Project Memory

## Project Purpose
Python simulator for a WSC/BWSC-style solar race car (Challenger class).
Models all energy losses to determine whether the car can finish a 3-day race
and what car specifications are required.

---

## Race Scenario (baseline)
- **Route:** Darwin → Adelaide, Stuart Highway (3022 km)
- **Race days:** 3
- **Driving window:** 8am–6pm (WSC regulations), effective ~10h/day after control stops
- **Required average speed to finish:** 3022 / (10h × 3days) = **100.7 km/h**
- **Solar location:** Stuart Highway, Australia (~-23.7° latitude)
- **Solar model:** sine bell-curve, sunrise 6:30, sunset 18:30, peak 1000 W/m², 6.5 peak-sun-hours/day

---

## Regulation Constraints (CANNOT be changed — WSC Challenger class)
| Parameter | Fixed Value |
|---|---|
| Solar panel area | **4.0 m²** (hard cap) |
| Battery capacity | **5.5 kWh** (hard cap) |

### Energy Budget Consequence
With these fixed, total available energy over 3 days:
- Solar: 4.0 × 0.245 × 6.5 × 3 × 0.867 × 0.98 ≈ **16.2 kWh**
- Battery (80% initial SOC usable): **4.4 kWh**
- **Total fixed budget: ~20.6 kWh**

This energy ceiling caps the achievable speed regardless of other improvements:
| Driving hours/day | Max avg speed (best car) | Distance in 3 days |
|---|---|---|
| 7.5 h/day | 113.6 km/h | 2556 km — **NOT enough to finish** |
| 8.5 h/day | 108.6 km/h | 2769 km — **NOT enough** |
| **10.0 h/day** | **102.3 km/h** | **3070 km — FINISHES 3022 km** |

**Key conclusion:** To finish in 3 days within regulation, you must drive ~10h/day at ~100-104 km/h. 133 km/h is physically impossible on regulation energy.

---

## All 10 Loss Categories & Models

### 1. Aerodynamic Drag — DOMINANT (81–83% of energy at race speed)
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
- REGULATION LOCKED: area=4.0 m² max
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

## Car Presets (models/car.py)

| Preset | Cd | A (m²) | m (kg) | Crr | Panel eff | Solar m² | Battery kWh |
|---|---|---|---|---|---|---|---|
| `challenger_class()` | 0.09 | 0.96 | 180 | 0.0015 | 24.5% | **4.0 (reg)** | **5.5 (reg)** |
| `optimized_regulation()` | 0.07 | 0.60 | 150 | 0.0012 | 26.0% | **4.0 (reg)** | **5.5 (reg)** |

**`optimized_regulation()` is the correct target preset** — stays within regulation,
finishes the race with 10h/day driving at avg 104.2 km/h, 10% battery remaining.

---

## Dynamic Speed Profile (core simulation design)

Speed is NOT constant — it varies each 30-minute timestep based on:
1. Solar irradiance at current time of day (bell curve, peaks at solar noon)
2. Battery SoC (discharge budget = spread remaining usable energy across remaining drive hours)
3. Grade at current route position (uphill slows, downhill allows faster speed + regen)
4. Altitude (affects air density via standard atmosphere model)

**Speed strategy algorithm** (`simulation/speed_strategy.py`):
```
P_available = P_solar + battery_discharge_budget(SoC, hours_remaining_today)
speed = bisection_solve(P_demand(v, grade, alt) = P_available)
speed = clip(speed, v_min=40, v_max=130)
```

**Example speed profile** (baseline car, flat route, one day):
| Time | Irr | Speed | SoC |
|---|---|---|---|
| 8:30 | 354 W/m² | 84 km/h | 77% |
| 10:00 | 707 W/m² | 94 km/h | 61% |
| 12:30 | 1000 W/m² | 102 km/h | 41% |
| 15:00 | 707 W/m² | 95 km/h | 18% |
| 16:00 | 475 W/m² | 92 km/h | 13% |

---

## Key Simulation Results

### Baseline Challenger (regulation-compliant, stock specs)
- Solar-neutral speed: **84.7 km/h** (runs forever on solar alone)
- 3 days × 7.5h/day: covers **1942 km** at avg **86.3 km/h** (64% of race)
- Loss breakdown: drag 78%, rolling 9%, aux 8.5%, drivetrain 4.5%

### Optimized Regulation (Cd=0.07, A=0.60, m=150kg — solar/bat fixed)
- **Finishes 3022 km in 3 days** (YES) — 29h driving, avg **104.2 km/h**
- Final battery SoC: 10.1% (nearly depleted — well-optimized)
- Loss breakdown: drag 81%, rolling 8.5%, aux 5%, drivetrain 2.4%

### Required Spec Changes (baseline → optimized_regulation)
| Loss | Baseline | Required | Improvement |
|---|---|---|---|
| Aerodynamic drag | Cd=0.09, A=0.96m² | **Cd=0.07, A=0.60m²** | −51% drag power |
| Rolling resistance | Crr=0.0015, 180kg | **Crr=0.0012, 150kg** | −33% |
| Drivetrain | η=0.9504 | **η=0.9751** | −50% loss |
| Battery I²R | V=150V, R=0.08Ω | **V=200V, R=0.04Ω** | −94% |
| Wiring I²R | R=0.04Ω | **R=0.02Ω, V=200V** | −94% |
| Solar temp derate | T_op=55°C, -11.4% | **T_op=45°C, -7.6%** | +4.4pp output |
| MPPT | 98% | **99%** | +1pp |
| Auxiliary | 55W | **30W** | −45% |

---

## File Structure
```
solarcar/
├── CLAUDE.md                    ← this file
├── main.py                      ← CLI: python main.py [--preset] [--drive-hours] [--route] [--sweep]
├── models/
│   ├── car.py                   ← CarConfig dataclass + presets
│   └── race.py                  ← RaceConfig dataclass
├── losses/
│   ├── aerodynamic.py           ← aerodynamic_drag_power()
│   ├── rolling.py               ← rolling_resistance_power()
│   ├── gradient.py              ← gradient_power()  (includes regen)
│   ├── drivetrain.py            ← drivetrain_input_power()
│   ├── electrical.py            ← wiring_loss_power(), battery_internal_loss_power()
│   ├── solar.py                 ← solar_panel_power(), temperature_derating()
│   └── auxiliary.py             ← auxiliary_power()
├── environment/
│   ├── solar_model.py           ← SolarModel (irradiance bell curve)
│   ├── atmosphere.py            ← air_density(altitude, temp)
│   └── route.py                 ← RouteSegment, RouteProfile (flat / wsc / csv)
└── simulation/
    ├── speed_strategy.py        ← SpeedStrategy (dynamic speed computation)
    ├── simulator.py             ← RaceSimulator.run() (main time-step loop)
    └── energy_budget.py         ← EnergyBudget (result aggregation + print)
```

## How to Run
```bash
# Dynamic speed, baseline car, flat route
python main.py

# Optimized car (regulation-compliant), WSC elevation route, 10h/day
python main.py --preset optimized_regulation --route wsc --drive-hours 10

# Fixed speed 100 km/h
python main.py --speed 100 --drive-hours 10

# Speed sweep 40–130 km/h
python main.py --sweep --drive-hours 10

# Verbose with speed trace
python main.py --preset optimized_regulation --drive-hours 10 --verbose

# Override individual params
python main.py --cd 0.07 --mass 155 --drive-hours 10
```

---

## What to Build Next (suggested)
1. **CSV export** — export time-series trace to CSV for plotting
2. **Matplotlib plots** — speed profile, SoC trace, power breakdown per day
3. **Sensitivity analysis** — which parameter has most impact on finish time?
4. **Wind model** — headwind/tailwind effect (Stuart Highway avg headwind data)
5. **Cloud/weather model** — stochastic irradiance variation
6. **Race strategy optimizer** — binary search for optimal constant speed per day
7. **Web dashboard** — interactive sliders for car parameters
