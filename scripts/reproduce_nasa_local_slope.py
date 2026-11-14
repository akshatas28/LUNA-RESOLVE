import rasterio
import numpy as np

FILE = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

ROW = 1999
COL = 2000

with rasterio.open(FILE) as ds:
    z = ds.read(1)

    # Centre and four immediate neighbours
    z_w = float(z[ROW, COL - 1])
    z_e = float(z[ROW, COL + 1])
    z_n = float(z[ROW - 1, COL])
    z_s = float(z[ROW + 1, COL])

    pixel_size = 5.0

    # Central finite differences
    dz_dx = (z_e - z_w) / (2 * pixel_size)
    dz_dy = (z_n - z_s) / (2 * pixel_size)

    # Slope from the surface normal of z = f(x, y)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope_deg = np.degrees(slope_rad)

    print("CENTRAL PIXEL FINITE-DIFFERENCE SLOPE")
    print("West elevation:", z_w)
    print("East elevation:", z_e)
    print("North elevation:", z_n)
    print("South elevation:", z_s)
    print("dz/dx:", dz_dx)
    print("dz/dy:", dz_dy)
    print("Calculated slope:", slope_deg, "degrees")

with rasterio.open("data/raw/lola/Site06_final_adj_5mpp_slp.tif") as ds:
    nasa_slope = float(ds.read(1)[ROW, COL])

print("\nNASA slope:", nasa_slope, "degrees")
print("Absolute difference:", abs(slope_deg - nasa_slope), "degrees")