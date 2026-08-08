import { useState, useEffect, useMemo } from 'react'
import Tooltip from './components/Tooltip'
import ChatShell from './components/ChatShell'
import OrbitScale from './components/OrbitScale'
import MethodologyPage from './components/MethodologyPage'
import LandingPage from './components/LandingPage'
import EntityOverview from './components/EntityOverview'
import AboutPage from './components/AboutPage'
import { apiFetch } from './api'
import './App.css'

// Constellations and Our Solar System will be added here once those datasets exist.
const ENTITY_OPTIONS = ['Exoplanets']

const TIER_OPTIONS = ['All', 'Tier 1', 'Tier 2', 'Tier 3']

const TIER_DESCRIPTIONS = {
  'All': 'Every potentially habitable planet — Tier 1, 2, or 3',
  'Tier 1': 'Strong candidate — rocky, in the conservative habitable zone, stable orbit, F/G/K star',
  'Tier 2': 'Moderate candidate — rocky, in the habitable zone, includes M dwarf systems',
  'Tier 3': 'In the habitable zone only — larger or less Earth-like composition',
}

const HZ_LABELS = {
  'conservative_hz': 'Conservative',
  'optimistic_hz': 'Optimistic',
  'outside_hz': 'Outside HZ',
}

/**
 * Compute a planet's surface gravity from its mass and radius, scaled to Earth's 9.81 m/s².
 *
 * @param massEarth - Planet mass in Earth masses.
 * @param radiusEarth - Planet radius in Earth radii.
 * @returns Surface gravity in m/s², or null if either input is missing/zero.
 */
function planetGravityMs2(massEarth, radiusEarth) {
  if (massEarth == null || radiusEarth == null || radiusEarth === 0) return null
  return (massEarth / (radiusEarth ** 2)) * 9.81
}

/**
 * Compute a planet's escape velocity from its mass and radius, scaled to Earth's 11.2 km/s.
 *
 * @param massEarth - Planet mass in Earth masses.
 * @param radiusEarth - Planet radius in Earth radii.
 * @returns Escape velocity in km/s, or null if either input is missing/non-positive.
 */
function planetEscapeVelocityKms(massEarth, radiusEarth) {
  if (massEarth == null || radiusEarth == null || radiusEarth <= 0) return null
  return Math.sqrt(massEarth / radiusEarth) * 11.2
}

/**
 * Root application component: fetches the habitable-planet list and the
 * currently-selected planet's detail, and renders the entity/tier filters,
 * planet viewer (comparison image + stats panel), navigation, chat shell,
 * and methodology overlay.
 *
 * @returns The CosmiDex application shell.
 */
