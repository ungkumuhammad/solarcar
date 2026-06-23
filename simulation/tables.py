"""Tabular views of a simulation run.

The speed-profile table condenses the per-timestep trace into one row per
*substantial* change in speed, so the dynamic profile is readable at a glance.
CSV exporters write both the condensed table and the full per-timestep trace.
"""
from __future__ import annotations
import csv
from typing import List, Dict

from simulation.energy_budget import EnergyBudget
from environment.route import control_stop_name_at


TABLE_COLUMNS = [
    "Day", "Time", "Dist_km", "Speed_kmh", "dSpeed", "Irr_Wm2",
    "Grade_pct", "Elev_m", "Solar_W", "Demand_W", "SoC_pct", "Note",
]


def _fmt_time(t: float) -> str:
    """Render an elapsed time (day + hour/24) as ``DwHH:MM``."""
    day = int(t)
    hod = (t - day) * 24.0
    h = int(hod)
    m = int(round((hod - h) * 60))
    if m == 60:
        h += 1
        m = 0
    return f"D{day + 1} {h:02d}:{m:02d}"


def speed_profile_table(budget: EnergyBudget, threshold_kmh: float = 5.0) -> List[Dict]:
    """One row per substantial speed change among the *driving* timesteps.

    Always emits each day's first driving row (shows morning start SoC after overnight
    charging) and the final driving row, plus any control-stop rows.
    """
    rows: List[Dict] = []
    last_emitted_speed = None
    last_day = None
    n = len(budget.time_trace)

    driving_idx = [i for i in range(n) if budget.driving_trace[i]]
    last_driving = driving_idx[-1] if driving_idx else None

    for i in range(n):
        driving = budget.driving_trace[i]
        control_stop = budget.control_stop_trace[i]
        day = budget.day_trace[i]
        speed = budget.speed_trace[i]

        if control_stop:
            # Collapse a multi-step halt into a single row at its start.
            if rows and rows[-1].get("_is_stop") and rows[-1]["Day"] == day \
                    and abs(rows[-1]["Dist_km"] - budget.distance_trace[i]) < 0.5:
                continue
            nm = control_stop_name_at(budget.distance_trace[i])
            note = f"CONTROL STOP — {nm}" if nm else "CONTROL STOP"
            rows.append(_make_row(budget, i, delta=0.0, note=note, is_stop=True))
            continue

        if not driving:
            continue

        first_of_day = day != last_day
        is_last = i == last_driving
        big_change = last_emitted_speed is None or abs(speed - last_emitted_speed) >= threshold_kmh

        if first_of_day or is_last or big_change:
            delta = 0.0 if last_emitted_speed is None else speed - last_emitted_speed
            note = "day start" if first_of_day else ("finish" if is_last else "")
            rows.append(_make_row(budget, i, delta=delta, note=note))
            last_emitted_speed = speed
        last_day = day

    return rows


def _make_row(budget: EnergyBudget, i: int, delta: float, note: str, is_stop: bool = False) -> Dict:
    return {
        "Day": budget.day_trace[i],
        "Time": _fmt_time(budget.time_trace[i]),
        "Dist_km": round(budget.distance_trace[i], 1),
        "Speed_kmh": round(budget.speed_trace[i], 1),
        "dSpeed": round(delta, 1),
        "Irr_Wm2": round(budget.irradiance_trace[i]),
        "Grade_pct": round(budget.grade_trace[i], 2),
        "Elev_m": round(budget.altitude_trace[i]),
        "Solar_W": round(budget.solar_trace[i]),
        "Demand_W": round(budget.demand_trace[i]),
        "SoC_pct": round(budget.soc_trace[i] * 100, 1),
        "Note": note,
        "_is_stop": is_stop,
    }


def print_speed_profile_table(budget: EnergyBudget, threshold_kmh: float = 5.0) -> None:
    rows = speed_profile_table(budget, threshold_kmh)
    if not rows:
        print("\n  (no driving steps to tabulate)")
        return
    print(f"\n  SPEED PROFILE — one row per >= {threshold_kmh:.0f} km/h change "
          f"(+ day starts, control stops, finish)")
    header = (f"  {'Time':>9}  {'Dist':>7}  {'Speed':>6}  {'Δ':>5}  {'Irr':>5}  "
              f"{'Grd%':>5}  {'Elev':>5}  {'Solar':>6}  {'Demand':>6}  {'SoC':>5}  Note")
    print(header)
    print("  " + "-" * (len(header) - 2))
    for r in rows:
        print(f"  {r['Time']:>9}  {r['Dist_km']:>6.1f}k  {r['Speed_kmh']:>5.1f}  "
              f"{r['dSpeed']:>+5.1f}  {r['Irr_Wm2']:>5}  {r['Grade_pct']:>+5.2f}  "
              f"{r['Elev_m']:>5}  {r['Solar_W']:>5}W  {r['Demand_W']:>5}W  "
              f"{r['SoC_pct']:>4.1f}%  {r['Note']}")


def write_table_csv(budget: EnergyBudget, path: str, threshold_kmh: float = 5.0) -> None:
    rows = speed_profile_table(budget, threshold_kmh)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TABLE_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in TABLE_COLUMNS})


def write_full_trace_csv(budget: EnergyBudget, path: str) -> None:
    """Export every recorded timestep with all aligned traces."""
    cols = [
        ("time", budget.time_trace), ("day", budget.day_trace),
        ("distance_km", budget.distance_trace), ("speed_kmh", budget.speed_trace),
        ("soc", budget.soc_trace), ("irradiance_wm2", budget.irradiance_trace),
        ("grade_pct", budget.grade_trace), ("altitude_m", budget.altitude_trace),
        ("solar_w", budget.solar_trace), ("demand_w", budget.demand_trace),
        ("driving", budget.driving_trace), ("control_stop", budget.control_stop_trace),
        ("drag_w", budget.drag_w_trace), ("rolling_w", budget.rolling_w_trace),
        ("gradient_w", budget.gradient_w_trace), ("drivetrain_w", budget.drivetrain_w_trace),
        ("aux_w", budget.aux_w_trace), ("electrical_w", budget.electrical_w_trace),
    ]
    names = [c[0] for c in cols]
    series = [c[1] for c in cols]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(names)
        for row in zip(*series):
            writer.writerow(row)
