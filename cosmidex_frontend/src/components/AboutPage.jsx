import './AboutPage.css'

/**
 * Full-screen overlay introducing CosmiDex and its author — project background,
 * roadmap, and links to the GitHub repo and LinkedIn. For the technical
 * data-source/methodology write-up, see MethodologyPage instead.
 *
 * @param props
 * @param props.onClose - Called when the user dismisses the overlay.
 * @returns The About overlay panel.
 */
export default function AboutPage({ onClose }) {
  return (
    <div className="about-overlay">
      <div className="about-panel">
        <button className="about-close" onClick={onClose} aria-label="Close">×</button>

        <h1>About</h1>

        <section>
          <h2>Author</h2>
          <h3>Zac Cheatle</h3>
          <p>
            {' '}
            <a href="https://github.com/zaccheatle/cosmidex" target="_blank" rel="noreferrer">
              Cosmidex Github Repository
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
            Placeholder
          </p>
        </section>

        <section>
          <h2>Project Roadmap</h2>
          <p>
            Placeholder
          </p>
        </section>

      </div>
    </div>
  )
}
