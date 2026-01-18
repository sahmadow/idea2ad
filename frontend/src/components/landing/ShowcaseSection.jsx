import { useState, useEffect, useRef } from 'react'

function ShowcaseSection() {
  const [isVisible, setIsVisible] = useState(false)
  const [activeStep, setActiveStep] = useState(0)
  const [metrics, setMetrics] = useState({
    impressions: 0,
    clicks: 0,
    conversions: 0,
    cpc: 0
  })
  const sectionRef = useRef(null)
  const hasAnimated = useRef(false)

  const targetMetrics = {
    impressions: 2847,
    clicks: 412,
    conversions: 23,
    cpc: 1.24
  }

  // Intersection observer for scroll trigger
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          setIsVisible(true)
          hasAnimated.current = true
        }
      },
      { threshold: 0.2 }
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    return () => observer.disconnect()
  }, [])

  // Step progression animation
  useEffect(() => {
    if (!isVisible) return

    const stepTimers = [
      setTimeout(() => setActiveStep(1), 1500),
      setTimeout(() => setActiveStep(2), 3000)
    ]

    return () => stepTimers.forEach(clearTimeout)
  }, [isVisible])

  // Metric counting animation
  useEffect(() => {
    if (activeStep !== 2) return

    const duration = 1500
    const steps = 60
    const interval = duration / steps

    let currentStep = 0
    const timer = setInterval(() => {
      currentStep++
      const progress = currentStep / steps
      const easeOut = 1 - Math.pow(1 - progress, 3)

      setMetrics({
        impressions: Math.round(targetMetrics.impressions * easeOut),
        clicks: Math.round(targetMetrics.clicks * easeOut),
        conversions: Math.round(targetMetrics.conversions * easeOut),
        cpc: Math.round(targetMetrics.cpc * easeOut * 100) / 100
      })

      if (currentStep >= steps) {
        clearInterval(timer)
        setMetrics(targetMetrics)
      }
    }, interval)

    return () => clearInterval(timer)
  }, [activeStep])

  return (
    <section ref={sectionRef} className="landing-section showcase-section">
      <h2 className="section-title">See It In Action</h2>
      <p className="section-subtitle">
        Watch how a landing page transforms into a high-converting ad campaign
      </p>

      <div className="showcase-workflow">
        {/* Step 1: Browser Mockup */}
        <div className={`workflow-step ${isVisible && activeStep >= 0 ? 'visible' : ''} ${activeStep === 0 ? 'active' : ''}`}>
          <span className="workflow-step-number">1</span>
          <div className="browser-mockup glass-panel">
            <div className="browser-header">
              <div className="browser-dots">
                <span className="dot red"></span>
                <span className="dot yellow"></span>
                <span className="dot green"></span>
              </div>
              <div className="browser-url-bar">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <span>https://yourproduct.com</span>
              </div>
            </div>
            <div className="browser-content">
              {/* Wireframe nav */}
              <div className="wireframe-nav">
                <div className="wireframe-logo"></div>
                <div className="wireframe-nav-links">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
              {/* Wireframe hero */}
              <div className="wireframe-hero">
                <div className="wireframe-badge"></div>
                <div className="wireframe-headline"></div>
                <div className="wireframe-subline"></div>
                <div className="wireframe-cta"></div>
              </div>
              {/* Wireframe features */}
              <div className="wireframe-features">
                <div className="wireframe-card"></div>
                <div className="wireframe-card"></div>
                <div className="wireframe-card"></div>
              </div>
            </div>
          </div>
          <span className="workflow-step-label">Your Landing Page</span>
        </div>

        {/* Connector 1 */}
        <div className={`workflow-connector ${isVisible && activeStep >= 1 ? 'visible' : ''}`}>
          <svg width="40" height="24" viewBox="0 0 40 24" fill="none" aria-hidden="true">
            <path d="M0 12h32M24 4l8 8-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>

        {/* Step 2: Ad Preview */}
        <div className={`workflow-step ${isVisible && activeStep >= 1 ? 'visible' : ''} ${activeStep === 1 ? 'active' : ''}`} style={{ animationDelay: '0.3s' }}>
          <span className="workflow-step-number">2</span>
          <div className="ad-preview-mockup glass-panel">
            <div className="ad-header">
              <div className="ad-avatar">L</div>
              <div className="ad-meta">
                <span className="ad-name">LaunchAd</span>
                <span className="ad-sponsored">Sponsored</span>
              </div>
              <svg className="ad-more" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <circle cx="12" cy="5" r="2" />
                <circle cx="12" cy="12" r="2" />
                <circle cx="12" cy="19" r="2" />
              </svg>
            </div>
            <p className="ad-text">
              Stop wasting hours on ad creation. Get AI-generated campaigns that convert in 60 seconds.
            </p>
            <div className="ad-image-placeholder">
              <div className="ad-image-gradient"></div>
            </div>
            <div className="ad-footer">
              <div className="ad-info">
                <span className="ad-headline">Launch Your Product Faster</span>
                <span className="ad-description">Try free - No credit card required</span>
              </div>
              <button className="ad-cta-btn">Learn more</button>
            </div>
          </div>
          <span className="workflow-step-label">Generated Ad</span>
        </div>

        {/* Connector 2 */}
        <div className={`workflow-connector ${isVisible && activeStep >= 2 ? 'visible' : ''}`}>
          <svg width="40" height="24" viewBox="0 0 40 24" fill="none" aria-hidden="true">
            <path d="M0 12h32M24 4l8 8-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>

        {/* Step 3: Results Dashboard */}
        <div className={`workflow-step ${isVisible && activeStep >= 2 ? 'visible' : ''} ${activeStep === 2 ? 'active' : ''}`} style={{ animationDelay: '0.6s' }}>
          <span className="workflow-step-number">3</span>
          <div className="results-dashboard glass-panel">
            <div className="dashboard-header">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M3 3v18h18" />
                <path d="m19 9-5 5-4-4-3 3" />
              </svg>
              <span>Campaign Results</span>
            </div>
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-value">{metrics.impressions.toLocaleString()}</span>
                <span className="metric-label">Impressions</span>
              </div>
              <div className="metric-card">
                <span className="metric-value">{metrics.clicks.toLocaleString()}</span>
                <span className="metric-label">Clicks</span>
              </div>
              <div className="metric-card">
                <span className="metric-value">{metrics.conversions}</span>
                <span className="metric-label">Conversions</span>
              </div>
              <div className="metric-card">
                <span className="metric-value">${metrics.cpc.toFixed(2)}</span>
                <span className="metric-label">CPC</span>
              </div>
            </div>
          </div>
          <span className="workflow-step-label">Real Results</span>
        </div>
      </div>
    </section>
  )
}

export default ShowcaseSection
