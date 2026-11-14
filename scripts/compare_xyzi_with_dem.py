import numpy as np
import rasterio

point_file = "data/raw/lola/Site06_final_adj.xyzi"
dem_file = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

points = np.fromfile(point_file, dtype="<f8").reshape(-1, 4)

# Convert point-cloud X/Y from km to metres.
x = points[:, 0] * 1000.0
y = points[:, 1] * 1000.0
point_z = points[:, 2] * 1000.0

with rasterio.open(dem_file) as dem:
    sampled = np.array([
        value[0]
        for value in dem.sample(zip(x, y))
    ])

valid = np.isfinite(sampled) & np.isfinite(point_z)

residual = point_z[valid] - sampled[valid]

print("POINT-CLOUD vs DEM COMPARISON")
print("Total points:", len(points))
print("Valid comparisons:", len(residual))
print("Excluded points:", len(points) - len(residual))

print("\nELEVATION RESIDUALS (point Z - DEM Z)")
print("Mean (m):", np.mean(residual))
print("Mean absolute (m):", np.mean(np.abs(residual)))
print("Median absolute (m):", np.median(np.abs(residual)))
print("RMSE (m):", np.sqrt(np.mean(residual ** 2)))
print("95th percentile absolute (m):",
      np.percentile(np.abs(residual), 95))
print("Maximum absolute (m):", np.max(np.abs(residual)))