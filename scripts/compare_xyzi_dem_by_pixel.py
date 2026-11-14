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
    z = points[:, 2] * 1000

    rows = np.floor(
        (y - dem.transform.f) / dem.transform.e
    ).astype(int)

    cols = np.floor(
        (x - dem.transform.c) / dem.transform.a
    ).astype(int)

    pixel_ids = rows * dem.width + cols

    dem_values = np.array([
        value[0] for value in dem.sample(zip(x, y))
    ])

valid = (
    np.isfinite(z)
    & np.isfinite(dem_values)
)

pixel_ids = pixel_ids[valid]
z = z[valid]
dem_values = dem_values[valid]

# Group observations by their DEM pixel.
unique_pixels, inverse = np.unique(
    pixel_ids, return_inverse=True
)

counts = np.bincount(inverse)
number_of_pixels = len(unique_pixels)

# Calculate mean elevation per pixel.
sum_z = np.bincount(inverse, weights=z)
mean_z = sum_z / counts

# Sort observations once to calculate medians efficiently.
order = np.lexsort((z, inverse))
sorted_z = z[order]
sorted_dem = dem_values[order]

starts = np.cumsum(counts) - counts

lower = starts + (counts - 1) // 2
upper = starts + counts // 2

median_z = (
    sorted_z[lower] + sorted_z[upper]
) / 2

# DEM elevation is constant within each pixel.
pixel_dem = sorted_dem[starts]

mean_residual = mean_z - pixel_dem
median_residual = median_z - pixel_dem

print("PIXEL-LEVEL COMPARISON")
print("Total point observations:", len(z))
print("Unique DEM pixels:", number_of_pixels)
print("Pixels with multiple observations:", np.sum(counts > 1))
print("Maximum observations in one pixel:", counts.max())

for name, residual in [
    ("MEAN POINT ELEVATION - DEM", mean_residual),
    ("MEDIAN POINT ELEVATION - DEM", median_residual),
]:
    print("\n", name)
    print("Mean absolute difference (m):",
          np.mean(np.abs(residual)))
    print("Median absolute difference (m):",
          np.median(np.abs(residual)))
    print("RMSE (m):",
          np.sqrt(np.mean(residual ** 2)))
    print("95th percentile absolute difference (m):",
          np.percentile(np.abs(residual), 95))
    print("Maximum absolute difference (m):",
          np.max(np.abs(residual)))