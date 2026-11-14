import rasterio
import numpy as np

RASTER = "data/raw/lola/Site06_final_adj_5mpp_surf.tif"

ROW = 1999
COL = 2000
WINDOW_RADIUS = 5
PIXEL_SIZE = 5.0

with rasterio.open(RASTER) as ds:

    z = ds.read(
        1,
        window=(
            (ROW - WINDOW_RADIUS, ROW + WINDOW_RADIUS + 1),
            (COL - WINDOW_RADIUS, COL + WINDOW_RADIUS + 1)
        ),
        masked=True
    )

    if np.ma.getmaskarray(z).any():
        raise ValueError("Window contains NoData pixels.")

    z = np.asarray(z, dtype=float)

    rows, cols = np.indices(z.shape)

    # Raster X increases with column.
    # Raster Y decreases with row.
    x = (cols.ravel() - WINDOW_RADIUS) * PIXEL_SIZE
    y = -(rows.ravel() - WINDOW_RADIUS) * PIXEL_SIZE

    A = np.column_stack([
        np.ones(z.size),
        x,
        y
    ])

    coefficients, _, _, _ = np.linalg.lstsq(
        A,
        z.ravel(),
        rcond=None
    )

    base_elevation, dz_dx, dz_dy = coefficients

    gradient = np.sqrt(dz_dx**2 + dz_dy**2)
    slope_degrees = np.degrees(np.arctan(gradient))

    fitted = (A @ coefficients).reshape(z.shape)
    residuals = z - fitted

    rmse = np.sqrt(np.mean(residuals**2))

    print("LOCAL TERRAIN PLANE")
    print(f"Base elevation: {base_elevation:.4f} m")
    print(f"East gradient: {dz_dx:.6f} m/m")
    print(f"North gradient: {dz_dy:.6f} m/m")
    print(f"Gradient magnitude: {gradient:.6f} m/m")
    print(f"Estimated slope: {slope_degrees:.4f} degrees")

    print("\nLOCAL SURFACE RESIDUALS")
    print(f"RMSE: {rmse:.4f} m")
    print(f"Minimum: {residuals.min():.4f} m")
    print(f"Maximum: {residuals.max():.4f} m")

    print("\nWINDOW")
    print(f"Valid samples: {z.size}")
    print(f"Elevation range: {z.min():.3f} to {z.max():.3f} m")