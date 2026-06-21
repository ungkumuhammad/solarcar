"""Aerodynamic drag loss model.

F_drag = 0.5 × Cd × A × ρ × v²
P_drag = F_drag × v   (scales as v³)
"""


def aerodynamic_drag_power(
    speed_ms: float,
    Cd: float,
    frontal_area: float,
    air_density: float = 1.225,
    headwind_ms: float = 0.0,
) -> float:
    """Return aerodynamic drag power in watts.

    headwind_ms: positive = facing headwind (increases drag), negative = tailwind.
    """
    effective_speed = speed_ms + headwind_ms
    F_drag = 0.5 * Cd * frontal_area * air_density * effective_speed ** 2
    return F_drag * speed_ms  # wheel power, not aero power in wind frame
