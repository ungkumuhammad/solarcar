"""Gradient / elevation loss model with regenerative braking recovery.

Uphill:   F_grade > 0 → additional power needed
Downhill: F_grade < 0 → regen recovery available
"""
import math


def gradient_power(
    speed_ms: float,
    grade_percent: float,
    mass_kg: float,
    regen_efficiency: float = 0.72,
    g: float = 9.81,
) -> float:
    """Return net gradient power in watts.

    Positive = power consumed (uphill).
    Negative = power recovered (downhill via regen).
    Regen efficiency is only applied on downhill segments.
    """
    theta = math.atan(grade_percent / 100.0)
    F_grade = mass_kg * g * math.sin(theta)
    P_grade = F_grade * speed_ms

    if P_grade < 0:
        # Downhill: partial recovery via regenerative braking
        return P_grade * regen_efficiency  # still negative (net gain)
    return P_grade  # uphill: full loss
