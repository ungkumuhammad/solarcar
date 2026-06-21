"""Main race simulation engine with time-step integration.

Each timestep (default 30 min):
1. Compute irradiance → solar power
2. Compute grade + altitude at current route position
3. Ask SpeedStrategy for target speed
4. Compute all losses at that speed
5. Update battery SoC
6. Advance distance
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional

from models.car import CarConfig
from models.race import RaceConfig
from environment.solar_model import SolarModel
from environment.atmosphere import air_density
from environment.route import RouteProfile
from losses.aerodynamic import aerodynamic_drag_power
from losses.rolling import rolling_resistance_power
from losses.gradient import gradient_power
from losses.drivetrain import drivetrain_input_power, drivetrain_loss_power
from losses.electrical import wiring_loss_power, battery_internal_loss_power
from losses.solar import solar_panel_power, temperature_derating
from losses.auxiliary import auxiliary_power
from simulation.speed_strategy import SpeedStrategy
from simulation.energy_budget import EnergyBudget


@dataclass
class SimResult:
    budget: EnergyBudget
    day_summaries: list   # per-day distance and SoC


class RaceSimulator:
    def __init__(
        self,
        car: CarConfig,
        race: RaceConfig,
        route: Optional[RouteProfile] = None,
        fixed_speed_kmh: Optional[float] = None,
    ):
        self.car = car
        self.race = race
        self.route = route or RouteProfile.flat(race.distance_km)
        self.fixed_speed = fixed_speed_kmh
        self.solar = SolarModel(
            sunrise_hour=race.sunrise_hour,
            sunset_hour=race.sunset_hour,
            peak_irradiance=race.peak_irradiance,
            cloud_factor=race.cloud_factor,
        )
        self.strategy = SpeedStrategy(
            car=car,
            v_min_kmh=race.speed_min_kmh,
            v_max_kmh=race.speed_max_kmh,
        )
        self.dt_h = race.time_step_min / 60.0   # timestep in hours

    def run(self, verbose: bool = False) -> EnergyBudget:
        car = self.car
        race = self.race
        budget = EnergyBudget()

        battery_kwh = car.battery_capacity_kwh * car.battery_initial_soc
        bat_min_kwh = car.battery_capacity_kwh * car.battery_soc_min
        distance_km = 0.0
        day_summaries = []

        for day in range(race.race_days):
            day_start_dist = distance_km
            if verbose:
                print(f"\n--- Day {day + 1} ---")

            hour = 0.0
            while hour < 24.0:
                abs_hour = hour
                is_driving = (
                    race.drive_start_hour <= abs_hour < race.drive_end_hour
                    and battery_kwh > bat_min_kwh
                    and distance_km < race.distance_km
                )

                irr = self.solar.irradiance(abs_hour)
                P_solar = solar_panel_power(
                    irr,
                    car.panel_area,
                    car.panel_efficiency,
                    car.panel_temp_coeff,
                    car.panel_temp_operating,
                    car.panel_temp_stc,
                    car.mppt_efficiency,
                )

                if is_driving:
                    grade_pct, alt_m = self.route.grade_at_distance(distance_km)
                    rho = air_density(alt_m, race.ambient_temp_c)
                    hours_left_today = race.drive_end_hour - abs_hour

                    if self.fixed_speed is not None:
                        speed_kmh = self.fixed_speed
                    else:
                        speed_kmh = self.strategy.compute_speed(
                            solar_power_w=P_solar,
                            battery_soc=battery_kwh / car.battery_capacity_kwh,
                            grade_percent=grade_pct,
                            altitude_m=alt_m,
                            hours_remaining_today=max(0.01, hours_left_today),
                        )

                    speed_ms = speed_kmh / 3.6

                    P_drag = aerodynamic_drag_power(speed_ms, car.Cd, car.frontal_area, rho)
                    P_roll = rolling_resistance_power(speed_ms, car.Crr, car.mass_kg, grade_pct, car.Crr_speed_factor)
                    P_grade_net = gradient_power(speed_ms, grade_pct, car.mass_kg, car.regen_efficiency)
                    P_mech = max(0.0, P_drag + P_roll + P_grade_net)
                    P_drive_in = drivetrain_input_power(P_mech, car.motor_efficiency, car.gear_efficiency)
                    P_drive_loss = P_drive_in - P_mech
                    P_aux = auxiliary_power(True, car.aux_power_driving, car.aux_power_parked)
                    P_elec = P_drive_in + P_aux
                    P_wire = wiring_loss_power(P_elec, car.bus_voltage, car.wire_resistance)
                    P_bat_int = battery_internal_loss_power(P_elec, car.bus_voltage, car.battery_resistance)
                    P_demand = P_elec + P_wire + P_bat_int

                    # Accumulate energy (Wh)
                    budget.drag_wh += P_drag * self.dt_h
                    budget.rolling_wh += P_roll * self.dt_h
                    budget.gradient_net_wh += P_grade_net * self.dt_h
                    budget.drivetrain_loss_wh += P_drive_loss * self.dt_h
                    budget.wiring_loss_wh += P_wire * self.dt_h
                    budget.battery_internal_loss_wh += P_bat_int * self.dt_h
                    budget.auxiliary_wh += P_aux * self.dt_h

                    net_w = P_solar - P_demand
                    delta_kwh = net_w * self.dt_h / 1000.0
                    battery_kwh = max(bat_min_kwh, min(car.battery_capacity_kwh, battery_kwh + delta_kwh))

                    dist_step = speed_kmh * self.dt_h
                    distance_km = min(race.distance_km, distance_km + dist_step)
                    budget.total_driving_hours += self.dt_h

                    # Traces (record every step while driving)
                    budget.time_trace.append(round(day + abs_hour / 24, 4))
                    budget.speed_trace.append(round(speed_kmh, 2))
                    budget.soc_trace.append(round(battery_kwh / car.battery_capacity_kwh, 4))
                    budget.solar_trace.append(round(P_solar, 1))
                    budget.demand_trace.append(round(P_demand, 1))

                    if verbose and irr > 50:
                        soc_pct = battery_kwh / car.battery_capacity_kwh * 100
                        print(f"  {abs_hour:4.1f}h  irr={irr:>5.0f}W/m²  solar={P_solar:>4.0f}W  "
                              f"spd={speed_kmh:>5.1f}km/h  grade={grade_pct:+.1f}%  "
                              f"demand={P_demand:>5.0f}W  SoC={soc_pct:.0f}%  dist={distance_km:.0f}km")

                else:
                    # Parked: only trickle aux draw, solar still charges
                    P_aux_park = auxiliary_power(False, car.aux_power_driving, car.aux_power_parked)
                    net_w = P_solar - P_aux_park
                    delta_kwh = net_w * self.dt_h / 1000.0
                    battery_kwh = max(0.0, min(car.battery_capacity_kwh, battery_kwh + delta_kwh))
                    budget.auxiliary_wh += P_aux_park * self.dt_h

                budget.solar_harvested_wh += P_solar * self.dt_h

                hour += self.dt_h

                if distance_km >= race.distance_km:
                    budget.race_completed = True
                    break

            day_dist = distance_km - day_start_dist
            day_summaries.append({"day": day + 1, "distance_km": round(day_dist, 1),
                                   "soc_end": round(battery_kwh / car.battery_capacity_kwh * 100, 1)})
            if budget.race_completed:
                break

        budget.total_distance_km = distance_km
        budget.final_soc = battery_kwh / car.battery_capacity_kwh
        budget.battery_net_used_wh = (
            car.battery_capacity_kwh * car.battery_initial_soc - battery_kwh
        ) * 1000.0
        budget.avg_speed_kmh = (
            distance_km / budget.total_driving_hours if budget.total_driving_hours > 0 else 0.0
        )

        return budget

    def sweep_speeds(self, speeds_kmh: list) -> list:
        """Run simulation for each fixed speed. Returns list of EnergyBudget."""
        results = []
        for spd in speeds_kmh:
            sim = RaceSimulator(self.car, self.race, self.route, fixed_speed_kmh=spd)
            results.append((spd, sim.run()))
        return results
