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
from losses.gradient import gradient_power, gravity_power
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
        control_stops_km: Optional[list] = None,
        speed_limits_km: Optional[list] = None,
        target_final_soc: Optional[float] = None,
        v_max_override_kmh: Optional[float] = None,
        max_regen_power_w: float = 3000.0,
    ):
        self.car = car
        self.race = race
        self.route = route or RouteProfile.flat(race.distance_km)
        self.fixed_speed = fixed_speed_kmh
        self.target_final_soc = target_final_soc
        self.v_max_override = v_max_override_kmh
        self.max_regen_w = max_regen_power_w
        # Control-stop checkpoint positions (cumulative km), sorted ascending.
        from environment.route import OFFICIAL_CONTROL_STOPS_KM, OFFICIAL_SPEED_LIMITS_KM
        stops = control_stops_km if control_stops_km is not None else list(OFFICIAL_CONTROL_STOPS_KM)
        self.control_stops_km = sorted(s for s in stops if s < race.distance_km)
        # Posted speed limits as (km_from, limit) steps.
        self.speed_limits_km = speed_limits_km if speed_limits_km is not None else list(OFFICIAL_SPEED_LIMITS_KM)
        self.solar = SolarModel(
            sunrise_hour=race.sunrise_hour,
            sunset_hour=race.sunset_hour,
            peak_irradiance=race.peak_irradiance,
            cloud_factor=race.cloud_factor,
        )
        # The strategy's ceiling must allow the override (if higher than the default
        # v_max); the per-step posted limit then clips it down where applicable.
        strategy_vmax = race.speed_max_kmh
        if v_max_override_kmh is not None and v_max_override_kmh > strategy_vmax:
            strategy_vmax = v_max_override_kmh
        self.strategy = SpeedStrategy(
            car=car,
            v_min_kmh=race.speed_min_kmh,
            v_max_kmh=strategy_vmax,
            target_final_soc=target_final_soc,
        )
        self.dt_h = race.time_step_min / 60.0   # timestep in hours

    def _v_max_at(self, distance_km: float) -> float:
        """Speed cap (km/h) at a position: posted limit, or the analysis override."""
        from environment.route import speed_limit_at_distance
        if self.v_max_override is not None:
            return self.v_max_override
        return speed_limit_at_distance(self.speed_limits_km, distance_km)

    def run(self, verbose: bool = False) -> EnergyBudget:
        car = self.car
        race = self.race
        budget = EnergyBudget()

        battery_kwh = car.battery_capacity_kwh * car.battery_initial_soc
        bat_min_kwh = car.battery_capacity_kwh * car.battery_soc_min
        distance_km = 0.0
        day_summaries = []

        # Location-based control stops: a halt is served when the car reaches each
        # checkpoint km. stop_remaining_min counts down the halt and can carry across
        # the 17:00 boundary to the next morning.
        next_stop_idx = 0
        stop_remaining_min = 0.0
        dt_min = race.time_step_min

        for day in range(race.race_days):
            day_start_dist = distance_km
            if verbose:
                print(f"\n--- Day {day + 1} ---")

            hour = 0.0
            while hour < 24.0:
                abs_hour = hour
                soc = battery_kwh / car.battery_capacity_kwh

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

                in_window = race.drive_start_hour <= abs_hour < race.drive_end_hour
                grade_pct, alt_m = self.route.grade_at_distance(distance_km)

                # Begin a control-stop halt if we've reached the next checkpoint.
                at_checkpoint = (
                    next_stop_idx < len(self.control_stops_km)
                    and distance_km >= self.control_stops_km[next_stop_idx] - 1e-6
                    and distance_km < race.distance_km
                )
                if in_window and at_checkpoint and stop_remaining_min <= 0:
                    stop_remaining_min = race.control_stop_duration_min

                serving_stop = in_window and stop_remaining_min > 0
                is_driving = (
                    in_window
                    and not serving_stop
                    and battery_kwh > bat_min_kwh
                    and distance_km < race.distance_km
                )

                if is_driving:
                    rho = air_density(alt_m, race.ambient_temp_c)
                    hours_left_today = race.drive_end_hour - abs_hour
                    v_cap = self._v_max_at(distance_km)   # posted limit / override (km/h)

                    if self.fixed_speed is not None:
                        speed_kmh = min(self.fixed_speed, v_cap)
                    else:
                        hours_left_total = max(
                            0.01, race.total_drive_hours - budget.total_driving_hours
                        )
                        speed_kmh = self.strategy.compute_speed(
                            solar_power_w=P_solar,
                            battery_soc=soc,
                            grade_percent=grade_pct,
                            altitude_m=alt_m,
                            hours_remaining_today=max(0.01, hours_left_today),
                            hours_remaining_total=hours_left_total,
                            v_max_kmh=v_cap,
                        )

                    speed_ms = speed_kmh / 3.6

                    P_drag = aerodynamic_drag_power(speed_ms, car.Cd, car.frontal_area, rho)
                    P_roll = rolling_resistance_power(speed_ms, car.Crr, car.mass_kg, grade_pct, car.Crr_speed_factor)
                    # Regen model: gravity offsets drag+rolling at full value; only the
                    # surplus on a descent is recovered into the battery.
                    P_grav = gravity_power(speed_ms, grade_pct, car.mass_kg)
                    P_grade_net = P_grav   # signed slope power (for trace/accounting)
                    balance = P_drag + P_roll + P_grav
                    P_mech = max(0.0, balance)
                    P_regen = 0.0
                    if balance < 0.0:
                        # Excess gravity power braked back into the pack.
                        P_regen = min(self.max_regen_w,
                                      -balance * car.regen_efficiency
                                      * car.motor_efficiency * car.gear_efficiency)
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
                    budget.regen_recovered_wh += P_regen * self.dt_h

                    net_w = P_solar - P_demand + P_regen
                    delta_kwh = net_w * self.dt_h / 1000.0
                    battery_kwh = max(bat_min_kwh, min(car.battery_capacity_kwh, battery_kwh + delta_kwh))

                    dist_step = speed_kmh * self.dt_h
                    distance_km = min(race.distance_km, distance_km + dist_step)
                    budget.total_driving_hours += self.dt_h

                    soc = battery_kwh / car.battery_capacity_kwh
                    budget.record_step(
                        time=day + abs_hour / 24, day=day + 1, distance_km=distance_km,
                        speed_kmh=speed_kmh, soc=soc, solar_w=P_solar, demand_w=P_demand,
                        irradiance=irr, grade_pct=grade_pct, altitude_m=alt_m,
                        driving=True, control_stop=False,
                        drag_w=P_drag, rolling_w=P_roll, gradient_w=P_grade_net,
                        drivetrain_w=P_drive_loss, aux_w=P_aux, electrical_w=P_wire + P_bat_int,
                    )

                    if verbose and irr > 50:
                        print(f"  {abs_hour:4.1f}h  irr={irr:>5.0f}W/m²  solar={P_solar:>4.0f}W  "
                              f"spd={speed_kmh:>5.1f}km/h  grade={grade_pct:+.1f}%  "
                              f"demand={P_demand:>5.0f}W  SoC={soc*100:.0f}%  dist={distance_km:.0f}km")

                else:
                    # Stationary: control-stop halt OR parked outside the drive window.
                    # Either way the car still charges from solar and draws parked aux.
                    P_aux_park = auxiliary_power(False, car.aux_power_driving, car.aux_power_parked)
                    net_w = P_solar - P_aux_park
                    delta_kwh = net_w * self.dt_h / 1000.0
                    battery_kwh = max(0.0, min(car.battery_capacity_kwh, battery_kwh + delta_kwh))
                    budget.auxiliary_wh += P_aux_park * self.dt_h

                    if serving_stop:
                        stop_remaining_min -= dt_min
                        if stop_remaining_min <= 0:
                            next_stop_idx += 1

                    # Record stationary daylight steps (charging) and all control stops;
                    # skip pure-night steps (irr == 0, not a stop) to keep traces compact.
                    if serving_stop or irr > 0:
                        soc = battery_kwh / car.battery_capacity_kwh
                        budget.record_step(
                            time=day + abs_hour / 24, day=day + 1, distance_km=distance_km,
                            speed_kmh=0.0, soc=soc, solar_w=P_solar, demand_w=P_aux_park,
                            irradiance=irr, grade_pct=grade_pct, altitude_m=alt_m,
                            driving=False, control_stop=bool(serving_stop),
                            aux_w=P_aux_park,
                        )

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

    def run_to_target_soc(self, target_soc: float, tol: float = 0.01,
                          max_scale: float = 30.0, verbose: bool = False):
        """Calibrate the whole-race discharge so the car finishes near target_soc.

        The speed cap makes final SoC a non-linear (but monotonically decreasing)
        function of discharge_scale, so we bisect on the scale. Returns
        (budget, scale, cap_limited): cap_limited is True if even max_scale can't
        drain the battery to the target (the achievable floor is returned).
        """
        self.target_final_soc = target_soc
        self.strategy.target_final_soc = target_soc

        def run_with(scale):
            self.strategy.discharge_scale = scale
            return self.run()

        # If even the most aggressive discharge can't reach the target, report the floor.
        b_hi = run_with(max_scale)
        if b_hi.final_soc > target_soc + tol:
            if verbose:
                print(f"  [calibrate] target {target_soc:.0%} not reachable within speed "
                      f"limits; floor is {b_hi.final_soc:.1%} at scale {max_scale}")
            return b_hi, max_scale, True

        lo, hi = 0.0, max_scale
        budget = b_hi
        for _ in range(24):
            mid = (lo + hi) / 2.0
            budget = run_with(mid)
            if abs(budget.final_soc - target_soc) <= tol:
                break
            if budget.final_soc > target_soc:
                lo = mid   # under-spent → discharge harder
            else:
                hi = mid   # over-spent → ease off
        if verbose:
            print(f"  [calibrate] scale={mid:.3f} → final SoC {budget.final_soc:.1%}")
        return budget, mid, False

    def sweep_speeds(self, speeds_kmh: list) -> list:
        """Run simulation for each fixed speed. Returns list of EnergyBudget."""
        results = []
        for spd in speeds_kmh:
            sim = RaceSimulator(self.car, self.race, self.route, fixed_speed_kmh=spd,
                                control_stops_km=self.control_stops_km,
                                speed_limits_km=self.speed_limits_km,
                                v_max_override_kmh=self.v_max_override)
            results.append((spd, sim.run()))
        return results
