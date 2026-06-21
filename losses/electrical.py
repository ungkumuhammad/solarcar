"""Electrical losses: wiring harness and battery internal resistance.

Both use I²R: current I = P_demand / V_bus
"""


def wiring_loss_power(
    power_demand_w: float,
    bus_voltage: float = 150.0,
    wire_resistance: float = 0.04,
) -> float:
    """Return wiring harness I²R loss in watts."""
    I = power_demand_w / bus_voltage
    return I ** 2 * wire_resistance


def battery_internal_loss_power(
    power_demand_w: float,
    bus_voltage: float = 150.0,
    battery_resistance: float = 0.08,
) -> float:
    """Return battery internal resistance I²R loss in watts."""
    I = power_demand_w / bus_voltage
    return I ** 2 * battery_resistance
