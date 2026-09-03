import { useState } from 'react'
import './AboutPage.css'

const PAGES = [
  {
    navTitle: 'About',
    title: 'About',
    content: (
      <>
        <section>
          <h2>Author</h2>
          <h4>Zac Cheatle</h4>
          <p>
            {' '}
            <a href="https://github.com/zaccheatle/cosmidex" target="_blank" rel="noreferrer">
            Github Repository
            </a>{' '} |
            {' '}
            <a href="https://www.linkedin.com/in/zaccheatle/" target="_blank" rel="noreferrer">
              LinkedIn
            </a>{' '}
          </p>
        </section>

        <section>
          <h2>Project Background</h2>
          <p>
            CosmiDex is a personal passion project that turns real astronomical data into
            something you can actually explore. It's a
            cross between 10-year-old Zac's love for Pokémon and adult Zac's
            love for space, where each cosmic
            entity gets its own Pokedex-style catalog entry for the user to explore at their own pace.
          </p>
        </section>
      </>
    ),
  },
  {
    navTitle: 'Architecture',
    title: 'Architecture',
    content: (
      <section>
        <p>
          Cosmidex is a full-stack ELT data engineering project. Data ingestion is orchestrated
          via Dagster → Postgres → layered dbt transforms (Bronze →
          Silver → Gold) → FastAPI → React. Cosmo, the in-app chat
          assistant, runs on Claude's tool-use API against a standalone MCP
          server exposing structured query tools (lookup, search, compare)
          for each cosmic entity, plus a pgvector RAG layer over reference
          articles for conceptual questions. The MCP server also runs
          standalone, so any MCP-compatible client can query the catalog directly.
          Cosmidex is deployed via AWS: Postgres and the API share a single
          EC2 instance — the API deploys as a Docker container via ECS,
          Postgres runs as a plain Docker container alongside it — generated
          artwork sits in S3 behind CloudFront, and the
          pipeline's scheduling lives in Dagster Cloud. As a self-funded solo project, 
          Cosmidex doesn't need a fully-managed, private setup — 
          but I still tried to follow production best practices where it made sense:
          Github repo & project board with milestones/issues, Terraform for IaC, 
          Docker for containerized deployment, and CI/CD via GitHub Actions and AWS Codepipeline.
        </p>
      </section>
    ),
  },
  {
    navTitle: 'Methodology: Universe',
    title: 'Methodology — The Universe',
    content: (
      <section>
        <h3>Data Source(s)</h3>
        <p></p>
        <h4>Articles</h4>
        <ul>
          <li>
            <a href="https://science.nasa.gov/universe/overview/" target="_blank" rel="noreferrer">
              The Universe's History
            </a> — NASA
          </li>
          <li>
            <a href="https://science.nasa.gov/universe/dark-matter-dark-energy/" target="_blank" rel="noreferrer">
              Dark Matter
            </a> — NASA (Chelsea Gohd, JPL)
          </li>
          <li>
            <a href="https://science.nasa.gov/mission/hubble/science/science-behind-the-discoveries/hubble-constant-and-tension/" target="_blank" rel="noreferrer">
              The Hubble Constant and Hubble Tension
            </a> — NASA
          </li>
        </ul>
        <h3>Caculated Metrics</h3>
        <p>None</p>
        <h3>Known Limitations</h3>
        <p>None</p>
        <h3>AI Generated Content</h3>
        <p>None</p>
      </section>
    ),
  },
  {
    navTitle: 'Methodology: Galaxies',
    title: 'Methodology — Galaxies',
    content: (
      <section>
        <h3>Data Source(s)</h3>
        <p></p>
        <h4>Articles</h4>
        <ul></ul>
        <h3>Caculated Metrics</h3>
        <p></p>
        <h3>Known Limitations</h3>
        <p></p>
        <h3>AI Generated Content</h3>
        <p></p>
      </section>
    ),
  },
  {
    navTitle: 'Methodology: Exoplanets',
    title: 'Methodology — Exoplanets',
    content: (
      <section>
        <h3>Data Source(s)</h3>
        <p>
          Exoplanet data comes from NASA's{' '}
          <a href="https://exoplanetarchive.ipac.caltech.edu/" target="_blank" rel="noreferrer"> Exoplanet Archive </a>{' '}
          (PSCompPars — Planetary Systems Composite Parameters table), pulled via its TAP service.
          CosmiDex displays all planets that fall into Tier 1, 2, or 3 of our habitability classification only;
          non-habitable planets are not shown but are available via the chatbox!
        </p>
        <h4>Articles</h4>
        <ul>
          <li>
            <a href="https://spaceplace.nasa.gov/all-about-exoplanets/en/" target="_blank" rel="noreferrer">
              All About Exoplanets
            </a> — NASA Space Place
          </li>
          <li>
            <a href="https://science.nasa.gov/exoplanets/how-we-find-and-characterize/" target="_blank" rel="noreferrer">
              How We Find and Characterize Exoplanets
            </a> — NASA
          </li>
          <li>
            <a href="https://science.nasa.gov/exoplanets/habitable-zone/" target="_blank" rel="noreferrer">
              The Habitable Zone
            </a> — NASA
          </li>
          <li>
            <a href="https://science.nasa.gov/universe/stars/" target="_blank" rel="noreferrer">
              Stars
            </a> — NASA
          </li>
          <li>
            <a href="https://science.nasa.gov/universe/stars/types/" target="_blank" rel="noreferrer">
              Star Types
            </a> — NASA
          </li>
        </ul>
        <h3>Calculated Metrics</h3>
        <p>
          <strong>Earth Similarity Index (ESI)</strong> is a weighted product of how closely a
          planet's radius, density, escape velocity, and equilibrium temperature match Earth's —
          temperature is weighted most heavily. 1.0 = identical to Earth, 0 = completely alien.
        </p>
        <p>
          <strong>Habitable Zone Distance (HZD)</strong> measures where a planet sits within its
          star's habitable zone: <code>(2 × orbital distance − hz_inner − hz_outer) / (hz_outer − hz_inner)</code>.
          0 = center of the zone, ±1 = the inner/outer edge.
        </p>
        <p>
          <strong>Tiers</strong> — Tier 1: ESI ≥ 0.8, in the conservative habitable zone, rocky
          composition, low orbital eccentricity, orbits an F/G/K star. Tier 2: ESI ≥ 0.6, in the
          habitable zone, rocky. Tier 3: in the habitable zone only, regardless of size or
          composition. Everything else is Non-Habitable.
        </p>
        <h3>Known Limitations</h3>
        <ul>
          <li>
            Surface temperature is estimated from stellar flux and distance, not measured — actual
            conditions (atmosphere, greenhouse effect, weather) are unknown for nearly all of these
            planets.
          </li>
          <li>
            An orbital eccentricity of exactly 0 sometimes means the orbit was assumed circular
            during fitting due to limited observational data, rather than confirmed as circular.
          </li>
          <li>
            Composition (Rock/Iron, Rock/Silicate, Water/Ice, Ice Giant, Gas Giant) is inferred from
            density alone — a coarse classification, not a direct measurement.
          </li>
        </ul>
        <h3>AI Generated Content</h3>
        <p>
          Planet illustrations and the size-comparison-vs-Earth images are generated by Google's
          Gemini image model, prompted using only real measured/derived fields already in the data
          (composition category, radius ratio, star spectral type) — no invented terrain, weather,
          or geology, since the underlying dataset doesn't include that. Planet descriptions are
          generated by Google's Gemini model from the same underlying stats. Both are marked with an
          "AI-generated" note wherever they appear.
        </p>
      </section>
    ),
  },
  {
    navTitle: 'Methodology: Solar System',
    title: 'Methodology — The Solar System',
    content: (
      <section>
        <h3>Data Source(s)</h3>
        <p></p>
        <h4>Articles</h4>
        <ul></ul>
        <h3>Caculated Metrics</h3>
        <p></p>
        <h3>Known Limitations</h3>
        <p></p>
        <h3>AI Generated Content</h3>
        <p></p>
      </section>
    ),
  },
  {
    navTitle: 'Roadmap',
    title: 'Roadmap',
    content: (
      <section>
        <h3>Upcoming Cosmic Entities</h3>
        <ul>
          <li><strong>Black Holes</strong> — a curated set of well-measured black holes, e.g. Sagittarius A* and M87*.</li>
          <li><strong>Nebulae</strong> — cataloged nebulae with type, distance, size, and composition.</li>
          <li><strong>Comets &amp; Asteroids</strong> — sourced from NASA JPL's Small-Body Database, the same kind of real structured catalog exoplanets already use.</li>
          <li><strong>Stars</strong> — notable individually-named stars (Sirius, Betelgeuse, Proxima Centauri) from the IAU's official list of approved star names.</li>
          <li><strong>Neutron Stars</strong> — a curated set of well-known pulsars (Crab Pulsar, Vela Pulsar) from the ATNF Pulsar Catalogue.</li>
        </ul>
      </section>
    ),
  },
]

/**
 * Full-screen overlay introducing CosmiDex — author, description, architecture,
 * per-entity data methodology, and roadmap, paged via a table of contents plus
 * a Prev/Next footer.
 *
 * @param props
 * @param props.onClose - Called when the user dismisses the overlay.
 * @returns The About overlay panel.
 */
export default function AboutPage({ onClose }) {
  const [page, setPage] = useState(0)
  const current = PAGES[page]

  return (
    <div className="about-overlay">
      <div className="about-panel">
        <button className="about-close" onClick={onClose} aria-label="Close">×</button>

        <h1>{current.title}</h1>

        <nav className="about-toc">
          {PAGES.map((p, i) => (
            <button
              key={p.navTitle}
              className={`about-toc-btn${i === page ? ' active' : ''}`}
              onClick={() => setPage(i)}
            >
              {p.navTitle}
            </button>
          ))}
        </nav>

        {current.content}

        <footer className="navigation">
          <button
            onClick={() => setPage(p => p - 1)}
            disabled={page === 0}
          >
            ← Previous
          </button>
          <span>{page + 1} / {PAGES.length}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page === PAGES.length - 1}
          >
            Next →
          </button>
        </footer>
      </div>
    </div>
  )
}
