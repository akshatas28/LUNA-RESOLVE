import rasterio
import numpy as np
from pathlib import Path

BASE = Path("data/raw/lola")

FILES = {
    "Surface elevation": "Site06_final_adj_5mpp_surf.tif",
    "NASA slope": "Site06_final_adj_5mpp_slp.tif",
    "Total elevation uncertainty": "Site06_final_adj_5mpp_toterr.tif",
    "Slope uncertainty": "Site06_final_adj_5mpp_slperr.tif",
}

# Same provisional sample used in our earlier analysis
ROW = 1999
COL = 2000

reference = None

for name, filename in FILES.items():
    path = BASE / filename

    print("\n" + "=" * 65)
    print(name)
    print("=" * 65)

    with rasterio.open(path) as ds:
        print("Dimensions:", ds.width, "x", ds.height)
        print("Bands:", ds.count)
        print("Data type:", ds.dtypes)
        print("CRS:", ds.crs)
        print("Transform:", ds.transform)
        print("Bounds:", ds.bounds)
        print("NoData:", ds.nodata)
        print("Tags:", ds.tags())

        grid = (
            ds.width,
            ds.height,
            ds.transform,
            ds.crs,
        )

        if reference is None:
            reference = grid
        else:
            print("Same grid as surface:", grid == reference)

        values = ds.read(1, masked=True)
        valid = values.compressed()

        print("Valid pixels:", valid.size)

        if valid.size:
            print("Minimum:", float(valid.min()))
            print("Maximum:", float(valid.max()))
            print("Mean:", float(valid.mean()))

        sample = ds.read(1, window=((ROW, ROW + 1), (COL, COL + 1)))[0, 0]

        if np.ma.is_masked(sample) or not np.isfinite(sample):
            print("Sample at row", ROW, "column", COL, ": NODATA")
        else:
            print(
                "Sample at row",
                ROW,
                "column",
                COL,
                ":",
                float(sample),
            )