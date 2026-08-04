const SCALE_MIN_AU = 0.01
const SCALE_MAX_AU = 35

// Earth is rendered separately (blue, two-line label) so it's excluded here.
// Colors approximate each planet's real-world appearance.
const REFERENCE_PLANETS = [
  { name: 'Mercury', au: 0.39, color: '#9c8d7c' },
  { name: 'Venus', au: 0.72, color: '#e8c989' },
  { name: 'Mars', au: 1.52, color: '#c1440e' },
  { name: 'Jupiter', au: 5.20, color: '#d8a86b' },
  { name: 'Saturn', au: 9.58, color: '#e3c16f' },
  { name: 'Uranus', au: 19.18, color: '#8fe0e6' },
  { name: 'Neptune', au: 30.07, color: '#3457c9' },
]

// Approximate visible color by spectral class, hottest (O) to coolest (Y).
const STAR_COLORS = {
  O: '#9bb0ff',
  B: '#aabfff',
  A: '#cad7ff',
  F: '#f8f7ff',
  G: '#ffd700',
  K: '#ffb366',
  M: '#ff6b4a',
  L: '#cc3300',
  T: '#993300',
  Y: '#663300',
}

const WIDTH = 900
const HEIGHT = 218
const MARGIN_X = 70
const BASELINE_Y = 121

// If the exoplanet's dot would land this close (in px) to a fixed reference
// dot, nudge the reference dot sideways so neither is hidden behind the other.
const DOT_COLLISION_GAP = 18

// If the exoplanet's label would land this close (in px) to Earth's label
// (same row), lift the exoplanet's label higher so the two don't overlap.
const EARTH_LABEL_COLLISION_GAP = 90
const EXOPLANET_LIFT = 32

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
 * Look up an approximate visible star color from its spectral class letter
 * (parsed out of strings like "Class M - Red-orange").
 *
 * @param spectralType - The host star's spectral type description.
 * @returns A hex color, or a neutral yellow fallback if the class is unknown.
 */
function starColorFor(spectralType) {
  const match = spectralType?.match(/Class ([A-Z])/)
  return (match && STAR_COLORS[match[1]]) ?? '#ffcc66'
}

function auLabel(au) {
  return `${au < 0.1 ? au.toFixed(3) : au.toFixed(2)} AU`
}

/**
 * Push a reference dot's x sideways, away from the exoplanet's dot, if the
 * two would otherwise land close enough to hide one behind the other.
 *
 * @param refX - The reference dot's unadjusted x-coordinate.
 * @param planetX - The exoplanet's x-coordinate.
 * @returns refX, or refX nudged by DOT_COLLISION_GAP if the two are too close.
 */
function dodgeDot(refX, planetX) {
  const dx = refX - planetX
  if (Math.abs(dx) >= DOT_COLLISION_GAP) return refX
  return planetX + (dx >= 0 ? DOT_COLLISION_GAP : -DOT_COLLISION_GAP)
}

/**
 * Log-scale diagram placing an exoplanet's orbital distance against our own
 * solar system's planets, so its distance from its star is grounded in
 * something familiar. All reference distances (Mercury through Neptune) are
 * real, fixed AU values — only the exoplanet marker, host star color, and
 * habitable-zone band come from actual mart data.
 *
 * @param props
 * @param props.planetName - The exoplanet's name, shown as its marker label.
 * @param props.hostStarName - The host star's name, shown at the scale's origin.
 * @param props.hostStarSpectralType - The host star's spectral type (drives its marker color).
 * @param props.orbitalAu - The exoplanet's orbital semi-major axis in AU.
 * @param props.hzInnerAu - Inner edge of the host star's conservative habitable zone, in AU.
 * @param props.hzOuterAu - Outer edge of the host star's conservative habitable zone, in AU.
 * @returns The SVG orbit-scale diagram, or null if orbitalAu is unknown.
 */
