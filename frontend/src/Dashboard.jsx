import { useState, useEffect } from 'react'
import { getCampaigns, deleteCampaign } from './api'

function Dashboard({ onSelectCampaign, onNewCampaign }) {
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadCampaigns()
  }, [])

  const loadCampaigns = async () => {
    try {
      setLoading(true)
      const data = await getCampaigns()
      setCampaigns(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!confirm('Delete this campaign?')) return
    try {
      await deleteCampaign(id)
      setCampaigns(campaigns.filter(c => c.id !== id))
    } catch (err) {
      alert('Failed to delete: ' + err.message)
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      DRAFT: 'rgba(156, 163, 175, 0.3)',
      ANALYZED: 'rgba(59, 130, 246, 0.3)',
      READY: 'rgba(34, 197, 94, 0.3)',
      PUBLISHED: 'rgba(139, 92, 246, 0.3)',
      ACTIVE: 'rgba(34, 197, 94, 0.5)',
      PAUSED: 'rgba(251, 191, 36, 0.3)',
      ARCHIVED: 'rgba(107, 114, 128, 0.3)'
    }
    return colors[status] || colors.DRAFT
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem' }}>
        <span className="loader"></span>
        <p style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>Loading campaigns...</p>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.75rem', margin: 0 }}>Your Campaigns</h2>
        <button onClick={onNewCampaign} className="btn-primary">
          + New Campaign
        </button>
      </div>

      {error && (
        <div style={{ color: '#ef4444', marginBottom: '1rem' }}>
          Error: {error}
        </div>
      )}

      {campaigns.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
          <h3 style={{ marginBottom: '0.5rem' }}>No campaigns yet</h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            Create your first campaign to get started
          </p>
          <button onClick={onNewCampaign} className="btn-primary">
            Create Campaign
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {campaigns.map(campaign => (
            <div
              key={campaign.id}
              className="glass-panel"
              onClick={() => onSelectCampaign(campaign)}
              style={{
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                padding: '1.25rem'
              }}
              onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{campaign.name}</h3>
                    <span
                      className="tag"
                      style={{
                        background: getStatusColor(campaign.status),
                        fontSize: '0.7rem',
                        padding: '0.25rem 0.5rem'
                      }}
                    >
                      {campaign.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                    {campaign.project_url}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Created: {new Date(campaign.created_at).toLocaleDateString()}
                    {campaign.meta_campaign_id && (
                      <span style={{ marginLeft: '1rem', color: 'var(--primary)' }}>
                        Meta ID: {campaign.meta_campaign_id}
                      </span>
                    )}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={(e) => handleDelete(campaign.id, e)}
                    style={{
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: '1px solid rgba(239, 68, 68, 0.4)',
                      color: '#ef4444',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.8rem'
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Dashboard
