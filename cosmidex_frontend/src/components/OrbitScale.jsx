const SCALE_MIN_AU = 0.01
const SCALE_MAX_AU = 35

const REFERENCE_PLANETS = [
  { name: 'Mercury', au: 0.39 },
  { name: 'Venus', au: 0.72 },
  { name: 'Earth', au: 1.0 },
  { name: 'Mars', au: 1.52 },
  { name: 'Jupiter', au: 5.20 },
  { name: 'Saturn', au: 9.58 },
  { name: 'Uranus', au: 19.18 },
  { name: 'Neptune', au: 30.07 },
]

const WIDTH = 900
const HEIGHT = 220
const MARGIN_X = 70
const BASELINE_Y = 130

/**
 * Convert an orbital distance in AU to an SVG x-coordinate on the log scale,
 * clamped to [SCALE_MIN_AU, SCALE_MAX_AU].
 *
 * @param au - Orbital distance in AU.
 * @returns The x-coordinate in SVG viewBox units.
 */
function auToX(au) {
  const clamped = Math.min(Math.max(au, SCALE_MIN_AU), SCALE_MAX_AU)
  const t =
    (Math.log10(clamped) - Math.log10(SCALE_MIN_AU)) /
    (Math.log10(SCALE_MAX_AU) - Math.log10(SCALE_MIN_AU))
  return MARGIN_X + t * (WIDTH - 2 * MARGIN_X)
}

/**
 * Log-scale diagram placing an exoplanet's orbital distance against our own
 * solar system's planets, so its distance from its star is grounded in
 * something familiar. All reference distances (Mercury through Neptune) are
 * real, fixed AU values — only the exoplanet marker and habitable-zone band
 * come from actual mart data.
 *
 * @param props
 * @param props.planetName - The exoplanet's name, shown as its marker label.
 * @param props.hostStarName - The host star's name, shown at the scale's origin.
 * @param props.orbitalAu - The exoplanet's orbital semi-major axis in AU.
 * @param props.hzInnerAu - Inner edge of the host star's conservative habitable zone, in AU.
 * @param props.hzOuterAu - Outer edge of the host star's conservative habitable zone, in AU.
 * @returns The SVG orbit-scale diagram, or null if orbitalAu is unknown.
 */
export default function OrbitScale({ planetName, hostStarName, orbitalAu, hzInnerAu, hzOuterAu }) {
  if (orbitalAu == null) return null

  const planetX = auToX(orbitalAu)
  const hasHz = hzInnerAu != null && hzOuterAu != null

  return (
    <div className="orbit-scale">
      <p className="orbit-scale-subtitle">
        <span className="orbit-scale-legend-swatch" /> Habitable zone of the planet's host star
      </p>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="orbit-scale-svg" preserveAspectRatio="xMidYMid meet">
        {hasHz && (
          <rect
            x={auToX(hzInnerAu)}
            y={BASELINE_Y - 26}
            width={Math.max(auToX(hzOuterAu) - auToX(hzInnerAu), 1)}
            height={52}
            fill="rgba(94, 222, 140, 0.18)"
            stroke="rgba(94, 222, 140, 0.5)"
            strokeWidth="1"
          />
        )}

        <line x1={MARGIN_X} y1={BASELINE_Y} x2={WIDTH - MARGIN_X} y2={BASELINE_Y} stroke="#2e2e4e" strokeWidth="2" />

        {/* Host star */}
        <circle cx={MARGIN_X} cy={BASELINE_Y} r="13" fill="#ffcc66" />
        <text x={MARGIN_X} y={BASELINE_Y + 42} textAnchor="middle" className="orbit-scale-label">
          {hostStarName ?? 'Host Star'}
        </text>
        <text x={MARGIN_X} y={BASELINE_Y + 60} textAnchor="middle" className="orbit-scale-label orbit-scale-label-muted">
          (Host Star)
        </text>

        {REFERENCE_PLANETS.map((p, i) => (
          <g key={p.name}>
            <circle cx={auToX(p.au)} cy={BASELINE_Y} r="6" fill="#8888aa" />
            <text
              x={auToX(p.au)}
              y={i % 2 === 0 ? BASELINE_Y - 22 : BASELINE_Y + 42}
              textAnchor="middle"
              className="orbit-scale-label orbit-scale-label-muted"
            >
              {p.name}
            </text>
          </g>
        ))}

        {/* This exoplanet */}
        <circle cx={planetX} cy={BASELINE_Y} r="10" fill="#bf5fff" stroke="#ffffff" strokeWidth="1.5" />
        <text x={planetX} y={BASELINE_Y - 46} textAnchor="middle" className="orbit-scale-label orbit-scale-label-planet">
          {planetName}
        </text>
        <text x={planetX} y={BASELINE_Y - 24} textAnchor="middle" className="orbit-scale-label orbit-scale-label-muted">
          {orbitalAu < 0.1 ? orbitalAu.toFixed(3) : orbitalAu.toFixed(2)} AU
        </text>
      </svg>
    </div>
  )
}
