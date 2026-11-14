
import csv
import json
from pathlib import Path

import numpy as np
import spiceypy as spice


ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "data" / "raw" / "spice"
METADATA_FILE = ROOT / "data" / "metadata" / "candidate_sites.json"

HORIZON_FILE = None
OUTPUT_FILE = None

KERNELS = [
    "naif0012.tls",
    "de440s.bsp",
    "moon_pa_de421_1900-2050.bpc",
    "moon_080317.tf",
]

MOON_RADIUS_M = 1_737_400.0
EARTH_RADIUS_KM = 6_378.137


def local_basis(latitude_deg, longitude_deg):
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


def read_horizon():
    with open(HORIZON_FILE, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise ValueError("Terrain horizon file is empty.")

    if not all(
        row["coverage_complete"].strip().lower() == "true"
        for row in rows
    ):
        raise ValueError("Terrain horizon coverage is incomplete.")

    rows.sort(key=lambda row: float(row["azimuth_deg"]))

    azimuths = np.array([
        float(row["azimuth_deg"]) for row in rows
    ])

    elevations = np.array([
        float(row["horizon_elevation_deg"]) for row in rows
    ])

    if len(np.unique(azimuths)) != len(azimuths):
        raise ValueError("Duplicate horizon azimuths found.")

    return azimuths, elevations


def interpolate_horizon(azimuth, azimuths, elevations):
    extended_azimuths = np.concatenate((
        [azimuths[-1] - 360.0],
        azimuths,
        [azimuths[0] + 360.0],
    ))

    extended_elevations = np.concatenate((
        [elevations[-1]],
        elevations,
        [elevations[0]],
    ))

    return np.interp(
        azimuth,
        extended_azimuths,
        extended_elevations,
    )


def calculate_earth_position(et, latitude, longitude):
    state, _ = spice.spkezr(
        "EARTH", et, "MOON_ME", "NONE", "MOON"
    )

    earth_vector = np.asarray(state[:3]) * 1000.0

    lat = np.radians(latitude)
    lon = np.radians(longitude)

    site_vector = MOON_RADIUS_M * np.array([
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat),
    ])

    earth_from_site = earth_vector - site_vector
    distance_m = np.linalg.norm(earth_from_site)
    direction = earth_from_site / distance_m

    east, north, up = local_basis(latitude, longitude)

    e = np.dot(direction, east)
    n = np.dot(direction, north)
    u = np.dot(direction, up)

    elevation = np.degrees(
        np.arctan2(u, np.hypot(e, n))
    )

    azimuth = np.degrees(np.arctan2(e, n)) % 360.0

    angular_radius = np.degrees(
        np.arcsin((EARTH_RADIUS_KM * 1000.0) / distance_m)
    )

    return elevation, azimuth, distance_m / 1000.0, angular_radius



def main():
    global HORIZON_FILE, OUTPUT_FILE

    with open(METADATA_FILE, encoding="utf-8") as file:
        metadata = json.load(file)

    site = metadata["sites"][metadata["active_site"]]

    latitude = site["latitude_deg"]
    longitude = site["longitude_deg"]

    site_slug = site["site_name"].lower().replace(" ", "_")

    horizon_files = {
        "NOBILE_RIM_1_R06": "nobile_rim_1_horizon_fine_0p5deg_2p5m_9975m.csv",
        "CONNECTING_RIDGE_R01": "connecting_ridge_horizon_fine_0p5deg_2p5m_7975m.csv",
    }

    if site["site_id"] not in horizon_files:
        raise ValueError(f"Unsupported site: {site['site_id']}")

    HORIZON_FILE = (
        ROOT / "data" / "processed" / horizon_files[site["site_id"]]
    )

    OUTPUT_FILE = (
        ROOT / "data" / "processed"
        / f"{site_slug}_earth_visibility.csv"
    )

    azimuths, horizon_elevations = read_horizon()

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

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        counts = {
            "fully_visible": 0,
            "partially_visible": 0,
            "not_visible": 0,
        }

        with open(
            OUTPUT_FILE, "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)

            writer.writerow([
                "utc",
                "earth_azimuth_deg",
                "earth_elevation_deg",
                "earth_distance_km",
                "earth_angular_radius_deg",
                "terrain_horizon_elevation_deg",
                "earth_visibility",
            ])

            for et in np.arange(
                start_et, end_et + 0.5, step_seconds
            ):
                utc = spice.et2utc(et, "ISOC", 3)

                elevation, azimuth, distance, radius = (
                    calculate_earth_position(
                        et, latitude, longitude
                    )
                )

                terrain_horizon = interpolate_horizon(
                    azimuth, azimuths, horizon_elevations
                )

                effective_horizon = max(0.0, terrain_horizon)

                upper_limb = elevation + radius
                lower_limb = elevation - radius

                if lower_limb > effective_horizon:
                    visibility = "fully_visible"
                elif upper_limb > effective_horizon:
                    visibility = "partially_visible"
                else:
                    visibility = "not_visible"

                counts[visibility] += 1

                writer.writerow([
                    utc,
                    f"{azimuth:.6f}",
                    f"{elevation:.6f}",
                    f"{distance:.3f}",
                    f"{radius:.6f}",
                    f"{terrain_horizon:.6f}",
                    visibility,
                ])

        print("Earth visibility calculation: COMPLETE")
        print("Site:", site["site_name"])
        print("Samples:", sum(counts.values()))
        print("Fully visible:", counts["fully_visible"])
        print("Partially visible:", counts["partially_visible"])
        print("Not visible:", counts["not_visible"])
        print("Output:", OUTPUT_FILE)

    finally:
        spice.kclear()



if __name__ == "__main__":
    main()
