"""Speed strategy: compute target speed from available power budget + terrain.

Power-balance algorithm:
1. P_available = P_solar + P_battery_budget
2. Solve P_demand(v, grade, alt) = P_available for v  (bisection)
3. Clip to [v_min, v_max]
"""
import math

from models.car import CarConfig
from environment.atmosphere import air_density
from losses.aerodynamic import aerodynamic_drag_power
from losses.rolling import rolling_resistance_power
from losses.gradient import gravity_power
from losses.drivetrain import drivetrain_input_power
from losses.electrical import wiring_loss_power, battery_internal_loss_power


class SpeedStrategy:
    def __init__(
        self,
        car: CarConfig,
        v_min_kmh: float = 40.0,
        v_max_kmh: float = 130.0,
        battery_soc_reserve: float = 0.10,
        max_battery_discharge_w: float = 500.0,
        target_final_soc: float = None,
        discharge_scale: float = 1.0,
        whole_race_max_battery_w: float = 5000.0,
    ):
        self.car = car
        self.v_min = v_min_kmh / 3.6
        self.v_max = v_max_kmh / 3.6
        self.soc_reserve = battery_soc_reserve
        self.max_bat_w = max_battery_discharge_w
        # Whole-race mode: when target_final_soc is set, the battery budget is spread
        # across the whole remaining race (not just today) so the car arrives at the
        # target SoC. discharge_scale is the calibration knob (tuned by the simulator).
        self.target_final_soc = target_final_soc
        self.discharge_scale = discharge_scale
        self.whole_race_max_bat_w = whole_race_max_battery_w

    def _total_demand(self, speed_ms: float, grade_pct: float, alt_m: float) -> float:
        """Total electrical power demanded from battery+solar at given speed."""
        rho = air_density(alt_m, self.car.__dict__.get("ambient_temp_c", 35.0))
        c = self.car
        P_drag = aerodynamic_drag_power(speed_ms, c.Cd, c.frontal_area, rho)
        P_roll = rolling_resistance_power(speed_ms, c.Crr, c.mass_kg, grade_pct, c.Crr_speed_factor)
        P_grav = gravity_power(speed_ms, grade_pct, c.mass_kg)  # raw, ± along slope
        P_mech = P_drag + P_roll + P_grav   # can be negative if downhill dominant
        P_mech = max(0.0, P_mech)           # motor draws 0 on a regen-braking descent
        P_drive_in = drivetrain_input_power(P_mech, c.motor_efficiency, c.gear_efficiency)
        P_elec = P_drive_in + c.aux_power_driving
        P_wire = wiring_loss_power(P_elec, c.bus_voltage, c.wire_resistance)
        P_bat_int = battery_internal_loss_power(P_elec, c.bus_voltage, c.battery_resistance)
        return P_elec + P_wire + P_bat_int

    def battery_discharge_budget(
        self, soc: float, hours_remaining_today: float, hours_remaining_total: float = None
    ) -> float:
        """Watts available from battery this timestep.

        Default (per-day): spreads usable energy above the reserve across the remaining
        drive hours *today*, so the battery arrives at reserve SoC by end of day.

        Whole-race (target_final_soc set): spreads usable energy above the *target* SoC
        across the remaining drive hours of the *whole race*, scaled by discharge_scale,
        so the car arrives at Adelaide near the target SoC.
        """
        c = self.car
        if self.target_final_soc is not None:
            usable_kwh = max(0.0, (soc - self.target_final_soc) * c.battery_capacity_kwh)
            hours = hours_remaining_total if hours_remaining_total and hours_remaining_total > 0 else hours_remaining_today
            if not hours or hours <= 0:
                return 0.0
            budget = self.discharge_scale * usable_kwh * 1000.0 / hours
            return min(self.whole_race_max_bat_w, budget)
        usable_kwh = max(0.0, (soc - self.soc_reserve) * c.battery_capacity_kwh)
        if hours_remaining_today <= 0:
            return 0.0
        return min(self.max_bat_w, usable_kwh * 1000.0 / hours_remaining_today)

    def compute_speed(
        self,
        solar_power_w: float,
        battery_soc: float,
        grade_percent: float = 0.0,
        altitude_m: float = 0.0,
        hours_remaining_today: float = 5.0,
        hours_remaining_total: float = None,
        v_max_kmh: float = None,
    ) -> float:
        """Return recommended speed in km/h given current conditions.

        If v_max_kmh is given (e.g. the posted speed limit at this location), it caps the
        speed for this step instead of the global v_max.
        """
        bat_w = self.battery_discharge_budget(battery_soc, hours_remaining_today, hours_remaining_total)
        P_avail = max(0.0, solar_power_w) + bat_w
        v_hi = self.v_max if v_max_kmh is None else min(self.v_max, v_max_kmh / 3.6)

        # Bisection: find v where demand ≈ P_avail
        lo, hi = self.v_min, v_hi
        for _ in range(50):
            mid = (lo + hi) / 2.0
            if self._total_demand(mid, grade_percent, altitude_m) < P_avail:
                lo = mid
            else:
                hi = mid

        speed_ms = (lo + hi) / 2.0
        # Ensure we stay within bounds even if P_avail can't sustain v_min
        speed_ms = max(self.v_min, min(v_hi, speed_ms))
        return speed_ms * 3.6  # km/h
