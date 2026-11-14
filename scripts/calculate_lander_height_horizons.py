
import csv
import os
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import map_coordinates
from rasterio.crs import CRS
from rasterio.warp import transform
from pyproj import Geod


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

RASTER = ROOT / "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

MISSION_FILE = (
    ROOT / "data/processed/nobile_rim_1_mission_environment.csv"
)

BASELINE_HORIZON_FILE = (
    ROOT / "data/processed/"
    "nobile_rim_1_horizon_fine_0p5deg_2p5m_9975m.csv"
)

OUTPUT_DIR = ROOT / "data/processed"

LATITUDE_DEG = -85.4381
LONGITUDE_DEG = 37.36667

MOON_RADIUS_M = 1_737_400.0

MAX_DISTANCE_M = 9_975.0
RADIAL_STEP_M = 2.5
AZIMUTH_STEP_DEG = 0.5

LANDER_HEIGHTS_M = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]

MOON_GEOD = Geod(a=MOON_RADIUS_M, b=MOON_RADIUS_M)

GEOGRAPHIC_CRS = CRS.from_proj4(
    "+proj=longlat +R=1737400 +no_defs"
)


# ============================================================
# HELPERS
# ============================================================

def bilinear_sample(data, rows, cols):
    return map_coordinates(
        data,
        [rows, cols],
        order=1,
        mode="nearest",
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


def observer_limb_angle(observer_ground_radius, observer_height):
    """
    Geometric angular depression of the lunar limb
    relative to the local terrain tangent plane.
    """
    observer_radius = observer_ground_radius + observer_height

    return -np.degrees(
        np.arccos(observer_ground_radius / observer_radius)
    )


def height_label(height):
    return str(height).replace(".", "p")


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# LOAD MISSION DATA
# ============================================================

with MISSION_FILE.open(
    "r", newline="", encoding="utf-8-sig"
) as file:
    mission_reader = csv.DictReader(file)
    mission_rows = list(mission_reader)

if not mission_rows:
    raise RuntimeError("Mission dataset is empty.")

mission_times = [row["utc"] for row in mission_rows]

if len(set(mission_times)) != len(mission_times):
    raise ValueError("Duplicate timestamps in mission dataset.")

solar_elevations = np.asarray([
    float(row["solar_elevation_deg"])
    for row in mission_rows
])

solar_azimuths = np.asarray([
    float(row["solar_azimuth_deg"])
    for row in mission_rows
])


# ============================================================
# LOAD BASELINE HORIZON
# ============================================================

with BASELINE_HORIZON_FILE.open(
    "r", newline="", encoding="utf-8-sig"
) as file:
    baseline_rows = list(csv.DictReader(file))

if not baseline_rows:
    raise RuntimeError("Baseline horizon dataset is empty.")

baseline_azimuths = np.asarray([
    float(row["azimuth_deg"])
    for row in baseline_rows
])

baseline_angles = np.asarray([
    float(row["horizon_elevation_deg"])
    for row in baseline_rows
])


# ============================================================
# TERRAIN HORIZON CALCULATION
# ============================================================

azimuths = np.arange(
    0.0,
    360.0,
    AZIMUTH_STEP_DEG,
)

distances = np.arange(
    RADIAL_STEP_M,
    MAX_DISTANCE_M + RADIAL_STEP_M,
    RADIAL_STEP_M,
)

# Results indexed by observer height.
horizon_results = {
    height: []
    for height in LANDER_HEIGHTS_M
}

print("LUNA-RESOLVE HEIGHT-AWARE TERRAIN HORIZON")
print("=" * 65)

print(f"DEM: {RASTER.name}")
print(f"Observer: {LATITUDE_DEG}, {LONGITUDE_DEG}")
print(f"Radial interval: {RADIAL_STEP_M} m")
print(f"Azimuth interval: {AZIMUTH_STEP_DEG} degrees")
print(f"Maximum range: {MAX_DISTANCE_M} m")
print(f"Observer heights: {LANDER_HEIGHTS_M}")

with rasterio.open(RASTER) as dem:

    terrain = dem.read(1)

    # Project observer into the DEM.
    observer_xs, observer_ys = transform(
        GEOGRAPHIC_CRS,
        dem.crs,
        [LONGITUDE_DEG],
        [LATITUDE_DEG],
    )

    observer_x = observer_xs[0]
    observer_y = observer_ys[0]

    observer_col = (
        (observer_x - dem.transform.c)
        / dem.transform.a - 0.5
    )

    observer_row = (
        (observer_y - dem.transform.f)
        / dem.transform.e - 0.5
    )

    if not (
        0 <= observer_row <= dem.height - 1
        and 0 <= observer_col <= dem.width - 1
    ):
        raise ValueError(
            "Observer lies outside valid DEM pixel centres."
        )

    observer_elevation = float(
        bilinear_sample(
            terrain,
            np.array([observer_row]),
            np.array([observer_col]),
        )[0]
    )

    print(f"\nObserver ground elevation: {observer_elevation:.4f} m")

    # Calculate all observer radii and limb angles.
    observer_radii = {
        height: MOON_RADIUS_M + observer_elevation + height
        for height in LANDER_HEIGHTS_M
    }

    ground_radius = MOON_RADIUS_M + observer_elevation

    limb_angles = {
        height: observer_limb_angle(ground_radius, height)
        for height in LANDER_HEIGHTS_M
    }

    # --------------------------------------------------------
    # PROCESS EACH AZIMUTH
    # --------------------------------------------------------

    for index, azimuth in enumerate(azimuths):

        if index % 60 == 0:
            print(
                f"Processing azimuth {azimuth:.1f} degrees "
                f"({index + 1}/{len(azimuths)})"
            )

        # Generate the same spherical geodesic samples
        # as the established baseline implementation.
        sample_lons, sample_lats, _ = MOON_GEOD.fwd(
            np.full(len(distances), LONGITUDE_DEG),
            np.full(len(distances), LATITUDE_DEG),
            np.full(len(distances), azimuth),
            distances,
        )

        sample_xs, sample_ys = transform(
            GEOGRAPHIC_CRS,
            dem.crs,
            sample_lons.tolist(),
            sample_lats.tolist(),
        )

        sample_xs = np.asarray(sample_xs)
        sample_ys = np.asarray(sample_ys)

        sample_cols = (
            (sample_xs - dem.transform.c)
            / dem.transform.a - 0.5
        )

        sample_rows = (
            (sample_ys - dem.transform.f)
            / dem.transform.e - 0.5
        )

        inside = (
            (sample_rows >= 0)
            & (sample_rows <= dem.height - 1)
            & (sample_cols >= 0)
            & (sample_cols <= dem.width - 1)
        )

        sample_elevations = np.full(
            len(distances),
            np.nan,
        )

        if np.any(inside):
            sample_elevations[inside] = bilinear_sample(
                terrain,
                sample_rows[inside],
                sample_cols[inside],
            )

        valid = np.isfinite(sample_elevations)

        valid_distances = distances[valid]
        valid_elevations = sample_elevations[valid]

        if len(valid_distances) == 0:
            raise RuntimeError(
                f"No valid terrain samples at azimuth {azimuth}."
            )

        # Calculate lunar spherical geometry once per azimuth.
        terrain_radii = MOON_RADIUS_M + valid_elevations
        central_angles = valid_distances / MOON_RADIUS_M

        terrain_vertical = (
            terrain_radii * np.cos(central_angles)
        )

        terrain_horizontal = (
            terrain_radii * np.sin(central_angles)
        )

        # ----------------------------------------------------
        # RECALCULATE THE FULL TERRAIN PROFILE PER HEIGHT
        # ----------------------------------------------------

        for height in LANDER_HEIGHTS_M:

            observer_radius = observer_radii[height]

            vertical = terrain_vertical - observer_radius

            horizontal = terrain_horizontal

            elevation_angles = np.degrees(
                np.arctan2(vertical, horizontal)
            )

            # Select the highest obstruction from ALL sampled
            # terrain points for this observer height.
            max_index = int(np.argmax(elevation_angles))

            raw_horizon = float(
                elevation_angles[max_index]
            )

            # Apply the geometric lunar limb at every height.
            # At zero height, the limb angle is 0 degrees.
            effective_horizon = max(
                raw_horizon,
                limb_angles[height],
            )

            max_valid_distance = float(valid_distances[-1])

            coverage_complete = (
                max_valid_distance
                >= MAX_DISTANCE_M - RADIAL_STEP_M * 0.5
            )

            horizon_results[height].append({
                "azimuth_deg": float(azimuth),
                "horizon_elevation_deg": effective_horizon,
                "raw_max_terrain_angle_deg": raw_horizon,
                "geometric_limb_angle_deg": limb_angles[height],
                "obstruction_distance_m": float(
                    valid_distances[max_index]
                ),
                "obstruction_elevation_m": float(
                    valid_elevations[max_index]
                ),
                "max_valid_distance_m": max_valid_distance,
                "valid_sample_count": int(len(valid_distances)),
                "coverage_complete": coverage_complete,
            })


# ============================================================
# ZERO-HEIGHT BASELINE COMPARISON
# ============================================================

zero_results = horizon_results[0.0]

zero_angles = np.asarray([
    row["raw_max_terrain_angle_deg"]
    for row in zero_results
])

baseline_order = np.argsort(baseline_azimuths)

baseline_sorted_azimuths = baseline_azimuths[baseline_order]
baseline_sorted_angles = baseline_angles[baseline_order]

if len(zero_angles) != len(baseline_angles):
    raise RuntimeError(
        "Zero-height horizon direction count differs from baseline."
    )

if not np.allclose(
    np.asarray([row["azimuth_deg"] for row in zero_results]),
    baseline_sorted_azimuths,
    atol=1e-9,
):
    raise RuntimeError(
        "Zero-height azimuth directions do not match baseline."
    )

baseline_difference = zero_angles - baseline_sorted_angles

baseline_max_difference = float(
    np.max(np.abs(baseline_difference))
)

print("\nZERO-HEIGHT BASELINE COMPARISON")
print(f"Maximum absolute horizon difference: {baseline_max_difference:.10f} deg")

if baseline_max_difference > 1e-6:
    raise RuntimeError(
        "Zero-height result does not reproduce the existing baseline."
    )

print("[OK] Zero-height terrain horizon reproduces the baseline.")


# ============================================================
# WRITE HORIZON DATASETS AND MISSION SCENARIOS
# ============================================================

summary_rows = []
scenario_rows = []

print("\nHEIGHT SCENARIO RESULTS")
print("-" * 65)

for height in LANDER_HEIGHTS_M:

    rows = horizon_results[height]

    label = height_label(height)

    horizon_output = (
        OUTPUT_DIR /
        f"nobile_rim_1_horizon_height_{label}m.csv"
    )

    fields = list(rows[0].keys())

    write_csv(
        horizon_output,
        rows,
        fields,
    )

    horizon_angles = np.asarray([
        row["horizon_elevation_deg"]
        for row in rows
    ])

    horizon_az = np.asarray([
        row["azimuth_deg"]
        for row in rows
    ])

    # The ground-level model uses zero degrees as its
    # effective horizon floor. Elevated observers instead
    # use their geometric lunar limb.
    effective_angles = horizon_angles

    solar_horizons = circular_interpolate(
        horizon_az,
        effective_angles,
        solar_azimuths,
    )

    visible = solar_elevations > solar_horizons

    visible_count = int(np.sum(visible))
    total_count = len(mission_rows)

    percentage = visible_count / total_count * 100.0

    summary_rows.append({
        "lander_height_m": height,
        "observer_ground_elevation_m": observer_elevation,
        "observer_absolute_elevation_m": observer_elevation + height,
        "geometric_limb_angle_deg": limb_angles[height],
        "visible_samples": visible_count,
        "total_samples": total_count,
        "visibility_percent": percentage,
        "horizon_file": horizon_output.name,
    })

    for index, mission_row in enumerate(mission_rows):
        scenario_rows.append({
            "utc": mission_row["utc"],
            "lander_height_m": height,
            "solar_elevation_deg": solar_elevations[index],
            "solar_azimuth_deg": solar_azimuths[index],
            "terrain_horizon_deg": solar_horizons[index],
            "solar_visible": bool(visible[index]),
        })

    print(
        f"{height:4.1f} m: "
        f"{visible_count}/{total_count} "
        f"({percentage:.2f}%)"
    )

    print(f"     Horizon file: {horizon_output.name}")


# ============================================================
# SAVE COMBINED OUTPUTS
# ============================================================

summary_output = (
    OUTPUT_DIR /
    "nobile_rim_1_lander_height_summary.csv"
)

scenario_output = (
    OUTPUT_DIR /
    "nobile_rim_1_lander_height_scenarios.csv"
)

write_csv(
    summary_output,
    summary_rows,
    list(summary_rows[0].keys()),
)

write_csv(
    scenario_output,
    scenario_rows,
    list(scenario_rows[0].keys()),
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 65)
print("HEIGHT-AWARE TERRAIN ANALYSIS COMPLETE")
print("=" * 65)

print(f"Observer ground elevation: {observer_elevation:.4f} m")
print(f"Azimuth directions: {len(azimuths)}")
print(f"Radial samples per direction: {len(distances)}")
print(f"Observer heights: {len(LANDER_HEIGHTS_M)}")

print("\nOUTPUT FILES")
print(f"Summary: {summary_output}")
print(f"Mission scenarios: {scenario_output}")

print("\nSCIENTIFIC SCOPE")
print("- Full sampled terrain profile used for each height.")
print("- 5 m DEM resolution; 2.5 m bilinear sampling.")
print("- 9975 m maximum terrain coverage.")
print("- Surface-level baseline checked against existing output.")
print("- Geometric visibility only; no RF or power-system modelling.")
print("- Results remain subject to coordinate/frame verification.")
