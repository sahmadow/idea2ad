function HowItWorksSection() {
  const steps = [
    {
      number: 1,
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
        </svg>
      ),
      title: 'Paste Your URL',
      description: 'Drop your landing page URL and let AI do the heavy lifting'
    },
    {
      number: 2,
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
          <path d="M19 3v4" />
          <path d="M21 5h-4" />
        </svg>
      ),
      title: 'AI Analyzes Everything',
      description: 'We extract your brand colors, USP, pain points, and create targeted ad copy'
    },
    {
      number: 3,
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09Z" />
          <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2Z" />
          <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
          <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
        </svg>
      ),
      title: 'Launch to Meta',
      description: 'One click to publish your campaign directly to Meta Ads Manager'
    }
  ]

  return (
    <section className="landing-section how-it-works">
      <h2 className="section-title">How It Works</h2>
      <p className="section-subtitle">
        Three simple steps from landing page to live ad campaign
      </p>

      <div className="steps-container">
        {steps.map((step, index) => (
          <div key={step.number} className="step-wrapper">
            <div className="step-card glass-panel">
              <span className="step-number">{step.number}</span>
              <div className="step-icon">{step.icon}</div>
              <h3 className="step-title">{step.title}</h3>
              <p className="step-description">{step.description}</p>
            </div>
            {index < steps.length - 1 && (
              <div className="step-connector">
                <svg width="40" height="24" viewBox="0 0 40 24" fill="none" aria-hidden="true">
                  <path d="M0 12h32M24 4l8 8-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}

export default HowItWorksSection
