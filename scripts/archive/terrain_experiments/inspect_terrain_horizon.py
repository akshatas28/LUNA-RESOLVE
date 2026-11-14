
import csv
import math

PATH = (
    "data/processed/"
    "nobile_rim_1_terrain_horizon_bilinear.csv"
)

with open(PATH, newline="") as file:
    rows = list(csv.DictReader(file))

rows = [
    row for row in rows
    if row["horizon_elevation_deg"]
    and math.isfinite(
        float(row["horizon_elevation_deg"])
    )
]

highest = sorted(
    rows,
    key=lambda r: float(r["horizon_elevation_deg"]),
    reverse=True
)

lowest = sorted(
    rows,
    key=lambda r: float(r["horizon_elevation_deg"])
)

print("HIGHEST 10 HORIZON DIRECTIONS")
print("-" * 75)

for row in highest[:10]:
    print(
        f"Azimuth: {float(row['azimuth_deg']):6.1f}° | "
        f"Horizon: {float(row['horizon_elevation_deg']):8.4f}° | "
        f"Distance: {float(row['obstruction_distance_m']):8.1f} m | "
        f"Terrain: {float(row['obstruction_elevation_m']):8.2f} m"
    )

print("\nLOWEST 10 HORIZON DIRECTIONS")
print("-" * 75)

for row in lowest[:10]:
    print(
        f"Azimuth: {float(row['azimuth_deg']):6.1f}° | "
        f"Horizon: {float(row['horizon_elevation_deg']):8.4f}° | "
        f"Distance: {float(row['obstruction_distance_m']):8.1f} m | "
        f"Terrain: {float(row['obstruction_elevation_m']):8.2f} m"
    )
