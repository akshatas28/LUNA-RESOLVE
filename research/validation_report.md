# LUNA-RESOLVE: Scientific Validation Report



**Report date:** 14 November 2026

**Study window:** 14 November–13 December 2026

**Sampling interval:** 30 minutes

**Candidate sites:** Nobile Rim 1 and Connecting Ridge



## 1. Purpose



This report documents the numerical consistency checks, terrain validation experiments, SPICE comparisons, and sensitivity analyses performed for LUNA-RESOLVE.



The project estimates terrain-aware solar visibility and geometric Earth-disk visibility at two lunar south-pole candidate locations.



The checks documented here establish implementation consistency and agreement between selected derived products. They do not establish independent absolute scientific accuracy or certify either location as a suitable landing site.



## 2. Candidate sites and reference data



| Site | Latitude | Longitude |

|---|---:|---:|

| Nobile Rim 1 | 85.4381° S | 37.36667° E |

| Connecting Ridge | 89.4632° S | 137.49° W |



The coordinates are representative regional reference points, not confirmed touchdown coordinates.



Terrain inputs are NASA Lunar Orbiter Laser Altimeter (LOLA) products obtained through the Planetary Geosciences Data Archive.



- Nobile Rim 1: Site06 adjusted surface, slope, total elevation error, and slope error products.

- Connecting Ridge: Site01 adjusted surface, slope, total elevation error, and slope error products.

- Native terrain raster resolution: 5 m/pixel.



The SPICE configuration uses the DE440s planetary ephemeris with the DE421 lunar orientation and MOON_ME frame kernels.



## 3. Mission dataset consistency



The two-site validation checked the solar, terrain, Earth, and combined mission datasets.



| Check | Nobile Rim 1 | Connecting Ridge |

|---|---:|---:|

| Solar observations | 1,441 | 1,441 |

| Terrain observations | 1,441 | 1,441 |

| Earth observations | 1,441 | 1,441 |

| Combined mission observations | 1,441 | 1,441 |

| Horizon directions | 720 | 720 |

| Timestamp agreement | Pass | Pass |

| 30-minute sampling cadence | Pass | Pass |

| Solar terrain classification mismatches | 0 | 0 |

| Complete horizon coverage flags | Pass | Pass |



The validation confirmed matching timestamps, strictly increasing observations, valid angular ranges, and agreement between stored solar terrain-visibility classifications and the implemented model rule.



### Mission visibility results



| Metric | Nobile Rim 1 | Connecting Ridge |

|---|---:|---:|

| Solar terrain-visible samples | 465 | 697 |

| Solar terrain visibility | 32.27% | 48.37% |

| Earth fully visible samples | 337 | 126 |

| Earth partially visible samples | 118 | 204 |

| Earth not visible samples | 986 | 1,111 |

| Earth at least partially visible | 31.58% | 22.90% |



Connecting Ridge has 16.10 percentage points more modeled solar terrain visibility. Nobile Rim 1 has 8.68 percentage points more modeled Earth-disk visibility.



These percentages describe the sampled mission window and the implemented geometric model. They are not estimates of generated electrical energy or usable communications availability.



## 4. Earth visibility classification validation



The Earth visibility implementation calculates the Earth direction, elevation, azimuth, distance, and angular radius from the lunar site.



The classification uses the terrain horizon interpolated at Earth's centre azimuth and an effective horizon defined as the greater of zero degrees and the terrain horizon.



Let:



- \(e\) be the Earth's centre elevation.

- \(r\) be the Earth's angular radius.

- \(h\) be the effective terrain horizon.



The model classifies visibility as follows:



- Fully visible when \(e-r > h\).

- Partially visible when \(e+r > h\), but the full-visibility condition is not met.

- Not visible otherwise.



A separate validation script recomputed all classifications from the saved Earth elevation, angular radius, and terrain horizon values.



| Validation result | Nobile Rim 1 | Connecting Ridge |

|---|---:|---:|

| Earth records checked | 1,441 | 1,441 |

| Classification mismatches | 0 | 0 |

| Earth elevation cross-check | Pass | Pass |

