
import csv
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]

SOLAR_FILE = ROOT / "data" / "processed" / "connecting_ridge_solar_illumination.csv"
HORIZON_FILE = ROOT / "data" / "processed" / "connecting_ridge_horizon_fine_0p5deg_2p5m_7975m.csv"
OUTPUT_FILE = ROOT / "data" / "processed" / "connecting_ridge_terrain_illumination.csv"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main():
    solar_rows = read_csv(SOLAR_FILE)
    horizon_rows = read_csv(HORIZON_FILE)

    if not solar_rows or not horizon_rows:
        raise ValueError("Solar or terrain horizon CSV is empty.")

    horizon_rows.sort(key=lambda row: float(row["azimuth_deg"]))

    azimuths = np.array([
        float(row["azimuth_deg"]) for row in horizon_rows
    ])

    horizon_angles = np.array([
        float(row["horizon_elevation_deg"]) for row in horizon_rows
    ])

    if len(np.unique(azimuths)) != len(azimuths):
        raise ValueError("Duplicate terrain horizon azimuths found.")

    if not all(row["coverage_complete"].strip().lower() == "true"
               for row in horizon_rows):
        raise ValueError("Terrain horizon has incomplete coverage.")

    # Circular interpolation handles azimuths around 0°/360°.
    extended_azimuths = np.concatenate((
        [azimuths[-1] - 360.0],
        azimuths,
        [azimuths[0] + 360.0],
    ))

    extended_horizons = np.concatenate((
        [horizon_angles[-1]],
        horizon_angles,
        [horizon_angles[0]],
    ))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    terrain_visible_count = 0
    terrain_blocked_count = 0

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "utc",
            "solar_azimuth_deg",
            "solar_elevation_deg",
            "terrain_horizon_elevation_deg",
            "geometrically_illuminated",
            "terrain_visible",
        ])

        for row in solar_rows:
            azimuth = float(row["solar_azimuth_deg"])
            elevation = float(row["solar_elevation_deg"])

            terrain_horizon = np.interp(
                azimuth,
                extended_azimuths,
                extended_horizons,
            )

            geometrically_illuminated = elevation > 0.0
            effective_horizon = max(0.0, terrain_horizon)
            terrain_visible = elevation > effective_horizon

            if terrain_visible:
                terrain_visible_count += 1
            else:
                terrain_blocked_count += 1

            writer.writerow([
                row["utc"],
                f"{azimuth:.6f}",
                f"{elevation:.6f}",
                f"{terrain_horizon:.6f}",
                geometrically_illuminated,
                terrain_visible,
            ])

    print("Terrain illumination classification: COMPLETE")
    print("Samples:", len(solar_rows))
    print("Terrain-visible samples:", terrain_visible_count)
    print("Terrain-blocked samples:", terrain_blocked_count)
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
