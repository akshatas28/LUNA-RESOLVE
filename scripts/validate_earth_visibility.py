
import csv
from datetime import datetime
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"

SITES = {
    "Nobile Rim 1": {
        "earth": "nobile_rim_1_earth_visibility.csv",
        "mission": "nobile_rim_1_mission_environment.csv",
    },
    "Connecting Ridge": {
        "earth": "connecting_ridge_earth_visibility.csv",
        "mission": "connecting_ridge_mission_environment.csv",
    },
}

EXPECTED_ROWS = 1441
EXPECTED_INTERVAL_SECONDS = 1800
TIMESTAMP_TOLERANCE_SECONDS = 0.01
NUMERIC_TOLERANCE = 0.00001

ALLOWED_CATEGORIES = {
    "fully_visible",
    "partially_visible",
    "not_visible",
}


def read_csv(filename):
    path = DATA_DIR / filename

    with open(path, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise ValueError(f"Empty CSV: {path}")

    return rows


def parse_timestamp(value):
    return datetime.fromisoformat(value)


def classify_earth_visibility(elevation, angular_radius, terrain_horizon):
    effective_horizon = max(0.0, terrain_horizon)

    upper_limb = elevation + angular_radius
    lower_limb = elevation - angular_radius

    if lower_limb > effective_horizon:
        return "fully_visible"

    if upper_limb > effective_horizon:
        return "partially_visible"

    return "not_visible"


def validate_site(site_name, config):
    print("\n" + "=" * 62)
    print(f"EARTH VISIBILITY VALIDATION: {site_name}")
    print("=" * 62)

    earth = read_csv(config["earth"])
    mission = read_csv(config["mission"])

    print(f"Earth dataset rows: {len(earth)}")
    print(f"Mission dataset rows: {len(mission)}")

    if len(earth) != EXPECTED_ROWS:
        raise ValueError("Unexpected Earth dataset row count.")

    if len(mission) != EXPECTED_ROWS:
        raise ValueError("Unexpected mission dataset row count.")

    print("[OK] Both datasets contain 1,441 observations.")

    # 1. Timestamp validation.
    earth_times = [row["utc"] for row in earth]
    mission_times = [row["utc"] for row in mission]

    if earth_times != mission_times:
        raise ValueError("Earth and mission timestamps do not match.")

    parsed_times = [parse_timestamp(value) for value in earth_times]

    intervals = [
        (parsed_times[i + 1] - parsed_times[i]).total_seconds()
        for i in range(len(parsed_times) - 1)
    ]

    if any(interval <= 0 for interval in intervals):
        raise ValueError("Timestamps are not strictly increasing.")

    bad_intervals = [
        interval
        for interval in intervals
        if abs(interval - EXPECTED_INTERVAL_SECONDS)
        > TIMESTAMP_TOLERANCE_SECONDS
    ]

    if bad_intervals:
        raise ValueError(f"Unexpected timestamp intervals: {bad_intervals[:10]}")

    print("[OK] Timestamps match and intervals are 30 minutes.")

    # 2. Recompute Earth visibility from saved geometric inputs.
    counts = {
        "fully_visible": 0,
        "partially_visible": 0,
        "not_visible": 0,
    }

    mismatches = []
    mission_value_mismatches = []

    for index, (earth_row, mission_row) in enumerate(zip(earth, mission)):
        elevation = float(earth_row["earth_elevation_deg"])
        azimuth = float(earth_row["earth_azimuth_deg"])
        distance = float(earth_row["earth_distance_km"])
        angular_radius = float(earth_row["earth_angular_radius_deg"])
        terrain_horizon = float(
            earth_row["terrain_horizon_elevation_deg"]
        )

        stored = earth_row["earth_visibility"].strip().lower()

        values = [
            elevation,
            azimuth,
            distance,
            angular_radius,
            terrain_horizon,
        ]

        if not all(np.isfinite(value) for value in values):
            raise ValueError(
                f"Non-finite Earth geometry at row {index + 2}."
            )

        if not 0 <= azimuth < 360:
            raise ValueError(f"Invalid Earth azimuth at row {index + 2}.")

        if distance <= 6378.137:
            raise ValueError(f"Invalid Earth distance at row {index + 2}.")

        if not 0 < angular_radius < 90:
            raise ValueError(f"Invalid angular radius at row {index + 2}.")

        if stored not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"Unexpected Earth category at row {index + 2}: {stored}"
            )

        recomputed = classify_earth_visibility(
            elevation,
            angular_radius,
            terrain_horizon,
        )

        counts[recomputed] += 1

        if recomputed != stored:
            mismatches.append({
                "row": index + 2,
                "utc": earth_row["utc"],
                "stored": stored,
                "recomputed": recomputed,
            })

        # 3. Compare standalone Earth data with mission data.
        comparisons = [
            ("earth_elevation_deg", elevation),
            ("earth_azimuth_deg", azimuth),
        ]

        for column, earth_value in comparisons:
            mission_value = float(mission_row[column])

            if abs(earth_value - mission_value) > NUMERIC_TOLERANCE:
                mission_value_mismatches.append({
                    "row": index + 2,
                    "column": column,
                    "earth_value": earth_value,
                    "mission_value": mission_value,
                })

        mission_category = mission_row["earth_visibility"].strip().lower()

        if mission_category != stored:
            mission_value_mismatches.append({
                "row": index + 2,
                "column": "earth_visibility",
                "earth_value": stored,
                "mission_value": mission_category,
            })

    # 4. Report classification results.
    print("\nRECOMPUTED EARTH VISIBILITY")
    for category, count in counts.items():
        percentage = count / len(earth) * 100
        print(f"{category}: {count} ({percentage:.2f}%)")

    if mismatches:
        print(f"\n[FAIL] Classification mismatches: {len(mismatches)}")
        for item in mismatches[:10]:
            print(item)
        raise ValueError("Earth visibility recomputation failed.")
    else:
        print("[OK] All stored Earth classifications match recomputed values.")

    # 5. Report mission dataset cross-check.
    if mission_value_mismatches:
        print(
            "\n[FAIL] Earth-to-mission mismatches:",
            len(mission_value_mismatches),
        )
        for item in mission_value_mismatches[:10]:
            print(item)
        raise ValueError("Earth and mission datasets do not agree.")
    else:
        print("[OK] Earth elevation and azimuth match the mission dataset.")
        print("[OK] Earth visibility labels match the mission dataset.")

    print(f"\n[PASS] {site_name} Earth visibility validation passed.")


def main():
    print("LUNA-RESOLVE EARTH VISIBILITY VALIDATION")
    print("=" * 62)

    for site_name, config in SITES.items():
        validate_site(site_name, config)

    print("\n" + "=" * 62)
    print("TWO-SITE EARTH VISIBILITY VALIDATION COMPLETE")
    print("=" * 62)
    print("All implemented checks passed.")
    print(
        "This validates classification consistency using saved geometry; "
        "it does not establish independent SPICE or terrain accuracy."
    )


if __name__ == "__main__":
    main()