| Earth azimuth cross-check | Pass | Pass |

| Mission label cross-check | Pass | Pass |



All stored classifications matched the recomputed values.



**Model limitation:** The Earth is treated as a circular angular disk, and the terrain horizon is evaluated at the disk centre azimuth. This does not model terrain obstruction independently across every direction of the apparent Earth disk. The observer position is calculated on the spherical lunar reference surface; site terrain elevation is not added to the observer position in the current Earth calculation.



This is a geometric visibility estimate, not an RF link-budget or communications-availability calculation.



## 5. Terrain slope validation: Nobile Rim 1



The local slope calculation was compared against NASA's published Site06 slope raster.



A central finite-difference calculation was evaluated over an 11 × 11 pixel neighbourhood.



| Metric | Result |

|---|---:|

| Valid comparisons | 121 |

| Mean absolute difference | 0.0009308° |

| Median absolute difference | 0.0008526° |

| Maximum absolute difference | 0.0026836° |

| 95th percentile difference | 0.0019264° |

| Comparisons within 0.01° | 121 / 121 |



At the reference pixel:



- Locally calculated slope: 15.0468677°.

- NASA published slope: 15.0470228°.

- Absolute difference: 0.0001551°.



The implementation closely reproduces NASA's published slope values over the tested neighbourhood.



This is a local numerical comparison, not a validation across the entire raster or at other lunar locations.



## 6. LOLA point-cloud and DEM consistency



The Nobile Rim 1 adjusted LOLA point cloud was compared with the corresponding 5 m elevation raster.



The binary point cloud contains 936,490 observations. Points were assigned to their corresponding DEM pixels after converting coordinates and elevations from kilometres to metres.



| Metric | Result |

|---|---:|

| Valid point observations | 936,490 |

| Unique DEM pixels sampled | 908,446 |

| Pixels with multiple observations | 27,494 |

| Maximum observations per pixel | 4 |



Using median point elevation per pixel:



| Difference metric | Result |

|---|---:|

| Mean absolute difference | 0.0001641 m |

| Median absolute difference | 0.0001385 m |

| RMSE | 0.0002072 m |

| 95th percentile absolute difference | 0.0003910 m |

| Maximum absolute difference | 0.0009530 m |



The median aggregation was corrected to sort observations by pixel and elevation before calculating medians. Earlier unsorted median results are superseded by the corrected results above.



The point cloud and DEM originate from the same NASA LOLA processing workflow. Their agreement demonstrates consistency between derived products, not independent absolute elevation accuracy.



## 7. Terrain horizon resolution convergence



Nobile Rim 1 radial sampling was progressively refined while comparing results at common azimuth directions.



| Radial comparison | Mean absolute difference | RMSE | Maximum absolute difference | 95th percentile |

|---|---:|---:|---:|---:|

| 5 m vs 2.5 m | 0.033136° | 0.083904° | 0.350799° | 0.191804° |

| 2.5 m vs 1.25 m | 0.005067° | 0.017677° | 0.145947° | 0.036345° |

| 1.25 m vs 0.625 m | 0.002776° | 0.007726° | 0.058004° | 0.019631° |

| 0.625 m vs 0.3125 m | 0.001631° | 0.005741° | 0.042917° | 0.009701° |



The differences decrease overall as radial sampling is refined.



However, sampling below the native 5 m pixel spacing uses interpolation between existing DEM pixels. It does not add terrain measurements or improve the source raster's native resolution.



The remaining local differences, especially near the observer, indicate that the horizon calculation is sensitive to terrain interpolation and near-field surface variation.



## 8. Terrain and observer uncertainty



The Nobile Rim 1 total Z uncertainty raster was sampled at the observer and at calculated obstruction locations.



At obstruction locations:



- Mean RMS Z uncertainty: 0.5346 m.

- Median RMS Z uncertainty: 0.5256 m.

- 95th percentile: 0.8485 m.

- Maximum: 2.6944 m.



These are sampled elevation uncertainty values. They are not formal horizon-angle confidence intervals.



