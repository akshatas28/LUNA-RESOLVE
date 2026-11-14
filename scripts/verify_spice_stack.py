
from pathlib import Path
import spiceypy as spice

ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "data" / "raw" / "spice"

KERNELS = [
    "naif0012.tls",
    "de440s.bsp",
    "moon_pa_de440_200625.bpc",
    "moon_de440_250416.tf",
]

UTC = "2026-11-14T00:00:00"


def main():
    spice.kclear()

    try:
        for filename in KERNELS:
            path = KERNEL_DIR / filename
            spice.furnsh(str(path))
            print(f"Loaded: {filename}")

        et = spice.str2et(UTC)

        print(f"\nUTC: {UTC}")
        print(f"ET: {et:.6f}")
        print(f"MOON_ME frame ID: {spice.namfrm('MOON_ME')}")

        for frame in ("J2000", "MOON_ME"):
            print(f"\nReference frame: {frame}")

            for target in ("SUN", "EARTH"):
                state, _ = spice.spkezr(
                    target,
                    et,
                    frame,
                    "NONE",
                    "MOON",
                )

                position = state[:3]
                distance = spice.vnorm(position)

                print(f"\n{target}")
                print(
                    "Position (km): "
                    f"X={position[0]:.6f}, "
                    f"Y={position[1]:.6f}, "
                    f"Z={position[2]:.6f}"
                )
                print(f"Distance (km): {distance:.6f}")

        print("\nCOMPLETE KERNEL STACK: SUCCESS")

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()
