"""
Fetch elevation data along the Darwin–Adelaide route using AWS Terrain Tiles.

Data source:
  AWS Open Data Registry — Terrain Tiles (Mapzen/Tilezen elevation)
  S3 bucket: s3://elevation-tiles-prod
  Format: Cloud-Optimised GeoTIFF (COG), EPSG:3857 (Web Mercator)
  Resolution: zoom level 9 (~305 m/pixel at equator)
  Endpoint: https://elevation-tiles-prod.s3.amazonaws.com/geotiff/{zoom}/{x}/{y}.tif

Elevation encoding (Mapzen Terrarium):
  elevation_m = (R * 256 + G + B / 256) - 32768
  Applied automatically by rasterio when reading the GeoTIFF.

Coordinate handling:
  Tiles are in EPSG:3857 (Web Mercator). WGS84 lat/lon coordinates must be
  reprojected to EPSG:3857 before sampling with rasterio.
  Reprojection uses pyproj Transformer (always_xy=True convention).

Generates 58 points: 11 named checkpoints + 47 intermediate points at ~50 km spacing.

Dependencies:
  pip install rasterio pyproj
"""

import csv
import datetime
import math
import os
import urllib.request
import rasterio
from rasterio.io import MemoryFile
from pyproj import Transformer

ROUTE_CSV = os.path.join(os.path.dirname(__file__), "../data/route.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/elevation")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "elevation_profile.csv")

ZOOM = 9
TILE_BASE = "https://elevation-tiles-prod.s3.amazonaws.com/geotiff"
INTERMEDIATE_SPACING_KM = 50

to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def load_checkpoints(csv_path):
    checkpoints = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            checkpoints.append({
                "location": row["location"],
                "cumulative_km": float(row["cumulative_km"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
            })
    return checkpoints


def interpolate_points(checkpoints, spacing_km):
    """Linear lat/lon interpolation between consecutive checkpoints."""
    points = []
    for i in range(len(checkpoints) - 1):
        a = checkpoints[i]
        b = checkpoints[i + 1]
        segment_km = b["cumulative_km"] - a["cumulative_km"]
        num_steps = max(1, int(segment_km / spacing_km))
        for step in range(1, num_steps):
            frac = step / num_steps
            cum_km = a["cumulative_km"] + frac * segment_km
            lat = a["latitude"] + frac * (b["latitude"] - a["latitude"])
            lon = a["longitude"] + frac * (b["longitude"] - a["longitude"])
            points.append({
                "location": f"interp_{cum_km:.0f}km",
                "cumulative_km": round(cum_km, 1),
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
            })
    return points


def build_full_profile(checkpoints, intermediate):
    return sorted(checkpoints + intermediate, key=lambda p: p["cumulative_km"])


def lat_lon_to_tile(lat, lon, zoom):
    """Convert WGS84 lat/lon to tile (x, y) at given zoom level."""
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


_tile_cache = {}


def fetch_tile(zoom, tx, ty):
    key = (zoom, tx, ty)
    if key in _tile_cache:
        return _tile_cache[key]
    url = f"{TILE_BASE}/{zoom}/{tx}/{ty}.tif"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = resp.read()
    _tile_cache[key] = data
    return data


def sample_elevation(lat, lon):
    """Sample elevation (m) at a WGS84 lat/lon coordinate."""
    tx, ty = lat_lon_to_tile(lat, lon, ZOOM)
    tile_bytes = fetch_tile(ZOOM, tx, ty)
    mx, my = to_3857.transform(lon, lat)
    with MemoryFile(tile_bytes) as mf:
        with mf.open() as ds:
            return float(list(ds.sample([(mx, my)]))[0][0])


def main():
    access_date = datetime.date.today().isoformat()
    checkpoints = load_checkpoints(ROUTE_CSV)
    print(f"Loaded {len(checkpoints)} checkpoints")

    intermediate = interpolate_points(checkpoints, INTERMEDIATE_SPACING_KM)
    print(f"Generated {len(intermediate)} intermediate points at ~{INTERMEDIATE_SPACING_KM} km spacing")

    full_profile = build_full_profile(checkpoints, intermediate)
    print(f"Total profile points: {len(full_profile)}")

    elevations = []
    for i, pt in enumerate(full_profile):
        elev = sample_elevation(pt["latitude"], pt["longitude"])
        elevations.append(elev)
        print(f"  [{i+1}/{len(full_profile)}] {pt['location']}: {elev:.1f} m")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fieldnames = ["point_id", "location_name", "cumulative_km", "latitude", "longitude", "elevation_m", "source"]
    with open(OUTPUT_FILE, "w", newline="") as f:
        f.write(f"# Source: AWS elevation-tiles-prod (Mapzen/Tilezen terrain tiles)\n")
        f.write(f"# Dataset: SRTM-derived GeoTIFF, zoom={ZOOM}, EPSG:3857, s3://elevation-tiles-prod/geotiff/\n")
        f.write(f"# Coordinates reprojected WGS84→EPSG:3857 (pyproj) before sampling (rasterio)\n")
        f.write(f"# Retrieved: {access_date}\n")
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, (pt, elev) in enumerate(zip(full_profile, elevations)):
            writer.writerow({
                "point_id": i,
                "location_name": pt["location"],
                "cumulative_km": pt["cumulative_km"],
                "latitude": pt["latitude"],
                "longitude": pt["longitude"],
                "elevation_m": round(elev, 1),
                "source": f"elevation-tiles-prod/geotiff/{ZOOM}",
            })

    print(f"\nWritten: {OUTPUT_FILE} ({len(full_profile)} rows)")
    print("Done.")


if __name__ == "__main__":
    main()
