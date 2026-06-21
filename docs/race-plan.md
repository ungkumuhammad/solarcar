# Solar Car Race Plan — BWSC 2027

## Goal

Complete the Bridgestone World Solar Challenge 2027 (Challenger class) in **3 days**.

| Item | Value | Source |
|---|---|---|
| Race | Bridgestone World Solar Challenge 2027 | Official BWSC website |
| Class | Toyota Challenger | BWSC 2027 Event Regulations §2.1 |
| Route | Darwin → Adelaide | BWSC 2027 Event Regulations §3.20.1 |
| Route distance | ~3,000 km | BWSC 2027 Event Regulations §3.20.1 |
| Official race dates | 22–29 August 2027 | BWSC 2027 Event Regulations (cover page) |
| Daily start | 08:00 | BWSC 2027 Event Regulations §3.21.1–2 |
| Daily finish | 17:00 | BWSC 2027 Event Regulations §3.21.3 |

> **Note on target dates**: The team's stated target of 24–26 October 2027 does not align with the official event schedule of 22–29 August 2027. All calculations below use the official 9-hour driving window (08:00–17:00) regardless of calendar date, as the race format is unchanged. Target dates to be confirmed by the team.

---

## Vehicle Specifications (Regulation Limits)

| Parameter | Limit | Source |
|---|---|---|
| Solar collector area | max 6 m² | BWSC 2027 Event Regulations §2.4.2 |
| Battery energy | max 11 MJ | BWSC 2027 Event Regulations §2.5.2 |

### Battery Pack — 18650 Cell Sizing to 11 MJ Limit

Using the regulation formula: **E = 3600 × V × q** (§2.5.2)

Cell used: Li-ion 18650, spec as provided by team (3.7 V nominal, 3.4 Ah rated, ~45 g/cell)

| Metric | Calculation | Result |
|---|---|---|
| Energy per cell | 3600 × 3.7 V × 3.4 Ah | 45,288 J (45.3 kJ) |
| Max cell count (at 11 MJ) | 11,000,000 J ÷ 45,288 J | 242 cells (floor, to stay ≤ 11 MJ) |
| Pack energy (242 cells) | 242 × 45,288 J | 10,959,696 J ≈ 10.96 MJ |
| Pack mass | 242 × 45 g | 10,890 g ≈ 10.9 kg |
| Usable energy (80% DoD, guideline) | 10.96 MJ × 0.80 | ~8.77 MJ (2.44 kWh) |

> Cell voltage, capacity, and mass figures are team-provided. The 80% depth-of-discharge figure is an engineering guideline for Li-ion longevity — actual usable capacity will depend on BMS design and thermal conditions. These numbers must be verified against the chosen cell's manufacturer datasheet.

---

## Route Checkpoints

> **Important**: Official control stop locations for 2027 will be specified in the official route notes (§3.20.3). Locations and distances below are based on the historical BWSC Stuart Highway route and are approximate. Update from official route notes when published.

| # | Location | Territory | Segment (km) | Cumulative (km) |
|---|---|---|---|---|
| Start | Darwin | NT | — | 0 |
| 1 | Katherine | NT | ~310 | ~310 |
| 2 | Daly Waters | NT | ~270 | ~580 |
| 3 | Tennant Creek | NT | ~270 | ~850 |
| 4 | Barrow Creek | NT | ~270 | ~1,120 |
| 5 | Alice Springs | NT | ~280 | ~1,400 |
| 6 | Kulgera | NT | ~270 | ~1,670 |
| 7 | Coober Pedy | SA | ~370 | ~2,040 |
| 8 | Glendambo | SA | ~250 | ~2,290 |
| 9 | Port Augusta | SA | ~260 | ~2,550 |
| Finish | Adelaide | SA | ~450 | ~3,000 |

---

## Required Average Speed

All driving-window figures based on §3.21.1–3: 08:00–17:00 = **9 hours/day**.  
Control stop duration: **30 minutes** per stop (§3.27.8).  
Route distance: **~3,000 km** (§3.20.1).

### Scenario A — No control-stop deduction (theoretical minimum)

```
Driving hours  = 3 days × 9 h                    = 27 h
Required speed = 3,000 km ÷ 27 h                 ≈ 111 km/h
```

### Scenario B — 9 control stops × 30 min each deducted

```
Stop time      = 9 stops × 0.5 h                 = 4.5 h
Effective drive = 27 h − 4.5 h                   = 22.5 h
Required speed = 3,000 km ÷ 22.5 h               ≈ 133 km/h
```

### Scenario B is the operationally relevant number: **~133 km/h average**

### Speed limit context (Australian road law, Stuart Highway)

| Territory | Legal speed limit | km range (approx) |
|---|---|---|
| Northern Territory | 130 km/h | 0 – ~1,670 km (Darwin to Kulgera) |
| South Australia | 110 km/h | ~1,670 – 3,000 km (Kulgera to Adelaide) |

```
Weighted legal ceiling = (1,670 × 130 + 1,330 × 110) ÷ 3,000 ≈ 121 km/h
```

> **Conclusion**: The 133 km/h required average exceeds both the NT speed limit (130 km/h) and the weighted legal ceiling (~121 km/h). A strict 3-day finish is **not achievable within road speed limits** once control stops are accounted for. The practical minimum with full speed-limit compliance is approximately **3.5 days**. Strategy refinement (energy budget, optimal cruise speed, control-stop efficiency) is required in subsequent planning phases.

---

## 3-Day Daily Distance Targets (For Reference)

| Day | Start | Finish | Drive hours | Target km | Cumulative |
|---|---|---|---|---|---|
| Day 1 | 08:00 | 17:00 | 9 h | ~1,000 km | ~1,000 km |
| Day 2 | 08:00 | 17:00 | 9 h | ~1,000 km | ~2,000 km |
| Day 3 | 08:00 | 17:00 | 9 h | ~1,000 km | ~3,000 km |

---

## Next Steps

Items to develop in subsequent planning phases:

1. **Confirm team's target dates** — Official event is 22–29 August 2027, not October.
2. **Confirm cell model and manufacturer datasheet** — Required to correctly apply §2.5.2 energy formula.
3. **Solar power budget** — Model daily Wh harvest from 6 m² array in August on the Stuart Highway latitude band, using irradiance data (BoM or NASA POWER).
4. **Power-speed curve** — Aerodynamic drag + rolling resistance model to determine efficient cruise speed and energy consumption at different speeds.
5. **Energy balance per day** — Confirm solar-in vs drive-out allows 3-day plan at legal speeds.
6. **Battery configuration** — Series/parallel layout, BMS design, thermal management.
7. **Strategy model** — Dynamic speed adjustment based on state-of-charge, solar forecast, and remaining distance.
8. **Official route notes** — Update control stop locations and distances once published by BWSC.
