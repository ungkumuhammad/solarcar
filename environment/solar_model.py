import math


class SolarModel:
    """Clear-sky sine irradiance model for a fixed latitude.

    Integrates to ~6.5 peak-sun-hours/day for Darwin-Adelaide corridor.
    """

    def __init__(
        self,
        sunrise_hour: float = 6.5,
        sunset_hour: float = 18.5,
        peak_irradiance: float = 1000.0,  # W/m²
        cloud_factor: float = 1.0,
    ):
        self.sunrise = sunrise_hour
        self.sunset = sunset_hour
        self.peak = peak_irradiance
        self.cloud_factor = cloud_factor

    def irradiance(self, hour_of_day: float) -> float:
        """Return irradiance W/m² at given decimal hour (0–24)."""
        if hour_of_day <= self.sunrise or hour_of_day >= self.sunset:
            return 0.0
        t = (hour_of_day - self.sunrise) / (self.sunset - self.sunrise)
        return self.peak * math.sin(math.pi * t) ** 1.5 * self.cloud_factor

    def daily_energy_wh_m2(self, dt_h: float = 0.5) -> float:
        """Integrate irradiance over one full day (Wh/m²)."""
        total = 0.0
        t = 0.0
        while t < 24.0:
            total += self.irradiance(t) * dt_h
            t += dt_h
        return total

    def peak_sun_hours(self) -> float:
        return self.daily_energy_wh_m2() / 1000.0
