import { useState, useEffect } from 'react'
import Tooltip from './components/Tooltip'
import './App.css'

function App() {
  const [planets, setPlanets] = useState([])
  const [selectedTier, setSelectedTier] = useState('all')
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/planets/notable/list')
      .then(res => res.json())
      .then(data => setPlanets(data))
  }, [])

  const filteredPlanets = selectedTier === 'all'
    ? planets
    : planets.filter(p => p.habitability_tier === selectedTier)

  const availableTiers = ['all', 'tier_2_moderate_candidate', 'tier_3_in_hz_only', 'non_habitable'].filter(tier => {
    if (tier === 'all') return true
    return planets.filter(p => p.habitability_tier === tier).length > 0
  })

  const tierDescriptions = {
    'all': 'Show all planets',
    'tier_2_moderate_candidate': 'Planets with good ESI scores inside the habitable zone — strong Earth-like candidates',
    'tier_3_in_hz_only': 'Planets inside the habitable zone but less Earth-like physically',
    'non_habitable': 'Planets outside the habitable zone or gas giants'
  }

  const currentPlanet = filteredPlanets[currentIndex]

  const tierLabels = {
    'tier_1_strong_candidate': 'Tier 1',
    'tier_2_moderate_candidate': 'Tier 2',
    'tier_3_in_hz_only': 'Tier 3',
    'non_habitable': 'Non-Habitable'
  }

  const hzLabels = {
    'conservative_hz': 'Conservative',
    'optimistic_hz': 'Optimistic',
    'outside_hz': 'Outside HZ'
  }

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
                    title={tierDescriptions[tier]}
                    className={`tier-btn ${selectedTier === tier ? 'active' : ''}`}
                    onClick={() => {
                      setSelectedTier(tier)
                      setCurrentIndex(0)
                    }}
                  >
                    {tier === 'all' ? 'All' :
                    tier === 'tier_2_moderate_candidate' ? 'Tier 2' :
                    tier === 'tier_3_in_hz_only' ? 'Tier 3' :
                    'Non-Habitable'}
                  </button>
                ))}
              </nav>
            </div>
        </div>
      </div>

      <main className="viewer">
        <div className="left-panel">
          <div className="planet-image">
            {currentPlanet && (
              <img src={currentPlanet.image_url} alt={currentPlanet.planet_name} />
            )}
          </div>
        </div>

        <div className="right-panel">
          <div className="planet-stats">
            {currentPlanet && (
              <>
                <h2>{currentPlanet.planet_name}<Tooltip text="Planet name — most exoplanets are named after their host star with a letter suffix; b for the first planet discovered, c for the second, and so on."/></h2>
                  <p>Discovery Year<Tooltip text="The year this planet was confirmed. The first exoplanet around a Sun-like star was discovered in 1995. The Kepler Space Telescope launched in 2009 revolutionized the field — most confirmed exoplanets were found by Kepler. The TESS mission launched in 2018 continues the search today." />
                    : <span>{currentPlanet.discovery_year}</span></p>
                  <p>Discovery Method<Tooltip text="How this planet was detected. Transit = planet passes in front of its star, dimming the light slightly — used by Kepler and TESS. Radial Velocity = the planet's gravity causes the star to wobble, detected by Doppler shift. Direct Imaging = the planet is photographed directly, only possible for large planets far from their star. Microlensing = a passing star's gravity bends and magnifies light, briefly revealing a planet." />
                    : <span>{currentPlanet.discovery_method}</span></p>

                <hr />
                  <p className="section-label">Solar System</p>
                  <p>Host Star<Tooltip text="The star this planet orbits." />
                    : <span>{currentPlanet.host_star_name}</span></p>
                  <p>Constellation<Tooltip text="The constellation this planet's host star appears in from Earth. Constellations are patterns of stars as seen from our perspective — the stars themselves may be vastly different distances apart. There are 88 officially recognized constellations defined by the International Astronomical Union." />
                    : <span>TBD</span></p>
                  <p>Host Star Age<Tooltip text="Age of the host star in billions of years. Our Sun is 4.6 billion years old with roughly 5 billion years remaining. Red dwarfs live for trillions of years — far longer than the current age of the universe. Sun-like G stars live 10-12 billion years. Hot blue-white stars burn through their fuel in just millions of years — too short for complex life to develop. The longer a star lives, the more time life has to emerge and evolve." />
                    : <span>{currentPlanet.star_age_description}</span></p>
                  <p>Radio Signal Travel Distance<Tooltip text="Approx. travel time from Earth to host star. Radio signals travel at the speed of light — 299,792 km/s — the absolute speed limit of the universe. This is the one-way travel time for a signal sent from Earth today. Any reply would take twice as long. For context: a signal to the Moon takes 1.3 seconds. A signal to Mars takes up to 20 minutes. Beyond our solar system, even the nearest star takes over 4 years. For distant Kepler planets thousands of light years away, any conversation would span civilizations." />
                    : <span>{currentPlanet.radio_signal_description}</span></p>
                  <p>Host Star Distance<Tooltip text="Distance of host star from Earth. 1 light year = 9.46 trillion km." />
                    : <span>{currentPlanet.distance_light_years.toFixed(1)} light years</span></p>
                  <p>Shuttle Travel Distance<Tooltip text="Approx. travel time from Earth to host star travelling at the Space Shuttle's top speed of 28,000 km/h — the fastest crewed vehicle humans have built." />
                    : <span>{currentPlanet.shuttle_travel_description}</span></p>
                  <p>Host Star Temperature<Tooltip text="The surface temperature of the host star in Kelvin. For reference: a candle flame burns at ~3,000K, our Sun is 5,778K, and a lightning bolt reaches ~30,000K. Red dwarfs (below 3,700K) are cooler than a welding torch. The hottest blue-white stars burn at over 30,000K — hotter than a lightning strike. Star temperature determines the color of light bathing the planet, where the habitable zone sits, and how long the star will live." />
                    : <span>{currentPlanet.stellar_effective_temp_k.toLocaleString()}K ({currentPlanet.star_temp_description})</span></p>

                <hr />
                  <p className="section-label">Orbit</p>
                  <p>Orbital Distance<Tooltip text="Distance from the planet to its host star, measured in AU. 1 AU is the distance from Earth to our Sun — about 150 million km." />
                    : <span>{currentPlanet.orbital_distance_description}</span></p>
                  <p>Orbital Eccentricity<Tooltip text="How circular or elliptical the planet's orbit is. 0 = perfect circle, 1 = extremely elongated. Earth's eccentricity is 0.017 — nearly circular." />
                    : <span>{currentPlanet.orbital_eccentricity != null ? currentPlanet.orbital_eccentricity.toFixed(3) : 'unknown'}</span></p>
                  <p>Orbital Period<Tooltip text="How long it takes this planet to complete one full orbit around its star. Earth's year is 365.25 days." />
                    : <span>{currentPlanet.year_description}</span></p>
                  <p>Orbital Stability<Tooltip text="How stable the planets orbit is. High = nearly circular like Earth, stable temperatures year-round. Moderate = some seasonal variation. Low = extreme temperature swings as the planet swings close to and far from its star, making liquid water unlikely." />
                    : <span>{currentPlanet.orbital_stability}</span></p>

                <hr />
                  <p className="section-label">Planet</p>
                  <p>Type<Tooltip text="Classification based on the Planetary Habitability Laboratory standard. Subterran = smaller than Earth. Terran = Earth-sized rocky world. Volatile-rich Terran = rocky but lower density, possibly water or ice rich. Superterran = larger rocky or mixed composition, no solar system equivalent. Hycean Candidate = Superterran in the habitable zone, possibly a global ocean under a hydrogen atmosphere. Neptunian = Neptune-sized. Hot Jovian = gas giant with an extremely short orbit. Jovian = Jupiter-sized. Super Jovian = larger than Jupiter." />
                    : <span>{currentPlanet.planet_type}</span></p>
                  <p>Radius<Tooltip text="Planet radius compared to Earth. Earth's radius is the baseline at 1.0." />
                    : <span>{currentPlanet.size_description}</span></p>
                  <p>Size Class<Tooltip text="Size classification based on planet radius compared to solar system bodies. Super Earths are the most common planet type in the galaxy yet our solar system has none — we don't fully understand why." />
                    : <span>{currentPlanet.size_class}</span></p>
                  <p>Gravity<Tooltip text="Surface gravity compared to Earth. Calculated from the planet's mass and radius. Affects whether humans could walk on the surface and whether the planet can hold an atmosphere." />
                    : <span>{currentPlanet.gravity_description}</span></p>
                  <p>Earth Similarity Index<Tooltip text="ESI measures how physically similar this planet is to Earth. Combines radius, density, escape velocity and surface temperature. 1.0 = identical to Earth, 0 = completely alien." />
                    : <span>{currentPlanet.esi_score ? currentPlanet.esi_score.toFixed(3) : 'unknown'}</span></p>
                  <p>
                    Escape Velocity
                    <Tooltip text="The minimum speed needed to escape this planet's gravitational pull without further propulsion. Earth's escape velocity is 11.2 km/s. Higher escape velocity means the planet can hold onto a thicker atmosphere — too low and gases leak into space over time." />
                    : <span>
                        {currentPlanet.escape_velocity_earth != null
                          ? `${(currentPlanet.escape_velocity_earth * 11.2).toFixed(1)} km/s (${currentPlanet.escape_velocity_earth.toFixed(2)}× Earth)`
                          : 'unknown'}
                      </span>
                  </p>

                <hr />
                  <p className="section-label">Habitability</p>
                  <p>Habitability Tier<Tooltip text="Our habitability classification. Tier 1 = strong Earth analog — rocky, in the conservative habitable zone, Earth-like ESI, stable orbit around a G or K type star. Tier 2 = moderate candidate with good ESI and in the habitable zone. Tier 3 = in the habitable zone but less Earth-like physically. Non-habitable = outside the zone or gas giant." />
                    : <span>{tierLabels[currentPlanet.habitability_tier] || currentPlanet.habitability_tier}</span></p>
                  <p>Theoretical Surface Climate<Tooltip text="Theoretical climate adapted from the Köppen Climate Classification — the scientific standard for Earth climate zones, applied here using equilibrium temperature as a proxy. Class A (Tropical) = above 18°C, warm year-round. Class B (Arid) = above 0°C but too hot for liquid water. Class C (Temperate) = 0°C to 18°C, liquid water possible. Class D (Continental) = -15°C to 0°C, seasonal ice likely. Class E (Polar) = -40°C to -15°C, similar to Earth polar regions. Class EF (Ice Cap) = below -40°C, permanently frozen. Class X = above 100°C, surface water impossible." />
                    : <span>{currentPlanet.temperature_description}</span></p>
                  <p>Habitable Zone<Tooltip text="The conservative zone is where liquid water is almost certainly stable. The optimistic zone extends further — water is possible but less certain." />
                    : <span>{hzLabels[currentPlanet.hz_membership] || currentPlanet.hz_membership}</span></p>
                  <p>Theoretical Surface Temperature<Tooltip text="Theoretical surface temperature using equilibrium temp which assumes no atmosphere. Earth's equilibrium temp is -5°C / 23°F but actual average is 15°C / 59°F due to greenhouse warming." />
                    : <span>{currentPlanet.equilibrium_temp_fahrenheit}°F | {currentPlanet.equilibrium_temp_celsius}°C</span></p>
                  <p>Habitable Zone Distance<Tooltip text="Where the planet sits within its star's habitable zone. 0 = perfect center, -1 = inner edge, +1 = outer edge. Beyond ±1 means outside the zone." />
                    : <span>{currentPlanet.hzd_score ? currentPlanet.hzd_score.toFixed(3) : 'unknown'}</span></p>
                  {/* <p></p>
                  <p>Weather Guesstimate<Tooltip text="Estimated atmospheric conditions based on planet type, temperature, and star type. These are scientific inferences, not direct measurements." />
                    : <span>{currentPlanet.weather_estimation || 'unknown'}</span></p> */}
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

    </div>
  )
}

export default App