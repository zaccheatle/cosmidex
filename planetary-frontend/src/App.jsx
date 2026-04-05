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
    'tier_1_strong_candidate': 'Tier 1 (Strong Candidate)',
    'tier_2_moderate_candidate': 'Tier 2 (Moderate Candidate)',
    'tier_3_in_hz_only': 'Tier 3 (In Habitable Zone)',
    'non_habitable': 'Non-Habitable'
  }

  const hzLabels = {
    'conservative_hz': 'Conservative (liquid water Likely)',
    'optimistic_hz': 'Optimistic (liquid water possible)',
    'outside_hz': 'Outside HZ (liquid water unlikely)'
  }

  return (
    <div className="app">

      <div className="top-bar">
        <div className="top-left">
          <h1>🌌 CosmiDex: A Codex for the Cosmos</h1>
        </div>
        <div className="top-right">
            <div className="filter-section">
              <span className="filter-label">Filter by Habitability Tier:</span>
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
                  <p>Planet Type<Tooltip text="Classification based on the Planetary Habitability Laboratory standard. Subterran = smaller than Earth. Terran = Earth-sized rocky world. Volatile-rich Terran = rocky but lower density, possibly water or ice rich. Superterran = larger rocky or mixed composition, no solar system equivalent. Hycean Candidate = Superterran in the habitable zone, possibly a global ocean under a hydrogen atmosphere. Neptunian = Neptune-sized. Hot Jovian = gas giant with an extremely short orbit. Jovian = Jupiter-sized. Super Jovian = larger than Jupiter." />
                    : <span>{currentPlanet.planet_type}</span></p>
                  <p>Earth Similarity Index<Tooltip text="ESI measures how physically similar this planet is to Earth. Combines radius, density, escape velocity and surface temperature. 1.0 = identical to Earth, 0 = completely alien." />
                    : <span>{currentPlanet.esi_score ? currentPlanet.esi_score.toFixed(3) : 'unknown'}</span></p>

                <hr />
                  <p className="section-label">Solar System</p>
                  <p>Host Star<Tooltip text="The star this planet orbits." />
                    : <span>{currentPlanet.host_star_name}</span></p>
                  <p>Constellation<Tooltip text="TBD" />
                    : <span>TBD</span></p>
                  <p>Host Star Type<Tooltip text="The classification of the host star by surface temperature. Our Sun is a G-type star. Red dwarfs are the coolest and most common. The hotter the star, the shorter its lifespan, leaving less time for life to develop." />
                    : <span>{currentPlanet.star_type_description}</span></p>
                  <p>Galaxy<Tooltip text="All confirmed exoplanets in the NASA catalog are within the Milky Way — our home galaxy. Current detection methods like transit photometry and radial velocity only work at stellar distances. The nearest galaxy, Andromeda, is 2.5 million light years away — so far that detecting an individual planet there is currently impossible. Every world in this catalog is a neighbor by cosmic standards." />
                    : <span>Milky Way</span></p>
                  <p>Host Star Distance<Tooltip text="Distance of host star from Earth. 1 light year = 9.46 trillion km. Even Proxima Centauri b at 4.2 light years away would take a radio signal over 4 years to reach." />
                    : <span>{currentPlanet.distance_light_years.toFixed(1)} light years</span></p>
                  <p>Host Star Travel Time from Earth<Tooltip text="Approx. time it would take to reach the host star travelling at the Space Shuttle's top speed of 28,000 km/h — the fastest crewed vehicle humans have built." />
                    : <span>{currentPlanet.shuttle_travel_description}</span></p>
                  <p>Host Star Temperature
                    <Tooltip text="The surface temperature of the host star. Our Sun is 5778K. Cooler stars burn dimmer and redder, hotter stars burn brighter and bluer. Star temperature determines where the habitable zone sits and how much energy the planet receives." />
                    : <span>
                        {currentPlanet.stellar_effective_temp_k ? (
                          <>
                            {currentPlanet.stellar_effective_temp_k.toLocaleString()}K
                            {' | '}
                            {Math.round((currentPlanet.stellar_effective_temp_k - 273.15) * 9/5 + 32).toLocaleString()}°F
                            {' | '}
                            {Math.round(currentPlanet.stellar_effective_temp_k - 273.15).toLocaleString()}°C
                            {/* {' ('}
                            {currentPlanet.stellar_effective_temp_k < 5778 ? 'cooler' : 'hotter'}
                            {' than our Sun)'} */}
                          </>
                        ) : 'unknown'}
                      </span>
                  </p>
                  <p></p>


                <hr />
                  <p className="section-label">Orbit</p>
                  <p>Year Length<Tooltip text="How long it takes this planet to complete one full orbit around its star. Earth's year is 365.25 days." />
                    : <span>{currentPlanet.year_description}</span></p>
                  <p>Orbital Eccentricity<Tooltip text="How circular or elliptical the planet's orbit is. 0 = perfect circle, 1 = extremely elongated. Earth's eccentricity is 0.017 — nearly circular." />
                    : <span>{currentPlanet.orbital_eccentricity != null ? currentPlanet.orbital_eccentricity.toFixed(3) : 'unknown'}</span>
                  </p>
                  <p>Orbital Distance<Tooltip text="Distance from the planet to its host star, measured in AU. 1 AU is the distance from Earth to our Sun — about 150 million km." />
                    : <span>{currentPlanet.orbital_distance_description}</span></p>
                  <p>Orbital Stability<Tooltip text="How the orbital eccentricity affects habitability. Low = nearly circular like Earth, stable temperatures year-round. Moderate = some seasonal variation. High = extreme temperature swings as the planet swings close to and far from its star, making liquid water unlikely." />
                    : <span>{currentPlanet.eccentricity_risk}</span>
                  </p>

                <hr />
                  <p className="section-label">Planet</p>
                  <p>Size<Tooltip text="Planet radius compared to Earth. Earth's radius is the baseline at 1.0." />
                    : <span>{currentPlanet.size_description}</span></p>
                  <p>Gravity<Tooltip text="Surface gravity compared to Earth. Calculated from the planet's mass and radius. Affects whether humans could walk on the surface and whether the planet can hold an atmosphere." />
                    : <span>{currentPlanet.gravity_description}</span></p>
                  <p>Size Class<Tooltip text="Size classification based on planet radius compared to solar system bodies. Super Earths are the most common planet type in the galaxy yet our solar system has none — we don't fully understand why." />
                    : <span>{currentPlanet.size_class}</span></p>
                  <p>Escape Velocity<Tooltip text="The minimum speed needed to escape this planet's gravitational pull without further propulsion. Earth's escape velocity is 11.2 km/s. Higher escape velocity means the planet can hold onto a thicker atmosphere — too low and gases leak into space over time." />
                    : <span>{currentPlanet.escape_velocity_earth 
                        ? currentPlanet.escape_velocity_earth.toFixed(2) + '× Earth (' + 
                          (currentPlanet.escape_velocity_earth < 0.5 ? 'atmosphere likely thin or absent)' :
                          currentPlanet.escape_velocity_earth < 0.8 ? 'thin atmosphere, some gas loss over time)' :
                          currentPlanet.escape_velocity_earth < 1.2 ? 'similar to Earth, good atmosphere retention)' :
                          currentPlanet.escape_velocity_earth < 2.0 ? 'thick atmosphere likely)' :
                          'strong gravitational grip)')
                          : 'unknown'}</span>
                  </p>

                <hr />
                  <p className="section-label">Habitability</p>
                  <p>Habitability Tier<Tooltip text="Our habitability classification. Tier 1 = strong Earth analog — rocky, in the conservative habitable zone, Earth-like ESI, stable orbit around a G or K type star. Tier 2 = moderate candidate with good ESI and in the habitable zone. Tier 3 = in the habitable zone but less Earth-like physically. Non-habitable = outside the zone or gas giant." />
                    : <span>{tierLabels[currentPlanet.habitability_tier] || currentPlanet.habitability_tier}</span></p>
                  <p>Climate<Tooltip text="Climate classification based on equilibrium temperature. Frozen = below -60°C, Cold = -60°C to 0°C, Temperate = 0°C to 50°C, Warm = 50°C to 100°C, Hot = 100°C to 500°C, Scorching = above 500°C." />
                    : <span>{currentPlanet.temperature_description}</span></p>
                  <p>Habitable Zone<Tooltip text="The conservative zone is where liquid water is almost certainly stable. The optimistic zone extends further — water is possible but less certain." />
                    : <span>{hzLabels[currentPlanet.hz_membership] || currentPlanet.hz_membership}</span></p>
                  <p>Seasons<Tooltip text="TBD"/>
                    : <span>TBD</span>
                  </p>
                  <p>Habitable Zone Distance<Tooltip text="Where the planet sits within its star's habitable zone. 0 = perfect center, -1 = inner edge, +1 = outer edge. Beyond ±1 means outside the zone." />
                    : <span>{currentPlanet.hzd_score ? currentPlanet.hzd_score.toFixed(3) : 'unknown'}</span></p>
                  <p>Equilibrium Temperature<Tooltip text="Theoretical surface temperature assuming no atmosphere. Earth's equilibrium temp is -5°C / 23°F but actual average is 15°C / 59°F due to greenhouse warming." />
                    : <span>{currentPlanet.equilibrium_temp_fahrenheit}°F | {currentPlanet.equilibrium_temp_celsius}°C</span></p>
                  <p></p>
                  <p>Weather Guesstimate<Tooltip text="Estimated atmospheric conditions based on planet type, temperature, and star type. These are scientific inferences, not direct measurements." />
                    : <span>{currentPlanet.weather_estimation || 'unknown'}</span></p>
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