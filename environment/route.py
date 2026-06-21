from __future__ import annotations
import csv
import math
from dataclasses import dataclass, field
from typing import List, Optional


# Official BWSC control-stop locations (cumulative km from Darwin), from data/route.csv
# rows flagged control_stop=TRUE: Katherine .. Port Augusta.
OFFICIAL_CONTROL_STOPS_KM = [310, 580, 850, 1120, 1400, 1670, 2040, 2290, 2550]


def load_control_stops_km(csv_path: str) -> List[float]:
    """Read cumulative-km of control stops from a route CSV.

    Expects columns ``cumulative_km`` and ``control_stop`` (TRUE/FALSE). Falls back
    to the official BWSC stop list if the file lacks those columns.
    """
    stops: List[float] = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            flag = str(row.get("control_stop", "")).strip().upper()
            if flag in ("TRUE", "1", "YES") and "cumulative_km" in row:
                stops.append(float(row["cumulative_km"]))
    return stops or list(OFFICIAL_CONTROL_STOPS_KM)


@dataclass
class RouteSegment:
    distance_km: float
    grade_percent: float = 0.0   # positive = uphill, negative = downhill
    altitude_m: float = 0.0
    name: str = ""

    @property
    def elevation_change_m(self) -> float:
        theta = math.atan(self.grade_percent / 100.0)
        return self.distance_km * 1000.0 * math.sin(theta)


@dataclass
class RouteProfile:
    segments: List[RouteSegment] = field(default_factory=list)

    def total_distance_km(self) -> float:
        return sum(s.distance_km for s in self.segments)

    def elevation_gain_m(self) -> float:
        return sum(s.elevation_change_m for s in self.segments if s.grade_percent > 0)

    def elevation_loss_m(self) -> float:
        return abs(sum(s.elevation_change_m for s in self.segments if s.grade_percent < 0))

    def grade_at_distance(self, distance_km: float) -> tuple[float, float]:
        """Return (grade_percent, altitude_m) at cumulative distance into route."""
        cumulative = 0.0
        for seg in self.segments:
            cumulative += seg.distance_km
            if distance_km <= cumulative:
                return seg.grade_percent, seg.altitude_m
        # Beyond route end: flat at last segment altitude
        last = self.segments[-1] if self.segments else RouteSegment(0)
        return 0.0, last.altitude_m

    @classmethod
    def flat(cls, distance_km: float) -> RouteProfile:
        return cls(segments=[RouteSegment(distance_km=distance_km, grade_percent=0.0)])

    @classmethod
    def wsc_approximation(cls) -> RouteProfile:
        """Rough elevation profile for Darwin→Adelaide (Stuart Highway)."""
        return cls(segments=[
            RouteSegment(200, 0.0, 50, "Darwin plains"),
            RouteSegment(300, 0.5, 150, "Katherine rise"),
            RouteSegment(200, 1.2, 400, "Tennant Creek approach"),
            RouteSegment(100, -0.8, 350, "Alice Springs descent"),
            RouteSegment(200, 0.3, 400, "Alice Springs plateau"),
            RouteSegment(250, -0.5, 200, "Coober Pedy run"),
            RouteSegment(300, 0.2, 250, "Port Augusta north"),
            RouteSegment(472, -0.3, 50, "Adelaide run-in"),
        ])

    @classmethod
    def from_csv(cls, path: str) -> RouteProfile:
        """CSV columns: distance_km, grade_percent, altitude_m, name (optional)."""
        segments = []
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                segments.append(RouteSegment(
                    distance_km=float(row["distance_km"]),
                    grade_percent=float(row.get("grade_percent", 0)),
                    altitude_m=float(row.get("altitude_m", 0)),
                    name=row.get("name", ""),
                ))
        return cls(segments=segments)
