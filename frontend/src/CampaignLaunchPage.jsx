import { useState, useEffect } from 'react'
import MetaAdPreview from './MetaAdPreview'

const CTA_OPTIONS = [
  { value: 'LEARN_MORE', label: 'Learn More' },
  { value: 'SHOP_NOW', label: 'Shop Now' },
  { value: 'SIGN_UP', label: 'Sign Up' },
  { value: 'BOOK_NOW', label: 'Book Now' },
  { value: 'CONTACT_US', label: 'Contact Us' },
  { value: 'GET_QUOTE', label: 'Get Quote' },
  { value: 'SUBSCRIBE', label: 'Subscribe' },
  { value: 'DOWNLOAD', label: 'Download' },
]

function CampaignLaunchPage({ selectedAd, campaignData, onBack, onPublishSuccess }) {
  const [fbConnected, setFbConnected] = useState(false)
  const [fbUser, setFbUser] = useState(null)
  const [pages, setPages] = useState([])
  const [selectedPage, setSelectedPage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [error, setError] = useState(null)

  // Campaign settings
  const [budget, setBudget] = useState(50)
  const [duration, setDuration] = useState(3)
  const [cta, setCta] = useState('LEARN_MORE')

  // Check if Facebook SDK is loaded
  useEffect(() => {
    checkFacebookStatus()
  }, [])

  const checkFacebookStatus = async () => {
    // Check if user already connected via backend session
    try {
      const response = await fetch('http://localhost:8000/meta/fb-status', {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        if (data.connected) {
          setFbConnected(true)
          setFbUser(data.user)
          setPages(data.pages || [])
        }
      }
    } catch (err) {
      console.log('FB status check failed, user not connected')
    }
  }

  const handleFacebookLogin = async () => {
    setLoading(true)
    setError(null)

    try {
      // Open Facebook OAuth popup
      const width = 600
      const height = 700
      const left = window.screenX + (window.outerWidth - width) / 2
      const top = window.screenY + (window.outerHeight - height) / 2

      const popup = window.open(
        'http://localhost:8000/auth/facebook',
        'Facebook Login',
        `width=${width},height=${height},left=${left},top=${top}`
      )

      // Listen for OAuth callback
      const handleMessage = async (event) => {
        if (event.origin !== 'http://localhost:8000') return

        if (event.data.type === 'FB_AUTH_SUCCESS') {
          setFbConnected(true)
          setFbUser(event.data.user)

          // Fetch user's pages
          const pagesResponse = await fetch('http://localhost:8000/meta/pages', {
            credentials: 'include'
          })
          if (pagesResponse.ok) {
            const pagesData = await pagesResponse.json()
            setPages(pagesData.pages || [])
          }

          popup?.close()
        } else if (event.data.type === 'FB_AUTH_ERROR') {
          setError(event.data.error || 'Facebook login failed')
          popup?.close()
        }

        window.removeEventListener('message', handleMessage)
      }

      window.addEventListener('message', handleMessage)

      // Poll for popup close
      const pollTimer = setInterval(() => {
        if (popup?.closed) {
          clearInterval(pollTimer)
          setLoading(false)
        }
      }, 500)

    } catch (err) {
      setError('Failed to initiate Facebook login: ' + err.message)
      setLoading(false)
    }
  }

  const handlePublish = async () => {
    if (!selectedPage || !selectedAd) {
      setError('Please select a Facebook Page')
      return
    }

    setPublishing(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/meta/publish-campaign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          page_id: selectedPage.id,
          ad: selectedAd,
          campaign_data: campaignData,
          settings: {
            budget: budget * 100, // Convert to cents
            duration_days: duration,
            call_to_action: cta,
          }
        })
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to publish campaign')
      }

      onPublishSuccess?.(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
      {/* Back Button */}
      <button
        onClick={onBack}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          marginBottom: '2rem',
          fontSize: '1rem'
        }}
      >
        ← Back to Ad Selection
      </button>

      <h1 style={{
        fontSize: '2rem',
        marginBottom: '0.5rem',
        background: 'linear-gradient(to right, #fff, #9ca3af)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
      }}>
        Launch Your Campaign
      </h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Connect your Facebook account and configure your campaign settings
      </p>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(300px, 400px) 1fr',
        gap: '3rem',
        alignItems: 'start'
      }}>
        {/* Left: Ad Preview */}
        <div>
          <h3 style={{ marginBottom: '1rem', color: 'var(--text-muted)' }}>Selected Ad</h3>
          <MetaAdPreview
            ad={selectedAd}
            selected={false}
            onSelect={() => {}}
            pageName={selectedPage?.name || 'Your Page'}
            websiteUrl={campaignData?.project_url || 'yourwebsite.com'}
          />
        </div>

        {/* Right: Settings */}
        <div className="glass-panel">
          {/* Step 1: Facebook Connection */}
          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{
                background: fbConnected ? '#22c55e' : '#3b82f6',
                color: '#fff',
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px'
              }}>
                {fbConnected ? '✓' : '1'}
              </span>
              Connect Facebook
            </h3>

            {!fbConnected ? (
              <button
                onClick={handleFacebookLogin}
                disabled={loading}
                style={{
                  background: '#1877f2',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '12px 24px',
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: loading ? 'wait' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  width: '100%',
                  justifyContent: 'center'
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
                {loading ? 'Connecting...' : 'Sign in with Facebook'}
              </button>
            ) : (
              <div style={{
                background: 'rgba(34, 197, 94, 0.1)',
                border: '1px solid rgba(34, 197, 94, 0.3)',
                borderRadius: '8px',
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: '#1877f2',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  fontWeight: 600
                }}>
                  {fbUser?.name?.charAt(0) || 'U'}
                </div>
                <div>
                  <div style={{ fontWeight: 600 }}>{fbUser?.name || 'Connected'}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Facebook connected</div>
                </div>
                <span style={{ marginLeft: 'auto', color: '#22c55e' }}>✓</span>
              </div>
            )}
          </div>

          {/* Step 2: Page Selection */}
          <div style={{ marginBottom: '2rem', opacity: fbConnected ? 1 : 0.5, pointerEvents: fbConnected ? 'auto' : 'none' }}>
            <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{
                background: selectedPage ? '#22c55e' : '#3b82f6',
                color: '#fff',
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px'
              }}>
                {selectedPage ? '✓' : '2'}
              </span>
              Select Facebook Page
            </h3>

            {pages.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {pages.map(page => (
                  <label
                    key={page.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 16px',
                      background: selectedPage?.id === page.id ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                      border: selectedPage?.id === page.id ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      cursor: 'pointer'
                    }}
                  >
                    <input
                      type="radio"
                      name="page"
                      checked={selectedPage?.id === page.id}
                      onChange={() => setSelectedPage(page)}
                      style={{ width: '18px', height: '18px' }}
                    />
                    <div>
                      <div style={{ fontWeight: 500 }}>{page.name}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {page.category || 'Facebook Page'}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <div style={{
                padding: '1rem',
                background: 'rgba(255,255,255,0.05)',
                borderRadius: '8px',
                color: 'var(--text-muted)',
                textAlign: 'center'
              }}>
                {fbConnected ? 'No pages found. Please ensure you have admin access to a Facebook Page.' : 'Connect Facebook to see your pages'}
              </div>
            )}
          </div>

          {/* Step 3: Campaign Settings */}
          <div style={{ marginBottom: '2rem', opacity: selectedPage ? 1 : 0.5, pointerEvents: selectedPage ? 'auto' : 'none' }}>
            <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{
                background: '#3b82f6',
                color: '#fff',
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px'
              }}>
                3
              </span>
              Campaign Settings
            </h3>

            <div style={{ display: 'grid', gap: '1.5rem' }}>
              {/* Budget */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Total Budget
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>$</span>
                  <input
                    type="number"
                    min="5"
                    max="10000"
                    value={budget}
                    onChange={(e) => setBudget(Math.max(5, parseInt(e.target.value) || 0))}
                    className="input-field"
                    style={{ flex: 1 }}
                  />
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>USD</span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Daily spend: ${(budget / duration).toFixed(2)}/day
                </div>
              </div>

              {/* Duration */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Duration
                </label>
                <select
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  className="input-field"
                  style={{ width: '100%' }}
                >
                  <option value={3}>3 days (Recommended)</option>
                  <option value={5}>5 days</option>
                  <option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={30}>30 days</option>
                </select>
              </div>

              {/* CTA */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Call to Action
                </label>
                <select
                  value={cta}
                  onChange={(e) => setCta(e.target.value)}
                  className="input-field"
                  style={{ width: '100%' }}
                >
                  {CTA_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              padding: '12px 16px',
              marginBottom: '1.5rem',
              color: '#ef4444'
            }}>
              {error}
            </div>
          )}

          {/* Publish Button */}
          <button
            onClick={handlePublish}
            disabled={!fbConnected || !selectedPage || publishing}
            className="btn-primary"
            style={{
              width: '100%',
              padding: '16px',
              fontSize: '1.1rem',
              fontWeight: 600,
              background: (fbConnected && selectedPage && !publishing)
                ? 'linear-gradient(135deg, #22c55e, #16a34a)'
                : 'rgba(255,255,255,0.1)',
              opacity: (fbConnected && selectedPage && !publishing) ? 1 : 0.5,
              cursor: (fbConnected && selectedPage && !publishing) ? 'pointer' : 'not-allowed'
            }}
          >
            {publishing ? '⏳ Publishing...' : '🚀 Publish Now'}
          </button>

          <p style={{
            textAlign: 'center',
            fontSize: '0.8rem',
            color: 'var(--text-muted)',
            marginTop: '1rem'
          }}>
            Campaign will be created in PAUSED status for your review
          </p>
        </div>
      </div>
    </div>
  )
}

export default CampaignLaunchPage