A 5 × 5 grid of hypothetical observer offsets spanning 10 m in each cardinal direction produced:



- Minimum sampled elevation: 5943.0493 m.

- Maximum sampled elevation: 5950.4253 m.

- Elevation range: 7.3760 m.



This demonstrates substantial local terrain variation around the representative reference coordinate. The offsets are sensitivity scenarios, not a measured probability distribution for the actual observer location.



Near-field obstruction angles are particularly sensitive to small elevation changes. No arbitrary exclusion radius has been applied to remove these effects.



## 9. SPICE frame and ephemeris comparisons



The project compared lunar orientation solutions using the DE421 and DE440 lunar frame products for the tested mission window.



The relative frame rotation at the tested epoch was approximately 0.000009957° (0.0358 arcseconds).



For the tested Nobile Rim 1 site and mission window, the angular comparisons were:



| Quantity | Mean absolute difference | Maximum absolute difference |

|---|---:|---:|

| Solar elevation | 0.000007023° | 0.000012758° |

| Solar azimuth | 0.000003847° | 0.000004880° |

| Earth elevation | 0.000008285° | 0.000011059° |

| Earth azimuth | 0.000003988° | 0.000005140° |



A separate comparison against JPL Horizons used geometric vectors, Moon-centred observer context, ICRF coordinates, kilometres, and TDB.



The tested DE441 Horizons and local DE440s vector differences were approximately:



- Sun: 22 m.

- Earth: 1.54 m.



These comparisons demonstrate close numerical agreement for the tested configurations. They are not a complete independent validation of all coordinate transformations, reference-frame conventions, or future mission epochs.



## 10. Reproducibility



Key validation and analysis scripts include:



- `scripts/run_final_validation.py`

- `scripts/validate_earth_visibility.py`

- `scripts/validate_lander_height_scenarios.py`

- `scripts/reproduce_nasa_local_slope.py`

- `scripts/validate_slope_neighbourhood.py`

- `scripts/compare_xyzi_with_dem.py`

- `scripts/compare_xyzi_dem_by_pixel.py`

- `scripts/compare_visibility_frames.py`

- `scripts/compare_radial_resolution.py`

- `scripts/compare_radial_finer.py`

- `scripts/compare_radial_finest.py`

- `scripts/compare_radial_ultrafine.py`



Supporting terrain analysis is documented in `research/terrain_validation.md`.



## 11. Limitations and pending validation



The following limitations remain relevant to interpreting the results:



1\. The candidate coordinates are representative regional reference points, not surveyed touchdown coordinates.

2\. Terrain horizon estimates depend on 5 m LOLA DEM resolution, interpolation, elevation uncertainty, and observer positioning.

3\. Sub-pixel radial sampling does not increase the native terrain data resolution.

4\. The Earth visibility model uses a circular disk and a centre-azimuth terrain horizon approximation.

5\. Earth geometric visibility does not establish RF communications availability.

6\. Solar geometric visibility does not establish usable power generation, thermal suitability, or battery performance.

7\. The tested SPICE and Horizons comparisons do not prove universal ephemeris or frame accuracy.

8\. The two-site validation scripts establish internal consistency, not independent absolute scientific accuracy.

9\. Slope alone does not establish landing safety or engineering suitability.

10\. No complete landing hazard, thermal, power-system, or communications link-budget assessment is included in these results.



Further work should prioritize independent coordinate-transformation checks, terrain horizon uncertainty characterization, and a more complete Earth-disk obstruction model.



## 12. Overall assessment



The current implementation has passed the documented two-site dataset consistency checks and the Earth visibility classification cross-checks.



The Nobile Rim 1 terrain slope calculation closely reproduces NASA's published slope raster in the tested neighbourhood. The LOLA point cloud and DEM show strong internal consistency. SPICE frame comparisons and radial-resolution experiments provide additional numerical evidence for the tested configurations.



The results support presenting LUNA-RESOLVE as a reproducible, terrain-aware geometric visibility analysis tool with explicit assumptions and limitations.



They do not support declaring either candidate site a confirmed landing location or claiming operational power or communications availability.
