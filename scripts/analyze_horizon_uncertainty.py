
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
OBSERVER_ELEVATION_M = 5946.8994


def horizon_angle(distance, obstruction_elevation):
    observer_radius = MOON_RADIUS_M + OBSERVER_ELEVATION_M
    obstruction_radius = MOON_RADIUS_M + obstruction_elevation

    central_angle = distance / MOON_RADIUS_M

    numerator = (
        obstruction_radius * np.cos(central_angle)
        - observer_radius
    )

    denominator = (
        obstruction_radius * np.sin(central_angle)
    )

    return np.degrees(np.arctan2(numerator, denominator))


def main():

    geographic_crs = CRS.from_proj4(
        f"+proj=longlat +R={MOON_RADIUS_M} +no_defs"
    )

    geod = Geod(a=MOON_RADIUS_M, b=MOON_RADIUS_M)

    transformer = None
    results = []

    with rasterio.open(UNCERTAINTY_FILE) as src:

        uncertainty_raster = src.read(1).astype(float)

        transformer = Transformer.from_crs(
            geographic_crs,
            src.crs,
            always_xy=True
        )

        with open(HORIZON_FILE, newline="") as file:

            reader = csv.DictReader(file)

            for record in reader:

                distance = float(
                    record["obstruction_distance_m"]
                )

                azimuth = float(
                    record["azimuth_deg"]
                )

                elevation = float(
                    record["obstruction_elevation_m"]
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

                sigma_z = map_coordinates(
                    uncertainty_raster,
                    [[row - 0.5], [col - 0.5]],
                    order=1,
                    mode="nearest"
                )[0]

                nominal = horizon_angle(
                    distance,
                    elevation
                )

                upper = horizon_angle(
                    distance,
                    elevation + sigma_z
                )

                lower = horizon_angle(
                    distance,
                    elevation - sigma_z
                )

                results.append({
                    "azimuth": azimuth,
                    "distance": distance,
                    "sigma_z": sigma_z,
                    "nominal": nominal,
                    "upper": upper,
                    "lower": lower,
                    "upper_change": upper - nominal,
                    "lower_change": nominal - lower,
                })

    upper_changes = np.array([
        item["upper_change"] for item in results
    ])

    lower_changes = np.array([
        item["lower_change"] for item in results
    ])

    maximum_changes = np.maximum(
        upper_changes,
        lower_changes
    )

    print("\nHORIZON ANGLE UNCERTAINTY SENSITIVITY")
    print("-" * 65)

    print("Directions analysed:", len(results))
    print(
        "Mean upper angle change:",
        f"{np.mean(upper_changes):.6f} deg"
    )
    print(
        "Mean lower angle change:",
        f"{np.mean(lower_changes):.6f} deg"
    )
    print(
        "Mean maximum absolute change:",
        f"{np.mean(maximum_changes):.6f} deg"
    )
    print(
        "95th percentile maximum change:",
        f"{np.percentile(maximum_changes, 95):.6f} deg"
    )
    print(
        "Maximum change:",
        f"{np.max(maximum_changes):.6f} deg"
    )

    print("\nLARGEST ANGLE SENSITIVITIES")
    print("-" * 65)

    for item in sorted(
        results,
        key=lambda x: max(
            x["upper_change"],
            x["lower_change"]
        ),
        reverse=True
    )[:10]:

        print(
            f"Azimuth: {item['azimuth']:6.1f} deg | "
            f"Distance: {item['distance']:8.2f} m | "
            f"RMS Z: {item['sigma_z']:.4f} m | "
            f"Nominal: {item['nominal']:.5f} deg | "
            f"Lower: {item['lower_change']:.5f} deg | "
            f"Upper: {item['upper_change']:.5f} deg"
        )


    print("\nSENSITIVITY BY OBSTRUCTION DISTANCE")
    print("-" * 65)

    distance_bands = [
        ("0-5 m", 0, 5),
        ("5-25 m", 5, 25),
        ("25-100 m", 25, 100),
        ("100-500 m", 100, 500),
        ("500-2000 m", 500, 2000),
        ("2000-5000 m", 2000, 5000),
        ("5000-9975 m", 5000, 9975),
    ]

    for label, minimum, maximum in distance_bands:

        group = [
            item for item in results
            if minimum <= item["distance"] < maximum
        ]

        if not group:
            continue

        changes = np.array([
            max(item["upper_change"], item["lower_change"])
            for item in group
        ])

        print(
            f"{label:14} | "
            f"Count: {len(group):3} | "
            f"Mean: {np.mean(changes):9.5f} deg | "
            f"95th percentile: {np.percentile(changes, 95):9.5f} deg | "
            f"Maximum: {np.max(changes):9.5f} deg"
        )


if __name__ == "__main__":
    main()
