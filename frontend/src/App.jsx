
import { useState, useEffect } from 'react'
import { analyzeUrl, publishToMeta, getCurrentUser, logout, saveCampaign } from './api'
import Dashboard from './Dashboard'
import AuthModal from './AuthModal'
import MetaAdPreview from './MetaAdPreview'
import CampaignLaunchPage from './CampaignLaunchPage'
import './App.css'

function App() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // Auth state
  const [user, setUser] = useState(null)
  const [showAuth, setShowAuth] = useState(false)
  const [view, setView] = useState('home') // 'home' | 'dashboard' | 'launch'

  // Ad selection state
  const [selectedAd, setSelectedAd] = useState(null)

  // Save campaign state
  const [saving, setSaving] = useState(false)
  const [campaignName, setCampaignName] = useState('')

  // Meta Publishing state
  const [pageId, setPageId] = useState('859037077302041')
  const [publishing, setPublishing] = useState(false)
  const [publishResult, setPublishResult] = useState(null)
  const [publishError, setPublishError] = useState(null)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const userData = await getCurrentUser()
    setUser(userData)
  }

  const handleLogout = () => {
    logout()
    setUser(null)
    setView('home')
  }

  const handleSaveCampaign = async () => {
    if (!result || !campaignName.trim()) return
    setSaving(true)
    try {
      await saveCampaign(campaignName, result)
      alert('Campaign saved!')
      setCampaignName('')
    } catch (err) {
      alert('Failed to save: ' + err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!url) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await analyzeUrl(url)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = (format = 'json') => {
    if (!result) return

    const timestamp = new Date().toISOString().split('T')[0]
    const filename = `idea2ad-campaign-${timestamp}`

    if (format === 'json') {
      const dataStr = JSON.stringify(result, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}.json`
      link.click()
      URL.revokeObjectURL(url)
    } else if (format === 'txt') {
      // Create a readable text version
      let textContent = `IDEA2AD CAMPAIGN EXPORT\n`
      textContent += `Generated: ${new Date().toLocaleString()}\n`
      textContent += `Source URL: ${result.project_url}\n`
      textContent += `\n${'='.repeat(60)}\n\n`

      textContent += `STRATEGIC ANALYSIS\n${'-'.repeat(60)}\n`
      textContent += `Summary: ${result.analysis.summary}\n\n`
      textContent += `USP: ${result.analysis.unique_selling_proposition}\n\n`
      textContent += `Pain Points:\n${result.analysis.pain_points.map(p => `  - ${p}`).join('\n')}\n\n`
      textContent += `Call to Action: ${result.analysis.call_to_action}\n\n`

      textContent += `\n${'='.repeat(60)}\n\n`
      textContent += `AUDIENCE TARGETING\n${'-'.repeat(60)}\n`
      textContent += `Age: ${result.targeting.age_min} - ${result.targeting.age_max}\n`
      textContent += `Genders: ${result.targeting.genders.join(', ')}\n`
      textContent += `Locations: ${result.targeting.geo_locations.join(', ')}\n`
      textContent += `Interests: ${result.targeting.interests.join(', ')}\n\n`

      textContent += `\n${'='.repeat(60)}\n\n`
      textContent += `AD COPY\n${'-'.repeat(60)}\n`
      result.suggested_creatives
        .filter(c => c.type === 'headline' || c.type === 'copy_primary')
        .forEach((c, i) => {
          textContent += `\n${c.type === 'headline' ? 'HEADLINE' : 'PRIMARY TEXT'} #${i + 1}\n`
          textContent += `"${c.content}"\n`
          textContent += `Rationale: ${c.rationale}\n`
        })

      textContent += `\n${'='.repeat(60)}\n\n`
      textContent += `IMAGE BRIEFS\n${'-'.repeat(60)}\n`
      if (result.image_briefs) {
        result.image_briefs.forEach((brief, i) => {
          textContent += `\nBRIEF #${i + 1}: ${brief.approach.toUpperCase()}\n`
          textContent += `${'-'.repeat(40)}\n`
          textContent += `Visual Description: ${brief.visual_description}\n\n`
          textContent += `Styling Notes: ${brief.styling_notes}\n\n`
          if (brief.text_overlays && brief.text_overlays.length > 0) {
            textContent += `Text Overlays:\n`
            brief.text_overlays.forEach((overlay, j) => {
              textContent += `  ${j + 1}. "${overlay.content}" (${overlay.position}, ${overlay.font_size}, ${overlay.color})\n`
            })
            textContent += `\n`
          }
          textContent += `Rationale: ${brief.rationale}\n`
          textContent += `Best Practices: ${brief.meta_best_practices.join('; ')}\n`
        })
      }

      const dataBlob = new Blob([textContent], { type: 'text/plain' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}.txt`
      link.click()
      URL.revokeObjectURL(url)
    }
  }

  const handlePublish = async () => {
    if (!result || !pageId) return

    setPublishing(true)
    setPublishError(null)
    setPublishResult(null)

    try {
      const data = await publishToMeta(result, pageId)
      setPublishResult(data)
    } catch (err) {
      setPublishError(err.message)
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="container">
      {/* Auth Modal */}
      {showAuth && (
        <AuthModal
          onClose={() => setShowAuth(false)}
          onSuccess={() => { setShowAuth(false); checkAuth() }}
        />
      )}

      {/* Navigation Header */}
      <header style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h1
            onClick={() => { setView('home'); setResult(null) }}
            style={{
              fontSize: '2.5rem',
              margin: 0,
              background: 'linear-gradient(to right, #fff, #9ca3af)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              cursor: 'pointer'
            }}
          >
            LaunchAd
          </h1>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {user ? (
              <>
                <button
                  onClick={() => setView(view === 'dashboard' ? 'home' : 'dashboard')}
                  className="btn-primary"
                  style={{ background: 'rgba(99, 102, 241, 0.2)', border: '1px solid rgba(99, 102, 241, 0.4)' }}
                >
                  {view === 'dashboard' ? 'New Campaign' : 'My Campaigns'}
                </button>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{user.email}</span>
                <button
                  onClick={handleLogout}
                  style={{
                    background: 'none',
                    border: '1px solid rgba(255,255,255,0.2)',
                    color: 'var(--text-muted)',
                    padding: '0.5rem 1rem',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  Sign Out
                </button>
              </>
            ) : (
              <button onClick={() => setShowAuth(true)} className="btn-primary">
                Sign In
              </button>
            )}
          </div>
        </div>
        {view === 'home' && (
          <p style={{ fontSize: '1.1rem', color: 'var(--text-muted)', margin: 0 }}>
            Turn your Landing Page into a Meta Ads Campaign in seconds.
          </p>
        )}
      </header>

      {/* Dashboard View */}
      {view === 'dashboard' && user && (
        <Dashboard
          onSelectCampaign={(c) => { /* TODO: Load campaign details */ }}
          onNewCampaign={() => setView('home')}
        />
      )}

      {/* Launch View - Campaign Settings */}
      {view === 'launch' && selectedAd && result && (
        <CampaignLaunchPage
          selectedAd={selectedAd}
          campaignData={result}
          onBack={() => setView('home')}
          onPublishSuccess={(publishResult) => {
            alert('Campaign published successfully!')
            console.log('Publish result:', publishResult)
            setView('home')
            setResult(null)
            setSelectedAd(null)
          }}
        />
      )}

      {/* Home View - Campaign Generator */}
      {view === 'home' && (
        <>
          <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem', flexDirection: 'column' }}>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <input
                  type="url"
                  className="input-field"
                  placeholder="https://your-product.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                />
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Analyzing...' : 'Generate Campaign'}
                </button>
              </div>
              {error && <div style={{ color: '#ef4444', textAlign: 'left' }}>Error: {error}</div>}
            </form>
          </div>

      {loading && (
        <div style={{ marginTop: '3rem' }}>
          <span className="loader"></span>
          <p style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>Reading your landing page... extracting insights... dreaming up ads...</p>
        </div>
      )}

      {result && (
        <>
          {/* Export & Save Buttons */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginTop: '2rem', marginBottom: '1rem' }}>
            {/* Save Campaign (requires auth) */}
            {user ? (
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Campaign name"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  style={{ width: '200px' }}
                />
                <button
                  onClick={handleSaveCampaign}
                  className="btn-primary"
                  disabled={saving || !campaignName.trim()}
                  style={{
                    background: 'rgba(34, 197, 94, 0.2)',
                    border: '1px solid rgba(34, 197, 94, 0.4)',
                    padding: '0.75rem 1.5rem'
                  }}
                >
                  {saving ? 'Saving...' : 'Save Campaign'}
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowAuth(true)}
                className="btn-primary"
                style={{
                  background: 'rgba(34, 197, 94, 0.2)',
                  border: '1px solid rgba(34, 197, 94, 0.4)',
                  padding: '0.75rem 1.5rem'
                }}
              >
                Sign in to Save
              </button>
            )}

            {/* Export Buttons */}
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => handleExport('json')}
                className="btn-primary"
                style={{
                  background: 'rgba(99, 102, 241, 0.2)',
                  border: '1px solid rgba(99, 102, 241, 0.4)',
                  padding: '0.75rem 1.5rem'
                }}
              >
                Export JSON
              </button>
              <button
                onClick={() => handleExport('txt')}
                className="btn-primary"
                style={{
                  background: 'rgba(236, 72, 153, 0.2)',
                  border: '1px solid rgba(236, 72, 153, 0.4)',
                  padding: '0.75rem 1.5rem'
                }}
              >
                Export TXT
              </button>
            </div>
          </div>

          <div className="dashboard-grid" style={{ animation: 'fadeIn 0.8s ease-out' }}>
          {/* Analysis Card */}
          <div className="glass-panel">
            <h2 className="card-title">📊 Summary</h2>
            <div style={{ marginBottom: '1.5rem' }}>
              <p>{result.analysis.summary}</p>
            </div>
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: 'var(--text-muted)', margin: '0.5rem 0' }}>🦄 USP</h4>
              <p style={{ color: 'var(--accent)', fontWeight: 600 }}>{result.analysis.unique_selling_proposition}</p>
            </div>
            <div>
              <h4 style={{ color: 'var(--text-muted)', margin: '0.5rem 0' }}>🔥 Pain Points</h4>
              <ul style={{ paddingLeft: '1.2rem' }}>
                {result.analysis.pain_points.map((point, i) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Styling Guide Card */}
          <div className="glass-panel">
            <h2 className="card-title">🎨 Brand Styling Guide</h2>

            {/* Colors */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: 'var(--text-muted)', margin: '0.5rem 0' }}>Primary Colors</h4>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                {result.analysis.styling_guide.primary_colors.map((color, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
                    <div style={{
                      width: '60px',
                      height: '60px',
                      background: color,
                      borderRadius: '8px',
                      border: '2px solid rgba(255,255,255,0.2)',
                      boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
                    }}></div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>{color}</span>
                  </div>
                ))}
              </div>

              {result.analysis.styling_guide.secondary_colors.length > 0 && (
                <>
                  <h4 style={{ color: 'var(--text-muted)', margin: '0.5rem 0' }}>Secondary Colors</h4>
                  <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    {result.analysis.styling_guide.secondary_colors.map((color, i) => (
                      <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
                        <div style={{
                          width: '50px',
                          height: '50px',
                          background: color,
                          borderRadius: '6px',
                          border: '2px solid rgba(255,255,255,0.2)',
                          boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
                        }}></div>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>{color}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Fonts */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: 'var(--text-muted)', margin: '0.5rem 0' }}>Typography</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {result.analysis.styling_guide.font_families.slice(0, 3).map((font, i) => (
                  <div key={i} style={{
                    background: 'rgba(255,255,255,0.05)',
                    padding: '0.75rem 1rem',
                    borderRadius: '6px',
                    border: '1px solid rgba(255,255,255,0.1)'
                  }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                      Font Family {i + 1}
                    </div>
                    <div style={{ fontFamily: font, fontSize: '1.1rem' }}>
                      {font}
                    </div>
                    <div style={{ fontFamily: font, fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      The quick brown fox jumps over the lazy dog
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Design Style & Mood */}
            <div>
              <h4 style={{ color: 'var(--text-muted)', margin: '0.5rem 0' }}>Design Attributes</h4>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span className="tag" style={{ background: 'rgba(99, 102, 241, 0.2)', border: '1px solid rgba(99, 102, 241, 0.4)', textTransform: 'capitalize' }}>
                  Style: {result.analysis.styling_guide.design_style}
                </span>
                <span className="tag" style={{ background: 'rgba(236, 72, 153, 0.2)', border: '1px solid rgba(236, 72, 153, 0.4)', textTransform: 'capitalize' }}>
                  Mood: {result.analysis.styling_guide.mood}
                </span>
              </div>
            </div>
          </div>

          {/* Targeting Card */}
          <div className="glass-panel">
            <h2 className="card-title">🎯 Audience Targeting</h2>
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: 'var(--text-muted)', margin: '0.5rem 0' }}>Demographics</h4>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span className="tag">Age: {result.targeting.age_min} - {result.targeting.age_max}</span>
                {result.targeting.genders.map(g => <span key={g} className="tag" style={{ textTransform: 'capitalize' }}>{g}</span>)}
                {result.targeting.geo_locations.map(l => <span key={l} className="tag">{l}</span>)}
              </div>
            </div>
            <div>
              <h4 style={{ color: 'var(--text-muted)', margin: '0.5rem 0' }}>Interests & Keywords</h4>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {result.targeting.interests.map((interest, i) => (
                  <span key={i} className="tag" style={{ background: 'rgba(99, 102, 241, 0.2)', border: '1px solid rgba(99, 102, 241, 0.4)' }}>
                    {interest}
                  </span>
                ))}
              </div>
            </div>
          </div>


          {/* Ad Previews Section */}
          {result.ads && result.ads.length > 0 && (
            <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
              <h2 className="card-title">📱 Choose Your Ad</h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
                Select the ad creative you want to launch. Click on an ad to select it.
              </p>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
                gap: '2rem',
                justifyItems: 'center',
                marginBottom: '2rem'
              }}>
                {result.ads.map((ad) => (
                  <MetaAdPreview
                    key={ad.id}
                    ad={ad}
                    selected={selectedAd?.id === ad.id}
                    onSelect={() => setSelectedAd(ad)}
                    pageName={new URL(result.project_url).hostname.replace('www.', '')}
                    websiteUrl={result.project_url}
                  />
                ))}
              </div>

              {/* Launch Button */}
              <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                <button
                  onClick={() => setView('launch')}
                  disabled={!selectedAd}
                  className="btn-primary"
                  style={{
                    background: selectedAd
                      ? 'linear-gradient(135deg, #1877f2, #0c63d4)'
                      : 'rgba(255,255,255,0.1)',
                    padding: '1rem 3rem',
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    opacity: selectedAd ? 1 : 0.5,
                    cursor: selectedAd ? 'pointer' : 'not-allowed',
                    transition: 'all 0.3s ease'
                  }}
                >
                  🚀 Launch My Campaign
                </button>
                {!selectedAd && (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.75rem' }}>
                    Select an ad above to continue
                  </p>
                )}
              </div>
            </div>
          )}

          </div>
        </>
      )}
        </>
      )}
    </div>
  )
}

export default App
