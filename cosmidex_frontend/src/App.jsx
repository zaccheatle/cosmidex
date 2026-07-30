import { useState, useEffect, useMemo } from 'react'
import Tooltip from './components/Tooltip'
import ChatShell from './components/ChatShell'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
const API_KEY = import.meta.env.VITE_API_KEY

const TIER_OPTIONS = ['All', 'Tier 1', 'Tier 2', 'Tier 3', 'Non-Habitable']

const TIER_DESCRIPTIONS = {
  'All': 'Show every planet in the current top-25 list',
  'Tier 1': 'Strong candidate — rocky, in the conservative habitable zone, stable orbit, F/G/K star',
  'Tier 2': 'Moderate candidate — rocky, in the habitable zone, includes M dwarf systems',
  'Tier 3': 'In the habitable zone only — larger or less Earth-like composition',
  'Non-Habitable': 'Outside the habitable zone, gas giant, or orbiting an unstable/evolved star',
}

const SORT_OPTIONS = [
  { value: 'esi_score', label: 'ESI Score' },
  { value: 'planet_name', label: 'Name' },
  { value: 'star_distance_light_years', label: 'Distance' },
  { value: 'equilibrium_temp_celsius', label: 'Temperature' },
]

const HZ_LABELS = {
  'conservative_hz': 'Conservative',
  'optimistic_hz': 'Optimistic',
  'outside_hz': 'Outside HZ',
}

const TIER_CONTEXT = {
  'Tier 1': 'Strong Earth analog',
  'Tier 2': 'Moderate candidate',
  'Tier 3': 'In the habitable zone only',
  'Non-Habitable': 'Outside the habitable zone',
}

// Our solar system's planets, for "where would this fall in our system" context
const SOLAR_SYSTEM_ORBIT_AU = [
  { name: 'Mercury', value: 0.39, unit: 'AU' },
  { name: 'Venus', value: 0.72, unit: 'AU' },
  { name: 'Earth', value: 1.00, unit: 'AU' },
  { name: 'Mars', value: 1.52, unit: 'AU' },
  { name: 'Jupiter', value: 5.20, unit: 'AU' },
  { name: 'Saturn', value: 9.58, unit: 'AU' },
  { name: 'Uranus', value: 19.2, unit: 'AU' },
  { name: 'Neptune', value: 30.1, unit: 'AU' },
]

const SOLAR_SYSTEM_ORBIT_DAYS = [
  { name: 'Mercury', value: 88, unit: 'days' },
  { name: 'Venus', value: 225, unit: 'days' },
  { name: 'Earth', value: 365, unit: 'days' },
  { name: 'Mars', value: 687, unit: 'days' },
  { name: 'Jupiter', value: 4333, unit: 'days' },
  { name: 'Saturn', value: 10759, unit: 'days' },
  { name: 'Uranus', value: 30687, unit: 'days' },
  { name: 'Neptune', value: 60190, unit: 'days' },
]

function solarSystemPosition(rawValue, table, noun) {
  const value = Number(rawValue)
  if (rawValue == null || Number.isNaN(value)) return 'No orbital data available'

  const first = table[0]
  const last = table[table.length - 1]

  if (value < first.value) {
    const pct = Math.round((value / first.value) * 100)
    return `${pct}% of ${first.name}'s ${noun} (${first.value} ${first.unit})`
  }
  if (value > last.value) {
    const multiple = (value / last.value).toFixed(1)
    return `${multiple}× ${last.name}'s ${noun} (${last.value} ${last.unit})`
  }
  for (let i = 0; i < table.length - 1; i++) {
    if (value >= table[i].value && value <= table[i + 1].value) {
      return `Between ${table[i].name} (${table[i].value} ${table[i].unit}) and ${table[i + 1].name} (${table[i + 1].value} ${table[i + 1].unit})`
    }
  }
  return 'No orbital data available'
}

function planetGravityMs2(massEarth, radiusEarth) {
  if (massEarth == null || radiusEarth == null || radiusEarth === 0) return null
  return (massEarth / (radiusEarth ** 2)) * 9.81
}

function planetEscapeVelocityKms(massEarth, radiusEarth) {
  if (massEarth == null || radiusEarth == null || radiusEarth <= 0) return null
  return Math.sqrt(massEarth / radiusEarth) * 11.2
}

