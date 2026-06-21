from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class RaceConfig:
    distance_km: float = 3022.0
    race_days: int = 4              # 3 days NOT achievable with regulation energy+time

    # WSC regulation drive window: 08:00 – 17:00 (9 h/day, hard limit)
    regulation_window_start: float = 8.0   # 08:00
    regulation_window_end: float = 17.0   # 17:00  → 9.0 h window

    # Control stops: mandatory halts at checkpoints (reduces effective drive time)
    control_stops_per_day: int = 2
    control_stop_duration_min: float = 30.0   # minutes per stop

    time_step_min: float = 30.0     # simulation timestep in minutes
    latitude: float = -23.7         # Stuart Highway midpoint (Australia)
    peak_irradiance: float = 1000.0 # W/m² clear sky peak
    sunrise_hour: float = 6.5
    sunset_hour: float = 18.5
    cloud_factor: float = 1.0       # 1=clear sky, <1=cloud cover
    ambient_temp_c: float = 35.0    # average race day air temp
    speed_min_kmh: float = 40.0     # safety/regulatory minimum
    speed_max_kmh: float = 130.0    # WSC speed limit

    @property
    def regulation_window_h(self) -> float:
        """Total permitted drive window per day (regulation hard limit)."""
        return self.regulation_window_end - self.regulation_window_start

    @property
    def control_stop_hours_per_day(self) -> float:
        return self.control_stops_per_day * self.control_stop_duration_min / 60.0

    @property
    def drive_hours_per_day(self) -> float:
        """Effective driving time per day after subtracting control stops."""
        return self.regulation_window_h - self.control_stop_hours_per_day

    @property
    def drive_start_hour(self) -> float:
        return self.regulation_window_start

    @property
    def drive_end_hour(self) -> float:
        """Effective drive end = start + effective hours (stops already subtracted)."""
        return self.regulation_window_start + self.drive_hours_per_day

    @property
    def total_drive_hours(self) -> float:
        return self.drive_hours_per_day * self.race_days

    def required_avg_speed(self) -> float:
        """Speed needed to cover full distance within effective driving time."""
        return self.distance_km / self.total_drive_hours

    @classmethod
    def wsc_3day(cls) -> RaceConfig:
        """3-day race attempt — NOT feasible with regulation energy (shown for analysis)."""
        return cls(race_days=3)

    @classmethod
    def wsc_4day(cls) -> RaceConfig:
        """4-day race — minimum feasible duration under regulation constraints."""
        return cls(race_days=4)
