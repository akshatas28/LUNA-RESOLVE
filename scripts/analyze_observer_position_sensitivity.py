
import numpy as np
import rasterio

from pathlib import Path
from pyproj import CRS, Geod, Transformer
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "lola"

LATITUDE = -85.4381
LONGITUDE = 37.36667

MOON_RADIUS_M = 1_737_400

FILES = {
    "ELEVATION": "Site06_final_adj_5mpp_surf.tif",
    "TOTAL_Z_UNCERTAINTY": "Site06_final_adj_5mpp_toterr.tif",
}

geographic_crs = CRS.from_proj4(
    f"+proj=longlat +R={MOON_RADIUS_M} +no_defs"
)

geod = Geod(a=MOON_RADIUS_M, b=MOON_RADIUS_M)


def main():

    rasters = {}

    for label, filename in FILES.items():

        src = rasterio.open(DATA / filename)

        transformer = Transformer.from_crs(
            geographic_crs,
            src.crs,
            always_xy=True
        )

        rasters[label] = (src, transformer)

    print("\nOBSERVER POSITION SENSITIVITY")
    print("=" * 75)

    print(
        f"{'EAST':>7} {'NORTH':>7} "
        f"{'ELEVATION':>12} {'Z UNCERTAINTY':>15}"
    )

    print("-" * 75)

    results = []

    offsets = [-10, -5, 0, 5, 10]

    for north in offsets:

        for east in offsets:

            distance = np.hypot(east, north)

            if distance == 0:
                azimuth = 0
            else:
                azimuth = np.degrees(
                    np.arctan2(east, north)
                ) % 360

            lon, lat, _ = geod.fwd(
                LONGITUDE,
                LATITUDE,
                azimuth,
                distance
            )

            values = {}

            for label, (src, transformer) in rasters.items():

                x, y = transformer.transform(lon, lat)

                col, row = (~src.transform) * (x, y)

                value = map_coordinates(
                    src.read(1),
                    [[row - 0.5], [col - 0.5]],
                    order=1,
                    mode="nearest"
                )[0]

                values[label] = float(value)

            results.append({
                "east": east,
                "north": north,
                "elevation": values["ELEVATION"],
                "uncertainty": values["TOTAL_Z_UNCERTAINTY"]
            })

            print(
                f"{east:7.1f} {north:7.1f} "
                f"{values['ELEVATION']:12.4f} "
                f"{values['TOTAL_Z_UNCERTAINTY']:15.4f}"
            )

    elevations = np.array([
        r["elevation"] for r in results
    ])

    print("\nSUMMARY")
    print("-" * 75)

    print("Sample locations:", len(results))
    print("Minimum elevation:", f"{elevations.min():.4f} m")
    print("Maximum elevation:", f"{elevations.max():.4f} m")
    print("Elevation range:", f"{np.ptp(elevations):.4f} m")
    print("Mean elevation:", f"{elevations.mean():.4f} m")

    for src, _ in rasters.values():
        src.close()


if __name__ == "__main__":
    main()
