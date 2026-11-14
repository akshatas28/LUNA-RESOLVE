import numpy as np
import spiceypy as spice
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "data" / "raw" / "spice"

UTC = "2026-11-14T00:00:00"

COMMON_KERNELS = [
    "naif0012.tls",
    "de440s.bsp",
]

FRAME_CONFIGS = {
    "DE421": [
        "moon_pa_de421_1900-2050.bpc",
        "moon_080317.tf",
    ],
    "DE440": [
        "moon_pa_de440_200625.bpc",
        "moon_de440_250416.tf",
    ],
}


def load_configuration(name):
    spice.kclear()

    for kernel in COMMON_KERNELS + FRAME_CONFIGS[name]:
        spice.furnsh(str(KERNEL_DIR / kernel))

    et = spice.str2et(UTC)

    rotation = spice.pxform("MOON_ME", "J2000", et)

    sun, _ = spice.spkezr(
        "SUN", et, "MOON_ME", "NONE", "MOON"
    )

    earth, _ = spice.spkezr(
        "EARTH", et, "MOON_ME", "NONE", "MOON"
    )

    return rotation, np.array(sun[:3]), np.array(earth[:3])


def rotation_difference_deg(rotation_a, rotation_b):
    relative = rotation_a.T @ rotation_b

    cosine = (np.trace(relative) - 1.0) / 2.0
    cosine = np.clip(cosine, -1.0, 1.0)

    return np.degrees(np.arccos(cosine))


def vector_difference(a, b):
    difference = np.linalg.norm(a - b)
    angle = np.degrees(
        np.arccos(
            np.clip(
                np.dot(a, b) /
                (np.linalg.norm(a) * np.linalg.norm(b)),
                -1.0,
                1.0,
            )
        )
    )

    return difference, angle


try:
    results = {}

    for name in ("DE421", "DE440"):
        rotation, sun, earth = load_configuration(name)
        results[name] = (rotation, sun, earth)

        print(f"\n{name} MOON_ME")
        print("-" * 45)
        print("Sun (km):", sun)
        print("Earth (km):", earth)

    r421, sun421, earth421 = results["DE421"]
    r440, sun440, earth440 = results["DE440"]

    print("\nFRAME COMPARISON")
    print("=" * 55)

    print(
        "Relative frame rotation:",
        f"{rotation_difference_deg(r440, r421):.9f} deg"
    )

    sun_delta, sun_angle = vector_difference(sun440, sun421)
    earth_delta, earth_angle = vector_difference(earth440, earth421)

    print("\nSUN VECTOR")
    print(f"Position difference: {sun_delta:.6f} km")
    print(f"Angular difference:  {sun_angle:.9f} deg")

    print("\nEARTH VECTOR")
    print(f"Position difference: {earth_delta:.6f} km")
    print(f"Angular difference:  {earth_angle:.9f} deg")

    print("\nFrame comparison: COMPLETE")

finally:
    spice.kclear()