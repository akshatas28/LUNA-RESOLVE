import numpy as np
import rasterio

points = np.fromfile(
    "data/raw/lola/Site06_final_adj.xyzi",
    dtype="<f8"
).reshape(-1, 4)

with rasterio.open(
    "data/raw/lola/Site06_final_adj_5mpp_surf.tif"
) as dem, rasterio.open(
    "data/raw/lola/Site06_final_adj_5mpp_slp.tif"
) as slope, rasterio.open(
    "data/raw/lola/Site06_final_adj_5mpp_slperr.tif"
) as slope_error:

    x = points[:, 0] * 1000
    y = points[:, 1] * 1000
    point_z = points[:, 2] * 1000

    rows = np.floor((y - dem.transform.f) / dem.transform.e).astype(int)
    cols = np.floor((x - dem.transform.c) / dem.transform.a).astype(int)

    dem_z = np.array([
        value[0] for value in dem.sample(zip(x, y))
    ])

    slope_values = np.array([
        value[0] for value in slope.sample(zip(x, y))
    ])

    slope_errors = np.array([
        value[0] for value in slope_error.sample(zip(x, y))
    ])

    centre_x = dem.transform.c + (cols + 0.5) * dem.transform.a
    centre_y = dem.transform.f + (rows + 0.5) * dem.transform.e

    offset = np.sqrt((x - centre_x)**2 + (y - centre_y)**2)
    residual = point_z - dem_z

valid = (
    np.isfinite(dem_z)
    & np.isfinite(slope_values)
    & np.isfinite(slope_errors)
)

indices = np.where(valid)[0]
indices = indices[np.argsort(np.abs(residual[indices]))[-10:][::-1]]

print("TOP 10 OUTLIER LOCATIONS")
for i in indices:
    print(
        f"\nX={x[i]:.3f} m, Y={y[i]:.3f} m"
        f"\nRow={rows[i]}, Col={cols[i]}"
        f"\nPixel centre=({centre_x[i]:.3f}, {centre_y[i]:.3f}) m"
        f"\nDistance to centre={offset[i]:.3f} m"
        f"\nPoint Z={point_z[i]:.3f} m"
        f"\nDEM Z={dem_z[i]:.3f} m"
        f"\nResidual={residual[i]:.3f} m"
        f"\nNASA slope={slope_values[i]:.3f} degrees"
        f"\nNASA slope RMS uncertainty={slope_errors[i]:.3f} degrees"
    )