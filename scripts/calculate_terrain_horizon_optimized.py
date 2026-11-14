
import math
import csv
import os

import numpy as np
import rasterio
from scipy.ndimage import map_coordinates
from rasterio.crs import CRS
from rasterio.warp import transform
from pyproj import Geod
from scipy.optimize import minimize_scalar

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

LATITUDE_DEG = -85.4381
LONGITUDE_DEG = 37.36667

MOON_RADIUS_M = 1_737_400.0

MAX_DISTANCE_M = 9_975.0
RADIAL_STEP_M = 2.5
AZIMUTH_STEP_DEG = 0.5

OUTPUT = "data/processed/nobile_rim_1_horizon_optimized_experimental.csv"

# Spherical lunar geodesic
MOON_GEOD = Geod(a=MOON_RADIUS_M, b=MOON_RADIUS_M)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def bilinear_sample(data, rows, cols):
    """Interpolate elevations at fractional raster indices."""
    return map_coordinates(
        data,
        [rows, cols],
        order=1,
        mode="nearest"
    )

def evaluate_horizon_at_distance(
    azimuth_deg,
    distance_m,
    terrain,
    dem,
    geographic_crs,
    observer_elevation
):
    """
    Evaluate the geometric horizon elevation angle at one
    distance along a spherical lunar geodesic.
    """

    if distance_m <= 0:
        raise ValueError("Distance must be greater than zero.")

    # Calculate the geographic position along the ray.
    sample_lon, sample_lat, _ = MOON_GEOD.fwd(
        LONGITUDE_DEG,
        LATITUDE_DEG,
        azimuth_deg,
        distance_m
    )

    # Transform the position into the DEM projection.
    sample_xs, sample_ys = transform(
        geographic_crs,
        dem.crs,
        [sample_lon],
        [sample_lat]
    )

    # Convert to fractional pixel-centre coordinates.
    sample_col = (
        (sample_xs[0] - dem.transform.c)
        / dem.transform.a - 0.5
    )

    sample_row = (
        (sample_ys[0] - dem.transform.f)
        / dem.transform.e - 0.5
    )

    # Reject positions outside the DEM pixel-centre extent.
    if not (
        0 <= sample_row <= dem.height - 1
        and 0 <= sample_col <= dem.width - 1
    ):
        return None

    elevation = float(
        bilinear_sample(
            terrain,
            np.array([sample_row]),
            np.array([sample_col])
        )[0]
    )

    if not np.isfinite(elevation):
        return None

    # Calculate the spherical obstruction elevation angle.
    terrain_radius = MOON_RADIUS_M + elevation
    observer_radius = MOON_RADIUS_M + observer_elevation
    central_angle = distance_m / MOON_RADIUS_M

    vertical = (
        terrain_radius * math.cos(central_angle)
        - observer_radius
    )

    horizontal = (
        terrain_radius * math.sin(central_angle)
    )

    horizon_angle = math.degrees(
        math.atan2(vertical, horizontal)
    )

    return horizon_angle, elevation


# --------------------------------------------------
# LOAD TERRAIN AND DEFINE OBSERVER
# --------------------------------------------------

