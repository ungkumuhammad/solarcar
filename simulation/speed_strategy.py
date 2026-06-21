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
from losses.gradient import gradient_power
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
    ):
        self.car = car
        self.v_min = v_min_kmh / 3.6
        self.v_max = v_max_kmh / 3.6
        self.soc_reserve = battery_soc_reserve
        self.max_bat_w = max_battery_discharge_w

    def _total_demand(self, speed_ms: float, grade_pct: float, alt_m: float) -> float:
        """Total electrical power demanded from battery+solar at given speed."""
        rho = air_density(alt_m, self.car.__dict__.get("ambient_temp_c", 35.0))
        c = self.car
        P_drag = aerodynamic_drag_power(speed_ms, c.Cd, c.frontal_area, rho)
        P_roll = rolling_resistance_power(speed_ms, c.Crr, c.mass_kg, grade_pct, c.Crr_speed_factor)
        P_grade = gradient_power(speed_ms, grade_pct, c.mass_kg, c.regen_efficiency)
        P_mech = P_drag + P_roll + P_grade  # can be negative if downhill dominant
        P_mech = max(0.0, P_mech)           # can't push below 0 at wheel
        P_drive_in = drivetrain_input_power(P_mech, c.motor_efficiency, c.gear_efficiency)
        P_elec = P_drive_in + c.aux_power_driving
        P_wire = wiring_loss_power(P_elec, c.bus_voltage, c.wire_resistance)
        P_bat_int = battery_internal_loss_power(P_elec, c.bus_voltage, c.battery_resistance)
        return P_elec + P_wire + P_bat_int

    def battery_discharge_budget(self, soc: float, hours_remaining_today: float) -> float:
        """Watts available from battery this timestep.

        Spreads remaining usable energy linearly across remaining drive hours so
        the battery arrives at reserve SoC by end of day.
        """
        c = self.car
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
    ) -> float:
        """Return recommended speed in km/h given current conditions."""
        bat_w = self.battery_discharge_budget(battery_soc, hours_remaining_today)
        P_avail = max(0.0, solar_power_w) + bat_w

        # Bisection: find v where demand ≈ P_avail
        lo, hi = self.v_min, self.v_max
        for _ in range(50):
            mid = (lo + hi) / 2.0
            if self._total_demand(mid, grade_percent, altitude_m) < P_avail:
                lo = mid
            else:
                hi = mid

        speed_ms = (lo + hi) / 2.0
        # Ensure we stay within bounds even if P_avail can't sustain v_min
        speed_ms = max(self.v_min, min(self.v_max, speed_ms))
        return speed_ms * 3.6  # km/h
