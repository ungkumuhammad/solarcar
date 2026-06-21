# Solar Car Race Plan — BWSC 2027

## Goal
Complete the Bridgestone World Solar Challenge 2027 (Challenger class) in **3 days**.

| Item | Value |
|---|---|
| Race | Bridgestone World Solar Challenge 2027 |
| Class | Toyota Challenger |
| Route | Darwin → Adelaide, ~3,022 km |
| Target start | 24 October 2027, 08:00 |
| Target finish | 26 October 2027, 17:00 |

> **⚠️ Date note**: Official BWSC 2027 is scheduled for **22–29 August 2027**, not October. Confirm race dates with the official regulations before finalising this plan.

---

## Vehicle Specs (as stated)

| Parameter | Value |
|---|---|
| Solar panel area | 4 m² |
| Battery chemistry | Li-ion 18650 |
| Cell spec | 3.7 V, 3.4 Ah, ~45 g/cell |
| Total battery mass | 20 kg |

> **⚠️ Spec note**: Official 2027 Challenger class allows 6 m² solar and 3 kWh battery. The 4 m² / 20 kg parameters above will be used until the user-provided regulations are confirmed.

### Battery Pack Estimate

| Metric | Calculation | Result |
|---|---|---|
| Cell count | 20,000 g ÷ 45 g/cell | ~444 cells |
| Gross pack energy | 444 × 3.7 V × 3.4 Ah | ~5.58 kWh |
| Usable energy (80% DoD) | 5.58 × 0.80 | ~4.46 kWh |

---

## Route Checkpoints

| # | Location | Segment (km) | Cumulative (km) |
|---|---|---|---|
| Start | Darwin | — | 0 |
| 1 | Katherine | ~310 | ~310 |
| 2 | Daly Waters | ~270 | ~580 |
| 3 | Tennant Creek | ~270 | ~850 |
| 4 | Barrow Creek | ~270 | ~1,120 |
| 5 | Alice Springs | ~280 | ~1,400 |
| 6 | Kulgera | ~270 | ~1,670 |
| 7 | Coober Pedy | ~370 | ~2,040 |
| 8 | Glendambo | ~250 | ~2,290 |
| 9 | Port Augusta | ~260 | ~2,550 |
| Finish | Adelaide | ~300 | ~3,022 |

---

## Required Average Speed

### Without control stops
```
Total distance   = 3,022 km
Driving hours    = 3 days × 9 h = 27 h
Required speed   = 3,022 ÷ 27 ≈ 112 km/h
```

### With 9 × 30-minute control stops
```
Stop time lost   = 9 × 0.5 h = 4.5 h
Effective drive  = 27 − 4.5 = 22.5 h
Required speed   = 3,022 ÷ 22.5 ≈ 134 km/h
```

### Legal speed cap impact
```
NT (0–1,670 km):  speed limit 130 km/h
SA (1,670–3,022 km): speed limit 110 km/h

Weighted max avg = (1,670 × 130 + 1,352 × 110) ÷ 3,022 ≈ 121 km/h
```

**Conclusion**: 3 days is theoretically feasible only if the car runs at the legal speed limit wall-to-wall and the 9 control stops are absorbed within the 27-hour window. A more conservative 3.5-day target (ending mid-afternoon Day 4) provides meaningful safety margin.

---

## 3-Day Daily Plan

| Day | Date | Drive window | Target distance | End point |
|---|---|---|---|---|
| Day 1 | 24 Oct | 08:00 – 17:00 | ~1,000 km | Near Alice Springs (~1,400 km) |
| Day 2 | 25 Oct | 08:00 – 17:00 | ~1,000 km | Near Glendambo (~2,290 km) |
| Day 3 | 26 Oct | 08:00 – 17:00 | ~730 km | Adelaide (~3,022 km) |

---

## Next Steps

1. **Confirm race dates** — verify whether the race is August 22–29 or October (user's stated dates).
2. **Confirm solar area & battery limits** — user to provide official regulation document.
3. **Solar power budget** — model daily Wh harvest from 4 m² (or 6 m²) in August/October along the Stuart Highway.
4. **Power-speed curve** — aerodynamic + rolling resistance model to find efficient cruise speed.
5. **Energy balance per day** — confirm energy in (solar) vs energy out (drive) allows 3-day plan.
6. **Battery design** — series/parallel configuration, BMS spec, thermal management.
7. **Strategy model** — dynamic speed adjustment based on state-of-charge and solar forecast.
