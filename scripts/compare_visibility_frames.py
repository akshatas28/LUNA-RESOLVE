
import csv
import json
from pathlib import Path

import numpy as np
import spiceypy as spice

ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "data" / "raw" / "spice"
METADATA_FILE = ROOT / "data" / "metadata" / "candidate_sites.json"

COMMON = [
    "naif0012.tls",
    "de440s.bsp",
]

CONFIGS = {
    "DE421": [
        "moon_pa_de421_1900-2050.bpc",
        "moon_080317.tf",
    ],
    "DE440": [
        "moon_pa_de440_200625.bpc",
        "moon_de440_250416.tf",
    ],
}

START_UTC = "2026-11-14T00:00:00"
END_UTC = "2026-12-14T00:00:00"
STEP_SECONDS = 1800
MOON_RADIUS_M = 1_737_400.0


def local_basis(lat_deg, lon_deg):
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)

    up = np.array([
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat),
    ])

    east = np.array([
        -np.sin(lon),
        np.cos(lon),
        0.0,
    ])

    north = np.cross(up, east)

    return east, north, up


def calculate_angles(et, body, lat, lon, basis):
    state, _ = spice.spkezr(
        body, et, "MOON_ME", "NONE", "MOON"
    )

    body_vector = np.asarray(state[:3]) * 1000.0

    site_vector = MOON_RADIUS_M * np.array([
        np.cos(np.radians(lat)) * np.cos(np.radians(lon)),
        np.cos(np.radians(lat)) * np.sin(np.radians(lon)),
        np.sin(np.radians(lat)),
    ])

    direction = body_vector - site_vector
    direction /= np.linalg.norm(direction)

    east, north, up = basis

    e = np.dot(direction, east)
    n = np.dot(direction, north)
    u = np.dot(direction, up)

    elevation = np.degrees(
        np.arctan2(u, np.hypot(e, n))
    )

    azimuth = np.degrees(np.arctan2(e, n)) % 360.0

    return elevation, azimuth


def calculate_configuration(name, epochs, lat, lon):
    spice.kclear()

    for kernel in COMMON + CONFIGS[name]:
        spice.furnsh(str(KERNEL_DIR / kernel))

    basis = local_basis(lat, lon)

    results = {
        "SUN": [],
        "EARTH": [],
    }

    for et in epochs:
        for body in results:
            results[body].append(
                calculate_angles(et, body, lat, lon, basis)
            )

    return {
        body: np.asarray(values)
        for body, values in results.items()
    }


def summarize(label, baseline, comparison):
    elevation_diff = comparison[:, 0] - baseline[:, 0]

    azimuth_diff = (
        (comparison[:, 1] - baseline[:, 1] + 180.0)
        % 360.0
    ) - 180.0

    print(f"\n{label}")
    print("-" * 55)

    for name, values in [
        ("Elevation", elevation_diff),
        ("Azimuth", azimuth_diff),
    ]:
        print(f"{name}:")
        print(f"  Mean absolute difference: {np.mean(np.abs(values)):.9f} deg")
        print(f"  RMSE: {np.sqrt(np.mean(values**2)):.9f} deg")
        print(f"  Maximum absolute difference: {np.max(np.abs(values)):.9f} deg")


def main():
    with open(METADATA_FILE, encoding="utf-8") as file:
        site = json.load(file)

    lat = site["latitude_deg"]
    lon = site["longitude_deg"]

    spice.kclear()

    try:
        for kernel in COMMON:
            spice.furnsh(str(KERNEL_DIR / kernel))

        start_et = spice.str2et(START_UTC)
        end_et = spice.str2et(END_UTC)

        epochs = np.arange(
            start_et,
            end_et + 0.5,
            STEP_SECONDS,
        )

    finally:
        spice.kclear()

    print("30-DAY LUNAR VISIBILITY FRAME COMPARISON")
    print("=" * 60)
    print(f"Site: {site['site_name']}")
    print(f"Latitude: {lat} deg")
    print(f"Longitude: {lon} deg")
    print(f"Observations: {len(epochs)}")

    results = {}

    for name in ("DE421", "DE440"):
        print(f"\nCalculating {name} configuration...")

        results[name] = calculate_configuration(
            name, epochs, lat, lon
        )

    for body in ("SUN", "EARTH"):
        summarize(
            body,
            results["DE440"][body],
            results["DE421"][body],
        )

    print("\n30-day frame comparison: COMPLETE")


if __name__ == "__main__":
    main()
