function TestimonialsSection() {
  const testimonials = [
    {
      quote: "I used to spend days creating ad campaigns. Now it takes me 5 minutes. LaunchAd paid for itself on the first day.",
      name: "Sarah M.",
      role: "Founder, TechStartup",
      initial: "S"
    },
    {
      quote: "The AI nailed our brand voice perfectly. Our CTR improved 40% compared to manually created ads.",
      name: "Alex R.",
      role: "Growth Marketer",
      initial: "A"
    },
    {
      quote: "Finally, a tool that understands indie makers. No bloat, just results. Highly recommend.",
      name: "Jordan K.",
      role: "Solo Entrepreneur",
      initial: "J"
    }
  ]

  return (
    <section className="landing-section testimonials-section">
      <h2 className="section-title">What Marketers Say</h2>

      <div className="testimonials-grid">
        {testimonials.map((testimonial, index) => (
          <div key={index} className="testimonial-card glass-panel">
            <div className="testimonial-quote-mark">"</div>
            <p className="testimonial-quote">{testimonial.quote}</p>
            <div className="testimonial-author">
              <div className="testimonial-avatar">
                {testimonial.initial}
              </div>
              <div className="testimonial-info">
                <span className="testimonial-name">{testimonial.name}</span>
                <span className="testimonial-role">{testimonial.role}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

export default TestimonialsSection