export default function OrbitScale({
  planetName,
  hostStarName,
  hostStarSpectralType,
  orbitalAu,
  hzInnerAu,
  hzOuterAu,
}) {
  if (orbitalAu == null) return null

  const planetX = auToX(orbitalAu)
  const earthX = auToX(1.0)
  const hasHz = hzInnerAu != null && hzOuterAu != null
  const hzInnerX = hasHz ? auToX(hzInnerAu) : null
  const hzOuterX = hasHz ? auToX(hzOuterAu) : null

  // If the exoplanet lands right on top of Earth's label row, lift the
  // exoplanet's label out of the way (its dotted line just gets longer).
  const exoplanetLift =
    Math.abs(planetX - earthX) < EARTH_LABEL_COLLISION_GAP ? EXOPLANET_LIFT : 0

  return (
    <div className="orbit-scale">
      <p className="orbit-scale-subtitle">
        <span className="orbit-scale-legend-swatch" /> Habitable zone of the planet's host star
      </p>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="orbit-scale-svg" preserveAspectRatio="xMidYMid meet">
        {hasHz && (
          <>
            <rect
              x={hzInnerX}
              y={BASELINE_Y - 21}
              width={Math.max(hzOuterX - hzInnerX, 1)}
              height={42}
              fill="rgba(94, 222, 140, 0.18)"
              stroke="rgba(94, 222, 140, 0.5)"
              strokeWidth="1"
            />
            {/* Box-plot-style whisker caps marking the HZ start/end distances */}
            <line x1={hzInnerX} x2={hzInnerX} y1={BASELINE_Y + 21} y2={BASELINE_Y + 27} stroke="rgba(94, 222, 140, 0.8)" strokeWidth="2" />
            <text x={hzInnerX} y={BASELINE_Y + 40} textAnchor="middle" className="orbit-scale-label-hz">
              {auLabel(hzInnerAu)}
            </text>
            <line x1={hzOuterX} x2={hzOuterX} y1={BASELINE_Y + 21} y2={BASELINE_Y + 27} stroke="rgba(94, 222, 140, 0.8)" strokeWidth="2" />
            <text x={hzOuterX} y={BASELINE_Y + 40} textAnchor="middle" className="orbit-scale-label-hz">
              {auLabel(hzOuterAu)}
            </text>
          </>
        )}

        <line x1={MARGIN_X} y1={BASELINE_Y} x2={WIDTH - MARGIN_X} y2={BASELINE_Y} stroke="#2e2e4e" strokeWidth="2.5" />

        {/* Host star — marker and name both colored by spectral type */}
        <circle cx={MARGIN_X} cy={BASELINE_Y} r="14" fill={starColorFor(hostStarSpectralType)} />
        <text
          x={MARGIN_X}
          y={BASELINE_Y + 34}
          textAnchor="middle"
          className="orbit-scale-label"
          style={{ fill: starColorFor(hostStarSpectralType) }}
        >
          {hostStarName ?? 'Host Star'}
        </text>
        <text x={MARGIN_X} y={BASELINE_Y + 48} textAnchor="middle" className="orbit-scale-label orbit-scale-label-muted">
          (Host Star)
        </text>

        {REFERENCE_PLANETS.map((p, i) => {
          const refX = dodgeDot(auToX(p.au), planetX)
          return (
            <g key={p.name}>
              <circle cx={refX} cy={BASELINE_Y} r="7" fill={p.color} />
              <text
                x={refX}
                y={(p.name === 'Mars' ? i % 2 !== 0 : i % 2 === 0) ? BASELINE_Y - 18 : BASELINE_Y + 34}
                textAnchor="middle"
                className="orbit-scale-label"
              >
                {p.name}
              </text>
            </g>
          )
        })}

        {/* Earth — green marker + two-line label (green, not blue, so it never
            visually blends with the blue exoplanet marker when they overlap) */}
        <line x1={earthX} x2={earthX} y1={BASELINE_Y - 45} y2={BASELINE_Y - 6} stroke="rgba(94, 222, 140, 0.7)" strokeWidth="2" strokeDasharray="3,3" />
        <circle cx={earthX} cy={BASELINE_Y} r="7" fill="#5ede8c" />
        <text x={earthX} y={BASELINE_Y - 69} textAnchor="middle" className="orbit-scale-label-green">
          Earth
        </text>
        <text x={earthX} y={BASELINE_Y - 52} textAnchor="middle" className="orbit-scale-label-green-muted">
          {auLabel(1.0)}
        </text>

        {/* This exoplanet — connected to the baseline by a dotted line, lifted
            higher (with a longer line) if it would otherwise overlap Earth's label */}
        <line x1={planetX} x2={planetX} y1={BASELINE_Y - 45 - exoplanetLift} y2={BASELINE_Y - 10} stroke="rgba(74, 158, 255, 0.6)" strokeWidth="2" strokeDasharray="3,3" />
        <circle cx={planetX} cy={BASELINE_Y} r="11" fill="#4a9eff" stroke="#ffffff" strokeWidth="1.5" />
        <text x={planetX} y={BASELINE_Y - 69 - exoplanetLift} textAnchor="middle" className="orbit-scale-label orbit-scale-label-planet">
          {planetName}
        </text>
        <text x={planetX} y={BASELINE_Y - 52 - exoplanetLift} textAnchor="middle" className="orbit-scale-label orbit-scale-label-muted">
          {auLabel(orbitalAu)}
        </text>
      </svg>
    </div>
  )
}
