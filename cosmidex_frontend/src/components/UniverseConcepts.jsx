import Tooltip from './Tooltip'

// Static content for the Universe entity's 3-entry mini catalog. Unlike
// Exoplanets/Galaxies, there's no dataset backing this — dark matter and dark
// energy aren't populations of individually-measured objects, just single,
// well-established concepts. Facts are drawn from real NASA sources (see
// data/rag_articles/dark_matter.md, hubble_tension.md), same standard as the
// rest of the app's sourced content.
export const UNIVERSE_ENTRIES = [
  {
    key: 'ordinary-matter',
    name: 'Ordinary Matter',
    percent: 5,
    color: '#4a9eff',
    tagline: 'Everything you can see',
    description:
      "Stars, planets, galaxies, the device you're reading this on — everything made of atoms is " +
      'ordinary matter. It\'s the only kind of matter we can directly observe, absorbing, reflecting, ' +
      'and emitting light across the spectrum. Despite being the only matter we can see, it makes up ' +
      'just a small fraction of everything in the universe.',
    facts: [
      {
        label: 'Share of the Universe',
        value: '5%',
        tooltip: 'What fraction of the universe\'s total mass-energy is ordinary matter, versus 27% dark matter and 68% dark energy.',
      },
      {
        label: 'Interacts via',
        value: 'Gravity + electromagnetism',
        tooltip: 'Ordinary matter reacts to light and other electromagnetic forces — that\'s why we can see, touch, and photograph it, unlike dark matter, which only interacts through gravity.',
      },
      {
        label: 'What it is',
        value: 'Atoms — protons, neutrons, electrons',
        tooltip: 'The basic particles that make up everything ordinary matter is built from.',
      },
      {
        label: 'Made of',
        value: 'Mostly hydrogen & helium from the Big Bang, plus heavier elements forged in stars',
        tooltip: 'Hydrogen and helium formed in the first minutes after the Big Bang. Every heavier element — carbon, oxygen, iron, everything else — was made later, inside stars.',
      },
      {
        label: 'Detectable across',
        value: 'Infrared to gamma rays',
        tooltip: 'Ordinary matter can be observed across a wide range of light wavelengths. Dark matter, by contrast, emits no light at any wavelength — that\'s precisely why it\'s "dark."',
      },
    ],
  },
  {
    key: 'dark-matter',
    name: 'Dark Matter',
    percent: 27,
    color: '#bf5fff',
    tagline: 'The invisible glue holding galaxies together',
    description:
      "Dark matter doesn't absorb, reflect, or emit light — it's invisible. But its gravity holds " +
      'galaxies together; without it, galaxies would fly apart. Swiss-born astronomer Fritz Zwicky ' +
      "first proposed it in 1933 after finding galaxies in the Coma Cluster moving too fast for the " +
      "gravity their visible matter alone could produce. Vera Rubin's 1970s observations of spiral " +
      'galaxy rotation provided the evidence that made it widely accepted.',
    facts: [
      {
        label: 'Share of the Universe',
        value: '27%',
        tooltip: 'What fraction of the universe\'s total mass-energy is dark matter — more than five times as much as all the ordinary matter (stars, planets, everything visible) combined.',
      },
      {
        label: 'Interacts via',
        value: 'Gravity only',
        tooltip: 'Dark matter has mass, so it pulls on other matter through gravity — but it doesn\'t interact with light or any other electromagnetic force. That\'s why it can\'t be seen directly, only detected through its gravitational effects.',
      },
      {
        label: 'First proposed',
        value: '1933 (Fritz Zwicky)',
        tooltip: 'Swiss-born astronomer Fritz Zwicky noticed galaxies in the Coma Cluster moving too fast for the gravity of their visible matter alone to explain — and proposed an invisible extra mass holding them together.',
      },
      {
        label: 'Key evidence',
        value: 'Gravitational lensing (Bullet Cluster)',
        tooltip: 'Gravitational lensing is when massive objects bend light passing near them, like a lens. In 2006, images of the Bullet Cluster — two colliding galaxy clusters — showed lensing revealing mass in a different location than the visible hot gas, some of the strongest direct evidence dark matter exists.',
      },
      {
        label: 'Leading candidates',
        value: 'WIMPs, axions, primordial black holes',
        tooltip: 'Hypothetical particles or objects scientists are searching for as the actual makeup of dark matter — none has been directly detected or confirmed yet.',
      },
    ],
  },
  {
    key: 'dark-energy',
    name: 'Dark Energy',
    percent: 68,
    color: '#5ede8c',
    tagline: "The mystery force accelerating the universe's expansion",
    description:
      'In 1998, astronomers found that distant supernovae were fainter — and therefore farther away — ' +
      "than expected, revealing that the universe's expansion isn't just continuing, it's speeding up. " +
      'Dark energy is the name scientists gave to whatever is causing that acceleration — spread ' +
      'throughout the universe rather than concentrated in galaxies like dark matter, and still ' +
      'fundamentally unexplained.',
    facts: [
      {
        label: 'Share of the Universe',
        value: '68%',
        tooltip: 'Dark energy makes up most of the universe\'s total mass-energy — more than dark matter and ordinary matter combined.',
      },
      {
        label: 'Discovered',
        value: '1998 (accelerating supernovae)',
        tooltip: 'Astronomers measure a supernova\'s distance from how bright it appears — dimmer means farther away. In 1998, distant supernovae were dimmer than expected, meaning the universe\'s expansion wasn\'t just continuing, it was speeding up.',
      },
      {
        label: 'Effect',
        value: 'Accelerating cosmic expansion',
        tooltip: 'The universe isn\'t just expanding — the rate of expansion itself is increasing over time. Dark energy is the name scientists gave to whatever is driving that acceleration.',
      },
      {
        label: 'Related mystery',
        value: 'The Hubble Tension',
        tooltip: 'Two different ways of measuring how fast the universe is expanding give different answers: ~70-76 km/s per megaparsec from nearby supernovae, vs. ~67-68 from the cosmic microwave background (the universe\'s oldest light). Scientists don\'t yet know why the two disagree — it\'s a genuinely unresolved mystery, not just a rounding error.',
      },
    ],
  },
]

