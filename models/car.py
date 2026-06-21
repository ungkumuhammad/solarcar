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

    # Battery — BWSC 2027 §2.5.2: max 11 MJ = 3.056 kWh
    battery_capacity_kwh: float = 3.056
    battery_initial_soc: float = 0.80   # fraction 0-1
    battery_soc_min: float = 0.10       # reserve, never go below
    battery_soc_max: float = 1.00

    # Solar panels — BWSC 2027 §2.4.2: max 6.0 m²
    panel_area: float = 6.0             # m²
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

    # ── BWSC 2027 regulation hard limits (Challenger class) ───────────────
    # §2.4.2: solar array ≤ 6.0 m²
    # §2.5.2: battery energy ≤ 11 MJ = 3.056 kWh
    REGULATION_PANEL_AREA_M2: float = 6.0
    REGULATION_BATTERY_KWH: float = 3.056

    @classmethod
    def optimized_regulation(cls) -> CarConfig:
        """Best achievable specs within BWSC 2027 regulation limits.

        Solar ≤ 6 m² (§2.4.2), battery ≤ 11 MJ / 3.056 kWh (§2.5.2).
        All other parameters pushed to engineering limits.
        """
        return cls(
            # Aerodynamic — single biggest lever (drag ∝ v³)
            Cd=0.07,
            frontal_area=0.60,          # very narrow teardrop, driver reclined
            # Mass
            mass_kg=150.0,              # carbon monocoque + lightweight driver
            # Rolling
            Crr=0.0012,                 # custom low-Crr solar race tyres
            # Drivetrain
            motor_efficiency=0.98,      # custom axial-flux hub motor
            gear_efficiency=0.995,      # direct-drive or toothed belt
            regen_efficiency=0.85,      # SiC inverter in gen mode
            # Electrical bus — higher voltage → lower I → less I²R
            bus_voltage=200.0,
            wire_resistance=0.02,
            battery_resistance=0.04,
            # Battery — BWSC 2027 §2.5.2: 11 MJ = 3.056 kWh
            battery_capacity_kwh=3.056,
            battery_initial_soc=0.90,
            # Solar — BWSC 2027 §2.4.2: max 6 m²; maximise efficiency within area
            panel_area=6.0,
            panel_efficiency=0.260,     # SunPower Maxeon Gen 6 (~26%)
            panel_temp_coeff=-0.0035,
            panel_temp_operating=45.0,  # active ventilation under panel
            mppt_efficiency=0.99,
            # Auxiliary
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
