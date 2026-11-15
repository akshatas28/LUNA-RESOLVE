# LUNA-RESOLVE

**Lunar South Pole Mission Environment Analysis**

**Live Dashboard:** https://luna-resolve.vercel.app

LUNA-RESOLVE is a terrain-aware analysis platform for evaluating solar illumination and geometric Earth visibility at candidate lunar south-pole exploration sites. It combines NASA lunar elevation data with SPICE-based celestial geometry to examine how local terrain and observer height affect the mission environment over a 30-day observation window.

The project currently analyzes two candidate locations: **Nobile Rim 1** and **Connecting Ridge**. Its interactive dashboard presents mission-environment observations, visibility timelines, site comparisons, and scientific assumptions.

## The Problem

Lunar south-pole terrain creates complex illumination and visibility conditions. Nearby ridges and crater walls can obstruct the Sun or Earth even when the celestial body is geometrically above the local horizontal plane.

Mission planning therefore needs more than a simple latitude-longitude or daylight estimate. It needs to account for local terrain, observation geometry, and changes over time.

## What LUNA-RESOLVE Does

- Calculates solar elevation and azimuth using SPICE-based geometry.
- Derives terrain horizon profiles from NASA Lunar Orbiter Laser Altimeter (LOLA) elevation data.
- Classifies solar visibility by comparing solar geometry with the local terrain horizon.
- Estimates geometric Earth-disk visibility, including fully visible, partially visible, and not-visible states.
- Examines how different observer heights affect terrain-limited solar visibility.
- Compares candidate sites using time-series data and visibility windows.
- Provides date-based inspection of individual mission observations.
- Presents results through an interactive dashboard with time-series charts, visibility timelines, and site comparisons.

## Live Dashboard

The production dashboard is available at:

**https://luna-resolve.vercel.app**

The dashboard includes:

- **Mission snapshot:** Solar visibility, Earth-disk visibility, and solar elevation metrics.
- **Time-series analysis:** Solar and Earth elevation charts with observation-level inspection.
- **Visibility timeline:** Date-based visibility analysis using 30-minute observation bins.
- **Mission observation table:** UTC timestamps, solar elevation, solar azimuth, effective terrain horizon, and visibility classifications.
- **Site comparison:** Side-by-side comparison of Nobile Rim 1 and Connecting Ridge.
- **Visibility windows:** Longest continuous windows, total visible duration, and first and last visible observation bins.
- **Scientific basis:** Data provenance, modeling assumptions, and interpretation boundaries.

The dashboard uses precomputed scientific outputs served as static data files. The Python science-processing workflow is separate from the deployed frontend.

## Candidate Sites

| Candidate site | Latitude | Longitude |
|---|---:|---:|
| Nobile Rim 1 | -85.4381° | +37.36667° |
| Connecting Ridge | -89.4632° | -137.49° |

The coordinates represent reference locations from the source dataset. They should not be interpreted as confirmed lander touchdown coordinates.

## Analysis Results

The current analysis covers **14 November to 13 December 2026**, using 1,441 observations at 30-minute intervals.

| Metric | Nobile Rim 1 | Connecting Ridge |
|---|---:|---:|
| Terrain-visible solar observations | 465 / 1,441 | 697 / 1,441 |
| Solar visibility percentage | 32.27% | 48.37% |
| Geometrically visible Earth-disk observations | 455 / 1,441 | 330 / 1,441 |
| Earth-disk visibility percentage | 31.58% | 22.90% |
| Fully visible Earth-disk observations | 337 | 126 |

These values describe the modeled observation window and the assumptions used by the analysis. They are not predictions of generated electrical power or operational communications availability.

## Technology Stack

**Scientific computing**
- Python
- SpiceyPy
- NumPy
- Rasterio
- SciPy
- PyProj

**Frontend**
- React
- Vite
- JavaScript
- SVG-based visualizations

**Deployment**
- Vercel
- GitHub

**Scientific data**
- NASA LOLA digital elevation products
- NASA/JPL SPICE planetary ephemerides and lunar orientation kernels

## Project Structure

