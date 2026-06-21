"""Auxiliary electrical loads (constant power, independent of speed)."""

# Default load breakdown when driving (watts)
DEFAULT_DRIVING_LOADS = {
    "telemetry_gps": 10.0,
    "driver_display": 5.0,
    "safety_electronics": 5.0,
    "motor_cooling_fan": 15.0,
    "steering_control": 5.0,
    "mandatory_lights": 10.0,
    "data_logging": 3.0,
    "horn_signals": 2.0,
}  # total: 55 W

DEFAULT_PARKED_LOADS = {
    "safety_electronics": 5.0,
    "data_logging": 3.0,
    "telemetry_gps": 2.0,
}  # total: 10 W


def auxiliary_power(is_driving: bool = True, driving_watts: float = 55.0, parked_watts: float = 10.0) -> float:
    """Return total auxiliary load in watts."""
    return driving_watts if is_driving else parked_watts
