import rasterio
import numpy as np
from pathlib import Path

raster_path = Path("data/raw/lola/Site06_final_adj_5mpp_surf.tif")

with rasterio.open(raster_path) as dataset:
    print("FILE:", raster_path.name)
    print("DRIVER:", dataset.driver)
    print("WIDTH:", dataset.width)
    print("HEIGHT:", dataset.height)
    print("BANDS:", dataset.count)
    print("DATA TYPE:", dataset.dtypes)
    print("CRS:", dataset.crs)
    print("TRANSFORM:", dataset.transform)
    print("RESOLUTION:", dataset.res)
    print("BOUNDS:", dataset.bounds)
    print("NODATA:", dataset.nodata)
    print("UNITS:", dataset.units)
    print("CRS DETAILS:", dataset.crs.to_wkt() if dataset.crs else None)

    print("\nDATA STATISTICS:")
    for band_number in range(1, dataset.count + 1):
        band = dataset.read(band_number, masked=True)

        print(f"\nBand {band_number}")
        print("Valid pixels:", band.count())

        if band.count() > 0:
            print("Minimum:", float(band.min()))
            print("Maximum:", float(band.max()))
            print("Mean:", float(band.mean()))

    print("\nRASTER TAGS:")
    for key, value in dataset.tags().items():
        print(f"{key}: {value}")