import rasterio
import numpy as np

BASE = "data/raw/lola/"
ROW = 1999
COL = 2000
RADIUS = 5

with rasterio.open(BASE + "Site06_final_adj_5mpp_slp.tif") as ds:
    nasa = ds.read(
        1,
        window=(
            (ROW - RADIUS, ROW + RADIUS + 1),
            (COL - RADIUS, COL + RADIUS + 1)
        ),
        masked=True
    )

with rasterio.open(BASE + "Site06_final_adj_5mpp_slperr.tif") as ds:
    uncertainty = ds.read(
        1,
        window=(
            (ROW - RADIUS, ROW + RADIUS + 1),
            (COL - RADIUS, COL + RADIUS + 1)
        ),
        masked=True
    )

nasa_values = nasa.compressed()
uncertainty_values = uncertainty.compressed()

print("NASA SLOPE: 55 m NEIGHBOURHOOD")
print("Valid pixels:", nasa_values.size)
print("Mean:", float(np.mean(nasa_values)), "degrees")
print("Median:", float(np.median(nasa_values)), "degrees")
print("Minimum:", float(np.min(nasa_values)), "degrees")
print("Maximum:", float(np.max(nasa_values)), "degrees")
print("Standard deviation:", float(np.std(nasa_values)), "degrees")

print("\nNASA SLOPE UNCERTAINTY: 55 m NEIGHBOURHOOD")
print("Mean RMS:", float(np.mean(uncertainty_values)), "degrees")
print("Median RMS:", float(np.median(uncertainty_values)), "degrees")
print("Minimum RMS:", float(np.min(uncertainty_values)), "degrees")
print("Maximum RMS:", float(np.max(uncertainty_values)), "degrees")

print("\nCENTRE PIXEL")
print("NASA slope:", float(nasa[ RADIUS, RADIUS]), "degrees")
print("NASA slope RMS:", float(uncertainty[RADIUS, RADIUS]), "degrees")