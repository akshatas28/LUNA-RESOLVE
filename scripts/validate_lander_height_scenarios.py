
import csv
import math
from pathlib import Path

BASE = Path("data/processed")

HEIGHTS = [0.0, 0.5, 1.0, 2.0, 3.0, 5.0]

SUMMARY_FILE = BASE / "nobile_rim_1_lander_height_summary.csv"
SCENARIO_FILE = BASE / "nobile_rim_1_lander_height_scenarios.csv"
BASELINE_FILE = BASE / "nobile_rim_1_horizon_fine_0p5deg_2p5m_9975m.csv"

# The original fine-resolution horizon file is the reference.
# Adjust this path only if your actual baseline filename differs.
if not BASELINE_FILE.exists():
    candidates = list(BASE.glob("nobile_rim_1_horizon*.csv"))
    candidates = [
        p for p in candidates
        if "height_" not in p.name
        and "summary" not in p.name
        and "scenarios" not in p.name
    ]
    if len(candidates) == 1:
        BASELINE_FILE = candidates[0]
    else:
        raise FileNotFoundError(
            "Could not uniquely identify the original baseline horizon CSV."
        )


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def number(row, field):
    value = float(row[field])
    if not math.isfinite(value):
        raise ValueError(f"Non-finite value in {field}: {value}")
    return value


print("LUNA-RESOLVE HEIGHT SCENARIO VALIDATION")
print("=" * 62)

# ------------------------------------------------------------
# 1. Summary validation
# ------------------------------------------------------------

summary = read_csv(SUMMARY_FILE)

assert len(summary) == len(HEIGHTS), (
    f"Expected {len(HEIGHTS)} height summaries, found {len(summary)}"
)

summary_by_height = {
    number(row, "lander_height_m"): row
    for row in summary
}

assert sorted(summary_by_height) == HEIGHTS

print("[OK] Six observer-height summary records found.")

previous_percent = -math.inf

for height in HEIGHTS:
    row = summary_by_height[height]

    visible = int(row["visible_samples"])
    total = int(row["total_samples"])
    percent = number(row, "visibility_percent")

    assert total == 1441, f"Unexpected sample count at {height} m"
    assert 0 <= visible <= total
    assert abs(percent - visible / total * 100) < 0.011

    assert percent >= previous_percent, (
        f"Visibility decreased at observer height {height} m"
    )

    previous_percent = percent

    print(
        f"[OK] {height:4.1f} m: "
        f"{visible}/{total} samples, {percent:.2f}% visibility"
    )

print("[OK] Visibility percentage is non-decreasing.")

# ------------------------------------------------------------
# 2. Height-specific horizon validation
# ------------------------------------------------------------

horizons = {}

for height in HEIGHTS:
    filename = f"nobile_rim_1_horizon_height_{str(height).replace('.', 'p')}m.csv"
    path = BASE / filename

    rows = read_csv(path)

    assert len(rows) == 720, (
        f"{filename}: expected 720 directions, found {len(rows)}"
    )

    assert all(row["coverage_complete"].lower() == "true" for row in rows), (
        f"Incomplete terrain coverage in {filename}"
    )

    directions = [number(row, "azimuth_deg") for row in rows]

    assert len(set(directions)) == 720
    assert all(0 <= az < 360 for az in directions)

    horizons[height] = {
        number(row, "azimuth_deg"): number(row, "horizon_elevation_deg")
        for row in rows
    }

    print(f"[OK] {height:4.1f} m horizon: 720 complete directions.")

# Compare horizon elevation at each common azimuth.
for lower, higher in zip(HEIGHTS[:-1], HEIGHTS[1:]):
    violations = []

    for azimuth in horizons[lower]:
        lower_angle = horizons[lower][azimuth]
        higher_angle = horizons[higher][azimuth]

        if higher_angle > lower_angle + 1e-7:
            violations.append(
                (azimuth, lower_angle, higher_angle)
            )

    assert not violations, (
        f"Horizon increased at {len(violations)} directions "
        f"between {lower} m and {higher} m. "
        f"First example: {violations[0] if violations else ''}"
    )

print("[OK] Horizon elevation is non-increasing with observer height.")

# ------------------------------------------------------------
# 3. Zero-height baseline regression
# ------------------------------------------------------------

baseline_rows = read_csv(BASELINE_FILE)

baseline = {
    number(row, "azimuth_deg"): number(row, "horizon_elevation_deg")
    for row in baseline_rows
}

assert len(baseline) == 720

zero_height_rows = read_csv(
    BASE / "nobile_rim_1_horizon_height_0p0m.csv"
)

zero_height_raw = {
    number(row, "azimuth_deg"):
        number(row, "raw_max_terrain_angle_deg")
    for row in zero_height_rows
}

differences = [
    abs(zero_height_raw[az] - baseline[az])
    for az in baseline
]

maximum_difference = max(differences)

print(f"Maximum zero-height baseline difference: {maximum_difference:.12f} deg")

assert maximum_difference <= 1e-6, (
    "Zero-height horizon does not reproduce the original baseline."
)

print("[OK] Zero-height baseline regression passed.")

# ------------------------------------------------------------
# 4. Combined mission scenario validation
# ------------------------------------------------------------

scenario_rows = read_csv(SCENARIO_FILE)

assert len(scenario_rows) == len(HEIGHTS) * 1441, (
    f"Expected {len(HEIGHTS) * 1441} rows, found {len(scenario_rows)}"
)

timestamps_by_height = {}
visible_counts = {}

for height in HEIGHTS:
    rows = [
        row for row in scenario_rows
        if number(row, "lander_height_m") == height
    ]

    assert len(rows) == 1441, (
        f"Expected 1441 scenario rows at {height} m, found {len(rows)}"
    )

    timestamps = [row["utc"] for row in rows]

    assert len(set(timestamps)) == 1441

    timestamps_by_height[height] = set(timestamps)

    count = 0

    for row in rows:
        number(row, "solar_elevation_deg")
        number(row, "solar_azimuth_deg")
        number(row, "terrain_horizon_deg")

        assert row["solar_visible"].lower() in ("true", "false")

        if row["solar_visible"].lower() == "true":
            count += 1

    visible_counts[height] = count

    expected = int(summary_by_height[height]["visible_samples"])

    assert count == expected, (
        f"Visibility count mismatch at {height} m: "
        f"scenario={count}, summary={expected}"
    )

assert all(
    timestamps_by_height[height] == timestamps_by_height[0.0]
    for height in HEIGHTS
)

print("[OK] All six scenarios contain 1441 matching timestamps.")
print("[OK] Scenario visibility counts match the summary.")

# ------------------------------------------------------------
# Final report
# ------------------------------------------------------------

print("\nHEIGHT SCENARIO VALIDATION COMPLETE")
print("=" * 62)

for height in HEIGHTS:
    count = visible_counts[height]
    print(
        f"{height:4.1f} m observer: "
        f"{count}/1441 ({count / 1441 * 100:.2f}%)"
    )

print("\nAll implemented consistency checks passed.")
print("This does not establish independent scientific accuracy.")
