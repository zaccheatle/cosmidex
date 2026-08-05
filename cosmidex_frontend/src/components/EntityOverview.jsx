import { useMemo } from 'react'

// Per-entity intro copy. Only Exoplanets exists today; future entities
// (Constellations, etc.) just add an entry here — the component below stays
// entity-agnostic.
const ENTITY_CONTENT = {
  Exoplanets: {
    title: 'Exoplanets',
    description:
      'For most of human history, every planet we knew belonged to our solar system . . .  '+
      'that changed in 1995, when astronomers in France caught a glimpse of the first exoplanet: '+
      'a planet within our galaxy orbiting a sun-like star other than our own. Since then, over sixty-three ' +
      'hundred exoplanets have been added to the Exoplanet Archive at NASA. Cosmidex focuses on the ones that may be capable of hosting life.',
  },
}

/**
 * Compute a handful of notable stats from the currently-loaded habitable
 * planet list — tier breakdown, average ESI, most common host star class,
 * and the closest habitable world by distance.
 *
 * @param planets - Planet summary rows (PLANET_SUMMARY_COLUMNS shape).
 * @returns Stat object, or null if there's nothing to compute yet.
 */
function useEntityStats(planets) {
  return useMemo(() => {
    if (!planets || planets.length === 0) return null

    const tierCounts = planets.reduce((acc, p) => {
      acc[p.habitability_tier] = (acc[p.habitability_tier] || 0) + 1
      return acc
    }, {})

    const esiScores = planets.map(p => p.esi_score).filter(v => v != null)
    const avgEsi = esiScores.length > 0
      ? (esiScores.reduce((sum, v) => sum + v, 0) / esiScores.length).toFixed(2)
      : null

    const spectralCounts = planets.reduce((acc, p) => {
      if (p.star_spectral_type) acc[p.star_spectral_type] = (acc[p.star_spectral_type] || 0) + 1
      return acc
    }, {})
    const topSpectralType = Object.entries(spectralCounts).sort((a, b) => b[1] - a[1])[0]?.[0]

    const withDistance = planets.filter(p => p.star_distance_light_years != null)
    const closest = withDistance.length > 0
      ? withDistance.reduce((a, b) => a.star_distance_light_years < b.star_distance_light_years ? a : b)
      : null

    return {
      tier1: tierCounts['Tier 1'] || 0,
      tier2: tierCounts['Tier 2'] || 0,
      tier3: tierCounts['Tier 3'] || 0,
      avgEsi,
      topSpectralType,
      closest,
    }
  }, [planets])
}

/**
 * Hero-style intro slide for the selected Cosmic Entity, shown as the
 * explorer's "before the first planet" step (below the app's top-bar, unlike
 * the full-screen app landing page). Title, description, and a handful of
 * stats computed from the already-loaded planet list.
 *
 * @param props
 * @param props.entity - The selected Cosmic Entity name (keys into ENTITY_CONTENT).
 * @param props.planets - The already-fetched habitable planet list.
 * @param props.listLoading - Whether that list is still being fetched.
 * @returns The entity overview hero block.
 */
export default function EntityOverview({ entity, planets, listLoading }) {
  const content = ENTITY_CONTENT[entity] ?? ENTITY_CONTENT.Exoplanets
  const stats = useEntityStats(planets)

  return (
    <div className="entity-overview-page">
      <div className="entity-overview-content">
        <h1 className="entity-overview-title">{content.title}</h1>
        <p className="entity-overview-description">{content.description}</p>

        <div className="entity-overview-stats">
          <div className="entity-overview-stat">
            <span className="entity-overview-stat-value">6,324</span>
            <span className="entity-overview-stat-label">Confirmed Exoplanets</span>
          </div>
          <div className="entity-overview-stat">
            <span className="entity-overview-stat-value">75</span>
            <span className="entity-overview-stat-label">Potentially Habitable Worlds</span>
          </div>
          {listLoading && !stats && (
            <div className="entity-overview-stat">
              <span className="entity-overview-stat-label">Loading stats…</span>
            </div>
          )}
          {stats && (
            <>
              <div className="entity-overview-stat">
                <span className="entity-overview-stat-value">{stats.tier1} / {stats.tier2} / {stats.tier3}</span>
                <span className="entity-overview-stat-label">Tier 1 / 2 / 3 Breakdown</span>
              </div>
              {stats.avgEsi && (
                <div className="entity-overview-stat">
                  <span className="entity-overview-stat-value">{stats.avgEsi}</span>
                  <span className="entity-overview-stat-label">Average ESI Score</span>
                </div>
              )}
              {stats.topSpectralType && (
                <div className="entity-overview-stat">
                  <span className="entity-overview-stat-value">{stats.topSpectralType}</span>
                  <span className="entity-overview-stat-label">Most Common Host Star</span>
                </div>
              )}
              {stats.closest && (
                <div className="entity-overview-stat">
                  <span className="entity-overview-stat-value">{stats.closest.planet_name}</span>
                  <span className="entity-overview-stat-label">
                    Closest Habitable World ({stats.closest.star_distance_light_years.toFixed(1)} ly)
                  </span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
