# Key Rules Summary — BWSC 2027 Challenger Class

Quick reference for race planning and strategy.  
All rules cited from: **2027 BWSC Event Regulations V1.0, Published 07 May 2026**  
Full text: `regulations/bwsc-2027-regulations.md`

---

## Hard Limits

| Rule | Value | Regulation ref |
|---|---|---|
| Solar collector area (Challenger) | max **6 m²** | §2.4.2 |
| Battery energy (Challenger) | max **11 MJ** | §2.5.2 |
| Battery energy formula | E = 3600 × V × q (joules) | §2.5.2 |
| Daily start time | **08:00** all days incl. Day 1 | §3.21.1, §3.21.2 |
| Daily finish time | **17:00** | §3.21.3 |
| Control stop duration | **30 minutes** + any penalty time | §3.27.8 |
| Night driving | Prohibited (sunset–sunrise) | §3.24.8 |
| Grid charging (Challenger) | Prohibited | §3.19.2 |
| Battery removal | Prohibited; damaged cells may be bypassed | §3.19.3 |
| Push-starting | Prohibited | §3.24.5 |

---

## Late Finish Penalty (§3.21.4)

| Minutes past 17:00 | Penalty |
|---|---|
| 1–10 minutes | 1 min penalty per minute late |
| Beyond 10 minutes | 2 min penalty per additional minute |

Penalty applied as equivalent delay to next day's official start time.

---

## Control Stop Procedure (§3.27)

1. Park in space designated by Control Stop officials (§3.27.4)
2. Arriving driver reconfigures vehicle for solar charging — alone, before timing starts (§3.27.6)
3. Arriving driver activates timing system — 30-minute clock starts (§3.27.7)
4. Team must not touch vehicle until 5 minutes before end (§3.27.10)
5. At T−5 min: departing driver (alone) reconfigures for driving (§3.27.11)
6. Vehicle departs only after full 30 minutes elapsed and all safety checks complete (§3.27.12)

> **Overnight control stop**: Timing pauses at 17:00 and resumes at 08:00 next day. Vehicle must be removed from control stop at 17:00. (§3.27.9)

---

## Energy Storage — 11 MJ Calculation for 18650 Cells

Using §2.5.2 formula: **E = 3600 × V × q**

With Samsung/standard 18650 (manufacturer spec: 3.7 V nominal, 3.4 Ah rated):

```
Energy per cell = 3600 × 3.7 V × 3.4 Ah = 45,288 J
Max cells       = 11,000,000 J ÷ 45,288 J = 242.9 → max 242 cells
Max pack mass   = 242 × 45 g             = 10,890 g ≈ 10.9 kg
```

> Cell spec (3.7 V, 3.4 Ah, 45 g) provided by team. Cell count limit will change if a different cell model is used — always recalculate using §2.5.2 formula with manufacturer's endorsed spec sheet.

---

## Driving Hours Per Day

| Day | Start | Finish | Available hours |
|---|---|---|---|
| Day 1 | 08:00 | 17:00 | 9.0 h |
| Day 2 | 08:00 | 17:00 | 9.0 h |
| Day 3 | 08:00 | 17:00 | 9.0 h |
| Day N | 08:00 | 17:00 | 9.0 h |

Start time for Day 2+ adjusts if team incurred late-finish penalty the previous day (§3.21.4).

---

## Route

| Detail | Value | Regulation ref |
|---|---|---|
| Route | Darwin → Adelaide via major highways | §3.20.1 |
| Approximate distance | ~3,000 km | §3.20.1 |
| Control stop locations | Published in official route notes | §3.20.3 |

> Exact control stop locations are not specified in V1.0 of the regulations. They will be published in the official route notes. The 9-stop estimate in `docs/race-plan.md` and `data/route.csv` is based on historical BWSC route patterns and should be updated once official route notes are released.
