from __future__ import annotations
import csv
import math
from dataclasses import dataclass, field
from typing import List, Optional


# Official BWSC control-stop locations (cumulative km from Darwin), from data/route.csv
# rows flagged control_stop=TRUE: Katherine .. Port Augusta.
OFFICIAL_CONTROL_STOPS_KM = [310, 580, 850, 1120, 1400, 1670, 2040, 2290, 2550]

# Posted speed limits along the route as (cumulative_km_from, limit_kmh) steps.
# NT Stuart Highway is 130 km/h; the NT→SA border is ~20 km south of Kulgera
# (~1690 km), after which SA limits the highway to 110 km/h. No derestricted
# section exists (BWSC §3.31.6 penalises exceeding any posted limit).
OFFICIAL_SPEED_LIMITS_KM = [(0.0, 130.0), (1690.0, 110.0)]

# Analysis ceiling used when a goal-seek "leaves the speed limit open" so it can find a
# result instead of stalling at the solar-saturated floor. Non-binding for the optimized
# car (power demand scales as v³, so it never actually reaches this). Any plan that drives
# above the posted limit is flagged via speed_limit_exceedance() — analysis only, not
# race-legal (§3.31.6).
OPEN_LIMIT_CEILING_KMH = 200.0


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


def load_speed_limits_km(csv_path: str) -> List[tuple]:
    """Read posted speed limits from a route CSV as (cumulative_km_from, limit) steps.

    Expects columns ``cumulative_km`` and ``speed_limit_kmh``. A new step is emitted
    each time the posted limit changes. Falls back to the official NT/SA limits.
    """
    steps: List[tuple] = []
    last_limit = None
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "speed_limit_kmh" not in row or "cumulative_km" not in row:
                continue
            try:
                km = float(row["cumulative_km"])
                limit = float(row["speed_limit_kmh"])
            except (TypeError, ValueError):
                continue
            if limit != last_limit:
                steps.append((km, limit))
                last_limit = limit
    return steps or list(OFFICIAL_SPEED_LIMITS_KM)


def speed_limit_at_distance(limits: List[tuple], distance_km: float) -> float:
    """Posted limit (km/h) at a cumulative distance, given (km_from, limit) steps."""
    limit = limits[0][1] if limits else 130.0
    for km_from, lim in limits:
        if distance_km >= km_from:
            limit = lim
        else:
            break
    return limit


def speed_limit_exceedance(distances, speeds, driving, limits, tol_kmh: float = 0.5) -> dict:
    """Scan a driven trace for steps that exceed the posted limit at their position.

    Used to remark on a goal-seek solution that "left the speed limit open": it reports
    how far the plan drives above the posted limit and the worst offence, so the result
    can still be shown but clearly flagged as analysis-only (not race-legal, §3.31.6).

    Returns a dict ``{steps, distance_km, max_speed_kmh, max_over_kmh}``. ``tol_kmh``
    absorbs bisection rounding so a legal (clipped) run reports zero exceedance.
    """
    steps = 0
    dist_over = 0.0
    max_speed = 0.0
    max_over = 0.0
    prev_dist = None
    for d, v, drv in zip(distances, speeds, driving):
        if drv and v is not None:
            # Evaluate the posted limit at the step's START position (the previous recorded
            # distance), mirroring how the simulator clips speed — so a step that merely
            # crosses a limit boundary isn't falsely flagged.
            start_dist = prev_dist if prev_dist is not None else d
            lim = speed_limit_at_distance(limits, start_dist)
            if v > lim + tol_kmh:
                steps += 1
                if prev_dist is not None and d >= prev_dist:
                    dist_over += d - prev_dist
                max_speed = max(max_speed, v)
                max_over = max(max_over, v - lim)
        prev_dist = d
    return {
        "steps": steps,
        "distance_km": round(dist_over, 1),
        "max_speed_kmh": round(max_speed, 1),
        "max_over_kmh": round(max_over, 1),
    }


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
