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

valid = np.isfinite(z) & np.isfinite(dem_values)

z = z[valid]
x = x[valid]
y = y[valid]
rows = rows[valid]
cols = cols[valid]
pixel_ids = pixel_ids[valid]
dem_values = dem_values[valid]

unique_pixels, inverse = np.unique(
    pixel_ids, return_inverse=True
)

counts = np.bincount(inverse)

order = np.lexsort((z, inverse))
sorted_z = z[order]
sorted_dem = dem_values[order]

starts = np.cumsum(counts) - counts

lower = starts + (counts - 1) // 2
upper = starts + counts // 2

median_z = (sorted_z[lower] + sorted_z[upper]) / 2
pixel_dem = sorted_dem[starts]

residual = median_z - pixel_dem

worst = np.argsort(np.abs(residual))[-10:][::-1]

print("TEN LARGEST PIXEL-LEVEL MEDIAN RESIDUALS")

for i in worst:
    start = starts[i]
    end = start + counts[i]

    point_indices = order[start:end]

    print("\nPixel row:", unique_pixels[i] // 4000)
    print("Pixel column:", unique_pixels[i] % 4000)
    print("Observations:", counts[i])
    print("DEM elevation (m):", pixel_dem[i])
    print("Point elevations (m):", z[point_indices].tolist())
    print("Median point elevation (m):", median_z[i])
    print("Residual (m):", residual[i])