function apiFetch(path) {
  return fetch(`${API_BASE_URL}${path}`, {
    headers: { 'X-API-Key': API_KEY },
  }).then(res => {
    if (!res.ok) {
      throw new Error(`Request failed (${res.status})`)
    }
    return res.json()
  })
}

function App() {
  const [planets, setPlanets] = useState([])
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState(null)

  const [selectedTier, setSelectedTier] = useState('All')
  const [sortBy, setSortBy] = useState('esi_score')
  const [sortDir, setSortDir] = useState('desc')
  const [currentIndex, setCurrentIndex] = useState(0)

  const [currentPlanet, setCurrentPlanet] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState(null)

  // Fetch the top-25 planet list once on mount
  useEffect(() => {
    setListLoading(true)
    setListError(null)
    apiFetch('/planets?limit=25')
      .then(data => setPlanets(data))
      .catch(err => setListError(err.message))
      .finally(() => setListLoading(false))
  }, [])

  const availableTiers = useMemo(
    () => TIER_OPTIONS.filter(
      tier => tier === 'All' || planets.some(p => p.habitability_tier === tier)
    ),
    [planets]
  )

  const filteredPlanets = useMemo(() => {
    const filtered = selectedTier === 'All'
      ? planets
      : planets.filter(p => p.habitability_tier === selectedTier)

    const sorted = [...filtered].sort((a, b) => {
      const aVal = a[sortBy]
      const bVal = b[sortBy]
      if (aVal == null) return 1
      if (bVal == null) return -1

      const compared = typeof aVal === 'string'
        ? aVal.localeCompare(bVal)
        : aVal - bVal

      return sortDir === 'asc' ? compared : -compared
    })

    return sorted
  }, [planets, selectedTier, sortBy, sortDir])

  // Reset to the first planet whenever the filtered/sorted list changes shape
  useEffect(() => {
    setCurrentIndex(0)
  }, [selectedTier, sortBy, sortDir])

  const currentSummary = filteredPlanets[currentIndex]

  // Fetch full detail for the currently displayed planet
  useEffect(() => {
    if (!currentSummary) {
      setCurrentPlanet(null)
      return
    }

    let cancelled = false
    setDetailLoading(true)
    setDetailError(null)

    apiFetch(`/planets/${encodeURIComponent(currentSummary.planet_name)}`)
      .then(data => {
        if (!cancelled) setCurrentPlanet(data)
      })
      .catch(err => {
        if (!cancelled) setDetailError(err.message)
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [currentSummary])

  return (
    <div className="app">

      <div className="top-bar">
        <div className="top-left">
          <h1>🌌 CosmiDex: A Codex for the Cosmos</h1>
        </div>
        <div className="top-right">
          <div className="filter-section">
            <span className="filter-label">Habitability Tier:</span>
            <nav className="tier-filter">
              {availableTiers.map(tier => (
                <button
                  key={tier}
                  title={TIER_DESCRIPTIONS[tier]}
                  className={`tier-btn ${selectedTier === tier ? 'active' : ''}`}
                  onClick={() => setSelectedTier(tier)}
                >
                  {tier}
                </button>
              ))}
            </nav>
          </div>
          <div className="sort-section">
            <span className="filter-label">Sort:</span>
            <select value={sortBy} onChange={e => setSortBy(e.target.value)}>
              {SORT_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <button
              className="sort-dir-btn"
              onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}
              title={sortDir === 'asc' ? 'Ascending' : 'Descending'}
            >
              {sortDir === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>
      </div>

      {listLoading && (
        <div className="state-message">Loading planets…</div>
      )}

      {listError && (
        <div className="state-message state-error">Couldn't load planets: {listError}</div>
      )}

      {!listLoading && !listError && filteredPlanets.length === 0 && (
        <div className="state-message">No planets match this filter.</div>
      )}

      {!listLoading && !listError && filteredPlanets.length > 0 && (
        <>
          <main className="viewer">
            <div className="left-panel">
              <div className="planet-image">
                {detailLoading && <div className="state-message">Loading…</div>}
                {!detailLoading && currentPlanet?.image_url && (
                  <img src={currentPlanet.image_url} alt={currentPlanet.planet_name} />
                )}
                {!detailLoading && currentPlanet && !currentPlanet.image_url && (
                  <div className="state-message">No image generated yet for this planet.</div>
                )}
              </div>
            </div>

            <div className="right-panel">
              <div className="planet-stats">
                {detailError && (
                  <div className="state-message state-error full-width">
                    Couldn't load planet detail: {detailError}
                  </div>
                )}

                {!detailError && currentPlanet && (
                  <>
                    <h2>{currentPlanet.planet_name}<Tooltip text="Planet name — most exoplanets are named after their host star with a letter suffix; b for the first planet discovered, c for the second, and so on."/></h2>
                      {currentPlanet.description && (
                        <p className="planet-description full-width">{currentPlanet.description}</p>
                      )}

                    <hr />
                      <p className="section-label full-width">Discovery</p>

                      <p>Discovery Facility<Tooltip text="The observatory or mission that discovered this planet — e.g. a ground-based observatory or a space telescope like Kepler or TESS." />
                        : <span>{currentPlanet.discovery_facility ?? 'Unknown'}</span></p>
                      <p>Discovery Instrument<Tooltip text="The specific instrument used to detect this planet, such as a spectrograph or CCD photometer." />
                        : <span>{currentPlanet.discovery_instrument ?? 'Unknown'}</span></p>

                      <p>Discovery Locale<Tooltip text="Whether this planet was discovered from a ground-based observatory or a space-based telescope." />
                        : <span>{currentPlanet.discovery_locale ?? 'Unknown'}</span></p>
                      <p>Discovery Method<Tooltip text="How this planet was detected. Transit = planet passes in front of its star, dimming the light slightly — used by Kepler and TESS. Radial Velocity = the planet's gravity causes the star to wobble, detected by Doppler shift. Direct Imaging = the planet is photographed directly, only possible for large planets far from their star. Microlensing = a passing star's gravity bends and magnifies light, briefly revealing a planet." />
                        : <span>{currentPlanet.discovery_method ?? 'Unknown'}</span></p>

                      <p>Discovery Telescope<Tooltip text="The specific telescope used to detect this planet." />
                        : <span>{currentPlanet.discovery_telescope ?? 'Unknown'}</span></p>
                      <p>Discovery Year<Tooltip text="The year this planet was confirmed. The first exoplanet around a Sun-like star was discovered in 1995. The Kepler Space Telescope launched in 2009 & revolutionized the field — most confirmed exoplanets were found by Kepler. The TESS mission launched in 2018 continues the search today." />
                        : <span>{currentPlanet.discovery_year ?? 'Unknown'}</span></p>

                    <hr />
                      <p className="section-label">Characteristics</p>
                      <p className="section-label context-label">Earth Context</p>

                      <p>Composition<Tooltip text="Estimated composition based on planet density. Rock/Iron and Rock/Silicate are Earth-like rocky worlds. Water/Ice indicates a lower-density world possibly rich in water or ice. Ice Giant and Gas Giant are Neptune- and Jupiter-like worlds with no solid surface." />
                        : <span>{currentPlanet.planet_composition}</span></p>
                      <p className="context-chunk">Earth: Rock/Silicate</p>

                      <p>Earth Similarity Index<Tooltip text="ESI measures how physically similar this planet is to Earth. Combines radius, density, escape velocity and surface temperature. 1.0 = identical to Earth, 0 = completely alien." />
                        : <span>{currentPlanet.esi_score != null ? currentPlanet.esi_score.toFixed(3) : 'Unknown'}</span></p>
                      <p className="context-chunk">1.0 = identical to Earth</p>

                      <p>Escape Velocity<Tooltip text="The minimum speed needed to escape this planet's gravitational pull without further propulsion. Earth's escape velocity is 11.2 km/s." />
                        : <span>{(() => {
                            const v = planetEscapeVelocityKms(currentPlanet.planet_mass_earth, currentPlanet.planet_radius_earth)
                            return v != null ? `${v.toFixed(1)} km/s` : 'Unknown'
                          })()}</span></p>
                      <p className="context-chunk">{(() => {
                            const v = planetEscapeVelocityKms(currentPlanet.planet_mass_earth, currentPlanet.planet_radius_earth)
                            return v != null ? `${(v / 11.2).toFixed(2)}× Earth (11.2 km/s)` : 'Earth: 11.2 km/s'
                          })()}</p>

                      <p>Gravity<Tooltip text="Surface gravity. Calculated from the planet's mass and radius. Affects whether humans could walk on the surface and whether the planet can hold an atmosphere." />
                        : <span>{(() => {
                            const g = planetGravityMs2(currentPlanet.planet_mass_earth, currentPlanet.planet_radius_earth)
                            return g != null ? `${g.toFixed(2)} m/s²` : 'Unknown'
                          })()}</span></p>
                      <p className="context-chunk">{(() => {
                            const g = planetGravityMs2(currentPlanet.planet_mass_earth, currentPlanet.planet_radius_earth)
                            return g != null ? `${(g / 9.81).toFixed(2)}× Earth (9.81 m/s²)` : 'Earth: 9.81 m/s²'
                          })()}</p>

                      <p>Radius<Tooltip text="Planet radius. Earth's radius is 6,371 km." />
                        : <span>{currentPlanet.planet_radius_earth != null ? `${Math.round(currentPlanet.planet_radius_earth * 6371).toLocaleString()} km` : 'Unknown'}</span></p>
                      <p className="context-chunk">{currentPlanet.planet_radius_earth != null ? `${currentPlanet.planet_radius_earth.toFixed(2)}× Earth (6,371 km)` : 'Earth: 6,371 km'}</p>

                      <p>Size Class<Tooltip text="Size classification based on planet radius compared to solar system bodies. Super Earths are the most common planet type in the galaxy yet our solar system has none — we don't fully understand why." />
                        : <span>{currentPlanet.planet_size_class}</span></p>
                      <p className="context-chunk">Earth: Terrestrial - Earth sized</p>

                    <hr />
                      <p className="section-label">Habitability</p>
                      <p className="section-label context-label">Earth Context</p>

                      <p>Habitability Tier<Tooltip text="Our habitability classification. Tier 1 = strong Earth analog — rocky, in the conservative habitable zone, Earth-like ESI, stable orbit around a G or K type star. Tier 2 = moderate candidate with good ESI and in the habitable zone. Tier 3 = in the habitable zone but less Earth-like physically. Non-habitable = outside the zone or gas giant." />
                        : <span>{currentPlanet.habitability_tier}</span></p>
                      <p className="context-chunk">{TIER_CONTEXT[currentPlanet.habitability_tier] ?? 'Unknown'}</p>

                      <p>Habitable Zone<Tooltip text="The conservative zone is where liquid water is almost certainly stable. The optimistic zone extends further — water is possible but less certain." />
                        : <span>{HZ_LABELS[currentPlanet.hz_membership] || currentPlanet.hz_membership}</span></p>
                      <p className="context-chunk">Earth: Conservative HZ</p>

                      <p>Habitable Zone Distance<Tooltip text="Where the planet sits within its star's habitable zone. 0 = perfect center, -1 = inner edge, +1 = outer edge. Beyond ±1 means outside the zone." />
                        : <span>{currentPlanet.hzd_score != null ? currentPlanet.hzd_score.toFixed(3) : 'Unknown'}</span></p>
                      <p className="context-chunk">Earth: ≈0 (center of Sun's HZ)</p>

                      <p>Planet Equilibrium Temperature<Tooltip text="The equilibrium temperature of a planet is a theoretical value representing the temperature it would have if it were a perfect blackbody heated only by its parent star, without an atmosphere or greenhouse effect. Earth's equilibrium temp is -5°C / 23°F but actual average is 15°C / 59°F due to greenhouse warming." />
                        : <span>{currentPlanet.equilibrium_temp_fahrenheit}°F | {currentPlanet.equilibrium_temp_celsius}°C</span></p>
                      <p className="context-chunk">{currentPlanet.estimated_planet_climate ?? 'Unknown'}</p>

                    <hr />
                      <p className="section-label">Orbit</p>
                      <p className="section-label context-label">Earth Context</p>

                      <p>Orbital Distance<Tooltip text="Distance from the planet to its host star, measured in AU. 1 AU is the distance from Earth to our Sun — about 150 million km." />
                        : <span>{currentPlanet.orbital_distance_description}</span></p>
                      <p className="context-chunk">{solarSystemPosition(currentPlanet.orbital_semi_major_axis_au, SOLAR_SYSTEM_ORBIT_AU, 'distance')} (Earth: 1 AU)</p>

                      <p>Orbital Eccentricity<Tooltip text="How circular or elliptical the planet's orbit is. 0 = perfect circle, 1 = extremely elongated. Earth's eccentricity is 0.017 — nearly circular." />
                        : <span>{currentPlanet.orbital_eccentricity != null ? currentPlanet.orbital_eccentricity.toFixed(3) : 'Unknown'}</span></p>
                      <p className="context-chunk">Earth: 0.017 (nearly circular)</p>

                      <p>Orbital Period<Tooltip text="How long it takes this planet to complete one full orbit around its star. Earth's year is 365.25 days." />
                        : <span>{currentPlanet.year_length}</span></p>
                      <p className="context-chunk">{solarSystemPosition(currentPlanet.orbital_period_days, SOLAR_SYSTEM_ORBIT_DAYS, 'orbital period')} (Earth: 365.25 days)</p>

                      <p>Orbital Stability<Tooltip text="How stable the planet's orbit is. Stable = nearly circular like Earth, stable temperatures year-round. Moderate = some seasonal variation. Unstable = extreme temperature swings as the planet swings close to and far from its star, making liquid water unlikely." />
                        : <span>{currentPlanet.orbital_stability}</span></p>
                      <p className="context-chunk">Earth: Stable</p>

                    <hr />
                      <p className="section-label">Host System</p>
                      <p className="section-label context-label">Solar System Context</p>

                      <p>Host Star<Tooltip text="The star this planet orbits." />
                        : <span>{currentPlanet.host_star_name}</span></p>
                      <p className="context-chunk">Our Sun: Sol</p>

                      <p>Host Star Age<Tooltip text="Age of the host star in billions of years. Our Sun is 4.6 billion years old with roughly 5 billion years remaining." />
                        : <span>{currentPlanet.star_age_description}</span></p>
                      <p className="context-chunk">Our Sun: 4.6 billion years</p>

                      <p>Host Star Distance From Earth<Tooltip text="Distance of host star from Earth. 1 light year = 9.46 trillion km." />
                        : <span>{currentPlanet.star_distance_light_years != null ? `${currentPlanet.star_distance_light_years.toFixed(1)} light years` : 'Unknown'}</span></p>
                      <p className="context-chunk">Time to reach our Sun: ~8 minutes</p>

                      <p>Host Star Temperature<Tooltip text="The surface temperature of the host star in Kelvin. For reference: a candle flame burns at ~3,000K, our Sun is 5,778K, and a lightning bolt reaches ~30,000K." />
                        : <span>{currentPlanet.stellar_effective_temp_k != null ? `${currentPlanet.stellar_effective_temp_k.toLocaleString()}K (${currentPlanet.star_temp_description})` : 'Unknown'}</span></p>
                      <p className="context-chunk">Our Sun: 5,778K (as hot as an electric arc welder)</p>

                      <p>Host Star Type<Tooltip text="Spectral classification of the host star, based on surface temperature."/>
                        : <span>{currentPlanet.star_spectral_type}</span></p>
                      <p className="context-chunk">Our Sun: Class G - Yellow</p>

                      <p>Shuttle Travel Distance From Earth<Tooltip text="Approx. travel time from Earth to host star travelling at the Space Shuttle's top speed of 28,000 km/h — the fastest crewed vehicle humans have built." />
                        : <span>{currentPlanet.shuttle_travel_description}</span></p>
                      <p className="context-chunk">Time to reach our Sun: ~223 Earth days</p>
                  </>
                )}
              </div>
            </div>
          </main>

          <footer className="navigation">
            <button onClick={() => setCurrentIndex(i => i - 1)} disabled={currentIndex === 0}>
              ← Previous
            </button>
            <span>{currentIndex + 1} / {filteredPlanets.length}</span>
            <button onClick={() => setCurrentIndex(i => i + 1)} disabled={currentIndex === filteredPlanets.length - 1}>
              Next →
            </button>
          </footer>
        </>
      )}

      <ChatShell />

    </div>
  )
}

export default App
