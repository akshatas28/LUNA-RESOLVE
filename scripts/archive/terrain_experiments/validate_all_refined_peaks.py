
import csv
import math
import numpy as np
import rasterio
from pyproj import Geod
from rasterio.crs import CRS
from rasterio.warp import transform
from scipy.ndimage import map_coordinates

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"
CSV_FILE = "data/processed/nobile_rim_1_horizon_optimized_experimental.csv"

R = 1737400.0
LAT, LON = -85.4381, 37.36667
GEOD = Geod(a=R, b=R)
STEP = 0.05
TOLERANCE = 0.002

with rasterio.open(RASTER) as dem:
    terrain = dem.read(1)
    geo_crs = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")

    ox, oy = transform(geo_crs, dem.crs, [LON], [LAT])
    oc = (ox[0] - dem.transform.c) / dem.transform.a - 0.5
    orow = (oy[0] - dem.transform.f) / dem.transform.e - 0.5

    observer = float(map_coordinates(
        terrain, [[orow], [oc]], order=1, mode="nearest"
    )[0])

    def evaluate(azimuth, distance):
        lon, lat, _ = GEOD.fwd(LON, LAT, azimuth, distance)
        xs, ys = transform(geo_crs, dem.crs, [lon], [lat])

        col = (xs[0] - dem.transform.c) / dem.transform.a - 0.5
        row = (ys[0] - dem.transform.f) / dem.transform.e - 0.5

        elevation = float(map_coordinates(
            terrain, [[row], [col]], order=1, mode="nearest"
        )[0])

        angle = distance / R
        vertical = (R + elevation) * math.cos(angle) - (R + observer)
        horizontal = (R + elevation) * math.sin(angle)

        return math.degrees(math.atan2(vertical, horizontal))

    rows = list(csv.DictReader(open(CSV_FILE, newline="")))
    discrepancies = []

    for index, item in enumerate(rows, 1):
        azimuth = float(item["azimuth_deg"])
        opt_distance = float(item["obstruction_distance_m"])
        opt_angle = float(item["horizon_elevation_deg"])

        distances = np.arange(
            max(2.5, opt_distance - 2.5),
            min(9975.0, opt_distance + 2.5) + STEP / 2,
            STEP
        )

        dense_max = max(evaluate(azimuth, d) for d in distances)
        discrepancy = dense_max - opt_angle
        discrepancies.append((azimuth, discrepancy, opt_distance))

        if index % 120 == 0:
            print(f"Checked {index}/{len(rows)} directions")

    errors = np.array([x[1] for x in discrepancies])
    abs_errors = np.abs(errors)

    print("\nFULL VALIDATION SUMMARY")
    print("Directions:", len(rows))
    print("Mean absolute difference:", np.mean(abs_errors))
    print("Maximum absolute difference:", np.max(abs_errors))
    print("95th percentile:", np.percentile(abs_errors, 95))
    print("Directions above tolerance:", np.sum(abs_errors > TOLERANCE))
    print("Tolerance:", TOLERANCE, "degrees")

    print("\nTOP 10 DISCREPANCIES")
    for azimuth, difference, distance in sorted(
        discrepancies, key=lambda x: abs(x[1]), reverse=True
    )[:10]:
        print(
            f"Azimuth {azimuth:.1f} | "
            f"Dense - optimizer: {difference:.8f} deg | "
            f"Distance: {distance:.3f} m"
        )
