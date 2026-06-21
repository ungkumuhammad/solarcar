from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RaceConfig:
    distance_km: float = 3022.0
    race_days: int = 3
    drive_start_hour: float = 8.0   # 08:00
    drive_end_hour: float = 17.5    # 17:30 (7.5h effective window)
    time_step_min: float = 30.0     # simulation timestep in minutes
    latitude: float = -23.7         # Stuart Highway midpoint (Australia)
    peak_irradiance: float = 1000.0 # W/m² clear sky peak
    sunrise_hour: float = 6.5
    sunset_hour: float = 18.5
    cloud_factor: float = 1.0       # 1=clear, 0.8=slight cloud
    ambient_temp_c: float = 35.0    # average race day air temp
    speed_min_kmh: float = 40.0     # regulatory/safety minimum
    speed_max_kmh: float = 130.0    # speed limit (WSC)

    @property
    def drive_hours_per_day(self) -> float:
        return self.drive_end_hour - self.drive_start_hour

    @property
    def total_drive_hours(self) -> float:
        return self.drive_hours_per_day * self.race_days

    def required_avg_speed(self) -> float:
        """Speed needed to cover full distance within driving window."""
        return self.distance_km / self.total_drive_hours
