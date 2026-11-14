import rasterio
import numpy as np

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

ROW = 1999
COL = 2000

with rasterio.open(RASTER) as ds:
    data = ds.read(
        1,
        window=((ROW - 5, ROW + 6), (COL - 5, COL + 6)),
        masked=True
    )

    print("11 x 11 TERRAIN ELEVATION WINDOW")
    print("Each cell represents a 5 m raster pixel.")
    print("Rows and columns are relative to the reference pixel.\n")

    for row in data:
        print(" ".join(
            "  NaN  " if np.ma.is_masked(v)
            else f"{float(v):7.2f}"
            for v in row
        ))

    values = data.compressed()

    print("\nSTATISTICS")
    print("Valid pixels:", len(values))
    print("Minimum:", float(values.min()))
    print("Maximum:", float(values.max()))
    print("Mean:", float(values.mean()))
    print("Standard deviation:", float(values.std()))