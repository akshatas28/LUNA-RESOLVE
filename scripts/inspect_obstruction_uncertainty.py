
import csv
import numpy as np
import rasterio

from pathlib import Path
from pyproj import CRS, Geod, Transformer
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[1]

HORIZON_FILE = (
    ROOT / "data" / "processed"
    / "nobile_rim_1_horizon_fine_0p5deg_2p5m_9975m.csv"
)

UNCERTAINTY_FILE = (
    ROOT / "data" / "raw" / "lola"
    / "Site06_final_adj_5mpp_toterr.tif"
)

LATITUDE = -85.4381
LONGITUDE = 37.36667

MOON_RADIUS_M = 1_737_400

def main():

    geographic_crs = CRS.from_proj4(
        f"+proj=longlat +R={MOON_RADIUS_M} +no_defs"
    )

    geod = Geod(
        a=MOON_RADIUS_M,
        b=MOON_RADIUS_M
    )

    with rasterio.open(UNCERTAINTY_FILE) as src:

        uncertainty = src.read(1).astype(float)

        transformer = Transformer.from_crs(
            geographic_crs,
            src.crs,
            always_xy=True
        )

        results = []

        with open(HORIZON_FILE, newline="") as file:

            reader = csv.DictReader(file)

            for record in reader:

                distance = float(
                    record["obstruction_distance_m"]
                )

                azimuth = float(
                    record["azimuth_deg"]
                )

                longitude, latitude, _ = geod.fwd(
                    LONGITUDE,
                    LATITUDE,
                    azimuth,
                    distance
                )

                x, y = transformer.transform(
                    longitude,
                    latitude
                )

                col, row = (~src.transform) * (x, y)

                value = map_coordinates(
                    uncertainty,
                    [[row - 0.5], [col - 0.5]],
                    order=1,
                    mode="nearest"
                )[0]

                results.append({
                    "azimuth": azimuth,
                    "distance": distance,
                    "horizon": float(
                        record["horizon_elevation_deg"]
                    ),
                    "uncertainty": value
                })

    values = np.array([
        item["uncertainty"]
        for item in results
    ])

    print("\nOBSTRUCTION UNCERTAINTY ANALYSIS")
    print("-" * 60)

    print("Directions analysed:", len(results))
    print("Mean RMS Z uncertainty:", f"{np.mean(values):.4f} m")
    print("Median RMS Z uncertainty:", f"{np.median(values):.4f} m")
    print("95th percentile:", f"{np.percentile(values, 95):.4f} m")
    print("Maximum:", f"{np.max(values):.4f} m")
    print("Minimum:", f"{np.min(values):.4f} m")

    print("\nHIGHEST UNCERTAINTY OBSTRUCTION LOCATIONS")
    print("-" * 60)

    for item in sorted(
        results,
        key=lambda x: x["uncertainty"],
        reverse=True
    )[:10]:

        print(
            f"Azimuth: {item['azimuth']:6.1f} deg | "
            f"Distance: {item['distance']:8.2f} m | "
            f"Horizon: {item['horizon']:9.5f} deg | "
            f"RMS Z uncertainty: {item['uncertainty']:.4f} m"
        )

if __name__ == "__main__":
    main()
