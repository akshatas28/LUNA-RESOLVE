import math
import rasterio
import numpy as np

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

LATITUDE = -85.4381
LONGITUDE = 37.36667

LUNAR_RADIUS_M = 1_737_400.0
CENTRAL_MERIDIAN_DEG = 0.0
SCALE_FACTOR = 1.0

# South-polar stereographic projection.
phi = math.radians(LATITUDE)
lam = math.radians(LONGITUDE - CENTRAL_MERIDIAN_DEG)

rho = (
    2.0
    * LUNAR_RADIUS_M
    * SCALE_FACTOR
    * math.tan((math.pi / 2.0 + phi) / 2.0)
)

x = rho * math.sin(lam)
y = rho * math.cos(lam)

print("PROJECTED REFERENCE COORDINATE")
print(f"X: {x:.3f} m")
print(f"Y: {y:.3f} m")

with rasterio.open(RASTER) as dataset:

    print("\nRASTER BOUNDS")
    print(dataset.bounds)

    inside = (
        dataset.bounds.left <= x <= dataset.bounds.right
        and dataset.bounds.bottom <= y <= dataset.bounds.top
    )

    print("\nINSIDE RASTER:", inside)

    if not inside:
        print("STOP: Coordinate falls outside the raster.")
        raise SystemExit(1)

    row, col = dataset.index(x, y)

    print("\nPIXEL LOCATION")
    print("Row:", row)
    print("Column:", col)

    print("\nPIXEL CENTRE")
    print(dataset.xy(row, col))

    elevation = dataset.read(
        1,
        window=((row, row + 1), (col, col + 1)),
        masked=True
    )[0, 0]

    print("\nNEAREST PIXEL SAMPLE")

    if np.ma.is_masked(elevation) or not np.isfinite(elevation):
        print("NoData")
    else:
        print(f"{float(elevation):.3f} m")