```text
LUNA-RESOLVE/
├── data/
│   ├── metadata/
│   ├── processed/
│   └── raw/
│       ├── lola/
│       └── spice/
├── frontend/
│   ├── public/
│   │   └── data/
│   └── src/
├── research/
│   ├── terrain_validation.md
│   └── validation_report.md
├── science/
│   ├── solar_illumination.py
│   ├── earth_visibility.py
│   ├── classify_terrain_illumination.py
│   └── build_mission_environment.py
├── scripts/
│   ├── calculate_terrain_horizon.py
│   ├── calculate_lander_height_horizons.py
│   ├── run_final_validation.py
│   ├── validate_earth_visibility.py
│   └── validate_lander_height_scenarios.py
└── tests/
```

## Run the Dashboard Locally

### Requirements

- Node.js and npm
- Python 3.11 or compatible
- Git

### Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in your browser.

### Build the frontend

```bash
npm run build
```

### Run lint checks

```bash
npm run lint
```

## Deployment

The frontend is deployed to Vercel and connected to the GitHub repository.

- **Live URL:** https://luna-resolve.vercel.app
- **Repository:** https://github.com/akshatas28/LUNA-RESOLVE
- **Framework:** Vite
- **Deployment target:** Production
- **Frontend root directory:** `frontend`

The dashboard is deployed as a standalone frontend. Scientific processing is performed separately, and the resulting dashboard data files are served from the frontend's public data directory.

## Scientific Validation

The project includes validation work covering:

- Solar and Earth time-series consistency across both sites.
- Earth-disk visibility classification consistency.
- Terrain slope comparison against the NASA LOLA slope product.
- LOLA point-cloud and elevation-raster consistency.
- Terrain-horizon radial-resolution convergence.
- Observer-height and terrain uncertainty sensitivity.
- Lunar reference-frame and ephemeris comparisons.

Supporting documentation:

- `research/validation_report.md`
- `research/terrain_validation.md`

Run the available validation scripts from the project root:

```bash
python scripts/run_final_validation.py
python scripts/validate_earth_visibility.py
python scripts/validate_lander_height_scenarios.py
```

These checks establish internal consistency and document selected comparisons. They do not independently establish the absolute accuracy of every modeled quantity.

## Data Sources

- [NASA Lunar Orbiter Laser Altimeter (LOLA) data](https://pgda.gsfc.nasa.gov/products/78)
- [NASA QuickMap](https://quickmap.lroc.asu.edu/)
- [NASA Moon Trek](https://trek.nasa.gov/moon/)
- [NASA/JPL Horizons](https://ssd.jpl.nasa.gov/horizons/)
- [Canadian Space Agency - Moon Exploration](https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/)

The raw terrain products and SPICE kernels are not necessarily included in the repository. Consult the project data metadata and research documentation for the inputs and provenance required to reproduce the scientific processing.

## Scientific Assumptions and Limitations

LUNA-RESOLVE is a mission-environment analysis tool, not a landing-site certification system.

- Geometric Earth-disk visibility does not establish radio-frequency link availability or communications performance.
- Solar visibility does not directly establish usable power generation, battery performance, or thermal safety.
- Terrain horizons depend on DEM resolution, interpolation, observer position, and observer height.
- Earth visibility uses a geometric disk model and terrain-horizon approximation; it is not a full communications or terrain-ray-tracing model.
- Candidate reference coordinates are not verified touchdown locations.
- The modeled time window and sampling interval limit the conclusions that can be drawn.
- Terrain, ephemeris, frame, and observer uncertainties must be considered when interpreting results.

The project does not declare either candidate site a confirmed landing location.

## Future Work

- Expand terrain analysis to additional lunar south-pole candidate sites.
- Improve near-field terrain and observer-footprint modeling.
- Extend uncertainty analysis into formal horizon-angle bounds.
- Add detailed communications geometry and link-budget analysis.
- Incorporate power-system and thermal constraints.
- Improve independent validation against additional lunar reference datasets.

## Contributors

**Akshata Sital Saptasagar**  
Scientific computing, SPICE-based geometry, terrain and visibility analysis, validation, and project integration.

**Pradeep Sital Saptasagar**  
LOLA terrain research, frontend development, dashboard implementation, and project integration.

## Project Status

Research and prototype implementation with a publicly deployed interactive dashboard. Current scientific outputs support comparative exploration of lunar south-pole illumination and geometric Earth visibility. Further modeling, uncertainty analysis, and independent verification are required before operational mission-planning use.
