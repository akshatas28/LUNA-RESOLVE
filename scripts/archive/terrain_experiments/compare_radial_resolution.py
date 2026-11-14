
import csv
import math
import numpy as np

BASELINE = (
    "data/processed/"
    "nobile_rim_1_horizon_baseline_1deg_5m_9975m.csv"
)

FINE = (
    "data/processed/"
    "nobile_rim_1_horizon_1deg_2p5m_9975m.csv"
)


def load_csv(path):
    with open(path, newline="") as f:
        return {
            round(float(row["azimuth_deg"]), 6): row
            for row in csv.DictReader(f)
        }


baseline = load_csv(BASELINE)
fine = load_csv(FINE)

common_azimuths = sorted(
    set(baseline).intersection(fine)
)

if len(common_azimuths) != 360:
    raise ValueError(
        f"Expected 360 common azimuths, got {len(common_azimuths)}"
    )

coarse_angles = np.array([
    float(baseline[a]["horizon_elevation_deg"])
    for a in common_azimuths
])

fine_angles = np.array([
    float(fine[a]["horizon_elevation_deg"])
    for a in common_azimuths
])

differences = fine_angles - coarse_angles
absolute = np.abs(differences)

print("RADIAL RESOLUTION COMPARISON")
print("-" * 55)
print("Common azimuth directions:", len(common_azimuths))

print("\n2.5M RADIAL MINUS 5M RADIAL")
print(f"Mean signed difference: {np.mean(differences):.6f} deg")
print(f"Mean absolute difference: {np.mean(absolute):.6f} deg")
print(f"RMSE: {math.sqrt(np.mean(differences ** 2)):.6f} deg")
print(f"Maximum absolute difference: {np.max(absolute):.6f} deg")
print(f"95th percentile absolute difference: {np.percentile(absolute, 95):.6f} deg")

print("\nEXTREMA AT COMMON AZIMUTHS")
print(
    f"Baseline minimum: {np.min(coarse_angles):.6f} deg "
    f"at {common_azimuths[int(np.argmin(coarse_angles))]:.1f} deg"
)
print(
    f"Fine minimum: {np.min(fine_angles):.6f} deg "
    f"at {common_azimuths[int(np.argmin(fine_angles))]:.1f} deg"
)
print(
    f"Baseline maximum: {np.max(coarse_angles):.6f} deg "
    f"at {common_azimuths[int(np.argmax(coarse_angles))]:.1f} deg"
)
print(
    f"Fine maximum: {np.max(fine_angles):.6f} deg "
    f"at {common_azimuths[int(np.argmax(fine_angles))]:.1f} deg"
)

print("\nLARGEST DIFFERENCES AND OBSTRUCTION LOCATIONS")

indices = np.argsort(absolute)[-10:][::-1]

for i in indices:
    az = common_azimuths[i]

    coarse = baseline[az]
    refined = fine[az]

    print(f"\nAzimuth: {az:.1f} deg")
    print(
        f"  Baseline: {float(coarse['horizon_elevation_deg']):.6f} deg"
        f" | Distance: {float(coarse['obstruction_distance_m']):.1f} m"
        f" | Terrain: {float(coarse['obstruction_elevation_m']):.3f} m"
    )
    print(
        f"  Fine:     {float(refined['horizon_elevation_deg']):.6f} deg"
        f" | Distance: {float(refined['obstruction_distance_m']):.1f} m"
        f" | Terrain: {float(refined['obstruction_elevation_m']):.3f} m"
    )
    print(
        f"  Difference: {differences[i]:+.6f} deg"
    )