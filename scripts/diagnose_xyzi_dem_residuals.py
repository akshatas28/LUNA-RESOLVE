import numpy as np
import rasterio

points = np.fromfile(
    "data/raw/lola/Site06_final_adj.xyzi",
    dtype="<f8"
).reshape(-1, 4)

with rasterio.open(
    "data/raw/lola/Site06_final_adj_5mpp_surf.tif"
) as dem:
    x = points[:, 0] * 1000
    y = points[:, 1] * 1000
    point_z = points[:, 2] * 1000

    dem_z = np.array([
        value[0] for value in dem.sample(zip(x, y))
    ])

valid = np.isfinite(dem_z) & np.isfinite(point_z)

residual = point_z[valid] - dem_z[valid]
valid_points = points[valid]

print("ABSOLUTE RESIDUAL PERCENTILES (m)")
for percentile in [50, 90, 95, 99, 99.5, 99.9, 99.99, 100]:
    print(
        f"{percentile}%:",
        np.percentile(np.abs(residual), percentile)
    )

print("\nTOP 10 LARGEST ABSOLUTE RESIDUALS")

indices = np.argsort(np.abs(residual))[-10:][::-1]

for i in indices:
    print(
        f"X={valid_points[i, 0]:.6f} km, "
        f"Y={valid_points[i, 1]:.6f} km, "
        f"Point Z={valid_points[i, 2]:.6f} km, "
        f"DEM Z={dem_z[valid][i]:.3f} m, "
        f"Residual={residual[i]:.3f} m"
    )