function App() {
  const [planets, setPlanets] = useState([])
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState(null)

  const [selectedEntity, setSelectedEntity] = useState('Exoplanets')
  const [selectedTier, setSelectedTier] = useState('All')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [atEntityIntro, setAtEntityIntro] = useState(true)

  const [currentPlanet, setCurrentPlanet] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState(null)

  const [showAbout, setShowAbout] = useState(false)
  const [showMethodology, setShowMethodology] = useState(false)
  const [showLanding, setShowLanding] = useState(true)

  // Fetch every potentially habitable planet (Tier 1/2/3) once on mount
  useEffect(() => {
    setListLoading(true)
    setListError(null)
    apiFetch('/planets?tier=Habitable&limit=100')
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

    return [...filtered].sort((a, b) => a.planet_name.localeCompare(b.planet_name))
  }, [planets, selectedTier])

  // Reset to the first planet whenever the filtered list changes shape
  useEffect(() => {
    setCurrentIndex(0)
  }, [selectedTier])

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

  if (showLanding) {
    return (
      <>
        <LandingPage
          onEnter={() => setShowLanding(false)}
          onShowAbout={() => setShowAbout(true)}
        />
        {showMethodology && <MethodologyPage onClose={() => setShowMethodology(false)} />}
        {showAbout && <AboutPage onClose={() => setShowAbout(false)} />}
      </>
    )
  }

  return (
    <div className="app">

      <div className="top-bar">
        <div className="top-left">
          <h1>🌌 Cosmidex: A Codex for the Cosmos</h1>
          <div className="header-link-group">
            <button className="methodology-link" title="Return to the Cosmidex home page" onClick={() => { setShowLanding(true); setAtEntityIntro(true) }}>
              Launch Pad
            </button>
            <button className="methodology-link" title="The methodology and data sources powering this project" onClick={() => setShowMethodology(true)}>
              Methodology &amp; Sources
            </button>
          </div>
        </div>
        <div className="top-right">
          <div className="filter-section">
            <span className="filter-label">Cosmic Entity:</span>
            <nav className="entity-filter">
              {ENTITY_OPTIONS.map(entity => (
                <button
                  key={entity}
                  title={entity === 'Exoplanets' ? 'NASA confirmed planets in the Milky Way that orbit a star other than our Sun.' : 'Coming soon'}
                  className={`entity-btn ${selectedEntity === entity ? 'active' : ''}`}
                  disabled={entity !== 'Exoplanets'}
                  onClick={() => { setSelectedEntity(entity); setAtEntityIntro(true) }}
                >
                  {entity}
                </button>
              ))}
            </nav>
          </div>
          {selectedEntity === 'Exoplanets' && (
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
          )}
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
          {atEntityIntro && (
            <EntityOverview entity={selectedEntity} planets={planets} listLoading={listLoading} />
          )}

          {!atEntityIntro && (
          <main className="viewer">
            <div className="left-panel">
              <div className="image-section">
                <div className="planet-image">
                  <p className="orbit-scale-title image-section-title-overlay">
                    Size Comparison vs. Earth
                    {currentPlanet && (
                      <Tooltip text={<><span className="tooltip-highlight">{currentPlanet.planet_name}</span> (right) rendered next to Earth (left), scaled to the real measured radius ratio between the two. {(() => {
                        const r = currentPlanet.planet_radius_earth
                        if (r == null) return null
                        const pct = (r * 100).toFixed(0)
                        const volumeRatio = r ** 3
                        const fitText = volumeRatio >= 1
                          ? `you could fit ~${volumeRatio.toFixed(1)} Earths inside it`
                          : `it would fit inside Earth ~${(1 / volumeRatio).toFixed(1)}x over`
                        return `Its radius is ${pct}% of Earth's — ${fitText}.`
                      })()}</>} />
                    )}
                  </p>
                  {detailLoading && <div className="state-message">Loading…</div>}
                  {!detailLoading && currentPlanet && currentPlanet.image_url && (
                    <>
                      <img src={currentPlanet.image_url} alt={currentPlanet.planet_name} />
                      <span className="ai-generated-note">*AI-generated image</span>
                    </>
                  )}
                  {!detailLoading && currentPlanet && !currentPlanet.image_url && (
                    <div className="state-message">No image generated yet for this planet.</div>
                  )}
                </div>
              </div>
            </div>

            <div className="right-panel">
              <div className="planet-stats">
                {detailError && (
                  <div className="state-message state-error">
                    Couldn't load planet detail: {detailError}
                  </div>
                )}

                {!detailError && currentPlanet && (
                  <>
                    <h2>{currentPlanet.planet_name}<Tooltip text="Planet name — most exoplanets are named after their host star with a letter suffix; b for the first planet discovered, c for the second, and so on."/></h2>
                      {currentPlanet.description && (
                        <p className="planet-description">
                          {currentPlanet.description}
                          <span className="ai-generated-note-inline"> *AI-generated description</span>
                        </p>
                      )}

                    <hr />
                      <p className="section-label">Characteristics<Tooltip text="The planet's physical properties — composition, size, gravity, and how they compare to Earth's." /></p>
                      <div className="stat-columns">
                        <p>Estimated Composition<Tooltip text="Estimated composition based on planet density. Rock/Iron and Rock/Silicate are Earth-like rocky worlds. Water/Ice indicates a lower-density world possibly rich in water or ice. Ice Giant and Gas Giant are Neptune- and Jupiter-like worlds with no solid surface." />
                          : <span>{currentPlanet.planet_composition}</span></p>
                        <p>Earth Similarity Index<Tooltip text="ESI measures how physically similar this planet is to Earth. Combines radius, density, escape velocity and surface temperature. 1.0 = identical to Earth, 0 = completely alien." />
                          : <span>{currentPlanet.esi_score != null ? currentPlanet.esi_score.toFixed(3) : 'Unknown'}</span></p>
                        <p>Escape Velocity<Tooltip text="The minimum speed needed to escape this planet's gravitational pull without further propulsion. Earth's escape velocity is 11.2 km/s." />
                          : <span>{(() => {
                              const v = planetEscapeVelocityKms(currentPlanet.planet_mass_earth, currentPlanet.planet_radius_earth)
                              return v != null ? `${v.toFixed(1)} km/s` : 'Unknown'
                            })()}</span></p>
                        <p>Gravity<Tooltip text="Surface gravity. Calculated from the planet's mass and radius. Affects whether humans could walk on the surface and whether the planet can hold an atmosphere." />
                          : <span>{(() => {
                              const g = planetGravityMs2(currentPlanet.planet_mass_earth, currentPlanet.planet_radius_earth)
                              return g != null ? `${g.toFixed(2)} m/s²` : 'Unknown'
                            })()}</span></p>
                        <p>Radius<Tooltip text="Planet radius. Earth's radius is 6,371 km." />
                          : <span>{currentPlanet.planet_radius_earth != null ? `${Math.round(currentPlanet.planet_radius_earth * 6371).toLocaleString()} km` : 'Unknown'}</span></p>
                        <p>Size Class<Tooltip text="Size classification based on planet radius compared to solar system bodies. Super Earths are the most common planet type in the galaxy yet our solar system has none — we don't fully understand why." />
                          : <span>{currentPlanet.planet_size_class}</span></p>
                      </div>

                    <hr />
                      <p className="section-label">Discovery<Tooltip text="How, when, and with what this planet was found." /></p>
                      <div className="stat-columns">
                        <p>Discovery Facility<Tooltip text="The observatory or mission that discovered this planet — e.g. a ground-based observatory or a space telescope like Kepler or TESS." />
                          : <span>{currentPlanet.discovery_facility ?? 'Unknown'}</span></p>
                        <p>Discovery Instrument<Tooltip text="The scientific instrument — spectrograph, photometer, etc. — used to make the detection." />
                          : <span>{currentPlanet.discovery_instrument ?? 'Unknown'}</span></p>
                        <p>Discovery Locale<Tooltip text="Whether the detecting telescope was ground-based or space-based." />
                          : <span>{currentPlanet.discovery_locale ?? 'Unknown'}</span></p>
                        <p>Discovery Method<Tooltip text="How this planet was detected. Transit = planet passes in front of its star, dimming the light slightly — used by Kepler and TESS. Radial Velocity = the planet's gravity causes the star to wobble, detected by Doppler shift. Direct Imaging = the planet is photographed directly, only possible for large planets far from their star. Microlensing = a passing star's gravity bends and magnifies light, briefly revealing a planet." />
                          : <span>{currentPlanet.discovery_method ?? 'Unknown'}</span></p>
                        <p>Discovery Telescope<Tooltip text="The specific telescope used to detect this planet, if known." />
                          : <span>{currentPlanet.discovery_telescope ?? 'Unknown'}</span></p>
                        <p>Discovery Year<Tooltip text="The year this planet was confirmed. The first exoplanet around a Sun-like star was discovered in 1995. The Kepler Space Telescope launched in 2009 & revolutionized the field — most confirmed exoplanets were found by Kepler. The TESS mission launched in 2018 continues the search today." />
                          : <span>{currentPlanet.discovery_year ?? 'Unknown'}</span></p>
                      </div>

                    <hr />
                      <p className="section-label">Habitability<Tooltip text="How this planet scores against our habitability criteria, and where it sits relative to its star's habitable zone." /></p>
                      <div className="stat-columns">
                        <p>Habitability Tier<Tooltip text="Our habitability classification. Tier 1 = strong Earth analog — rocky, in the conservative habitable zone, Earth-like ESI, stable orbit around a G or K type star. Tier 2 = moderate candidate with good ESI and in the habitable zone. Tier 3 = in the habitable zone but less Earth-like physically. Non-habitable = outside the zone or gas giant." />
                          : <span>{currentPlanet.habitability_tier}</span></p>
                        <p>Habitable Zone<Tooltip text="The conservative zone is where liquid water is almost certainly stable. The optimistic zone extends further — water is possible but less certain." />
                          : <span>{HZ_LABELS[currentPlanet.hz_membership] || currentPlanet.hz_membership}</span></p>
                        <p>Habitable Zone Distance<Tooltip text="Where the planet sits within its star's habitable zone. 0 = perfect center, -1 = inner edge, +1 = outer edge. Beyond ±1 means outside the zone." />
                          : <span>{currentPlanet.hzd_score != null ? currentPlanet.hzd_score.toFixed(3) : 'Unknown'}</span></p>
                        <p>Planet Equilibrium Temperature<Tooltip text="The equilibrium temperature of a planet is a theoretical value representing the temperature it would have if it were a perfect blackbody heated only by its parent star, without an atmosphere or greenhouse effect. Earth's equilibrium temp is -18°C / -1°F but actual average is 15°C / 59°F due to greenhouse warming." />
                          : <span>{currentPlanet.equilibrium_temp_k_final != null ? `${currentPlanet.equilibrium_temp_k_final.toLocaleString()}K | ` : ''}{currentPlanet.equilibrium_temp_fahrenheit}°F | {currentPlanet.equilibrium_temp_celsius}°C</span></p>
                      </div>

                    <hr />
                      <p className="section-label">Host Star<Tooltip text="The star this planet orbits, and how it compares to our Sun." /></p>
                      <div className="stat-columns">
                        <p>Host Star<Tooltip text="The star this planet orbits." />
                          : <span>{currentPlanet.host_star_name}</span></p>
                        <p>Host Star Age<Tooltip text="Age of the host star in billions of years. Our Sun is 4.6 billion years old with roughly 5 billion years remaining." />
                          : <span>{currentPlanet.star_age_description}</span></p>
                        <p>Host Star Distance From Earth<Tooltip text="Distance of host star from Earth. 1 light year = 9.46 trillion km (5.88 trillion miles)." />
                          : <span>{currentPlanet.star_distance_light_years != null ? `${currentPlanet.star_distance_light_years.toFixed(1)} light years` : 'Unknown'}</span></p>
                        <p>Host Star Temperature<Tooltip text="The surface temperature of the host star in Kelvin. For reference: a candle flame burns at ~3,000K, our Sun is 5,778K, and a lightning bolt reaches ~30,000K." />
                          : <span>{(() => {
                              const k = currentPlanet.stellar_effective_temp_k
                              if (k == null) return 'Unknown'
                              const c = k - 273.15
                              const f = c * 9 / 5 + 32
                              return `${k.toLocaleString()}K | ${f.toFixed(0)}°F | ${c.toFixed(0)}°C`
                            })()}</span></p>
                        <p>Host Star Type<Tooltip text="Spectral classification of the host star, based on surface temperature."/>
                          : <span>{currentPlanet.star_spectral_type}</span></p>
                        <p>Shuttle Travel Distance From Earth<Tooltip text="Approx. travel time from Earth to host star travelling at the Space Shuttle's top speed of 28,000 km/h — the fastest crewed vehicle humans have built." />
                          : <span>{currentPlanet.shuttle_travel_description}</span></p>
                      </div>

                    <hr />
                      <p className="section-label">Orbit<Tooltip text="How this planet moves around its star — distance, eccentricity, period, and stability." /></p>
                      <div className="stat-columns">
                        <p>Orbital Distance<Tooltip text="Distance from the planet to its host star, measured in AU. 1 AU is the distance from Earth to our Sun — about 150 million km." />
                          : <span>{currentPlanet.orbital_distance_description}</span></p>
                        <p>Orbital Eccentricity<Tooltip text="How circular or elliptical the planet's orbit is. 0 = perfect circle, 1 = extremely elongated. Earth's eccentricity is 0.017 — nearly circular. Note: a value of exactly 0 may mean the orbit was assumed circular during fitting due to limited data, rather than actually measured as circular — this is common for planets found via radial velocity with sparse observations." />
                          : <span>{currentPlanet.orbital_eccentricity != null ? currentPlanet.orbital_eccentricity.toFixed(3) : 'Unknown'}</span></p>
                        <p>Orbital Period<Tooltip text="How long it takes this planet to complete one full orbit around its star. Earth's year is 365.25 days." />
                          : <span>{currentPlanet.year_length}</span></p>
                        <p>Orbital Stability<Tooltip text="How stable the planet's orbit is. Stable = nearly circular like Earth, stable temperatures year-round. Moderate = some seasonal variation. Unstable = extreme temperature swings as the planet swings close to and far from its star, making liquid water unlikely." />
                          : <span>{currentPlanet.orbital_stability}</span></p>
                      </div>

                    <hr />
                      <p className="section-label">Solar System Context<Tooltip text={<><span className="tooltip-highlight">{currentPlanet.planet_name}</span>'s orbital distance (in AU) plotted on a log scale against our solar system's inner planets, so you can visualize its orbit in the context of our solar system.</>} /></p>
                      <OrbitScale
                        planetName={currentPlanet.planet_name}
                        hostStarName={currentPlanet.host_star_name}
                        hostStarSpectralType={currentPlanet.star_spectral_type}
                        orbitalAu={currentPlanet.orbital_semi_major_axis_au}
                        hzInnerAu={currentPlanet.hz_inner_conservative_au}
                        hzOuterAu={currentPlanet.hz_outer_conservative_au}
                      />
                  </>
                )}
              </div>
            </div>
          </main>
          )}

          <footer className="navigation">
            <button
              onClick={() => {
                if (currentIndex === 0) setAtEntityIntro(true)
                else setCurrentIndex(i => i - 1)
              }}
              disabled={atEntityIntro}
            >
              ← Previous
            </button>
            <span>{atEntityIntro ? 'Overview' : `${currentIndex + 1} / ${filteredPlanets.length}`}</span>
            <button
              onClick={() => {
                if (atEntityIntro) setAtEntityIntro(false)
                else setCurrentIndex(i => i + 1)
              }}
              disabled={!atEntityIntro && currentIndex === filteredPlanets.length - 1}
            >
              Next →
            </button>
          </footer>
        </>
      )}

      <ChatShell />

      {showMethodology && <MethodologyPage onClose={() => setShowMethodology(false)} />}

    </div>
  )
}

export default App
