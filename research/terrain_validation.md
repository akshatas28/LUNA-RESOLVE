\# LUNA-RESOLVE: Terrain Slope Validation



\## 1. Objective



Validate the local terrain-slope calculation against NASA's published LOLA slope raster for the Nobile Rim 1 Site06 dataset.



\## 2. Input datasets



Source: NASA Planetary Geosciences Data Archive (PGDA), Site06.



\- `Site06\_final\_adj\_5mpp\_surf.tif`

\- `Site06\_final\_adj\_5mpp\_slp.tif`

\- `Site06\_final\_adj\_5mpp\_toterr.tif`

\- `Site06\_final\_adj\_5mpp\_slperr.tif`



Raster resolution: 5 m/pixel.



All four products have matching dimensions, CRS metadata, transforms and bounds.



\## 3. Reference location



\- Site: Nobile Rim 1

\- Latitude: -85.4381°

\- Longitude: 37.36667°

\- Raster row: 1999

\- Raster column: 2000



The coordinate is a representative region reference point, not a confirmed landing coordinate.



\## 4. Method



Calculated local slope using central finite differences on the elevation raster.



The resulting slope was compared with NASA's published slope raster at the corresponding pixels.



\## 5. Validation results



Comparison window: 11 × 11 pixels (55 m neighbourhood).



\- Valid comparisons: 121

\- Mean absolute difference: 0.0009308177°

\- Median absolute difference: 0.0008525848°

\- Maximum absolute difference: 0.0026836395°

\- 95th percentile difference: 0.0019264221°

\- Comparisons within 0.01°: 121 / 121



Centre pixel:



\- Calculated slope: 15.0468677°

\- NASA slope: 15.0470228°

\- Absolute difference: 0.0001551°



\## 6. Interpretation



The implementation closely reproduces NASA's published slope values across the tested 55 m neighbourhood.



This is a local numerical validation. It does not establish accuracy across the entire raster or other lunar locations.



\## 7. Limitations and pending work



\- Verify the exact projection parameters and pixel registration.

\- Reconcile the Site06 DE421/MOON\_ME data provenance with the DE440 SPICE ephemeris.

\- Verify coordinate transformations independently.

\- Do not interpret slope alone as landing-site suitability.

\- Do not treat RMS uncertainty as a guaranteed error bound.



\## 8. Reproduction scripts



\- `scripts/reproduce\_nasa\_local\_slope.py`

\- `scripts/validate\_slope\_neighbourhood.py`

\- `scripts/compare\_nasa\_lola\_products.py`



## Point-cloud to DEM consistency validation

Source products:
- Site06_final_adj.xyzi
- Site06_final_adj_5mpp_surf.tif

The binary point cloud contains 936,490 observations.
Coordinates and elevations were converted from kilometres to metres.
Each observation was assigned to its corresponding 5 m DEM pixel.

Results:
- Valid point observations: 936,490
- Unique DEM pixels sampled: 908,446
- Pixels containing multiple observations: 27,494
- Maximum observations per pixel: 4

Median point elevation compared with DEM pixel elevation:
- Mean absolute difference: 0.0001641 m
- Median absolute difference: 0.0001385 m
- RMSE: 0.0002072 m
- 95th percentile absolute difference: 0.0003910 m
- Maximum absolute difference: 0.0009530 m

Mean point elevation compared with DEM pixel elevation:
- Mean absolute difference: 0.0002508 m
- Median absolute difference: 0.0001386 m
- RMSE: 0.0073369 m
- 95th percentile absolute difference: 0.0003918 m
- Maximum absolute difference: 4.1332 m

Methodological note:
Median calculations sort observations by pixel and elevation before
aggregation. An earlier implementation did not sort elevations within
each pixel and produced invalid median statistics. Those earlier
median results are superseded by the corrected results above.

Limitation:
The point cloud and DEM originate from the same NASA LOLA processing
workflow. This comparison demonstrates consistency between derived
products, not independent absolute elevation accuracy.


## Observer Position and Terrain Uncertainty Analysis

### Reference Point

The Nobile Rim 1 coordinate (-85.4381°, 37.36667°) is a representative regional reference point, not a surveyed landing or touchdown coordinate.

### LOLA Terrain Resolution

The elevation model has a spatial resolution of 5 metres per pixel. Terrain horizon calculations use bilinear interpolation between raster pixels, with radial sampling at 2.5-metre intervals.

Sub-pixel sampling provides numerical interpolation, not additional terrain measurements or improved native DEM resolution.

### Elevation Uncertainty

The NASA total Z uncertainty raster was inspected at the observer and at 720 calculated obstruction locations.

Results at obstruction locations:

- Mean RMS Z uncertainty: 0.5346 m
- Median RMS Z uncertainty: 0.5256 m
- 95th percentile: 0.8485 m
- Maximum: 2.6944 m

These are sampled elevation uncertainty values, not formal horizon-angle confidence intervals.

### Observer Position Sensitivity

A 5-by-5 grid of hypothetical observer offsets, spanning 10 metres in each cardinal direction, was evaluated.

- Minimum sampled elevation: 5943.0493 m
- Maximum sampled elevation: 5950.4253 m
- Elevation range: 7.3760 m

This demonstrates substantial local terrain variation. The tested offsets are sensitivity scenarios and do not represent a measured probability distribution for the reference coordinate.

### Near-Field Horizon Limitations

The largest horizon-angle sensitivity occurs at very short obstruction distances. At these distances, small elevation changes can produce large angular changes.

The current regional reference coordinate and 5-metre DEM do not justify interpreting every near-field obstruction as a precisely located physical feature.

Near-field results therefore require qualification. No arbitrary exclusion radius has been applied.

### Interpretation

The current terrain horizon is a DEM-derived geometric estimate. Its accuracy is affected by terrain resolution, elevation uncertainty, observer positioning and interpolation.

The sensitivity experiments do not establish a formal statistical uncertainty interval for the complete horizon model.
