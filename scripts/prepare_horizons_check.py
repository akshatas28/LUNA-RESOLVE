
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
            spice.furnsh(str(KERNEL_DIR / filename))

        et = spice.str2et(UTC)

        print("HORIZONS VALIDATION REFERENCE")
        print("=============================")
        print(f"UTC: {UTC}")
        print(f"SPICE ET: {et:.6f}")
        print("Observer: Moon centre (MOON)")
        print("Correction: NONE (geometric)")
        print("Units: km")
        print("SPICE frame: J2000")
        print("Horizons comparison frame: ICRF")
        print()

        for target in ("SUN", "EARTH"):
            state, _ = spice.spkezr(
                target,
                et,
                "J2000",
                "NONE",
                "MOON",
            )

            x, y, z = state[:3]
            distance = spice.vnorm(state[:3])

            print(f"{target}")
            print(f"  X = {x:.6f} km")
            print(f"  Y = {y:.6f} km")
            print(f"  Z = {z:.6f} km")
            print(f"  Range = {distance:.6f} km")
            print()

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()
