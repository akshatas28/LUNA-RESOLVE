
import csv
import math
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

SITES = {
    "Nobile Rim 1": {
        "prefix": "nobile_rim_1",
        "horizon": "nobile_rim_1_horizon_fine_0p5deg_2p5m_9975m.csv",
    },
    "Connecting Ridge": {
        "prefix": "connecting_ridge",
        "horizon": "connecting_ridge_horizon_fine_0p5deg_2p5m_7975m.csv",
    },
}

EXPECTED_SAMPLES = 1441
EXPECTED_HORIZON_DIRECTIONS = 720
EXPECTED_INTERVAL_SECONDS = 1800


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        columns = reader.fieldnames or []

    if not rows:
        raise ValueError(f"CSV contains no data: {path}")

    return rows, columns


def find_column(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate

    raise KeyError(
        f"Could not find any of {candidates}. Available columns: {columns}"
    )


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_bool(value):
    normalized = str(value).strip().lower()

    if normalized in ("true", "1", "yes"):
        return True
    if normalized in ("false", "0", "no"):
        return False

    raise ValueError(f"Unrecognized boolean value: {value!r}")


def numeric_values(rows, column):
    values = np.asarray([float(row[column]) for row in rows], dtype=float)

    if not np.all(np.isfinite(values)):
        raise ValueError(f"Non-finite values found in {column}")

    return values


def validate_site(site_name, config):
    prefix = config["prefix"]

    files = {
        "solar": PROCESSED / f"{prefix}_solar_illumination.csv",
        "terrain": PROCESSED / f"{prefix}_terrain_illumination.csv",
        "earth": PROCESSED / f"{prefix}_earth_visibility.csv",
        "mission": PROCESSED / f"{prefix}_mission_environment.csv",
        "horizon": PROCESSED / config["horizon"],
    }

    print(f"\n{'=' * 62}")
    print(f"SITE VALIDATION: {site_name}")
    print("=" * 62)

    loaded = {}

    for name, path in files.items():
        rows, columns = read_csv(path)
        loaded[name] = (rows, columns)
        print(f"[OK] {name}: {len(rows)} rows")

    solar, solar_cols = loaded["solar"]
    terrain, terrain_cols = loaded["terrain"]
    earth, earth_cols = loaded["earth"]
    mission, mission_cols = loaded["mission"]
    horizon, horizon_cols = loaded["horizon"]

    # Timestamp consistency across all four time-series files.
    time_column_names = ["utc", "UTC", "timestamp", "time_utc"]

    timestamps = {}

    for name, (rows, columns) in loaded.items():
        if name == "horizon":
            continue

        column = find_column(columns, time_column_names)
        timestamps[name] = [parse_timestamp(row[column]) for row in rows]

    reference_times = timestamps["solar"]

    for name, values in timestamps.items():
        if values != reference_times:
            raise ValueError(
                f"{site_name}: timestamps differ in {name} dataset."
            )

    print("\nTIMESTAMP VALIDATION")
    print("[OK] All four time-series datasets have matching timestamps.")

    if len(reference_times) != EXPECTED_SAMPLES:
        raise ValueError(
            f"Expected {EXPECTED_SAMPLES} observations; "
            f"found {len(reference_times)}."
        )

    if any(
        reference_times[i] <= reference_times[i - 1]
        for i in range(1, len(reference_times))
    ):
        raise ValueError("Timestamps are not strictly increasing.")

    intervals = [
        (reference_times[i] - reference_times[i - 1]).total_seconds()
        for i in range(1, len(reference_times))
    ]

    tolerance_seconds = 0.01

    incorrect_intervals = [
        interval for interval in intervals
        if abs(interval - EXPECTED_INTERVAL_SECONDS) > tolerance_seconds
    ]

    if incorrect_intervals:
        raise ValueError(
            "Unexpected timestamp interval(s): "
            f"{incorrect_intervals[:10]}"
        )

    print(f"[OK] {EXPECTED_SAMPLES} strictly increasing observations.")
    print("[OK] Every interval is exactly 30 minutes.")

    # Numeric and angular validation.
    solar_elev = numeric_values(mission, "solar_elevation_deg")
    solar_az = numeric_values(mission, "solar_azimuth_deg")
    terrain_horizon = numeric_values(
        mission, "terrain_horizon_elevation_deg"
    )
    earth_elev = numeric_values(mission, "earth_elevation_deg")
    earth_az = numeric_values(mission, "earth_azimuth_deg")

    if np.any((solar_elev < -90) | (solar_elev > 90)):
        raise ValueError("Solar elevation outside [-90, 90].")

    if np.any((earth_elev < -90) | (earth_elev > 90)):
        raise ValueError("Earth elevation outside [-90, 90].")

    if np.any((solar_az < 0) | (solar_az >= 360)):
        raise ValueError("Solar azimuth outside [0, 360).")

    if np.any((earth_az < 0) | (earth_az >= 360)):
        raise ValueError("Earth azimuth outside [0, 360).")

    print("\nNUMERIC VALIDATION")
    print("[OK] Solar and Earth elevations are within valid bounds.")
    print("[OK] Solar and Earth azimuths are within [0, 360).")
    print(
        f"Solar elevation range: {solar_elev.min():.4f}° "
        f"to {solar_elev.max():.4f}°"
    )

    # Recalculate terrain visibility using the implemented model rule.
    stored_visibility = np.asarray([
        parse_bool(row["terrain_visible"])
        for row in mission
    ])

    effective_horizon = np.maximum(0.0, terrain_horizon)
    recalculated_visibility = solar_elev > effective_horizon

    mismatches = int(np.sum(
        stored_visibility != recalculated_visibility
    ))

    if mismatches:
        raise ValueError(
            f"{mismatches} terrain visibility classification mismatches."
        )

    print("\nTERRAIN VISIBILITY")
    print("[OK] Zero terrain classification mismatches.")

    # Earth visibility category validation.
    earth_visibility_col = find_column(
        mission_cols, ["earth_visibility"]
    )

    categories = {
        str(row[earth_visibility_col]).strip().lower()
        for row in mission
    }

    allowed_categories = {
        "fully_visible",
        "partially_visible",
        "not_visible",
    }

    if not categories.issubset(allowed_categories):
        raise ValueError(
            f"Unexpected Earth visibility categories: "
            f"{categories - allowed_categories}"
        )

    print("[OK] Earth visibility categories are valid.")

    # Horizon coverage validation.
    if len(horizon) != EXPECTED_HORIZON_DIRECTIONS:
        raise ValueError(
            f"Expected {EXPECTED_HORIZON_DIRECTIONS} horizon directions; "
            f"found {len(horizon)}."
        )

    coverage_col = find_column(
        horizon_cols, ["coverage_complete"]
    )

    incomplete = sum(
        not parse_bool(row[coverage_col])
        for row in horizon
    )

    if incomplete:
        raise ValueError(
            f"{incomplete} horizon directions have incomplete coverage."
        )

    print("\nTERRAIN HORIZON")
    print(f"[OK] {EXPECTED_HORIZON_DIRECTIONS} directions.")
    print("[OK] All directions report complete coverage.")

    # Summary.
    solar_count = int(stored_visibility.sum())
    earth_count = sum(
        str(row[earth_visibility_col]).strip().lower()
        in ("fully_visible", "partially_visible")
        for row in mission
    )

    print("\nMISSION SUMMARY")
    print(f"Samples: {len(mission)}")
    print(
        f"Solar terrain-visible: {solar_count}/{len(mission)} "
        f"({solar_count / len(mission) * 100:.2f}%)"
    )
    print(
        f"Earth at least partially visible: {earth_count}/{len(mission)} "
        f"({earth_count / len(mission) * 100:.2f}%)"
    )

    print(f"\n[PASS] {site_name} consistency validation passed.")


def main():
    print("LUNA-RESOLVE TWO-SITE DATA VALIDATION")
    print("=" * 62)

    for site_name, config in SITES.items():
        validate_site(site_name, config)

    print("\n" + "=" * 62)
    print("TWO-SITE VALIDATION COMPLETE")
    print("=" * 62)
    print("All implemented consistency checks passed.")
    print("This does not establish independent scientific accuracy.")


if __name__ == "__main__":
    main()
