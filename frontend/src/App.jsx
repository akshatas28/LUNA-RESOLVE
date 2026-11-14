import { useEffect, useMemo, useState } from 'react'
import './App.css'

const SITES = {
  nobile_rim_1: {
    name: 'Nobile Rim 1',
    latitude: '85.4381° S',
    longitude: '37.36667° E',
    missionFile: '/data/nobile_rim_1_mission_environment.csv',
    heightFile: '/data/nobile_rim_1_lander_height_scenarios.csv',
    supportsHeightScenarios: true,
  },
  connecting_ridge: {
    name: 'Connecting Ridge',
    latitude: '89.4632° S',
    longitude: '137.49° W',
    missionFile: '/data/connecting_ridge_mission_environment.csv',
    heightFile: null,
    supportsHeightScenarios: false,
  },
}

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/)
  const headers = lines[0].split(',')

  return lines.slice(1).map((line) => {
    const values = line.split(',')
    const row = Object.fromEntries(
      headers.map((key, i) => [key, values[i]])
    )

    return {
      utc: row.utc,
      solar: Number(row.solar_elevation_deg),
      solarAzimuth: Number(row.solar_azimuth_deg),
      horizon: Math.max(0, Number(row.terrain_horizon_elevation_deg)),
      terrainVisible: row.terrain_visible === 'True',
      earth: Number(row.earth_elevation_deg),
      earthAzimuth: Number(row.earth_azimuth_deg),
      earthVisibility: row.earth_visibility,
    }
  })
}

function parseHeightCSV(text) {
  const lines = text.trim().split(/\r?\n/)
  const headers = lines[0].split(',')

  return lines.slice(1).map((line) => {
    const values = line.split(',')
    const row = Object.fromEntries(
      headers.map((key, i) => [key, values[i]])
    )

    return {
      utc: row.utc,
      height: Number(row.lander_height_m),
      horizon: Number(row.terrain_horizon_deg),
      terrainVisible: row.solar_visible === 'True',
    }
  })
}

function formatDate(value) {
  return new Date(`${value.replace(' ', 'T')}Z`).toLocaleDateString(
    'en-IN',
    {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      timeZone: 'UTC',
    },
  )
}

function Metric({ label, value, detail }) {
  return (
    <article className="metric-card">
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
      <span className="metric-detail">{detail}</span>
    </article>
  )
}

function LineChart({ data, valueKey, color, label, threshold = 0 }) {
  const [activeIndex, setActiveIndex] = useState(null)

  const width = 900
  const height = 250
  const padding = { top: 18, right: 18, bottom: 34, left: 48 }

  const values = data.map((d) => d[valueKey])
  const min = Math.min(...values, threshold)
  const max = Math.max(...values, threshold)
  const range = Math.max(max - min, 1)

  const x = (i) =>
    padding.left +
    (i / Math.max(data.length - 1, 1)) *
      (width - padding.left - padding.right)

  const y = (v) =>
    height -
    padding.bottom -
    ((v - min) / range) *
      (height - padding.top - padding.bottom)

  const points = values.map((v, i) => `${x(i)},${y(v)}`).join(' ')
  const zeroY = y(threshold)
  const selected = activeIndex === null ? null : data[activeIndex]

  function handlePointerMove(event) {
    const bounds = event.currentTarget.getBoundingClientRect()
    const relativeX = (event.clientX - bounds.left) / bounds.width
    const chartX = relativeX * width
    const usableWidth = width - padding.left - padding.right

    const index = Math.round(
      ((chartX - padding.left) / usableWidth) * (data.length - 1),
    )

    setActiveIndex(
      Math.max(0, Math.min(data.length - 1, index))
    )
  }

  return (
    <div className="chart-wrap">
      <div className="chart-heading">
        <span>{label}</span>
        <span className="chart-unit">Degrees · Hover to inspect</span>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="line-chart"
        role="img"
        aria-label={label}
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setActiveIndex(null)}
      >
        {[0, 1, 2, 3, 4].map((i) => {
          const gy =
            padding.top +
            (i * (height - padding.top - padding.bottom)) / 4

          const value = max - (i * range) / 4

          return (
            <g key={i}>
              <line
                x1={padding.left}
                x2={width - padding.right}
                y1={gy}
                y2={gy}
                className="grid-line"
              />

              <text
                x={padding.left - 9}
                y={gy + 4}
                textAnchor="end"
                className="axis-label"
              >
                {value.toFixed(1)}°
              </text>
            </g>
          )
        })}

        <line
          x1={padding.left}
          x2={width - padding.right}
          y1={zeroY}
          y2={zeroY}
          className="zero-line"
        />

        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {selected && (
          <>
            <line
              x1={x(activeIndex)}
              x2={x(activeIndex)}
              y1={padding.top}
              y2={height - padding.bottom}
              stroke="#dce5e9"
              strokeDasharray="4 4"
              opacity="0.65"
            />

            <circle
              cx={x(activeIndex)}
              cy={y(selected[valueKey])}
              r="6"
              fill={color}
              stroke="#ffffff"
              strokeWidth="2"
            />
          </>
        )}

        <text
          x={padding.left}
          y={height - 8}
          className="axis-label"
        >
          Start
        </text>

        <text
          x={width - padding.right}
          y={height - 8}
          textAnchor="end"
          className="axis-label"
        >
          End
        </text>
      </svg>

      {selected ? (
        <div className="chart-tooltip">
          <strong>{selected.utc.replace('T', ' ')} UTC</strong>

          <span>
            {label}: {selected[valueKey].toFixed(4)}°
          </span>

          {valueKey === 'solar' ? (
            <>
              <span>
                Solar azimuth: {selected.solarAzimuth.toFixed(4)}°
              </span>

              <span>
                Effective horizon: {selected.horizon.toFixed(4)}°
              </span>

              <span>
                Terrain visibility:{' '}
                {selected.terrainVisible ? 'Visible' : 'Blocked'}
              </span>
            </>
          ) : (
            <>
              <span>
                Earth azimuth: {selected.earthAzimuth.toFixed(4)}°
              </span>

              <span>
                Earth disk:{' '}
                {selected.earthVisibility.replace('_', ' ')}
              </span>
            </>
          )}
        </div>
      ) : (
        <p className="chart-footnote">
          Move your pointer over the chart to inspect individual observations.
        </p>
      )}
    </div>
  )
}

