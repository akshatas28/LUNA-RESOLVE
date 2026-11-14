
import math
import rasterio
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

    row, col = dem.index(x, y)

    pixel_x, pixel_y = rasterio.transform.xy(
        dem.transform, row, col, offset="center"
    )

    print("OBSERVER")
    print(f"Projected coordinate: ({x:.3f}, {y:.3f})")
    print(f"Pixel: row={row}, col={col}")
    print(f"Pixel centre: ({pixel_x:.3f}, {pixel_y:.3f})")
    print(
        "Coordinate-to-pixel-centre distance:",
        f"{math.hypot(pixel_x-x, pixel_y-y):.3f} m"
    )

    print("\nNEAR-FIELD RAY SAMPLING")
    print("-" * 75)

    for azimuth in range(140, 156):

        azimuth_rad = math.radians(azimuth)

        # Same local-north calculation as the current engine.
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

        map_angle = north_angle - azimuth_rad

        print(f"\nAzimuth: {azimuth} degrees")

        for distance in (5, 10, 15, 20, 25, 30):

            sx = x + distance * math.cos(map_angle)
            sy = y + distance * math.sin(map_angle)

            r, c = dem.index(sx, sy)

            elevation = dem.read(
                1,
                window=rasterio.windows.Window(c, r, 1, 1)
            )[0, 0]

            print(
                f"Distance={distance:2d} m | "
                f"row={r:4d} col={c:4d} | "
                f"elevation={elevation:9.3f} m"
            )
