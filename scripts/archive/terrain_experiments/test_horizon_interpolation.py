
import math
import numpy as np
import rasterio

from scipy.ndimage import map_coordinates
from rasterio.crs import CRS
from rasterio.warp import transform

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

LAT = -85.4381
LON = 37.36667

with rasterio.open(RASTER) as dem:

    geographic_crs = CRS.from_proj4(
        "+proj=longlat +R=1737400 +no_defs"
    )

    xs, ys = transform(
        geographic_crs,
        dem.crs,
        [LON],
        [LAT]
    )

    x, y = xs[0], ys[0]

    terrain = dem.read(1)

    # Convert projected coordinates to fractional
    # array indices. Integer indices represent pixel centres.
    col_f = (x - dem.transform.c) / dem.transform.a - 0.5
    row_f = (y - dem.transform.f) / dem.transform.e - 0.5

    def bilinear_elevation(px, py):

        col = (
            (px - dem.transform.c) / dem.transform.a - 0.5
        )

        row = (
            (py - dem.transform.f) / dem.transform.e - 0.5
        )

        if (
            row < 0 or col < 0
            or row > dem.height - 1
            or col > dem.width - 1
        ):
            return np.nan

        return float(
            map_coordinates(
                terrain,
                [[row], [col]],
                order=1,
                mode="nearest"
            )[0]
        )

    observer_elevation = bilinear_elevation(x, y)

    print("OBSERVER ELEVATION COMPARISON")
    print("-" * 55)

    nearest_row, nearest_col = dem.index(x, y)

    nearest_elevation = float(
        terrain[nearest_row, nearest_col]
    )

    print(f"Nearest pixel elevation: {nearest_elevation:.6f} m")
    print(f"Bilinear elevation:      {observer_elevation:.6f} m")
    print(f"Difference:              {observer_elevation-nearest_elevation:.6f} m")

    north_xs, north_ys = transform(
        geographic_crs,
        dem.crs,
        [LON, LON],
        [LAT, LAT + 0.0001]
    )

    north_angle = math.atan2(
        north_ys[1] - north_ys[0],
        north_xs[1] - north_xs[0]
    )

    print("\nNEAR-FIELD INTERPOLATION")
    print("-" * 75)

    for azimuth in (140, 143, 146, 150, 153, 155):

        map_angle = north_angle - math.radians(azimuth)

        print(f"\nAzimuth: {azimuth} degrees")

        for distance in (5, 10, 15, 20, 25, 30):

            sx = x + distance * math.cos(map_angle)
            sy = y + distance * math.sin(map_angle)

            row, col = dem.index(sx, sy)

            nearest = float(terrain[row, col])
            interpolated = bilinear_elevation(sx, sy)

            print(
                f"Distance={distance:2d} m | "
                f"Nearest={nearest:10.3f} m | "
                f"Bilinear={interpolated:10.3f} m"
            )
