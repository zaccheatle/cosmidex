import './LandingPage.css'
import './AboutPage.css'

/**
 * Intro/hero screen shown before the planet explorer — gives cold visitors
 * context on what CosmiDex is before dropping them into a random planet's
 * stats. Always shown on load; dismissing it just reveals the explorer,
 * which has been loading its data in the background the whole time.
 *
 * @param props
 * @param props.onEnter - Called when the user clicks through to the explorer.
 * @param props.onShowAbout - Called when the user clicks "About".
 * @returns The landing page overlay.
 */
export default function LandingPage({ onEnter, onShowAbout }) {
  return (
    <div className="landing-page">
      <div className="landing-starfield" />

      <div className="landing-content"> 
        <h1 className="landing-title">🌌Cosmidex</h1>
        <p className="landing-tagline">A Codex for the Cosmos</p>

        <p className="landing-intro">
          An interactive, Pokédex like explorer of cosmic entities across the Milky Way.
        </p>

        <div className="landing-stats">
          <div className="landing-stat">
            <span className="landing-stat-value">6,324</span>
            <span className="landing-stat-label">Confirmed Exoplanets</span>
          </div>
          <div className="landing-stat">
            <span className="landing-stat-value">75</span>
            <span className="landing-stat-label">Potentially Habitable Worlds</span>
          </div>
        </div>

        <div className="landing-actions">
          <button className="landing-enter-btn" onClick={onEnter}>
            Explore the Codex→
          </button>
          <button className="landing-about-btn" onClick={onShowAbout}>
            About
          </button>
        </div>
      </div>
    </div>
  )
}
