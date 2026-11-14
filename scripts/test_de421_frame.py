import spiceypy as spice
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "data" / "raw" / "spice"

KERNELS = [
    "naif0012.tls",
    "de440s.bsp",
    "moon_pa_de421_1900-2050.bpc",
    "moon_080317.tf",
]

UTC = "2026-11-14T00:00:00"

spice.kclear()

try:
    print("DE421 MOON_ME FRAME DIAGNOSTIC")
    print("=" * 55)

    for kernel in KERNELS:
        path = KERNEL_DIR / kernel
        spice.furnsh(str(path))
        print(f"Loaded: {kernel}")

    et = spice.str2et(UTC)

    print(f"\nUTC: {UTC}")
    print(f"ET: {et:.6f}")

    frame_id = spice.namfrm("MOON_ME")
    print(f"\nMOON_ME frame ID: {frame_id}")

    if frame_id == 0:
        raise RuntimeError("MOON_ME frame was not found.")

    center, frame_class, class_id = spice.frinfo(frame_id)

    print(f"Frame centre: {center}")
    print(f"Frame class: {frame_class}")
    print(f"Frame class ID: {class_id}")

    rotation = spice.pxform("MOON_ME", "J2000", et)

    print("\nMOON_ME to J2000 rotation matrix:")
    for row in rotation:
        print("  ", " ".join(f"{value: .12f}" for value in row))

    sun_state, _ = spice.spkezr(
        "SUN", et, "MOON_ME", "NONE", "MOON"
    )

    earth_state, _ = spice.spkezr(
        "EARTH", et, "MOON_ME", "NONE", "MOON"
    )

    print("\nSun position in DE421 MOON_ME (km):")
    print(sun_state[:3])

    print("\nEarth position in DE421 MOON_ME (km):")
    print(earth_state[:3])

    print("\nDE421 frame diagnostic: COMPLETE")

finally:
    spice.kclear()