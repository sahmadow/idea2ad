import HeroSection from './components/landing/HeroSection'
import ShowcaseSection from './components/landing/ShowcaseSection'
import HowItWorksSection from './components/landing/HowItWorksSection'
import FeaturesSection from './components/landing/FeaturesSection'
import TestimonialsSection from './components/landing/TestimonialsSection'
import PricingSection from './components/landing/PricingSection'
import FounderSection from './components/landing/FounderSection'
import Footer from './components/landing/Footer'
import './LandingPage.css'

function LandingPage({ onTryNow, onLogin }) {
  const handleUrlSubmit = async (url) => {
    // Pass URL to parent and trigger the try now flow
    await onTryNow(url)
  }

  return (
    <div style={{
      position: 'relative',
      minHeight: '100vh',
      overflow: 'hidden'
    }}>
      {/* Navigation */}
      <nav style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1rem 2rem',
        background: 'rgba(15, 17, 21, 0.8)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        zIndex: 100
      }}>
        <h1 style={{
          fontSize: '1.5rem',
          margin: 0,
          background: 'linear-gradient(to right, #fff, #9ca3af)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontWeight: 700
        }}>
          LaunchAd
        </h1>
        <button
          onClick={onLogin}
          style={{
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            color: 'white',
            padding: '0.5rem 1.25rem',
            borderRadius: '8px',
            fontSize: '0.9rem',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)'
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'
          }}
        >
          Sign In
        </button>
      </nav>

      {/* Hero Section */}
      <HeroSection onSubmit={handleUrlSubmit} />

      {/* Showcase Section */}
      <ShowcaseSection />

      {/* How It Works Section */}
      <HowItWorksSection />

      {/* Features Section */}
      <FeaturesSection />

      {/* Testimonials Section */}
      <TestimonialsSection />

      {/* Pricing Section */}
      <PricingSection onGetStarted={() => onTryNow('')} />

      {/* Founder Section */}
      <FounderSection />

      {/* Footer */}
      <Footer />
    </div>
  )
}

export default LandingPage
