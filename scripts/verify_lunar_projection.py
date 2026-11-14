import math
import rasterio
from rasterio.crs import CRS
from rasterio.warp import transform

latitude = -85.4381
longitude = 37.36667
radius = 1737400.0

with rasterio.open(
    "data/raw/lola/Site06_final_adj_5mpp_surf.tif"
) as dem:

    geographic_crs = CRS.from_proj4(
        "+proj=longlat +R=1737400 +no_defs"
    )

    projected_x, projected_y = transform(
        geographic_crs,
        dem.crs,
        [longitude],
        [latitude]
    )

    x_proj = projected_x[0]
    y_proj = projected_y[0]

    phi = math.radians(latitude)
    lam = math.radians(longitude)

    rho = 2 * radius * math.tan(
        (math.pi / 2 + phi) / 2
    )

    x_manual = rho * math.sin(lam)
    y_manual = rho * math.cos(lam)

    print("PROJ TRANSFORMATION")
    print(f"X: {x_proj:.6f} m")
    print(f"Y: {y_proj:.6f} m")

    print("\nMANUAL FORMULA")
    print(f"X: {x_manual:.6f} m")
    print(f"Y: {y_manual:.6f} m")

    print("\nDIFFERENCE")
    print(f"X: {abs(x_proj - x_manual):.9f} m")
    print(f"Y: {abs(y_proj - y_manual):.9f} m")

    print("\nRASTER LOCATION")
    row, col = dem.index(x_proj, y_proj)
    print(f"Row: {row}")
    print(f"Column: {col}")
    print("Inside raster:", 0 <= row < dem.height and 0 <= col < dem.width)