function VisibilityTimeline({ data }) {
  const days = Object.values(
    data.reduce((groups, item) => {
      const date = item.utc.slice(0, 10)

      if (!groups[date]) groups[date] = []

      groups[date].push(item)

      return groups
    }, {}),
  )

  return (
    <div className="timeline-card">
      <div className="timeline-legend">
        <span><i className="legend-sun" /> Sun visible</span>
        <span><i className="legend-blocked" /> Sun blocked</span>
        <span><i className="legend-earth" /> Earth fully visible</span>
        <span><i className="legend-partial" /> Earth partially visible</span>
        <span><i className="legend-hidden" /> Earth not visible</span>
      </div>

      <div className="timeline-axis">
        <span>UTC DATE</span>
        <span>00:00</span>
        <span>06:00</span>
        <span>12:00</span>
        <span>18:00</span>
        <span>24:00</span>
      </div>

      {days.map((day) => (
        <div className="timeline-day" key={day[0].utc.slice(0, 10)}>
          <div className="timeline-date">
            {new Date(
              `${day[0].utc.slice(0, 10)}T00:00:00Z`
            ).toLocaleDateString(
              'en-IN',
              {
                day: '2-digit',
                month: 'short',
                timeZone: 'UTC',
              },
            )}
          </div>

          <div className="timeline-tracks">
            <div className="timeline-track">
              {day.map((item) => (
                <div
                  key={`${item.utc}-sun`}
                  className={`timeline-cell ${
                    item.terrainVisible ? 'sun-visible' : 'sun-blocked'
                  }`}
                  title={`${item.utc} UTC | Sun: ${
                    item.terrainVisible ? 'Visible' : 'Blocked'
                  } | Elevation: ${item.solar.toFixed(3)}°`}
                />
              ))}
            </div>

            <div className="timeline-track">
              {day.map((item) => (
                <div
                  key={`${item.utc}-earth`}
                  className={`timeline-cell earth-${item.earthVisibility}`}
                  title={`${item.utc} UTC | Earth: ${
                    item.earthVisibility.replace('_', ' ')
                  } | Elevation: ${item.earth.toFixed(3)}°`}
                />
              ))}
            </div>
          </div>
        </div>
      ))}

      <p className="timeline-note">
        Each cell represents one 30-minute observation. Hover over a cell
        for its UTC timestamp and modelled visibility.
      </p>
    </div>
  )
}

