import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

LAT = -85.4381
LON = 37.36667
RADIUS_M = 10000.0

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

    radius_pixels = int(RADIUS_M / 5)

    window = rasterio.windows.Window(
        col - radius_pixels,
        row - radius_pixels,
        2 * radius_pixels + 1,
        2 * radius_pixels + 1
    )

    terrain = dem.read(1, window=window)

    rows, cols = np.indices(terrain.shape)

    # Calculate actual pixel-centre coordinates.
    pixel_x = (
        dem.transform.c
        + (window.col_off + cols + 0.5) * dem.transform.a
    )

    pixel_y = (
        dem.transform.f
        + (window.row_off + rows + 0.5) * dem.transform.e
    )

    distance = np.hypot(pixel_x - x, pixel_y - y)

    inside_circle = distance <= RADIUS_M
    valid = np.isfinite(terrain)

    valid_inside = inside_circle & valid
    nodata_inside = inside_circle & ~valid
    outside_circle = ~inside_circle

    values = terrain[valid_inside]

    print("REFERENCE POINT")
    print(f"Latitude: {LAT}")
    print(f"Longitude: {LON}")
    print(f"Projected X: {x:.6f} m")
    print(f"Projected Y: {y:.6f} m")
    print(f"Raster row: {row}")
    print(f"Raster column: {col}")

    print("\nTERRAIN WINDOW")
    print("Window dimensions:", terrain.shape)
    print(f"Requested radius: {RADIUS_M:.0f} m")
    print(f"Pixels inside circle: {inside_circle.sum():,}")
    print(f"Valid terrain pixels: {valid_inside.sum():,}")
    print(f"NoData pixels inside circle: {nodata_inside.sum():,}")
    print(f"Pixels outside circle: {outside_circle.sum():,}")

    print("\nELEVATION STATISTICS")
    print(f"Minimum: {values.min():.3f} m")
    print(f"Maximum: {values.max():.3f} m")
    print(f"Mean: {values.mean():.3f} m")
    print(f"Standard deviation: {values.std():.3f} m")