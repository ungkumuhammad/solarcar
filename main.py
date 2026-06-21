#!/usr/bin/env python3
"""Solar Car Race Simulator — CLI entry point.

Usage examples:
  python main.py                             # dynamic speed, WSC route
  python main.py --speed 100                 # fixed 100 km/h
  python main.py --preset target_133kmh      # target specs for 133 km/h race
  python main.py --sweep                     # speed sweep 40–130 km/h
  python main.py --route wsc --verbose
"""
import argparse
import sys

import os

from models.car import CarConfig
from models.race import RaceConfig
from environment.route import RouteProfile, load_control_stops_km, OFFICIAL_CONTROL_STOPS_KM
from simulation.simulator import RaceSimulator
from simulation.energy_budget import EnergyBudget
from simulation import tables


def build_car(args) -> CarConfig:
    preset = getattr(args, "preset", None)
    if preset == "challenger":
        car = CarConfig.challenger_class()
    elif preset == "optimized_regulation":
        car = CarConfig.optimized_regulation()
    elif preset == "json" and args.car_config:
        car = CarConfig.from_json(args.car_config)
    else:
        car = CarConfig()

    # Allow per-parameter overrides
    overrides = {
        "Cd": args.cd, "frontal_area": args.frontal_area,
        "mass_kg": args.mass, "Crr": args.crr,
        "panel_area": args.panel_area, "panel_efficiency": args.panel_eff,
        "battery_capacity_kwh": args.battery_kwh,
    }
    for attr, val in overrides.items():
        if val is not None:
            setattr(car, attr, val)
    return car


def build_route(args) -> RouteProfile:
    route_name = getattr(args, "route", "flat")
    if route_name == "wsc":
        return RouteProfile.wsc_approximation()
    elif route_name and route_name.endswith(".csv"):
        return RouteProfile.from_csv(route_name)
    return RouteProfile.flat(args.distance)


