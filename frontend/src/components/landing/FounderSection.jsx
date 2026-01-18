function FounderSection() {
  return (
    <section className="landing-section founder-section">
      <h2 className="section-title">Built by a Maker, for Makers</h2>

      <div className="founder-content glass-panel">
        <div className="founder-avatar">S</div>

        <p className="founder-greeting">Hey, I'm Saleh</p>

        <div className="founder-message">
          <p>
            I built LaunchAd because I was tired of spending hours creating
            Meta ads for my projects. Every time I launched something new,
            the ad creation process was the same tedious grind.
          </p>
          <p>
            Now I paste a URL and have a campaign ready in 60 seconds.
            Every feature comes from real pain I felt as a solo founder.
          </p>
        </div>

        <p className="founder-cta-text">Questions? I read every email.</p>

        <a href="mailto:hello@launchad.com" className="founder-email">
          hello@launchad.com
        </a>
      </div>
    </section>
  )
}

export default FounderSection
