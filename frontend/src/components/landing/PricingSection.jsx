function PricingSection({ onGetStarted }) {
  const plans = [
    {
      name: "Single Campaign",
      price: "$29",
      period: "one-time",
      features: [
        "One complete campaign",
        "Full landing page analysis",
        "AI-generated creatives",
        "Export to JSON/TXT"
      ],
      cta: "Get Started",
      popular: false
    },
    {
      name: "Pro Monthly",
      price: "$129",
      period: "/month",
      features: [
        "Unlimited campaigns",
        "Priority support",
        "Direct Meta publishing",
        "Advanced analytics"
      ],
      cta: "Go Pro",
      popular: true
    }
  ]

  return (
    <section className="landing-section pricing-section">
      <h2 className="section-title">Simple Pricing</h2>
      <p className="section-subtitle">
        No hidden fees. Cancel anytime.
      </p>

      <div className="pricing-grid">
        {plans.map((plan, index) => (
          <div
            key={index}
            className={`pricing-card glass-panel ${plan.popular ? 'pricing-card-popular' : ''}`}
          >
            {plan.popular && (
              <div className="pricing-badge">POPULAR</div>
            )}
            <h3 className="pricing-plan-name">{plan.name}</h3>
            <div className="pricing-price">
              <span className="pricing-amount">{plan.price}</span>
              <span className="pricing-period">{plan.period}</span>
            </div>
            <ul className="pricing-features">
              {plan.features.map((feature, i) => (
                <li key={i} className="pricing-feature">
                  <svg
                    className="pricing-check"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>
            <button
              className={`pricing-cta ${plan.popular ? 'pricing-cta-primary' : ''}`}
              onClick={onGetStarted}
            >
              {plan.cta}
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}

export default PricingSection
