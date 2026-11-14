
import csv
import math
import numpy as np
import rasterio

from scipy.ndimage import map_coordinates
from rasterio.crs import CRS
from rasterio.warp import transform
from pyproj import Geod

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"
FINE_CSV = "data/processed/nobile_rim_1_horizon_fine_0p5deg_2p5m_9975m.csv"
OPT_CSV = "data/processed/nobile_rim_1_horizon_optimized_experimental.csv"

LAT = -85.4381
LON = 37.36667
R = 1737400.0
GEOD = Geod(a=R, b=R)

def sample_elevation(data, row, col):
    return float(map_coordinates(
        data, [[row], [col]], order=1, mode="nearest"
    )[0])

def evaluate(terrain, dem, geo_crs, azimuth, distance):
    lon, lat, _ = GEOD.fwd(LON, LAT, azimuth, distance)

    xs, ys = transform(geo_crs, dem.crs, [lon], [lat])

    col = (xs[0] - dem.transform.c) / dem.transform.a - 0.5
    row = (ys[0] - dem.transform.f) / dem.transform.e - 0.5

    if not (0 <= row <= dem.height - 1 and
            0 <= col <= dem.width - 1):
        return None

    elevation = sample_elevation(terrain, row, col)

    return elevation

with rasterio.open(RASTER) as dem:
    terrain = dem.read(1)

    geo_crs = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")

    ox, oy = transform(
        geo_crs, dem.crs, [LON], [LAT]
    )

    observer_col = (ox[0] - dem.transform.c) / dem.transform.a - 0.5
    observer_row = (oy[0] - dem.transform.f) / dem.transform.e - 0.5

    observer_elevation = sample_elevation(
        terrain, observer_row, observer_col
    )

    def horizon_angle(elevation, distance):
        tr = R + elevation
        obs = R + observer_elevation
        angle = distance / R

        vertical = tr * math.cos(angle) - obs
        horizontal = tr * math.sin(angle)

        return math.degrees(math.atan2(vertical, horizontal))

    fine = {
        float(r["azimuth_deg"]): r
        for r in csv.DictReader(open(FINE_CSV, newline=""))
    }

    optimized = {
        float(r["azimuth_deg"]): r
        for r in csv.DictReader(open(OPT_CSV, newline=""))
    }

    print("OBSERVER ELEVATION:", observer_elevation)

    for azimuth in [80.5, 214.5]:
        print("\nAZIMUTH:", azimuth)
        print("Fine CSV:", fine[azimuth]["horizon_elevation_deg"],
              "at", fine[azimuth]["obstruction_distance_m"], "m")
        print("Optimized CSV:", optimized[azimuth]["horizon_elevation_deg"],
              "at", optimized[azimuth]["obstruction_distance_m"], "m")

        distances = (
            [2.5, 205.0, 206.10502698, 207.5]
            if azimuth == 80.5
            else [37.5, 39.40983006, 40.0, 42.5]
        )

        print("DISTANCE | TERRAIN ELEVATION | HORIZON ANGLE")

        for distance in distances:
            elevation = evaluate(
                terrain, dem, geo_crs, azimuth, distance
            )

            if elevation is None:
                print(distance, "OUTSIDE DEM")
                continue

            angle = horizon_angle(elevation, distance)

            print(
                f"{distance:10.4f} | "
                f"{elevation:18.6f} | "
                f"{angle:14.8f}"
            )