function SiteComparison() {
  const [comparison, setComparison] = useState([])
  const [loadingComparison, setLoadingComparison] = useState(true)
  const [comparisonError, setComparisonError] = useState('')

  useEffect(() => {
    let cancelled = false

    Promise.all(
      Object.entries(SITES).map(async ([id, site]) => {
        const response = await fetch(site.missionFile)

        if (!response.ok) {
          throw new Error(`Could not load ${site.name} comparison data.`)
        }

        const rows = parseCSV(await response.text())

        if (!rows.length) {
          throw new Error(`${site.name} dataset is empty.`)
        }

        const solarVisible = rows.filter(
          (row) => row.terrainVisible
        ).length

        const earthVisible = rows.filter(
          (row) => row.earthVisibility !== 'not_visible'
        ).length

        const earthFullyVisible = rows.filter(
          (row) => row.earthVisibility === 'fully_visible'
        ).length

        return {
          id,
          name: site.name,
          samples: rows.length,
          startTime: rows[0].utc,
          endTime: rows[rows.length - 1].utc,
          solarPercent: (solarVisible / rows.length) * 100,
          earthPercent: (earthVisible / rows.length) * 100,
          earthFullyVisible,
        }
      })
    )
      .then((results) => {
        if (!cancelled) {
          const [first, second] = results

          if (
            first.samples !== second.samples ||
            first.startTime !== second.startTime ||
            first.endTime !== second.endTime
          ) {
            throw new Error(
              'The site datasets do not share the same observation window.'
            )
          }

          setComparison(results)
        }
      })
      .catch((error) => {
        if (!cancelled) setComparisonError(error.message)
      })
      .finally(() => {
        if (!cancelled) setLoadingComparison(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  if (loadingComparison) {
    return (
      <section className="comparison-section">
        <p>Loading site comparison...</p>
      </section>
    )
  }

  if (comparisonError || comparison.length !== 2) {
    return (
      <section className="comparison-section">
        <p>{comparisonError || 'Comparison data unavailable.'}</p>
      </section>
    )
  }

  const nobile = comparison.find(
    (site) => site.id === 'nobile_rim_1'
  )

  const connecting = comparison.find(
    (site) => site.id === 'connecting_ridge'
  )

  if (!nobile || !connecting) return null

  const metrics = [
    {
      label: 'TERRAIN-MODELLED SUN VISIBILITY',
      format: (site) => `${site.solarPercent.toFixed(1)}%`,
      value: (site) => site.solarPercent,
      bar: true,
      detail: 'Percentage of observations with direct solar visibility',
    },
    {
      label: 'EARTH DISK VISIBLE',
      format: (site) => `${site.earthPercent.toFixed(1)}%`,
      value: (site) => site.earthPercent,
      bar: true,
      detail: 'Percentage of observations with partial or full Earth visibility',
    },
    {
      label: 'EARTH FULLY VISIBLE',
      format: (site) => site.earthFullyVisible.toLocaleString('en-IN'),
      detail: 'Number of observations with the full Earth disk visible',
    },
    {
      label: 'OBSERVATIONS',
      format: (site) => site.samples.toLocaleString('en-IN'),
      detail: 'Samples in each mission dataset',
    },
  ]

  return (
    <>
      <section className="section-heading">
        <div>
          <p className="eyebrow">05 / SITE COMPARISON</p>
          <h2>Compare candidate regions</h2>
        </div>

        <span className="section-note">
          0 m reference · Same analysis window
        </span>
      </section>

      <section className="comparison-section">
        <div className="comparison-header">
          <span>METRIC</span>
          <span>{nobile.name.toUpperCase()}</span>
          <span>{connecting.name.toUpperCase()}</span>
        </div>

        {metrics.map((metric) => (
          <div className="comparison-row" key={metric.label}>
            <div className="comparison-metric">
              <strong>{metric.label}</strong>
              <small>{metric.detail}</small>
            </div>

            {[nobile, connecting].map((site) => (
              <div className="comparison-value" key={site.id}>
                <strong>{metric.format(site)}</strong>

                {metric.bar && (
                  <div
                    className="comparison-bar-track"
                    role="img"
                    aria-label={`${site.name}: ${metric.format(site)} visibility`}
                  >
                    <div
                      className={`comparison-bar-fill ${
                        site.id === 'nobile_rim_1'
                          ? 'nobile-bar'
                          : 'connecting-bar'
                      }`}
                      style={{
                        width: `${Math.max(
                          0,
                          Math.min(100, metric.value(site))
                        )}%`,
                      }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
      </section>

      <p className="chart-footnote">
        Both sites are compared using their 0 m reference datasets.
        Bars use a common 0–100% scale. Solar visibility uses the
        terrain-horizon model. Earth visibility represents geometric
        disk visibility, not communications availability.
      </p>
    </>
  )
}

function formatDuration(minutes) {
  const totalMinutes = Math.round(minutes)
  const days = Math.floor(totalMinutes / 1440)
  const hours = Math.floor((totalMinutes % 1440) / 60)
  const remainingMinutes = totalMinutes % 60

  const parts = []

  if (days) parts.push(`${days}d`)
  if (hours) parts.push(`${hours}h`)
  if (remainingMinutes) parts.push(`${remainingMinutes}m`)

  return parts.length ? parts.join(' ') : '0m'
}

function VisibilityWindowComparison({ selectedHeight }) {
  const [rows, setRows] = useState([])
  const [heightRows, setHeightRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    Promise.all([
      fetch('/data/visibility_window_summary.csv'),
      fetch('/data/nobile_rim_1_height_visibility_windows.csv'),
    ])
      .then(async ([summaryResponse, heightResponse]) => {
        if (!summaryResponse.ok || !heightResponse.ok) {
          throw new Error('Could not load visibility-window datasets.')
        }

        const [summaryText, heightText] = await Promise.all([
          summaryResponse.text(),
          heightResponse.text(),
        ])

        function parseRows(text) {
          const lines = text.trim().split(/\r?\n/)
          const headers = lines[0].split(',')

          return lines.slice(1).map((line) => {
            const values = line.split(',')
            const row = Object.fromEntries(
              headers.map((header, index) => [header, values[index]])
            )

            return {
              ...row,
              window_count: Number(row.window_count),
              longest_window_minutes: Number(row.longest_window_minutes),
              total_visible_minutes: Number(row.total_visible_minutes),
            }
          })
        }

        return {
          summary: parseRows(summaryText),
          heights: parseRows(heightText),
        }
      })
      .then(({ summary, heights }) => {
        if (!cancelled) {
          setRows(summary)
          setHeightRows(heights)
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return <p className="chart-footnote">Loading visibility-window analysis...</p>
  }

  if (error || !rows.length || !heightRows.length) {
    return (
      <section className="window-section">
        <p>{error || 'Visibility-window data unavailable.'}</p>
      </section>
    )
  }

  const sites = [
    { id: 'Nobile Rim 1', label: 'NOBILE RIM 1' },
    { id: 'Connecting Ridge', label: 'CONNECTING RIDGE' },
  ]

  const types = [
    { id: 'Solar visibility', label: 'SOLAR VISIBILITY' },
    { id: 'Earth disk visibility', label: 'EARTH DISK VISIBILITY' },
  ]

  function getResult(site, type) {
    if (site.id === 'Nobile Rim 1' && type.id === 'Solar visibility') {
      return heightRows.find(
        (row) => Number(row.observer_height_m) === selectedHeight
      )
    }

    return rows.find(
      (row) =>
        row.site === site.id &&
        row.visibility_type === type.id
    )
  }

  return (
    <>
      <section className="section-heading">
        <div>
          <p className="eyebrow">06 / VISIBILITY WINDOWS</p>
          <h2>Continuous visibility analysis</h2>
        </div>

        <span className="section-note">
          UTC · 30-minute observation bins
        </span>
      </section>

      <section className="window-section">
        <div className="window-header">
          <span>METRIC</span>
          <span>NOBILE RIM 1</span>
          <span>CONNECTING RIDGE</span>
        </div>

        {types.map((type) => (
          <div className="window-metric-group" key={type.id}>
            <h3>{type.label}</h3>

            <div className="window-grid">
              {sites.map((site) => {
                const result = getResult(site, type)

                if (!result) {
                  return (
                    <article className="window-card" key={site.id}>
                      <span>{site.label}</span>
                      <strong>Unavailable</strong>
                    </article>
                  )
                }

                const isHeightAware =
                  site.id === 'Nobile Rim 1' &&
                  type.id === 'Solar visibility'

                return (
                  <article className="window-card" key={site.id}>
                    <span>{site.label}</span>

                    {isHeightAware && (
                      <small className="window-height-label">
                        {selectedHeight} m observer height
                      </small>
                    )}

                    <div className="window-primary">
                      <strong>
                        {formatDuration(result.longest_window_minutes)}
                      </strong>
                      <small>Longest continuous window</small>
                    </div>

                    <div className="window-detail">
                      <span>Separate windows</span>
                      <strong>{result.window_count}</strong>
                    </div>

                    <div className="window-detail">
                      <span>Total visible time</span>
                      <strong>
                        {formatDuration(result.total_visible_minutes)}
                      </strong>
                    </div>

                    <div className="window-timestamp">
                      <span>FIRST VISIBLE BIN (UTC)</span>
                      <strong>
                        {result.longest_window_start_utc
                          .replace('T', ' ')
                          .replace('.000', '')}
                      </strong>
                    </div>

                    <div className="window-timestamp">
                      <span>LAST VISIBLE BIN (UTC)</span>
                      <strong>
                        {result.longest_window_end_utc
                          .replace('T', ' ')
                          .replace('.000', '')}
                      </strong>
                    </div>
                  </article>
                )
              })}
            </div>
          </div>
        ))}
      </section>

      <p className="chart-footnote">
        Nobile Rim 1 solar windows use the selected observer height.
        Connecting Ridge solar windows and both Earth visibility results
        use the 0 m reference datasets. Durations use 30-minute observation
        bins and are sampled estimates, not exact physical transition times.
        Earth visibility represents geometric disk visibility, not
        communications availability.
      </p>
    </>
  )
}

function ModelProvenance() {
  const sources = [
    {
      number: '01',
      title: 'SPICE ephemeris and lunar orientation',
      detail:
        'DE440s planetary ephemeris with DE421 lunar orientation and frame definitions. Used to calculate geometric Sun and Earth directions in the lunar reference frame.',
      tag: 'SPICE · DE440s + DE421',
    },
    {
      number: '02',
      title: 'Lunar terrain elevation',
      detail:
        'NASA Lunar Orbiter Laser Altimeter (LOLA) south-pole terrain products. The analysed surface elevation grids have 5 m pixel spacing.',
      tag: 'NASA LOLA · 5 m DEM',
    },
    {
      number: '03',
      title: 'Terrain horizon sampling',
      detail:
        'Terrain horizons are evaluated at 0.5° azimuth intervals using 2.5 m radial sampling of the bilinearly interpolated DEM. Maximum analysed radius is 9,975 m for Nobile Rim 1 and 7,975 m for Connecting Ridge.',
      tag: '0.5° AZIMUTH · 2.5 m RADIAL',
    },
    {
      number: '04',
      title: 'Mission time sampling',
      detail:
        'The analysis spans 14 November 2026 00:00 UTC through 13 December 2026 23:30 UTC, at 30-minute intervals, producing 1,441 observations per site.',
      tag: '30 DAYS · 30-MINUTE INTERVAL',
    },
    {
      number: '05',
      title: 'Observer-height scenarios',
      detail:
        'Nobile Rim 1 solar visibility is evaluated at 0, 0.5, 1, 2, 3 and 5 m above the terrain surface. Connecting Ridge currently uses its 0 m surface-reference scenario.',
      tag: '0–5 m · SCENARIO ANALYSIS',
    },
    {
      number: '06',
      title: 'Earth visibility interpretation',
      detail:
        'Earth is treated as an apparent angular disk and classified by geometric visibility against the local terrain horizon. This is not an RF link budget or a communications availability prediction.',
      tag: 'GEOMETRIC DISK VISIBILITY',
    },
  ]

  const limitations = [
    'Solar visibility does not directly quantify generated electrical energy.',
    'Earth visibility does not establish usable radio-frequency communications.',
    'Terrain horizons are limited to the available local DEM coverage.',
    'Thirty-minute sampling estimates visibility transitions; it does not locate their exact times.',
    'Observer-height scenarios do not model lander attitude, antenna geometry or equipment obstruction.',
    'Coordinate and reference-frame consistency with the source terrain products remains subject to independent verification.',
  ]

  return (
    <>
      <section className="section-heading">
        <div>
          <p className="eyebrow">07 / SCIENTIFIC BASIS</p>
          <h2>Model assumptions & data provenance</h2>
        </div>

        <span className="section-note">
          Sources · Sampling · Limitations
        </span>
      </section>

      <section className="provenance-grid">
        {sources.map((source) => (
          <article className="provenance-card" key={source.number}>
            <span className="provenance-number">{source.number}</span>
            <h3>{source.title}</h3>
            <p>{source.detail}</p>
            <span className="provenance-tag">{source.tag}</span>
          </article>
        ))}
      </section>

      <section className="limitations-card">
        <h3>Interpretation boundaries</h3>

        <ul>
          {limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      </section>
    </>
  )
}

function App() {
  const [selectedSite, setSelectedSite] = useState('nobile_rim_1')
  const [data, setData] = useState([])
  const [heightScenarios, setHeightScenarios] = useState([])
  const [selectedHeight, setSelectedHeight] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDate, setSelectedDate] = useState('2026-11-14')
  const [observationPage, setObservationPage] = useState(0)

  const site = SITES[selectedSite]

  useEffect(() => {
    let cancelled = false

    setLoading(true)
    setError('')
    setData([])
    setHeightScenarios([])
    setSelectedHeight(0)
    setObservationPage(0)
    setSelectedDate('2026-11-14')

    const requests = [
      fetch(site.missionFile).then((response) => {
        if (!response.ok) {
          throw new Error('Could not load mission dataset.')
        }

        return response.text()
      }),
    ]

    if (site.heightFile) {
      requests.push(
        fetch(site.heightFile).then((response) => {
          if (!response.ok) {
            throw new Error('Could not load lander-height scenarios.')
          }

          return response.text()
        })
      )
    }

    Promise.all(requests)
      .then(([missionText, heightText]) => {
        if (cancelled) return

        const missionRows = parseCSV(missionText)

        if (!missionRows.length) {
          throw new Error('Mission dataset is empty.')
        }

        setData(missionRows)
        setHeightScenarios(
          heightText ? parseHeightCSV(heightText) : []
        )
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [selectedSite, site.heightFile, site.missionFile])

  const selectedData = useMemo(() => {
    if (!data.length) return []

    if (!site.supportsHeightScenarios) {
      return data.map((item) => ({
        ...item,
        selectedHeight: 0,
      }))
    }

    if (!heightScenarios.length) return []

    const scenarioMap = new Map(
      heightScenarios
        .filter((item) => item.height === selectedHeight)
        .map((item) => [item.utc, item])
    )

    return data.map((item) => {
      const scenario = scenarioMap.get(item.utc)

      if (!scenario) return null

      return {
        ...item,
        horizon: scenario.horizon,
        terrainVisible: scenario.terrainVisible,
        selectedHeight,
      }
    }).filter(Boolean)
  }, [data, heightScenarios, selectedHeight, site])

  const stats = useMemo(() => {
    if (!selectedData.length || !data.length) return null

    const solarVisible = selectedData.filter(
      (d) => d.terrainVisible
    ).length

    const earthVisible = data.filter(
      (d) => d.earthVisibility !== 'not_visible'
    ).length

    const fullyVisible = data.filter(
      (d) => d.earthVisibility === 'fully_visible'
    ).length

    return {
      solarMin: Math.min(...selectedData.map((d) => d.solar)),
      solarMax: Math.max(...selectedData.map((d) => d.solar)),
      solarVisible,
      earthVisible,
      fullyVisible,
    }
  }, [data, selectedData])

  const dailyData = useMemo(() => {
    const observations = selectedData.filter(
      (item) => item.utc.slice(0, 10) === selectedDate,
    )

    if (!observations.length) return null

    const solarVisible = observations.filter(
      (item) => item.terrainVisible,
    ).length

    const earthVisible = observations.filter(
      (item) => item.earthVisibility !== 'not_visible'
    ).length

    const solarValues = observations.map((item) => item.solar)

    return {
      observations,
      solarPercent: (solarVisible / observations.length) * 100,
      earthPercent: (earthVisible / observations.length) * 100,
      minSolar: Math.min(...solarValues),
      maxSolar: Math.max(...solarValues),
    }
  }, [selectedData, selectedDate])

  const firstDate = data.length ? data[0].utc.slice(0, 10) : ''
  const lastDate = data.length
    ? data[data.length - 1].utc.slice(0, 10)
    : ''

  const pageSize = 12

  const totalPages = dailyData
    ? Math.ceil(dailyData.observations.length / pageSize)
    : 0

  const paginatedObservations = dailyData
    ? dailyData.observations.slice(
        observationPage * pageSize,
        (observationPage + 1) * pageSize,
      )
    : []

  if (loading) {
    return (
      <main className="loading-screen">
        Loading lunar mission environment...
      </main>
    )
  }

  if (error || !stats || !selectedData.length) {
    return (
      <main className="loading-screen error">
        {error || 'No mission data available.'}
      </main>
    )
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">L</div>

          <div>
            <strong>LUNA-RESOLVE</strong>
            <span>MISSION ENVIRONMENT ANALYSIS</span>
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot" />
          DATASET LOADED
        </div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">LUNAR SOUTH POLE / SITE EXPLORATION</p>

          <h1>{site.name}</h1>

          <p className="hero-description">
            A terrain-aware view of solar illumination and Earth visibility
            across a 30-day mission window.
          </p>

          <div className="site-tags">
            <span>{site.latitude}</span>
            <span>{site.longitude}</span>
            <span>MOON_ME</span>
          </div>
        </div>

        <div className="mission-window">
          <span>ANALYSIS WINDOW (UTC)</span>
          <strong>{formatDate(data[0].utc)}</strong>
          <span>TO</span>
          <strong>{formatDate(data[data.length - 1].utc)}</strong>

          <small>
            {data.length.toLocaleString('en-IN')} observations · 30-minute interval
          </small>
        </div>
      </section>

      <div className="daily-control site-control">
        <label htmlFor="site-selector">SELECT LANDING-SITE REGION</label>

        <select
          id="site-selector"
          value={selectedSite}
          onChange={(event) => setSelectedSite(event.target.value)}
        >
          {Object.entries(SITES).map(([id, item]) => (
            <option key={id} value={id}>
              {item.name}
            </option>
          ))}
        </select>
      </div>

      {/* 01 / MISSION SNAPSHOT */}

      <section className="section-heading">
        <div>
          <p className="eyebrow">01 / MISSION SNAPSHOT</p>
          <h2>Environmental overview</h2>
        </div>

        <span className="section-note">
          Based on current model outputs
        </span>
      </section>

      <section className="metrics-grid">
        <Metric
          label="TERRAIN-MODELLED SUN VISIBILITY"
          value={`${(
            (stats.solarVisible / selectedData.length) * 100
          ).toFixed(1)}%`}
          detail={`${stats.solarVisible} of ${selectedData.length} samples · ${selectedHeight} m observer height`}
        />

        <Metric
          label="EARTH DISK VISIBLE"
          value={`${(
            (stats.earthVisible / data.length) * 100
          ).toFixed(1)}%`}
          detail={`${stats.earthVisible} samples partially or fully visible · 0 m reference model`}
        />

        <Metric
          label="EARTH FULLY VISIBLE"
          value={`${stats.fullyVisible}`}
          detail="Full-disk visibility samples · 0 m reference model"
        />

        <Metric
          label="SOLAR ELEVATION RANGE"
          value={`${stats.solarMin.toFixed(2)}° to ${stats.solarMax.toFixed(2)}°`}
          detail="Geometric elevation"
        />
      </section>

      {/* 02 / TIME SERIES */}

      <section className="section-heading">
        <div>
          <p className="eyebrow">02 / TIME SERIES</p>
          <h2>Visibility conditions</h2>
        </div>

        <span className="section-note">30-minute sampling</span>
      </section>

      <section className="charts-grid">
        <article className="chart-card">
          <LineChart
            data={selectedData}
            valueKey="solar"
            color="#e9ad58"
            label="Solar elevation"
          />

          <p className="chart-footnote">
            Geometric Sun elevation relative to the local horizontal.
          </p>
        </article>

        <article className="chart-card">
          <LineChart
            data={selectedData}
            valueKey="earth"
            color="#69b8d1"
            label="Earth elevation"
          />

          <p className="chart-footnote">
            Earth-centre elevation. Disk visibility also accounts for its
            apparent angular radius and the local surface-reference terrain
            horizon model.
          </p>
        </article>
      </section>

      {/* 03 / VISIBILITY ANALYSIS */}

      <section className="section-heading">
        <div>
          <p className="eyebrow">03 / VISIBILITY ANALYSIS</p>
          <h2>30-day mission visibility timeline</h2>
        </div>

        <span className="section-note">
          UTC · 30-minute observations
        </span>
      </section>

      {site.supportsHeightScenarios && (
        <div className="height-control">
          <div>
            <label htmlFor="lander-height">
              OBSERVER HEIGHT ABOVE TERRAIN
            </label>

            <p>
              Compare terrain-aware solar visibility at different lander heights.
            </p>
          </div>

          <select
            id="lander-height"
            value={selectedHeight}
            onChange={(event) => {
              setSelectedHeight(Number(event.target.value))
              setObservationPage(0)
            }}
          >
            <option value={0}>0 metres · Surface reference</option>
            <option value={0.5}>0.5 metres</option>
            <option value={1}>1 metre</option>
            <option value={2}>2 metres</option>
            <option value={3}>3 metres</option>
            <option value={5}>5 metres</option>
          </select>
        </div>
      )}

      <div className="daily-control">
        <label htmlFor="mission-date">SELECT MISSION DATE</label>

        <input
          id="mission-date"
          type="date"
          min={firstDate}
          max={lastDate}
          value={selectedDate}
          onChange={(event) => {
            setSelectedDate(event.target.value)
            setObservationPage(0)
          }}
        />
      </div>

      {dailyData && (
        <div className="daily-summary">
          <div className="daily-stat">
            <span>Solar visibility</span>
            <strong>{dailyData.solarPercent.toFixed(1)}%</strong>
          </div>

          <div className="daily-stat">
            <span>Earth visibility</span>
            <strong>{dailyData.earthPercent.toFixed(1)}%</strong>
          </div>

          <div className="daily-stat">
            <span>Minimum solar elevation</span>
            <strong>{dailyData.minSolar.toFixed(2)}°</strong>
          </div>

          <div className="daily-stat">
            <span>Maximum solar elevation</span>
            <strong>{dailyData.maxSolar.toFixed(2)}°</strong>
          </div>

          <div className="daily-stat">
            <span>Observations</span>
            <strong>{dailyData.observations.length}</strong>
          </div>
        </div>
      )}

      {dailyData && (
        <section className="observation-section">
          <h3>Selected-day observations</h3>
          <p>UTC · 30-minute sampling interval</p>

          <div className="observation-table-wrapper">
            <table className="observation-table">
              <thead>
                <tr>
                  <th>UTC timestamp</th>
                  <th>Solar elevation</th>
                  <th>Solar azimuth</th>
                  <th>Effective horizon</th>
                  <th>Solar visibility</th>
                  <th>Earth visibility</th>
                </tr>
              </thead>

              <tbody>
                {paginatedObservations.map((item) => (
                  <tr key={item.utc}>
                    <td>
                      {item.utc.replace('T', ' ').replace('.000', '')}
                    </td>
                    <td>{item.solar.toFixed(3)}°</td>
                    <td>{item.solarAzimuth.toFixed(3)}°</td>
                    <td>{item.horizon.toFixed(3)}°</td>
                    <td>
                      {item.terrainVisible ? 'Visible' : 'Blocked'}
                    </td>
                    <td>
                      {item.earthVisibility.replace('_', ' ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination-controls">
            <button
              onClick={() =>
                setObservationPage((page) => Math.max(0, page - 1))
              }
              disabled={observationPage === 0}
            >
              Previous
            </button>

            <span>
              Page {observationPage + 1} of {totalPages}
            </span>

            <button
              onClick={() =>
                setObservationPage((page) =>
                  Math.min(totalPages - 1, page + 1)
                )
              }
              disabled={observationPage >= totalPages - 1}
            >
              Next
            </button>
          </div>
        </section>
      )}

      <VisibilityTimeline data={selectedData} />

      {/* 04 / MODEL INTERPRETATION */}

      <section className="section-heading">
        <div>
          <p className="eyebrow">04 / MODEL INTERPRETATION</p>
          <h2>What these results represent</h2>
        </div>
      </section>

      <section className="interpretation-grid">
        <article className="info-card">
          <span className="info-index">01</span>
          <h3>Solar illumination</h3>

          <p>
            Solar visibility is classified by comparing geometric solar
            elevation against the effective local terrain horizon for the
            selected observer height.
          </p>

          <span className="info-status">
            {site.supportsHeightScenarios
              ? 'HEIGHT-AWARE TERRAIN MODEL'
              : 'SURFACE-REFERENCE TERRAIN MODEL'}
          </span>
        </article>

        <article className="info-card">
          <span className="info-index">02</span>
          <h3>Earth visibility</h3>

          <p>
            The Earth disk is classified as fully visible, partially visible,
            or not visible using its apparent angular radius. Current Earth
            visibility results use the original 0 m surface-reference model.
          </p>

          <span className="info-status">GEOMETRIC DISK MODEL</span>
        </article>

        <article className="info-card">
          <span className="info-index">03</span>
          <h3>Model limitations</h3>

          <p>
            Visibility does not establish usable electrical power or an
            available communications link. RF and power-system constraints
            are not modelled here.
          </p>

          <span className="info-status">
            DECISION SUPPORT · NOT CERTIFICATION
          </span>
        </article>
      </section>

      {/* 05 / SITE COMPARISON */}

      <SiteComparison />

      {/* 06 / VISIBILITY WINDOWS */}

      <VisibilityWindowComparison selectedHeight={selectedHeight} />

      {/* 07 / SCIENTIFIC BASIS */}

      <ModelProvenance />

      <footer className="footer">
        <span>LUNA-RESOLVE · LUNAR MISSION ANALYSIS</span>
        <span>Reference location · {site.name}</span>
      </footer>
    </main>
  )
}

export default App