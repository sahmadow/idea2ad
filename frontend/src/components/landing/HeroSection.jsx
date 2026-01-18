import { useState } from 'react'

function HeroSection({ onSubmit }) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const normalizeUrl = (input) => {
    let normalized = input.trim()
    if (!normalized.match(/^https?:\/\//i)) {
      normalized = 'https://' + normalized
    }
    return normalized
  }

  const isValidDomain = (input) => {
    const cleaned = input.trim().replace(/^https?:\/\//i, '')
    return cleaned.length > 0 && cleaned.includes('.')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!url || !isValidDomain(url)) return

    setLoading(true)
    setError(null)

    try {
      const normalizedUrl = normalizeUrl(url)
      await onSubmit(normalizedUrl)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="hero-section">
      {/* Background glows */}
      <div className="hero-glow hero-glow-primary" />
      <div className="hero-glow hero-glow-accent" />

      {/* Badge */}
      <div className="hero-badge">
        AI-Powered Ad Generation
      </div>

      {/* Headline */}
      <h1 className="hero-headline">
        Say goodbye to manual ad creation
      </h1>

      {/* Subheadline */}
      <p className="hero-subheadline">
        Turn any landing page into a Meta Ads campaign in 60 seconds.
        AI analyzes your page and generates ready-to-launch creatives.
      </p>

      {/* URL Input Form */}
      <form onSubmit={handleSubmit} className="hero-form">
        <input
          type="text"
          className="hero-input"
          placeholder="your-landing-page.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          disabled={loading}
        />
        <button
          type="submit"
          className="hero-cta"
          disabled={loading || !url}
        >
          {loading ? (
            <>
              <span style={{
                width: '16px',
                height: '16px',
                border: '2px solid rgba(255,255,255,0.3)',
                borderTopColor: 'white',
                borderRadius: '50%',
                animation: 'rotation 0.8s linear infinite',
                display: 'inline-block'
              }} />
              Analyzing...
            </>
          ) : (
            <>Generate My First Ad - Free</>
          )}
        </button>
      </form>

      {/* Error Display */}
      {error && (
        <div className="hero-error">
          Error: {error}
        </div>
      )}

      {/* Social Proof */}
      <div className="hero-social-proof">
        <div className="social-proof-avatars">
          <div className="social-proof-avatar">JD</div>
          <div className="social-proof-avatar">MK</div>
          <div className="social-proof-avatar">AS</div>
          <div className="social-proof-avatar">+</div>
        </div>
        <p className="social-proof-text">
          Join <strong>500+ marketers</strong> saving 10+ hours/week
        </p>
      </div>
    </section>
  )
}

export default HeroSection
