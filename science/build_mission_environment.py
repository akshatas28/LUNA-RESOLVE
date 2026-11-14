
import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
METADATA_FILE = ROOT / "data" / "metadata" / "candidate_sites.json"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def is_true(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def get_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def find_visibility_windows(rows, visibility_field, visible_condition):
    if len(rows) < 2:
        raise ValueError("At least two observations are required.")

    timestamps = [get_timestamp(row["utc"]) for row in rows]
    intervals = [
        timestamps[i + 1] - timestamps[i]
        for i in range(len(timestamps) - 1)
    ]

    step = intervals[0]

    tolerance_seconds = 0.01

    if step.total_seconds() <= 0 or any(
        interval.total_seconds() <= 0
        or abs((interval - step).total_seconds()) > tolerance_seconds
        for interval in intervals
    ):
        raise ValueError("Timestamps must be strictly increasing and evenly spaced.")

    windows = []
    start_index = None

    def close_window(end_index):
        count = end_index - start_index + 1
        duration = step * count

        windows.append({
            "start_utc": rows[start_index]["utc"],
            "end_utc": rows[end_index]["utc"],
            "duration_minutes": duration.total_seconds() / 60,
            "observations": count,
        })

    for index, row in enumerate(rows):
        visible = visible_condition(row[visibility_field])

        if visible and start_index is None:
            start_index = index

        elif not visible and start_index is not None:
            close_window(index - 1)
            start_index = None

    if start_index is not None:
        close_window(len(rows) - 1)

    return windows


def summarize_windows(site_name, visibility_type, windows):
    if not windows:
        return {
            "site": site_name,
            "visibility_type": visibility_type,
            "window_count": 0,
            "longest_window_minutes": 0,
            "longest_window_start_utc": "",
            "longest_window_end_utc": "",
            "total_visible_minutes": 0,
        }

    longest = max(windows, key=lambda window: window["duration_minutes"])

    return {
        "site": site_name,
        "visibility_type": visibility_type,
        "window_count": len(windows),
        "longest_window_minutes": round(longest["duration_minutes"], 1),
        "longest_window_start_utc": longest["start_utc"],
        "longest_window_end_utc": longest["end_utc"],
        "total_visible_minutes": round(
            sum(window["duration_minutes"] for window in windows), 1
        ),
    }


def main():
    with open(METADATA_FILE, encoding="utf-8") as file:
        metadata = json.load(file)

    summaries = []

    for site_id, site in metadata["sites"].items():
        site_slug = site["site_name"].lower().replace(" ", "_")

        files = {
            "solar": DATA / f"{site_slug}_solar_illumination.csv",
            "terrain": DATA / f"{site_slug}_terrain_illumination.csv",
            "earth": DATA / f"{site_slug}_earth_visibility.csv",
        }

        datasets = {
            name: read_csv(path)
            for name, path in files.items()
        }

        if any(not rows for rows in datasets.values()):
            raise ValueError(f"An input dataset is empty for {site['site_name']}.")

        timestamps = [
            {row["utc"] for row in rows}
            for rows in datasets.values()
        ]

        if not all(value == timestamps[0] for value in timestamps[1:]):
            raise ValueError(f"Dataset timestamps do not match for {site['site_name']}.")

        terrain_by_time = {
            row["utc"]: row for row in datasets["terrain"]
        }

        earth_by_time = {
            row["utc"]: row for row in datasets["earth"]
        }

        output = DATA / f"{site_slug}_mission_environment.csv"

        with open(output, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow([
                "utc",
                "solar_elevation_deg",
                "solar_azimuth_deg",
                "terrain_horizon_elevation_deg",
                "terrain_visible",
                "earth_elevation_deg",
                "earth_azimuth_deg",
                "earth_visibility",
            ])

            for solar in datasets["solar"]:
                utc = solar["utc"]
                terrain = terrain_by_time[utc]
                earth = earth_by_time[utc]

                writer.writerow([
                    utc,
                    solar["solar_elevation_deg"],
                    solar["solar_azimuth_deg"],
                    terrain["terrain_horizon_elevation_deg"],
                    terrain["terrain_visible"],
                    earth["earth_elevation_deg"],
                    earth["earth_azimuth_deg"],
                    earth["earth_visibility"],
                ])

        mission_rows = read_csv(output)

        solar_windows = find_visibility_windows(
            mission_rows,
            "terrain_visible",
            is_true,
        )

        earth_windows = find_visibility_windows(
            mission_rows,
            "earth_visibility",
            lambda value: value.strip().lower() != "not_visible",
        )

        summaries.append(
            summarize_windows(
                site["site_name"],
                "Solar visibility",
                solar_windows,
            )
        )

        summaries.append(
            summarize_windows(
                site["site_name"],
                "Earth disk visibility",
                earth_windows,
            )
        )

        print(f"\nSite: {site['site_name']}")
        print(f"Mission observations: {len(mission_rows)}")
        print(f"Solar visibility windows: {len(solar_windows)}")
        print(f"Earth visibility windows: {len(earth_windows)}")
        print(f"Mission environment: {output}")


    # Calculate solar visibility windows for each Nobile Rim 1 observer height.
    height_file = DATA / "nobile_rim_1_lander_height_scenarios.csv"
    height_rows = read_csv(height_file)

    if not height_rows:
        raise ValueError("Nobile Rim 1 height-scenario dataset is empty.")

    height_groups = {}

    for row in height_rows:
        height = float(row["lander_height_m"])
        height_groups.setdefault(height, []).append(row)

    height_summaries = []

    for height in sorted(height_groups):
        windows = find_visibility_windows(
            height_groups[height],
            "solar_visible",
            is_true,
        )

        longest = max(
            windows,
            key=lambda window: window["duration_minutes"],
            default=None,
        )

        height_summaries.append({
            "site": "Nobile Rim 1",
            "observer_height_m": height,
            "window_count": len(windows),
            "longest_window_minutes": (
                round(longest["duration_minutes"], 1)
                if longest else 0
            ),
            "longest_window_start_utc": (
                longest["start_utc"] if longest else ""
            ),
            "longest_window_end_utc": (
                longest["end_utc"] if longest else ""
            ),
            "total_visible_minutes": round(
                sum(w["duration_minutes"] for w in windows), 1
            ),
        })

    height_output = DATA / "nobile_rim_1_height_visibility_windows.csv"

    with open(height_output, "w", newline="", encoding="utf-8") as file:
        fields = [
            "site",
            "observer_height_m",
            "window_count",
            "longest_window_minutes",
            "longest_window_start_utc",
            "longest_window_end_utc",
            "total_visible_minutes",
        ]

        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(height_summaries)

    print("\nHEIGHT-DEPENDENT VISIBILITY WINDOWS: COMPLETE")
    print("Observer heights:", len(height_summaries))
    print("Output:", height_output)


    summary_output = DATA / "visibility_window_summary.csv"

    with open(summary_output, "w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "site",
            "visibility_type",
            "window_count",
            "longest_window_minutes",
            "longest_window_start_utc",
            "longest_window_end_utc",
            "total_visible_minutes",
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    print("\nVISIBILITY WINDOW ANALYSIS: COMPLETE")
    print("Sites analysed:", len(metadata["sites"]))
    print("Summary:", summary_output)


if __name__ == "__main__":
    main()
