
import math
import numpy as np
import rasterio
from pyproj import Geod
from rasterio.crs import CRS
from rasterio.warp import transform
from scipy.ndimage import map_coordinates

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"
R = 1737400.0
LAT, LON = -85.4381, 37.36667
GEOD = Geod(a=R, b=R)

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

        return math.degrees(math.atan2(vertical, horizontal)), elevation

    cases = [
        (80.5, 204.0, 209.0, 206.10502698),
        (214.5, 37.0, 42.5, 39.40983006),
    ]

    for azimuth, start, end, optimizer_distance in cases:
        distances = np.arange(start, end + 0.025, 0.05)
        results = [(d, *evaluate(azimuth, d)) for d in distances]

        best = max(results, key=lambda item: item[1])
        optimizer_result = evaluate(azimuth, optimizer_distance)

        print(f"\nAZIMUTH {azimuth} DEGREES")
        print(f"Dense sweep maximum: {best[1]:.8f} degrees")
        print(f"Dense sweep distance: {best[0]:.4f} m")
        print(f"Optimizer distance: {optimizer_distance:.4f} m")
        print(f"Optimizer angle: {optimizer_result[0]:.8f} degrees")
        print(f"Difference: {optimizer_result[0] - best[1]:.8f} degrees")