def print_day_table(budget: EnergyBudget) -> None:
    if not budget.speed_trace:
        return
    print("\n  SPEED PROFILE SAMPLE (every 5 records)")
    print(f"  {'Day.Hr':>7}  {'Speed':>8}  {'Solar':>7}  {'Demand':>7}  {'SoC':>6}")
    print("  " + "-" * 46)
    for i in range(0, len(budget.speed_trace), max(1, len(budget.speed_trace) // 20)):
        t = budget.time_trace[i]
        day = int(t) + 1
        hr = (t % 1) * 24
        print(f"  Day{day} {hr:4.1f}h  {budget.speed_trace[i]:>7.1f}km/h"
              f"  {budget.solar_trace[i]:>6.0f}W  {budget.demand_trace[i]:>6.0f}W"
              f"  {budget.soc_trace[i]*100:>5.1f}%")


def run_sweep(car: CarConfig, race: RaceConfig, route: RouteProfile, speeds) -> None:
    print(f"\n{'Speed':>7}  {'Distance':>9}  {'Done':>5}  {'AvgSpd':>7}  "
          f"{'Solar':>8}  {'BatUsed':>8}  {'Surplus':>9}")
    print("-" * 72)
    for spd in speeds:
        sim = RaceSimulator(car, race, route, fixed_speed_kmh=spd)
        b = sim.run()
        surplus = b.total_energy_available_wh() - b.total_energy_consumed_wh()
        print(f"{spd:>6.0f}  {b.total_distance_km:>8.0f}km  "
              f"{'YES' if b.race_completed else 'NO':>5}  "
              f"{b.avg_speed_kmh:>6.1f}  "
              f"{b.solar_harvested_wh/1000:>7.2f}kWh  "
              f"{b.battery_net_used_wh/1000:>7.2f}kWh  "
              f"{surplus/1000:>+8.2f}kWh")


def main():
    parser = argparse.ArgumentParser(
        description="Solar Car Race Simulator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--speed", type=float, default=None,
                        help="Fixed target speed km/h (dynamic if omitted)")
    parser.add_argument("--distance", type=float, default=3022.0, help="Race distance km")
    parser.add_argument("--days", type=int, default=4, help="Race days (3-day NOT feasible under regulation)")
    parser.add_argument("--stops", type=int, default=9,
                        help="Number of control stops (taken at checkpoint locations)")
    parser.add_argument("--stop-min", type=float, default=30.0, help="Minutes per control stop")
    parser.add_argument("--preset", choices=["challenger", "optimized_regulation"],
                        default="challenger", help="Car preset")
    parser.add_argument("--car-config", type=str, help="Path to JSON car config")
    parser.add_argument("--route", default="flat", help="'flat', 'wsc', or path to CSV")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--sweep", action="store_true", help="Sweep speeds 40–130 km/h")
    # Visualisation / export
    parser.add_argument("--plot", action="store_true", help="Save dashboard + per-day PNGs")
    parser.add_argument("--table", action="store_true",
                        help="Print speed-profile table (one row per substantial speed change)")
    parser.add_argument("--csv", action="store_true", help="Export speed table + full trace CSVs")
    parser.add_argument("--out", default="output", help="Output directory for plots/CSVs")
    parser.add_argument("--table-threshold", type=float, default=5.0, dest="table_threshold",
                        help="km/h change that counts as a new table row")
    # Parameter overrides
    parser.add_argument("--cd", type=float, default=None)
    parser.add_argument("--frontal-area", type=float, default=None, dest="frontal_area")
    parser.add_argument("--mass", type=float, default=None)
    parser.add_argument("--crr", type=float, default=None)
    parser.add_argument("--panel-area", type=float, default=None, dest="panel_area")
    parser.add_argument("--panel-eff", type=float, default=None)
    parser.add_argument("--battery-kwh", type=float, default=None)

    args = parser.parse_args()

    car = build_car(args)
    route = build_route(args)

    # Control-stop positions: from a CSV route if given, else official BWSC stops.
    route_name = getattr(args, "route", "flat")
    if route_name and route_name.endswith(".csv") and os.path.exists(route_name):
        control_stops_km = load_control_stops_km(route_name)
    else:
        control_stops_km = list(OFFICIAL_CONTROL_STOPS_KM)
    control_stops_km = [s for s in control_stops_km if s < args.distance][:args.stops]

    race = RaceConfig(
        distance_km=args.distance,
        race_days=args.days,
        num_control_stops=len(control_stops_km),
        control_stop_duration_min=args.stop_min,
    )

    print(f"\n{'='*60}")
    print(f"  Solar Car Race Simulator")
    print(f"  Race:  {race.distance_km:.0f} km  |  {race.race_days} days")
    print(f"  Time:  {race.regulation_window_h:.0f}h window/day (08:00–17:00)  |  "
          f"{race.num_control_stops} control stops × {race.control_stop_duration_min:.0f} min "
          f"= {race.total_control_stop_hours:.1f} h total")
    print(f"  Need:  {race.required_avg_speed():.1f} km/h avg  "
          f"over {race.total_drive_hours:.1f} h effective drive time")
    print(f"  Car:   Cd={car.Cd}  A={car.frontal_area}m²  m={car.mass_kg}kg"
          f"  Crr={car.Crr}  bat={car.battery_capacity_kwh}kWh")
    print(f"  Solar: {car.panel_area}m² @ {car.panel_efficiency*100:.1f}%  "
          f"MPPT={car.mppt_efficiency*100:.0f}%  T_op={car.panel_temp_operating}°C")
    print(f"{'='*60}")

    if args.sweep:
        run_sweep(car, race, route, range(40, 135, 5))
        return

    sim = RaceSimulator(car, race, route, fixed_speed_kmh=args.speed,
                        control_stops_km=control_stops_km)
    budget = sim.run(verbose=args.verbose)
    budget.print_summary()

    if args.verbose:
        print_day_table(budget)

    if args.table:
        tables.print_speed_profile_table(budget, threshold_kmh=args.table_threshold)

    if args.csv:
        os.makedirs(args.out, exist_ok=True)
        table_path = os.path.join(args.out, "speed_table.csv")
        trace_path = os.path.join(args.out, "full_trace.csv")
        tables.write_table_csv(budget, table_path, threshold_kmh=args.table_threshold)
        tables.write_full_trace_csv(budget, trace_path)
        print(f"\n  CSV written: {table_path}, {trace_path}")

    if args.plot:
        from simulation.plots import generate_plots
        paths = generate_plots(budget, car, race, outdir=args.out)
        print(f"  Plots written: {', '.join(paths)}")


if __name__ == "__main__":
    main()
