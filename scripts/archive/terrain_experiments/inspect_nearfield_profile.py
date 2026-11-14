
import numpy as np
import rasterio
from pyproj import Geod
from rasterio.crs import CRS
from rasterio.warp import transform
from scipy.ndimage import map_coordinates

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

LAT = -85.4381
LON = 37.36667
AZIMUTH = 232.0
MOON_RADIUS = 1737400.0

geod = Geod(a=MOON_RADIUS, b=MOON_RADIUS)

with rasterio.open(RASTER) as dem:
    terrain = dem.read(1)

    geographic_crs = CRS.from_proj4(
        "+proj=longlat +R=1737400 +no_defs"
    )

    distances = np.arange(
        0.3125, 20.3125, 0.3125, dtype=np.float64
    )

    lons, lats, _ = geod.fwd(
        np.full(len(distances), LON),
        np.full(len(distances), LAT),
        np.full(len(distances), AZIMUTH),
        distances
    )

    xs, ys = transform(
        geographic_crs,
        dem.crs,
        lons.tolist(),
        lats.tolist()
    )

    cols = (
        (np.asarray(xs, dtype=np.float64) - dem.transform.c)
        / dem.transform.a - 0.5
    )

    rows = (
        (np.asarray(ys, dtype=np.float64) - dem.transform.f)
        / dem.transform.e - 0.5
    )

    elevations = map_coordinates(
        terrain,
        [rows, cols],
        order=1,
        mode="nearest"
    ).astype(np.float64)

    observer_x, observer_y = transform(
        geographic_crs,
        dem.crs,
        [LON],
        [LAT]
    )

    observer_col = (
        (observer_x[0] - dem.transform.c)
        / dem.transform.a - 0.5
    )

    observer_row = (
        (observer_y[0] - dem.transform.f)
        / dem.transform.e - 0.5
    )

    observer_elevation = float(
        map_coordinates(
            terrain,
            [[observer_row], [observer_col]],
            order=1,
            mode="nearest"
        )[0]
    )

    print(f"Observer elevation: {observer_elevation:.4f} m")
    print(f"Azimuth: {AZIMUTH} degrees")
    print("\nDISTANCE | ELEVATION | RELATIVE HEIGHT | HORIZON ANGLE")
    print("-" * 65)

    for distance, elevation in zip(distances, elevations):
        distance = float(distance)
        elevation = float(elevation)

        angle = np.degrees(np.arctan2(
            (MOON_RADIUS + elevation)
            * np.cos(distance / MOON_RADIUS)
            - (MOON_RADIUS + observer_elevation),
            (MOON_RADIUS + elevation)
            * np.sin(distance / MOON_RADIUS)
        ))

        print(
            f"{distance:8.2f} | "
            f"{elevation:9.4f} | "
            f"{elevation - observer_elevation:+15.4f} | "
            f"{angle:13.6f}"
        )
