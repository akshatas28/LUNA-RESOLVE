
import csv
import json
from pathlib import Path

import numpy as np
import spiceypy as spice


ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "data" / "raw" / "spice"
METADATA_FILE = ROOT / "data" / "metadata" / "candidate_sites.json"

KERNELS = [
    "naif0012.tls",
    "de440s.bsp",
    "moon_pa_de421_1900-2050.bpc",
    "moon_080317.tf",
]

MOON_RADIUS_M = 1_737_400.0


def local_basis(latitude_deg, longitude_deg):
    """Local east, north and up unit vectors in MOON_ME."""
    lat = np.radians(latitude_deg)
    lon = np.radians(longitude_deg)

    up = np.array([
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat),
    ])

    east = np.array([-np.sin(lon), np.cos(lon), 0.0])
    north = np.cross(up, east)

    return east, north, up


def calculate_solar_position(et, latitude_deg, longitude_deg):
    """Calculate geometric solar elevation and azimuth."""
    sun_state, _ = spice.spkezr(
        "SUN", et, "MOON_ME", "NONE", "MOON"
    )
    sun_vector = np.asarray(sun_state[:3]) * 1000.0

    lat = np.radians(latitude_deg)
    lon = np.radians(longitude_deg)

    site_vector = MOON_RADIUS_M * np.array([
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat),
    ])

    sun_from_site = sun_vector - site_vector
    sun_direction = sun_from_site / np.linalg.norm(sun_from_site)

    east, north, up = local_basis(latitude_deg, longitude_deg)

    east_component = np.dot(sun_direction, east)
    north_component = np.dot(sun_direction, north)
    up_component = np.dot(sun_direction, up)

    elevation_deg = np.degrees(
        np.arctan2(
            up_component,
            np.hypot(east_component, north_component),
        )
    )

    azimuth_deg = np.degrees(
        np.arctan2(east_component, north_component)
    ) % 360.0

    return elevation_deg, azimuth_deg


def main():
    with open(METADATA_FILE, encoding="utf-8") as file:
        metadata = json.load(file)

    site = metadata["sites"][metadata["active_site"]]

    latitude = site["latitude_deg"]
    longitude = site["longitude_deg"]

    site_slug = site["site_name"].lower().replace(" ", "_")
    output_file = (
        ROOT / "data" / "processed"
        / f"{site_slug}_solar_illumination.csv"
    )

    # Initial demonstration window: one lunar day of sampling.
    start_utc = "2026-11-14T00:00:00"
    end_utc = "2026-12-14T00:00:00"
    step_minutes = 30

    spice.kclear()

    try:
        for kernel in KERNELS:
            spice.furnsh(str(KERNEL_DIR / kernel))

        start_et = spice.str2et(start_utc)
        end_et = spice.str2et(end_utc)
        step_seconds = step_minutes * 60

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "utc",
                "et_seconds",
                "solar_elevation_deg",
                "solar_azimuth_deg",
                "geometrically_illuminated",
            ])

            sample_count = 0

            for et in np.arange(start_et, end_et + 0.5, step_seconds):
                utc = spice.et2utc(et, "ISOC", 3)
                elevation, azimuth = calculate_solar_position(
                    et, latitude, longitude
                )

                writer.writerow([
                    utc,
                    f"{et:.6f}",
                    f"{elevation:.6f}",
                    f"{azimuth:.6f}",
                    elevation > 0.0,
                ])

                sample_count += 1

        print(f"Site: {site['site_name']}")
        print(f"Samples written: {sample_count}")
        print(f"Time step: {step_minutes} minutes")
        print(f"Output: {output_file}")
        print("Solar illumination calculation: COMPLETE")

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()
