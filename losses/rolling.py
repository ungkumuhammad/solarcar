"""Rolling resistance loss model.

F_roll = Crr × m × g × cos(θ)
P_roll = F_roll × v
"""
import math


def rolling_resistance_power(
    speed_ms: float,
    Crr: float,
    mass_kg: float,
    grade_percent: float = 0.0,
    speed_factor: float = 0.01,
    g: float = 9.81,
) -> float:
    """Return rolling resistance power in watts.

    speed_factor: fractional Crr increase per m/s (Michelin empirical model).
    """
    Crr_eff = Crr * (1.0 + speed_ms * speed_factor)
    theta = math.atan(grade_percent / 100.0)
    F_roll = Crr_eff * mass_kg * g * math.cos(theta)
    return F_roll * speed_ms
