
import numpy as np
import rasterio
from pathlib import Path
from rasterio.crs import CRS
from rasterio.warp import transform
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "lola"

LATITUDE = -85.4381
LONGITUDE = 37.36667

GEOGRAPHIC_CRS = CRS.from_proj4(
    "+proj=longlat +R=1737400 +no_defs"
)

FILES = [
    "Site06_final_adj_5mpp_toterr.tif",
    "Site06_final_adj_5mpp_slperr.tif",
]

def main():
    for filename in FILES:
        path = DATA / filename

        print("\n" + "=" * 65)
        print(filename)
        print("=" * 65)

        with rasterio.open(path) as src:
            data = src.read(1).astype(float)

            xs, ys = transform(
                GEOGRAPHIC_CRS,
                src.crs,
                [LONGITUDE],
                [LATITUDE],
            )

            col = (
                (xs[0] - src.transform.c)
                / src.transform.a - 0.5
            )

            row = (
                (ys[0] - src.transform.f)
                / src.transform.e - 0.5
            )

            if not (
                0 <= row <= src.height - 1
                and 0 <= col <= src.width - 1
            ):
                raise ValueError("Observer outside raster.")

            value = map_coordinates(
                data,
                [[row], [col]],
                order=1,
                mode="nearest",
            )[0]

            valid = data[np.isfinite(data)]

            print("Dimensions:", src.width, "x", src.height)
            print("Pixel size:", src.res)
            print("CRS:", src.crs)
            print("Observer uncertainty:", f"{value:.6f}")
            print("Minimum:", f"{np.min(valid):.6f}")
            print("Maximum:", f"{np.max(valid):.6f}")
            print("Mean:", f"{np.mean(valid):.6f}")
            print("Valid pixels:", len(valid))

if __name__ == "__main__":
    main()
