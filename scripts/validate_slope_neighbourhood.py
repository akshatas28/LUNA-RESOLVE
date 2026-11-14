import rasterio
import numpy as np

BASE = "data/raw/lola/"
ROW = 1999
COL = 2000
RADIUS = 5
PIXEL_SIZE = 5.0

# Read a 13x13 window: 11x11 target pixels plus a one-pixel halo
window = (
    (ROW - RADIUS - 1, ROW + RADIUS + 2),
    (COL - RADIUS - 1, COL + RADIUS + 2)
)

with rasterio.open(BASE + "Site06_final_adj_5mpp_surf.tif") as ds:
    elevation = ds.read(1, window=window)

with rasterio.open(BASE + "Site06_final_adj_5mpp_slp.tif") as ds:
    nasa = ds.read(1, window=(
        (ROW - RADIUS, ROW + RADIUS + 1),
        (COL - RADIUS, COL + RADIUS + 1)
    ))

# Central finite differences, excluding the one-pixel halo
dz_drow = (
    elevation[2:, 1:-1] - elevation[:-2, 1:-1]
) / (2 * PIXEL_SIZE)

dz_dcol = (
    elevation[1:-1, 2:] - elevation[1:-1, :-2]
) / (2 * PIXEL_SIZE)

calculated = np.degrees(
    np.arctan(np.sqrt(dz_drow**2 + dz_dcol**2))
)

difference = np.abs(calculated - nasa)

valid = (
    np.isfinite(calculated)
    & np.isfinite(nasa)
)

diff = difference[valid]

print("SLOPE REPRODUCTION: 55 m NEIGHBOURHOOD")
print("Valid comparisons:", diff.size)
print("Mean absolute difference:", float(np.mean(diff)), "degrees")
print("Median absolute difference:", float(np.median(diff)), "degrees")
print("Maximum absolute difference:", float(np.max(diff)), "degrees")
print("95th percentile difference:", float(np.percentile(diff, 95)), "degrees")
print("Matches within 0.001 degrees:", int(np.sum(diff < 0.001)))
print("Matches within 0.01 degrees:", int(np.sum(diff < 0.01)))