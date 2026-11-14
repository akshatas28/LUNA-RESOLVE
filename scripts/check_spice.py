
from pathlib import Path

import spiceypy as spice


KERNEL_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "spice"
)

KERNELS = [
    "naif0012.tls",
    "de440s.bsp",
    "moon_pa_de440_200625.bpc",
    "moon_de440_250416.tf",
]

def main():
    spice.kclear()

    try:
        # Load and validate all required kernels.
        for filename in KERNELS:
            kernel_path = KERNEL_DIR / filename

            if not kernel_path.is_file():
                raise FileNotFoundError(kernel_path)

            spice.furnsh(str(kernel_path))
            print(f"Loaded: {filename}")

        # Verify the lunar reference frame.
        frame_id = spice.namfrm("MOON_ME")

        if frame_id == 0:
            raise RuntimeError("MOON_ME frame was not found.")

        print(f"\nLunar reference frame: MOON_ME ({frame_id})")

        # UTC observation time.
        utc = "2026-11-14T00:00:00"
        et = spice.str2et(utc)

        print(f"UTC: {utc}")
        print(f"Ephemeris time: {et:.3f} seconds past J2000")

        # Geometric positions relative to the Moon's centre.
        for target in ("SUN", "EARTH"):
            state, light_time = spice.spkezr(
                target,
                et,
                "MOON_ME",
                "NONE",
                "MOON",
            )

            position = state[:3]
            distance = spice.vnorm(position)

            print(f"\n{target} relative to Moon:")
            print(
                "Position (km): "
                f"X={position[0]:.3f}, "
                f"Y={position[1]:.3f}, "
                f"Z={position[2]:.3f}"
            )
            print(f"Distance: {distance:.3f} km")

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()
