from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict


@dataclass
class CarConfig:
    # Aerodynamic
    Cd: float = 0.09
    frontal_area: float = 0.96      # m²

    # Mass
    mass_kg: float = 180.0          # total incl. driver

    # Rolling resistance
    Crr: float = 0.0015             # rolling resistance coefficient
    Crr_speed_factor: float = 0.01  # fractional Crr increase per m/s

    # Drivetrain
    motor_efficiency: float = 0.96
    gear_efficiency: float = 0.99
    regen_efficiency: float = 0.72  # motor-gen × inverter

    # Electrical bus
    bus_voltage: float = 150.0      # V nominal
    wire_resistance: float = 0.04   # Ω total harness
    battery_resistance: float = 0.08  # Ω internal

    # Battery
    battery_capacity_kwh: float = 5.5
    battery_initial_soc: float = 0.80   # fraction 0-1
    battery_soc_min: float = 0.10       # reserve, never go below
    battery_soc_max: float = 1.00

    # Solar panels
    panel_area: float = 4.0             # m²
    panel_efficiency: float = 0.245     # STC efficiency
    panel_temp_coeff: float = -0.0038   # per °C (negative for c-Si)
    panel_temp_stc: float = 25.0        # °C STC reference
    panel_temp_operating: float = 55.0  # °C typical operating

    # MPPT
    mppt_efficiency: float = 0.98

    # Auxiliary loads
    aux_power_driving: float = 55.0  # W while driving
    aux_power_parked: float = 10.0   # W when parked/charging

    @classmethod
    def challenger_class(cls) -> CarConfig:
        """Top-tier Challenger preset (Nuon/Vattenfall level)."""
        return cls()  # defaults are challenger class

    @classmethod
    def target_133kmh(cls) -> CarConfig:
        """Specs required to average 133 km/h over 3 days."""
        return cls(
            Cd=0.07,
            frontal_area=0.60,
            mass_kg=150.0,
            Crr=0.0012,
            motor_efficiency=0.98,
            gear_efficiency=0.995,
            regen_efficiency=0.85,
            bus_voltage=200.0,
            wire_resistance=0.02,
            battery_resistance=0.04,
            battery_capacity_kwh=15.0,
            battery_initial_soc=0.90,
            panel_area=5.0,
            panel_efficiency=0.260,
            panel_temp_coeff=-0.0035,
            panel_temp_operating=45.0,
            mppt_efficiency=0.99,
            aux_power_driving=30.0,
            aux_power_parked=8.0,
        )

    @classmethod
    def from_json(cls, path: str) -> CarConfig:
        with open(path) as f:
            return cls(**json.load(f))

    def to_json(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)
