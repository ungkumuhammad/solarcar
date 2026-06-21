"""Drivetrain loss model (motor + gearbox/belt).

P_motor_in = P_mech / (η_motor × η_gear)
Loss = P_motor_in − P_mech
"""


def drivetrain_input_power(
    mechanical_power_w: float,
    motor_efficiency: float = 0.96,
    gear_efficiency: float = 0.99,
) -> float:
    """Return total electrical input power required by drivetrain in watts."""
    return mechanical_power_w / (motor_efficiency * gear_efficiency)


def drivetrain_loss_power(
    mechanical_power_w: float,
    motor_efficiency: float = 0.96,
    gear_efficiency: float = 0.99,
) -> float:
    """Return drivetrain loss in watts."""
    return drivetrain_input_power(mechanical_power_w, motor_efficiency, gear_efficiency) - mechanical_power_w
