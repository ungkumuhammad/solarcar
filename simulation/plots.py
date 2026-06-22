"""Matplotlib visualisations of a simulation run.

Two figures are produced:
  * dashboard.png    — 5 stacked panels (speed, SoC, power breakdown, elevation,
                       irradiance) over elapsed race time, with control stops and
                       overnight/parked charging visible.
  * power_by_day.png — stacked bar of energy (Wh) consumed per loss category per day.

Uses the headless Agg backend so it works without a display.
"""
from __future__ import annotations
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from simulation.energy_budget import EnergyBudget


LOSS_SERIES = [
    ("Aerodynamic drag", "drag_w_trace", "#d62728"),
    ("Rolling resistance", "rolling_w_trace", "#ff7f0e"),
    ("Gradient (net)", "gradient_w_trace", "#8c564b"),
    ("Drivetrain", "drivetrain_w_trace", "#9467bd"),
    ("Auxiliary", "aux_w_trace", "#2ca02c"),
    ("Electrical (wire+batt)", "electrical_w_trace", "#1f77b4"),
]


def _title(car, race, budget: EnergyBudget) -> str:
    done = "FINISHED" if budget.race_completed else "did not finish"
    return (f"Solar Car — {budget.total_distance_km:.0f} km ({done})  |  "
            f"avg {budget.avg_speed_kmh:.1f} km/h  |  final SoC {budget.final_soc*100:.1f}%  |  "
            f"Cd={car.Cd} A={car.frontal_area}m² m={car.mass_kg}kg")


def generate_plots(budget: EnergyBudget, car, race, outdir: str = "output") -> list:
    os.makedirs(outdir, exist_ok=True)
    paths = []
    paths.append(_dashboard(budget, car, race, outdir))
    paths.append(_power_by_day(budget, race, outdir))
    return paths


def _day_boundaries(t):
    """Elapsed-time values where the race day rolls over (for vertical guide lines)."""
    bounds = set()
    for v in t:
        bounds.add(int(v))
    return sorted(b for b in bounds if b > 0)


def _dashboard(budget: EnergyBudget, car, race, outdir: str) -> str:
    t = budget.time_trace
    drive = budget.driving_trace

    fig, axes = plt.subplots(5, 1, figsize=(13, 15), sharex=True)
    fig.suptitle(_title(car, race, budget), fontsize=12, y=0.995)

    # Mark control stops once for the legend.
    stop_t = [t[i] for i in range(len(t)) if budget.control_stop_trace[i]]

    def mark_stops(ax):
        for i, st in enumerate(stop_t):
            ax.axvline(st, color="0.6", lw=0.8, ls=":",
                       label="control stop" if i == 0 else None)
        for b in _day_boundaries(t):
            ax.axvline(b, color="0.3", lw=0.8, ls="--")

    # 1) Speed (km/h) — 0 while parked/stopped
    ax = axes[0]
    ax.plot(t, budget.speed_trace, color="#1f77b4", lw=1.2)
    ax.fill_between(t, budget.speed_trace, color="#1f77b4", alpha=0.15)
    ax.set_ylabel("Speed\n(km/h)")
    mark_stops(ax)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title("Dynamic speed profile (drops to 0 at control stops / overnight)", fontsize=9)

    # 2) State of charge (%)
    ax = axes[1]
    soc_pct = [s * 100 for s in budget.soc_trace]
    ax.plot(t, soc_pct, color="#2ca02c", lw=1.4)
    ax.fill_between(t, soc_pct, color="#2ca02c", alpha=0.15)
    ax.set_ylabel("Battery\nSoC (%)")
    ax.set_ylim(0, 100)
    mark_stops(ax)
    ax.set_title("SoC carries across days; ramps up during evening/morning charging", fontsize=9)

    # 3) Power breakdown (stacked) + solar input line
    ax = axes[2]
    labels = [s[0] for s in LOSS_SERIES]
    colors = [s[2] for s in LOSS_SERIES]
    stacks = [getattr(budget, s[1]) for s in LOSS_SERIES]
    ax.stackplot(t, *stacks, labels=labels, colors=colors, alpha=0.85)
    ax.plot(t, budget.solar_trace, color="black", lw=1.0, ls="-", label="Solar input")
    ax.set_ylabel("Power\n(W)")
    mark_stops(ax)
    ax.legend(loc="upper right", fontsize=7, ncol=2)
    ax.set_title("Instantaneous power demand by loss category, vs solar input", fontsize=9)

    # 4) Elevation (m) with up/down shading
    ax = axes[3]
    ax.plot(t, budget.altitude_trace, color="#8c564b", lw=1.2)
    ax.fill_between(t, budget.altitude_trace, color="#8c564b", alpha=0.2)
    ax.set_ylabel("Elevation\n(m)")
    mark_stops(ax)
    ax.set_title("Route elevation at the car's position", fontsize=9)

    # 5) Irradiance (W/m²) — full daylight envelope incl. parked charging
    ax = axes[4]
    ax.plot(t, budget.irradiance_trace, color="#ff7f0e", lw=1.2)
    ax.fill_between(t, budget.irradiance_trace, color="#ff7f0e", alpha=0.2)
    ax.set_ylabel("Irradiance\n(W/m²)")
    ax.set_xlabel("Elapsed race time (day index; tick = start of day)")
    mark_stops(ax)
    ax.set_title("Solar irradiance (clear-sky bell curve by time of day)", fontsize=9)

    fig.tight_layout(rect=[0, 0, 1, 0.99])
    path = os.path.join(outdir, "dashboard.png")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _power_by_day(budget: EnergyBudget, race, outdir: str) -> str:
    dt_h = race.time_step_min / 60.0
    days = sorted(set(budget.day_trace))
    # Aggregate energy (Wh) per day per loss category from the power traces.
    energy = {label: [] for label, _, _ in LOSS_SERIES}
    for d in days:
        idxs = [i for i, dd in enumerate(budget.day_trace) if dd == d]
        for label, attr, _ in LOSS_SERIES:
            series = getattr(budget, attr)
            energy[label].append(sum(series[i] for i in idxs) * dt_h)

    fig, ax = plt.subplots(figsize=(10, 6))
    bottoms = [0.0] * len(days)
    x = [f"Day {d}" for d in days]
    for label, _, color in LOSS_SERIES:
        vals = energy[label]
        ax.bar(x, vals, bottom=bottoms, label=label, color=color, alpha=0.88)
        bottoms = [b + v for b, v in zip(bottoms, vals)]

    for xi, tot in enumerate(bottoms):
        ax.text(xi, tot, f"{tot/1000:.1f} kWh", ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Energy consumed (Wh)")
    ax.set_title("Power/energy breakdown per race day")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    path = os.path.join(outdir, "power_by_day.png")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