/**
 * Segmented horizontal bar showing the universe's composition (Ordinary
 * Matter / Dark Matter / Dark Energy), with the currently-viewed entry's
 * segment highlighted and the other two dimmed.
 *
 * @param props
 * @param props.activeKey - Key of the entry currently being viewed.
 * @returns The composition bar visual.
 */
function CompositionBar({ activeKey }) {
  return (
    <div className="composition-bar">
      {UNIVERSE_ENTRIES.map(entry => (
        <div
          key={entry.key}
          className={`composition-segment ${entry.key === activeKey ? 'active' : 'dimmed'}`}
          style={{ flexBasis: `${entry.percent}%`, backgroundColor: entry.color }}
        >
          <span className="composition-segment-label">{entry.percent}%</span>
        </div>
      ))}
    </div>
  )
}

/**
 * Left-panel visual for a Universe concept entry — the composition bar plus
 * the entry's name and share, in place of Exoplanets' planet image.
 *
 * @param props
 * @param props.entry - One of UNIVERSE_ENTRIES.
 * @returns The concept's left-panel visual.
 */
export function UniverseConceptVisual({ entry }) {
  return (
    <>
      <p className="orbit-scale-title image-section-title-overlay">
        Composition of the Universe
        <Tooltip text="Ordinary matter, dark matter, and dark energy make up the universe's total mass-energy content. This entry's share is highlighted below." />
      </p>
      <div className="universe-concept-visual">
        <CompositionBar activeKey={entry.key} />
        <span className="universe-concept-percent" style={{ color: entry.color }}>{entry.percent}%</span>
        <span className="universe-concept-name" style={{ color: entry.color }}>{entry.name}</span>
      </div>
    </>
  )
}

/**
 * Right-panel stats block for a Universe concept entry — tagline,
 * description, and a fact list, in the same shape as Exoplanets' stats panel.
 *
 * @param props
 * @param props.entry - One of UNIVERSE_ENTRIES.
 * @returns The concept's right-panel stats block.
 */
export function UniverseConceptStats({ entry }) {
  return (
    <>
      <h2>{entry.name}</h2>
      <p className="planet-description">{entry.tagline}</p>

      <hr />
      <p className="section-label">Overview</p>
      <p className="planet-description">{entry.description}</p>

      <hr />
      <p className="section-label">By the Numbers</p>
      <div className="stat-columns">
        {entry.facts.map(fact => (
          <p key={fact.label}>{fact.label}<Tooltip text={fact.tooltip} />
            : <span>{fact.value}</span></p>
        ))}
      </div>
    </>
  )
}
