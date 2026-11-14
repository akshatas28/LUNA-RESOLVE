
import numpy as np
import rasterio

from pathlib import Path
from pyproj import CRS, Transformer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "lola"

LATITUDE = -85.4381
LONGITUDE = 37.36667

RADIUS = 1737400.0

FILES = {
    "ELEVATION": "Site06_final_adj_5mpp_surf.tif",
    "TOTAL_Z_UNCERTAINTY": "Site06_final_adj_5mpp_toterr.tif",
    "SLOPE_UNCERTAINTY": "Site06_final_adj_5mpp_slperr.tif",
}

def main():

    geographic_crs = CRS.from_proj4(
        f"+proj=longlat +R={RADIUS} +no_defs"
    )

    print("OBSERVER NEIGHBORHOOD INSPECTION")
    print("=" * 75)

    for label, filename in FILES.items():

        path = DATA / filename

        with rasterio.open(path) as src:

            transformer = Transformer.from_crs(
                geographic_crs,
                src.crs,
                always_xy=True
            )

            x, y = transformer.transform(
                LONGITUDE,
                LATITUDE
            )

            col_float, row_float = (
                (~src.transform) * (x, y)
            )

            col = int(np.floor(col_float))
            row = int(np.floor(row_float))

            window = rasterio.windows.Window(
                col - 3,
                row - 3,
                7,
                7
            )

            grid = src.read(1, window=window)

            print("\n", label)
            print("Raster:", filename)
            print("Observer pixel row:", row)
            print("Observer pixel column:", col)
            print("Observer fractional pixel position:",
                  f"row={row_float:.4f}, col={col_float:.4f}")
            print("Pixel size:", src.res)

            print("\n7 x 7 neighborhood:")

            for values in grid:
                print(" ".join(
                    f"{v:10.3f}" if np.isfinite(v)
                    else "      NaN"
                    for v in values
                ))

if __name__ == "__main__":
    main()
