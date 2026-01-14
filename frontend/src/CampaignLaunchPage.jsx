import { useState, useEffect, useRef } from 'react'
import MetaAdPreview from './MetaAdPreview'

// API URL from environment
const API_URL = import.meta.env.VITE_API_URL || "https://idea2ad-production.up.railway.app"

// Fixed campaign settings
const DURATION_DAYS = 3
const CTA_VALUE = 'LEARN_MORE'
const CTA_LABEL = 'Learn More'

// Helper to get session token from localStorage
const getSessionToken = () => localStorage.getItem('fb_session')

// Helper to make authenticated API calls
const apiCall = async (endpoint, options = {}) => {
  const token = getSessionToken()
  const headers = {
    ...options.headers,
  }
  if (token) {
    headers['X-FB-Session'] = token
  }
  return fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include'  // Also try cookies as fallback
  })
}

function CampaignLaunchPage({ selectedAd, campaignData, onBack, onPublishSuccess, onOAuthStart }) {
  const [fbConnected, setFbConnected] = useState(false)
  const [fbUser, setFbUser] = useState(null)
  const [pages, setPages] = useState([])
  const [selectedPage, setSelectedPage] = useState(null)
  const [adAccounts, setAdAccounts] = useState([])
  const [selectedAdAccount, setSelectedAdAccount] = useState(null)
  const [loading, setLoading] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [error, setError] = useState(null)

  // Campaign settings
  const [budget, setBudget] = useState(50)
  const [locations, setLocations] = useState([])
  const [locationQuery, setLocationQuery] = useState('')
  const [locationSuggestions, setLocationSuggestions] = useState([])
  const [searchingLocations, setSearchingLocations] = useState(false)
  const locationDropdownRef = useRef(null)

  // Payment method status
  const [hasPaymentMethod, setHasPaymentMethod] = useState(null) // null = not checked, true/false = checked
  const [paymentCheckLoading, setPaymentCheckLoading] = useState(false)
  const [addPaymentUrl, setAddPaymentUrl] = useState('https://business.facebook.com/settings/billing/payment_methods')

  // Check for session token (App.jsx already stored it from URL, just verify and check status)
  useEffect(() => {
    const token = localStorage.getItem('fb_session')
    console.log('[Launch OAuth] Mounted, fb_session in localStorage:', token ? 'present' : 'absent')

    if (token) {
      console.log('[Launch OAuth] Token found, checking FB status')
      checkFacebookStatus()
    }
  }, [])

  // Check Facebook status on mount
  useEffect(() => {
    checkFacebookStatus()
  }, [])

  // Click outside to close location dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (locationDropdownRef.current && !locationDropdownRef.current.contains(event.target)) {
        setLocationSuggestions([])
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Debounced location search
  useEffect(() => {
    if (locationQuery.length < 2) {
      setLocationSuggestions([])
      return
    }

    const timer = setTimeout(async () => {
      setSearchingLocations(true)
      try {
        const response = await fetch(
          `${API_URL}/meta/location-search?q=${encodeURIComponent(locationQuery)}`,
          { credentials: 'include' }
        )
        if (response.ok) {
          const data = await response.json()
          setLocationSuggestions(data.cities || [])
        }
      } catch {
        // Silently fail on location search
      } finally {
        setSearchingLocations(false)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [locationQuery])

  const addLocation = (city) => {
    if (!locations.find(l => l.key === city.key)) {
      setLocations([...locations, city])
    }
    setLocationQuery('')
    setLocationSuggestions([])
  }

  const removeLocation = (key) => {
    setLocations(locations.filter(l => l.key !== key))
  }

  const checkFacebookStatus = async () => {
    // Check if user already connected via backend session
    try {
      console.log('[OAuth] Checking fb-status with token:', getSessionToken()?.slice(0, 8) + '...')
      const response = await apiCall('/meta/fb-status')

      if (response.ok) {
        const data = await response.json()
        console.log('[OAuth] fb-status response:', data)
        if (data.connected) {
          setFbConnected(true)
          setFbUser(data.user)
          setPages(data.pages || [])
          setAdAccounts(data.adAccounts || [])
          // Auto-select first ad account if available
          if (data.adAccounts?.length > 0) {
            const selected = data.adAccounts.find(a => a.id === data.selectedAdAccountId) || data.adAccounts[0]
            setSelectedAdAccount(selected)
          }
        }
      }
    } catch (err) {
      console.log('[OAuth] fb-status check failed:', err)
      // User not connected to FB - expected state
    }
  }

  // Check payment method status for selected ad account
  const checkPaymentStatus = async () => {
    if (!selectedAdAccount) {
      setHasPaymentMethod(null)
      return
    }

    setPaymentCheckLoading(true)
    try {
      console.log('[Payment] Checking payment status for:', selectedAdAccount.id)
      const response = await apiCall(`/meta/payment-status?ad_account_id=${selectedAdAccount.id}`)

      if (response.ok) {
        const data = await response.json()
        console.log('[Payment] Status response:', data)
        setHasPaymentMethod(data.has_payment_method)
        if (data.add_payment_url) {
          setAddPaymentUrl(data.add_payment_url)
        }
      } else {
        console.log('[Payment] Check failed, response not ok')
        setHasPaymentMethod(false)
      }
    } catch (err) {
      console.log('[Payment] Check failed:', err)
      setHasPaymentMethod(false)
    } finally {
      setPaymentCheckLoading(false)
    }
  }

  // Check payment status when ad account changes
  useEffect(() => {
    if (selectedAdAccount) {
      checkPaymentStatus()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAdAccount?.id])

  const handleFacebookLogin = async () => {
    console.log('[Launch OAuth] Starting login, saving campaign state via onOAuthStart')
    onOAuthStart?.() // Save state before OAuth in case redirect happens
    setLoading(true)
    setError(null)

    console.log('[Launch OAuth] Opening Facebook login popup')
    console.log('[OAuth] API_URL:', API_URL)

    try {
      const width = 600
      const height = 700
      const left = window.screenX + (window.outerWidth - width) / 2
      const top = window.screenY + (window.outerHeight - height) / 2

      const popup = window.open(
        `${API_URL}/auth/facebook`,
        'Facebook Login',
        `width=${width},height=${height},left=${left},top=${top}`
      )
      console.log('[OAuth] Popup opened:', popup ? 'success' : 'BLOCKED')

      // Helper function to handle successful session
      const handleSessionSuccess = async (sessionId) => {
        console.log('[OAuth] Handling session success:', sessionId?.slice(0, 8) + '...')
        // Store session in localStorage
        if (sessionId) {
          localStorage.setItem('fb_session', sessionId)
          console.log('[OAuth] Session stored in localStorage')
        }

        // Check session status via API
        try {
          const response = await apiCall('/meta/fb-status')
          console.log('[OAuth] fb-status response status:', response.status)

          if (response.ok) {
            const data = await response.json()
            console.log('[OAuth] fb-status data:', data)

            if (data.connected) {
              console.log('[OAuth] Connected! Setting state...')
              setFbConnected(true)
              setFbUser(data.user)
              setPages(data.pages || [])
              setAdAccounts(data.adAccounts || [])

              if (data.adAccounts?.length > 0) {
                const selected = data.adAccounts.find(a => a.id === data.selectedAdAccountId) || data.adAccounts[0]
                setSelectedAdAccount(selected)
              }
            } else {
              console.log('[OAuth] Not connected after OAuth flow')
            }
          } else {
            console.error('[OAuth] fb-status failed:', response.status)
          }
        } catch (err) {
          console.error('[OAuth] Session check failed:', err)
          setError('Failed to verify Facebook connection')
        }

        setLoading(false)
      }

      // Listen for postMessage from OAuth callback (cross-domain)
      const messageHandler = async (event) => {
        // Verify message is from our API domain
        if (event.data?.type === 'FB_AUTH_SUCCESS' && event.data?.session_id) {
          console.log('[OAuth] Received postMessage with session')
          window.removeEventListener('message', messageHandler)
          clearInterval(pollTimer)
          await handleSessionSuccess(event.data.session_id)
        } else if (event.data?.type === 'FB_AUTH_ERROR') {
          console.error('[OAuth] Auth error:', event.data.error)
          window.removeEventListener('message', messageHandler)
          clearInterval(pollTimer)
          setError('Facebook login failed: ' + event.data.error)
          setLoading(false)
        }
      }
      window.addEventListener('message', messageHandler)

      // Also poll for popup close as fallback (in case postMessage fails)
      const pollTimer = setInterval(async () => {
        if (popup?.closed) {
          clearInterval(pollTimer)
          console.log('[OAuth] Popup closed, checking if session was received...')

          // Give postMessage a moment to be processed
          setTimeout(async () => {
            // Only check via API if we haven't already handled via postMessage
            if (!fbConnected) {
              window.removeEventListener('message', messageHandler)
              console.log('[OAuth] Checking session via API fallback...')
              await handleSessionSuccess(null) // Will use existing localStorage token if any
            }
          }, 100)
        }
      }, 500)

      // Cleanup after 5 minutes (timeout)
      setTimeout(() => {
        window.removeEventListener('message', messageHandler)
        clearInterval(pollTimer)
        if (!fbConnected) {
          setLoading(false)
        }
      }, 5 * 60 * 1000)

    } catch (err) {
      console.error('[OAuth] Error:', err)
      setError('Failed to initiate Facebook login: ' + err.message)
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await fetch(`${API_URL}/meta/disconnect`, {
        method: 'POST',
        credentials: 'include'
      })
      // Reset all Facebook-related state
      setFbConnected(false)
      setFbUser(null)
      setPages([])
      setAdAccounts([])
      setSelectedPage(null)
      setSelectedAdAccount(null)
    } catch (err) {
      setError('Failed to disconnect: ' + err.message)
    }
  }

  const handlePublish = async () => {
    if (!selectedPage || !selectedAd) {
      setError('Please select a Facebook Page')
      return
    }

    if (!selectedAdAccount) {
      setError('Please select an Ad Account')
      return
    }

    setPublishing(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/meta/publish-campaign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          page_id: selectedPage.id,
          ad_account_id: selectedAdAccount.id,
          ad: selectedAd,
          campaign_data: campaignData,
          settings: {
            budget: budget * 100, // Convert to cents
            duration_days: DURATION_DAYS,
            call_to_action: CTA_VALUE,
            locations: locations.map(l => ({ key: l.key, name: l.name })),
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
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{fbUser?.name || 'Connected'}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Facebook connected</div>
                </div>
                <span style={{ color: '#22c55e', marginRight: '8px' }}>✓</span>
                <button
                  onClick={handleDisconnect}
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontSize: '0.85rem',
                    color: 'var(--text-muted)',
                    cursor: 'pointer'
                  }}
                >
                  Disconnect
                </button>
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

          {/* Step 3: Ad Account Selection */}
          <div style={{ marginBottom: '2rem', opacity: selectedPage ? 1 : 0.5, pointerEvents: selectedPage ? 'auto' : 'none' }}>
            <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{
                background: selectedAdAccount ? '#22c55e' : '#3b82f6',
                color: '#fff',
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px'
              }}>
                {selectedAdAccount ? '✓' : '3'}
              </span>
              Select Ad Account
            </h3>

            {adAccounts.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {adAccounts.map(account => (
                  <label
                    key={account.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 16px',
                      background: selectedAdAccount?.id === account.id ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                      border: selectedAdAccount?.id === account.id ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      cursor: 'pointer'
                    }}
                  >
                    <input
                      type="radio"
                      name="adAccount"
                      checked={selectedAdAccount?.id === account.id}
                      onChange={() => setSelectedAdAccount(account)}
                      style={{ width: '18px', height: '18px' }}
                    />
                    <div>
                      <div style={{ fontWeight: 500 }}>{account.name || account.id}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {account.currency} • {account.id}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            ) : (
              <div style={{
                padding: '1rem',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '8px',
                color: '#ef4444',
                textAlign: 'center'
              }}>
                {fbConnected ? 'No ad accounts found. Please reconnect to Facebook and create an ad account during the setup.' : 'Connect Facebook to see your ad accounts'}
              </div>
            )}
          </div>

          {/* Step 4: Campaign Settings */}
          <div style={{ marginBottom: '2rem', opacity: selectedAdAccount ? 1 : 0.5, pointerEvents: selectedAdAccount ? 'auto' : 'none' }}>
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
                4
              </span>
              Campaign Settings
            </h3>

            <div style={{ display: 'grid', gap: '1.5rem' }}>
              {/* Budget */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Ad Budget
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      padding: '12px 16px',
                      background: budget === 50 ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                      border: budget === 50 ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      cursor: 'pointer'
                    }}
                  >
                    <input
                      type="radio"
                      name="budget"
                      checked={budget === 50}
                      onChange={() => setBudget(50)}
                      style={{ width: '18px', height: '18px', marginTop: '2px' }}
                    />
                    <div>
                      <div style={{ fontWeight: 600 }}>$50 <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>— Standard</span></div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Good for initial understanding</div>
                    </div>
                  </label>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      padding: '12px 16px',
                      background: budget === 100 ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                      border: budget === 100 ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      cursor: 'pointer'
                    }}
                  >
                    <input
                      type="radio"
                      name="budget"
                      checked={budget === 100}
                      onChange={() => setBudget(100)}
                      style={{ width: '18px', height: '18px', marginTop: '2px' }}
                    />
                    <div>
                      <div style={{ fontWeight: 600 }}>$100 <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>— Higher Certainty</span></div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>More data for better insights</div>
                    </div>
                  </label>
                </div>
                <div style={{
                  fontSize: '0.8rem',
                  color: 'var(--text-muted)',
                  marginTop: '0.75rem',
                  padding: '12px',
                  background: 'rgba(251, 191, 36, 0.1)',
                  border: '1px solid rgba(251, 191, 36, 0.2)',
                  borderRadius: '6px'
                }}>
                  <strong style={{ color: '#fbbf24' }}>Important:</strong> Meta might charge 10-20% more or less than your set budget. We do not take any commission from your Meta advertising budget. All ad costs are charged directly by Meta to the payment method linked in your Facebook account.
                </div>
              </div>

              {/* Duration - Fixed */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Duration
                </label>
                <div style={{
                  padding: '12px 16px',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)'
                }}>
                  {DURATION_DAYS} days
                </div>
              </div>

              {/* CTA - Fixed */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Call to Action
                </label>
                <div style={{
                  padding: '12px 16px',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)'
                }}>
                  {CTA_LABEL}
                </div>
              </div>

              {/* Locations */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
                  Target Locations
                </label>

                {/* Selected cities */}
                {locations.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    {locations.map(loc => (
                      <span
                        key={loc.key}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '6px 12px',
                          background: 'rgba(59, 130, 246, 0.2)',
                          border: '1px solid rgba(59, 130, 246, 0.3)',
                          borderRadius: '20px',
                          fontSize: '0.9rem'
                        }}
                      >
                        {loc.name}, {loc.region || loc.country_name}
                        <button
                          onClick={() => removeLocation(loc.key)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--text-muted)',
                            cursor: 'pointer',
                            padding: 0,
                            fontSize: '1.1rem',
                            lineHeight: 1
                          }}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                {/* Search input */}
                <div style={{ position: 'relative' }} ref={locationDropdownRef}>
                  <input
                    type="text"
                    value={locationQuery}
                    onChange={(e) => setLocationQuery(e.target.value)}
                    placeholder="Search for a city..."
                    className="input-field"
                    style={{ width: '100%' }}
                    disabled={!fbConnected}
                  />

                  {/* Suggestions dropdown */}
                  {locationSuggestions.length > 0 && (
                    <div style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      background: '#1a1a2e',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '8px',
                      marginTop: '4px',
                      maxHeight: '200px',
                      overflowY: 'auto',
                      zIndex: 1000,
                      boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
                    }}>
                      {locationSuggestions.map(city => (
                        <div
                          key={city.key}
                          onClick={() => addLocation(city)}
                          style={{
                            padding: '10px 14px',
                            cursor: 'pointer',
                            borderBottom: '1px solid rgba(255,255,255,0.05)'
                          }}
                          onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
                          onMouseLeave={(e) => e.target.style.background = 'transparent'}
                        >
                          <div style={{ fontWeight: 500 }}>{city.name}</div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {city.region ? `${city.region}, ` : ''}{city.country_name}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                  {searchingLocations ? (
                    <span style={{ color: '#3b82f6' }}>Searching cities...</span>
                  ) : (
                    'For this test we recommend choosing 1 to 3 cities max'
                  )}
                </div>
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

          {/* Launch Disclaimer */}
          <div style={{
            fontSize: '0.85rem',
            color: 'var(--text-muted)',
            marginBottom: '1rem',
            padding: '12px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            lineHeight: 1.5
          }}>
            Clicking "Launch" charges you <strong style={{ color: 'var(--text-primary)' }}>$12</strong> immediately (non-refundable) and authorizes Meta to charge <strong style={{ color: 'var(--text-primary)' }}>${budget === 50 ? '40-60' : '80-120'}</strong> for ads over 72 hours. See{' '}
            <a href="https://launchad.io/terms-of-service" target="_blank" rel="noopener noreferrer" style={{ color: '#3b82f6' }}>
              Terms & Conditions
            </a>.
          </div>

          {/* Payment Method Warning */}
          {selectedAdAccount && hasPaymentMethod === false && (
            <div style={{
              padding: '16px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              marginBottom: '1rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '1.2rem' }}>⚠️</span>
                <strong style={{ color: '#ef4444' }}>Payment Method Required</strong>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '0 0 12px 0' }}>
                Your Meta ad account needs a payment method before you can create ads.
              </p>
              <div style={{ display: 'flex', gap: '8px' }}>
                <a
                  href={addPaymentUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    background: '#3b82f6',
                    color: 'white',
                    borderRadius: '6px',
                    textDecoration: 'none',
                    fontSize: '0.9rem',
                    fontWeight: 500
                  }}
                >
                  Add Payment Method ↗
                </a>
                <button
                  onClick={checkPaymentStatus}
                  disabled={paymentCheckLoading}
                  style={{
                    padding: '8px 16px',
                    background: 'rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '6px',
                    color: 'var(--text-primary)',
                    cursor: paymentCheckLoading ? 'wait' : 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  {paymentCheckLoading ? 'Checking...' : 'Refresh'}
                </button>
              </div>
            </div>
          )}

          {/* Publish Button */}
          <button
            onClick={handlePublish}
            disabled={!fbConnected || !selectedPage || !selectedAdAccount || publishing || locations.length === 0 || hasPaymentMethod === false}
            className="btn-primary"
            style={{
              width: '100%',
              padding: '16px',
              fontSize: '1.1rem',
              fontWeight: 600,
              background: (fbConnected && selectedPage && selectedAdAccount && !publishing && locations.length > 0 && hasPaymentMethod !== false)
                ? 'linear-gradient(135deg, #22c55e, #16a34a)'
                : 'rgba(255,255,255,0.1)',
              opacity: (fbConnected && selectedPage && selectedAdAccount && !publishing && locations.length > 0 && hasPaymentMethod !== false) ? 1 : 0.5,
              cursor: (fbConnected && selectedPage && selectedAdAccount && !publishing && locations.length > 0 && hasPaymentMethod !== false) ? 'pointer' : 'not-allowed'
            }}
          >
            {publishing
              ? '⏳ Publishing...'
              : hasPaymentMethod === false
                ? 'Add Payment Method First'
                : `Launch Campaign - Total: ~$${budget === 50 ? '57-72' : '102-132'}`
            }
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