with rasterio.open(RASTER) as dem:

    terrain = dem.read(1)

    geographic_crs = CRS.from_proj4(
        "+proj=longlat +R=1737400 +no_defs"
    )

    # Project observer into raster coordinates.
    xs, ys = transform(
        geographic_crs,
        dem.crs,
        [LONGITUDE_DEG],
        [LATITUDE_DEG]
    )

    observer_x = xs[0]
    observer_y = ys[0]

    # Fractional pixel-centre coordinates.
    observer_col = (
        (observer_x - dem.transform.c) / dem.transform.a
        - 0.5
    )

    observer_row = (
        (observer_y - dem.transform.f) / dem.transform.e
        - 0.5
    )

    if not (
        0 <= observer_row <= dem.height - 1
        and 0 <= observer_col <= dem.width - 1
    ):
        raise ValueError("Observer lies outside valid raster pixel centres.")

    observer_elevation = float(
        bilinear_sample(
            terrain,
            np.array([observer_row]),
            np.array([observer_col])
        )[0]
    )

    observer_radius = MOON_RADIUS_M + observer_elevation

    # --------------------------------------------------
    # GEODESIC RAY CONFIGURATION
    # --------------------------------------------------

    azimuths = np.arange(
        0.0, 360.0, AZIMUTH_STEP_DEG
    )

    distances = np.arange(
        RADIAL_STEP_M,
        MAX_DISTANCE_M + RADIAL_STEP_M,
        RADIAL_STEP_M
    )

    results = []

    # --------------------------------------------------
    # HORIZON CALCULATION
    # --------------------------------------------------

    for azimuth in azimuths:

        # Generate locations along a spherical geodesic.
        # Azimuth is clockwise from geographic north.
        sample_lons, sample_lats, back_azimuths = MOON_GEOD.fwd(
            np.full(len(distances), LONGITUDE_DEG),
            np.full(len(distances), LATITUDE_DEG),
            np.full(len(distances), azimuth),
            distances
        )

        # Project geodesic locations into LOLA raster CRS.
        sample_xs, sample_ys = transform(
            geographic_crs,
            dem.crs,
            sample_lons.tolist(),
            sample_lats.tolist()
        )

        sample_xs = np.asarray(sample_xs)
        sample_ys = np.asarray(sample_ys)

        # Convert projected coordinates into fractional
        # raster pixel-centre indices.
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
            len(distances), np.nan
        )

        if np.any(inside):
            sample_elevations[inside] = bilinear_sample(
                terrain,
                sample_rows[inside],
                sample_cols[inside]
            )

        valid = np.isfinite(sample_elevations)

        valid_distances = distances[valid]
        valid_elevations = sample_elevations[valid]

        if len(valid_distances) == 0:
            results.append({
                "azimuth_deg": float(azimuth),
                "horizon_elevation_deg": np.nan,
                "obstruction_distance_m": np.nan,
                "obstruction_elevation_m": np.nan,
                "max_valid_distance_m": 0.0,
                "valid_sample_count": 0,
                "coverage_complete": False
            })
            continue

        # --------------------------------------------------
        # SPHERICAL OBSTRUCTION ANGLES
        # --------------------------------------------------

        terrain_radii = MOON_RADIUS_M + valid_elevations

        central_angles = valid_distances / MOON_RADIUS_M

        vertical = (
            terrain_radii * np.cos(central_angles)
            - observer_radius
        )

        horizontal = (
            terrain_radii * np.sin(central_angles)
        )

        elevation_angles = np.degrees(
            np.arctan2(vertical, horizontal)
        )

        # --------------------------------------------------
        # REFINE LOCAL HORIZON MAXIMA
        # --------------------------------------------------

        # Start with the best directly sampled point.
        best_index = int(np.argmax(elevation_angles))

        best_angle = float(elevation_angles[best_index])
        best_distance = float(valid_distances[best_index])
        best_elevation = float(valid_elevations[best_index])


        # Identify sampled local maxima.
        local_maxima = []

        # Include the first radial sample as a possible boundary maximum.
        if elevation_angles[0] >= elevation_angles[1]:
            local_maxima.append(0)

        # Interior local maxima.
        for i in range(1, len(elevation_angles) - 1):
            if elevation_angles[i] >= elevation_angles[i - 1] and elevation_angles[i] >= elevation_angles[i + 1]:
                local_maxima.append(i)

        # Refine each local maximum within its neighbouring
        # radial sample interval.
        for i in local_maxima:

            if i == 0:
                lower_distance = valid_distances[0]
                upper_distance = valid_distances[1]
            else:
                lower_distance = valid_distances[i - 1]
                upper_distance = valid_distances[i + 1]


            def objective(distance):
                result = evaluate_horizon_at_distance(
                    azimuth_deg=float(azimuth),
                    distance_m=float(distance),
                    terrain=terrain,
                    dem=dem,
                    geographic_crs=geographic_crs,
                    observer_elevation=observer_elevation
                )

                if result is None:
                    return float("inf")

                return -result[0]

            optimization = minimize_scalar(
                objective,
                bounds=(lower_distance, upper_distance),
                method="bounded",
                options={"xatol": 0.01}
            )

            if optimization.success and np.isfinite(optimization.fun):

                refined_distance = float(optimization.x)

                refined_result = evaluate_horizon_at_distance(
                    azimuth_deg=float(azimuth),
                    distance_m=refined_distance,
                    terrain=terrain,
                    dem=dem,
                    geographic_crs=geographic_crs,
                    observer_elevation=observer_elevation
                )

                if refined_result is not None:
                    refined_angle, refined_elevation = refined_result

                    if refined_angle > best_angle:
                        best_angle = float(refined_angle)
                        best_distance = refined_distance
                        best_elevation = float(refined_elevation)

        max_valid_distance = float(valid_distances[-1])


        coverage_complete = (
            max_valid_distance >=
            MAX_DISTANCE_M - RADIAL_STEP_M * 0.5
        )

        results.append({
            "azimuth_deg": float(azimuth),
            "horizon_elevation_deg": best_angle,
            "obstruction_distance_m": best_distance,
            "obstruction_elevation_m": best_elevation,
            "max_valid_distance_m": max_valid_distance,
            "valid_sample_count": int(len(valid_distances)),
            "coverage_complete": coverage_complete
        })


# --------------------------------------------------
# SAVE RESULTS
# --------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT),
    exist_ok=True
)

fieldnames = [
    "azimuth_deg",
    "horizon_elevation_deg",
    "obstruction_distance_m",
    "obstruction_elevation_m",
    "max_valid_distance_m",
    "valid_sample_count",
    "coverage_complete"
]

with open(OUTPUT, "w", newline="") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(results)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

angles = np.array([
    item["horizon_elevation_deg"]
    for item in results
])

valid_angles = angles[np.isfinite(angles)]

coverage = np.array([
    item["coverage_complete"]
    for item in results
])

max_distances = np.array([
    item["max_valid_distance_m"]
    for item in results
])

print("LUNA-RESOLVE GEODESIC TERRAIN HORIZON")
print("-" * 50)
print(f"Observer elevation: {observer_elevation:.4f} m")
print(f"Azimuth directions: {len(azimuths)}")
print(f"Radial interval: {RADIAL_STEP_M:.1f} m")
print(f"Requested maximum distance: {MAX_DISTANCE_M:.0f} m")
print(f"Valid directions: {len(valid_angles)}")
print(f"Directions with full coverage: {np.sum(coverage)}")
print(f"Directions without full coverage: {np.sum(~coverage)}")
print(f"Minimum maximum-distance coverage: {np.min(max_distances):.1f} m")

if len(valid_angles) == 0:
    raise RuntimeError("No valid horizon directions were calculated.")

print("\nHORIZON STATISTICS")
print(f"Minimum: {np.min(valid_angles):.4f} deg")
print(f"Maximum: {np.max(valid_angles):.4f} deg")
print(f"Mean: {np.mean(valid_angles):.4f} deg")

print("\nSaved:", OUTPUT)
