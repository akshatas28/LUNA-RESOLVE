
import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

MISSION_FILE = PROCESSED / "nobile_rim_1_mission_environment.csv"
HORIZON_FILE = PROCESSED / "nobile_rim_1_horizon_fine_0p5deg_2p5m_9975m.csv"

OUTPUT_FILE = PROCESSED / "nobile_rim_1_lander_height_scenarios.csv"
SUMMARY_FILE = PROCESSED / "nobile_rim_1_lander_height_summary.csv"

MOON_RADIUS_M = 1_737_400.0
OBSERVER_ELEVATION_M = 5946.8994

LANDER_HEIGHTS_M = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        columns = reader.fieldnames or []

    if not rows:
        raise ValueError(f"No data found in {path}")

    return rows, columns


def require_columns(columns, names, filename):
    missing = [name for name in names if name not in columns]

    if missing:
        raise KeyError(
            f"Missing columns in {filename}: {missing}. "
            f"Available columns: {columns}"
        )


def circular_interpolate(angles, values, query_angles):
    angles = np.asarray(angles, dtype=float) % 360.0
    values = np.asarray(values, dtype=float)
    query_angles = np.asarray(query_angles, dtype=float) % 360.0

    order = np.argsort(angles)
    angles = angles[order]
    values = values[order]

    extended_angles = np.concatenate((
        [angles[-1] - 360.0],
        angles,
        [angles[0] + 360.0],
    ))

    extended_values = np.concatenate((
        [values[-1]],
        values,
        [values[0]],
    ))

    return np.interp(
        query_angles,
        extended_angles,
        extended_values,
    )


def adjusted_obstruction_angle(distance_m, terrain_elevation_m, height_m):
    observer_radius = (
        MOON_RADIUS_M + OBSERVER_ELEVATION_M + height_m
    )

    target_radius = MOON_RADIUS_M + terrain_elevation_m
    central_angle = distance_m / MOON_RADIUS_M

    numerator = (
        target_radius * np.cos(central_angle)
        - observer_radius
    )

    denominator = target_radius * np.sin(central_angle)

    terrain_angle = np.degrees(
        np.arctan2(numerator, denominator)
    )

    geometric_limb = -np.degrees(
        np.arccos(MOON_RADIUS_M / observer_radius)
    )

    return np.maximum(terrain_angle, geometric_limb)


def main():
    mission, mission_columns = read_csv(MISSION_FILE)
    horizon, horizon_columns = read_csv(HORIZON_FILE)

    require_columns(
        mission_columns,
        ["utc", "solar_elevation_deg", "solar_azimuth_deg"],
        MISSION_FILE.name,
    )

    require_columns(
        horizon_columns,
        [
            "azimuth_deg",
            "horizon_elevation_deg",
            "obstruction_distance_m",
            "obstruction_elevation_m",
            "coverage_complete",
        ],
        HORIZON_FILE.name,
    )

    mission_times = [row["utc"] for row in mission]

    if len(set(mission_times)) != len(mission_times):
        raise ValueError("Duplicate timestamps in mission dataset.")

    if not all(
        str(row["coverage_complete"]).strip().lower()
        in ("true", "1", "yes")
        for row in horizon
    ):
        raise ValueError("Horizon dataset has incomplete directions.")

    solar_elevations = np.asarray([
        float(row["solar_elevation_deg"]) for row in mission
    ])

    solar_azimuths = np.asarray([
        float(row["solar_azimuth_deg"]) for row in mission
    ])

    horizon_azimuths = np.asarray([
        float(row["azimuth_deg"]) for row in horizon
    ])

    baseline_horizon = np.asarray([
        float(row["horizon_elevation_deg"]) for row in horizon
    ])

    obstruction_distances = np.asarray([
        float(row["obstruction_distance_m"]) for row in horizon
    ])

    obstruction_elevations = np.asarray([
        float(row["obstruction_elevation_m"]) for row in horizon
    ])

    if np.any(obstruction_distances <= 0):
        raise ValueError("Obstruction distances must be positive.")

    if not np.all(np.isfinite(solar_elevations)):
        raise ValueError("Invalid solar elevations.")

    if not np.all(np.isfinite(baseline_horizon)):
        raise ValueError("Invalid baseline horizon values.")

    output_rows = []
    summary_rows = []

    print("LANDER HEIGHT SCENARIO ANALYSIS")
    print("=" * 60)

    for height in LANDER_HEIGHTS_M:

        if height == 0.0:
            # Preserve the established terrain-horizon baseline.
            adjusted_horizon = baseline_horizon.copy()

            # The existing surface-level model uses the geometric
            # horizon as a minimum effective obstruction angle.
            effective_horizon = np.maximum(0.0, adjusted_horizon)

            method = "existing_baseline"

        else:
            # Approximation: transform the currently recorded
            # maximum obstruction point for the elevated observer.
            adjusted_horizon = adjusted_obstruction_angle(
                obstruction_distances,
                obstruction_elevations,
                height,
            )

            effective_horizon = adjusted_horizon
            method = "single_obstruction_sensitivity"

        solar_horizons = circular_interpolate(
            horizon_azimuths,
            effective_horizon,
            solar_azimuths,
        )

        visible = solar_elevations > solar_horizons

        visible_count = int(np.sum(visible))
        percentage = visible_count / len(mission) * 100.0

        summary_rows.append({
            "lander_height_m": height,
            "observer_elevation_m": OBSERVER_ELEVATION_M + height,
            "visible_samples": visible_count,
            "total_samples": len(mission),
            "visibility_percent": percentage,
            "minimum_effective_horizon_deg": float(
                np.min(effective_horizon)
            ),
            "maximum_effective_horizon_deg": float(
                np.max(effective_horizon)
            ),
            "method": method,
        })

        for index, row in enumerate(mission):
            output_rows.append({
                "utc": row["utc"],
                "lander_height_m": height,
                "solar_elevation_deg": solar_elevations[index],
                "solar_azimuth_deg": solar_azimuths[index],
                "adjusted_terrain_horizon_deg": solar_horizons[index],
                "solar_visible": bool(visible[index]),
                "method": method,
            })

        print(
            f"{height:4.1f} m observer: "
            f"{visible_count}/{len(mission)} "
            f"({percentage:.2f}%)"
        )

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(output_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(output_rows)

    with SUMMARY_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(summary_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print("\nOUTPUTS")
    print(OUTPUT_FILE)
    print(SUMMARY_FILE)

    print("\nSCIENTIFIC LIMITATION")
    print(
        "Elevated heights use a transformed single-obstruction "
        "approximation. The obstruction that dominates at ground "
        "level may not dominate at elevated heights."
    )

    print(
        "Recompute the complete terrain horizon from the DEM for "
        "each observer height before using elevated results "
        "as mission predictions."
    )


if __name__ == "__main__":
    main()
