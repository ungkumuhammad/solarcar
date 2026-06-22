from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class EnergyBudget:
    # Race outcome
    total_distance_km: float = 0.0
    total_driving_hours: float = 0.0
    race_completed: bool = False
    final_soc: float = 0.0
    avg_speed_kmh: float = 0.0

    # Posted-speed-limit exceedance (nonzero only when a goal-seek left the cap open;
    # legal runs report all zeros). Flags an analysis-only plan that is not race-legal.
    over_limit_steps: int = 0
    over_limit_distance_km: float = 0.0
    over_limit_max_kmh: float = 0.0
    over_limit_max_over_kmh: float = 0.0

    # Energy sources (Wh, positive = energy put into system)
    solar_harvested_wh: float = 0.0
    regen_recovered_wh: float = 0.0    # captured within gradient_wh
    battery_net_used_wh: float = 0.0   # positive = battery discharged net

    # Energy losses (Wh, positive = energy consumed)
    drag_wh: float = 0.0
    rolling_wh: float = 0.0
    gradient_net_wh: float = 0.0       # positive = net uphill cost
    drivetrain_loss_wh: float = 0.0
    wiring_loss_wh: float = 0.0
    battery_internal_loss_wh: float = 0.0
    auxiliary_wh: float = 0.0
    panel_temp_loss_wh: float = 0.0    # reference: what panel would produce at STC vs actual
    mppt_loss_wh: float = 0.0

    # Time-series traces for plotting (all aligned, one entry per recorded timestep)
    time_trace: list = field(default_factory=list)    # elapsed time as day + hour/24
    speed_trace: list = field(default_factory=list)   # km/h (0 while parked/stopped)
    soc_trace: list = field(default_factory=list)     # fraction 0-1
    solar_trace: list = field(default_factory=list)   # W (solar input)
    demand_trace: list = field(default_factory=list)  # W (total electrical demand)

    # Extended traces (driving and parked/charging steps)
    distance_trace: list = field(default_factory=list)    # cumulative km
    day_trace: list = field(default_factory=list)         # race day number (1-based)
    irradiance_trace: list = field(default_factory=list)  # W/m²
    grade_trace: list = field(default_factory=list)       # % (positive uphill)
    altitude_trace: list = field(default_factory=list)    # m
    driving_trace: list = field(default_factory=list)     # bool: True=driving
    control_stop_trace: list = field(default_factory=list)  # bool: True=control-stop halt

    # Per-loss instantaneous power traces (W); zero while parked/stopped
    drag_w_trace: list = field(default_factory=list)
    rolling_w_trace: list = field(default_factory=list)
    gradient_w_trace: list = field(default_factory=list)
    drivetrain_w_trace: list = field(default_factory=list)
    aux_w_trace: list = field(default_factory=list)
    electrical_w_trace: list = field(default_factory=list)  # wiring + battery internal

    def record_step(
        self, *, time, day, distance_km, speed_kmh, soc, solar_w, demand_w,
        irradiance, grade_pct, altitude_m, driving, control_stop=False,
        drag_w=0.0, rolling_w=0.0, gradient_w=0.0, drivetrain_w=0.0,
        aux_w=0.0, electrical_w=0.0,
    ) -> None:
        """Append one aligned row to every trace list (driving or parked step)."""
        self.time_trace.append(round(time, 4))
        self.day_trace.append(day)
        self.distance_trace.append(round(distance_km, 2))
        self.speed_trace.append(round(speed_kmh, 2))
        self.soc_trace.append(round(soc, 4))
        self.solar_trace.append(round(solar_w, 1))
        self.demand_trace.append(round(demand_w, 1))
        self.irradiance_trace.append(round(irradiance, 1))
        self.grade_trace.append(round(grade_pct, 3))
        self.altitude_trace.append(round(altitude_m, 1))
        self.driving_trace.append(driving)
        self.control_stop_trace.append(control_stop)
        self.drag_w_trace.append(round(drag_w, 1))
        self.rolling_w_trace.append(round(rolling_w, 1))
        self.gradient_w_trace.append(round(gradient_w, 1))
        self.drivetrain_w_trace.append(round(drivetrain_w, 1))
        self.aux_w_trace.append(round(aux_w, 1))
        self.electrical_w_trace.append(round(electrical_w, 1))

    def total_energy_consumed_wh(self) -> float:
        return (
            self.drag_wh + self.rolling_wh + max(0.0, self.gradient_net_wh)
            + self.drivetrain_loss_wh + self.wiring_loss_wh
            + self.battery_internal_loss_wh + self.auxiliary_wh
        )

    def total_energy_available_wh(self) -> float:
        return self.solar_harvested_wh + self.battery_net_used_wh

    def energy_surplus_wh(self) -> float:
        return self.total_energy_available_wh() - self.total_energy_consumed_wh()

    def loss_breakdown(self) -> Dict[str, float]:
        total = self.total_energy_consumed_wh()
        if total == 0:
            return {}
        return {
            "Aerodynamic drag": self.drag_wh / total * 100,
            "Rolling resistance": self.rolling_wh / total * 100,
            "Gradient (net)": max(0, self.gradient_net_wh) / total * 100,
            "Drivetrain losses": self.drivetrain_loss_wh / total * 100,
            "Wiring losses": self.wiring_loss_wh / total * 100,
            "Battery int. losses": self.battery_internal_loss_wh / total * 100,
            "Auxiliary loads": self.auxiliary_wh / total * 100,
        }

    def print_summary(self) -> None:
        print("=" * 60)
        print("  SOLAR CAR RACE ENERGY BUDGET")
        print("=" * 60)
        print(f"  Distance covered:   {self.total_distance_km:>8.1f} km")
        print(f"  Driving time:       {self.total_driving_hours:>8.1f} h")
        print(f"  Average speed:      {self.avg_speed_kmh:>8.1f} km/h")
        print(f"  Race completed:     {'YES' if self.race_completed else 'NO':>8s}")
        print(f"  Final battery SoC:  {self.final_soc * 100:>7.1f}%")
        if self.over_limit_distance_km > 0:
            print(f"  ⚠ Exceeds posted limit: drives above NT130/SA110 for "
                  f"{self.over_limit_distance_km:.1f} km, peak {self.over_limit_max_kmh:.1f} km/h "
                  f"(+{self.over_limit_max_over_kmh:.1f} over) — analysis only, not race-legal (§3.31.6).")
        print()
        print("  ENERGY SOURCES (Wh)")
        print(f"    Solar harvested:  {self.solar_harvested_wh:>8.1f}")
        print(f"    Battery used:     {self.battery_net_used_wh:>8.1f}")
        print(f"  Total in:         {self.total_energy_available_wh():>10.1f}")
        print()
        print("  ENERGY LOSSES (Wh)")
        print(f"    Aerodynamic drag: {self.drag_wh:>8.1f}")
        print(f"    Rolling resist.:  {self.rolling_wh:>8.1f}")
        print(f"    Gradient net:     {self.gradient_net_wh:>8.1f}")
        print(f"    Drivetrain:       {self.drivetrain_loss_wh:>8.1f}")
        print(f"    Wiring:           {self.wiring_loss_wh:>8.1f}")
        print(f"    Battery internal: {self.battery_internal_loss_wh:>8.1f}")
        print(f"    Auxiliary loads:  {self.auxiliary_wh:>8.1f}")
        print(f"  Total out:        {self.total_energy_consumed_wh():>10.1f}")
        print()
        print("  LOSS BREAKDOWN (%)")
        for name, pct in self.loss_breakdown().items():
            bar = "#" * int(pct / 2)
            print(f"    {name:<22} {pct:>5.1f}%  {bar}")
        print("=" * 60)
