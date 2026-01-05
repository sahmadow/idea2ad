import { useState } from 'react'

function MetaAdPreview({
  ad,
  selected,
  onSelect,
  pageName = "Your Page",
  websiteUrl = "yourwebsite.com"
}) {
  const [imageLoaded, setImageLoaded] = useState(false)

  // Extract domain from URL for display
  const displayUrl = websiteUrl.replace(/^https?:\/\//, '').replace(/\/$/, '').split('/')[0]

  return (
    <div
      onClick={onSelect}
      style={{
        background: '#fff',
        borderRadius: '8px',
        overflow: 'hidden',
        maxWidth: '400px',
        cursor: 'pointer',
        border: selected ? '3px solid #1877f2' : '3px solid transparent',
        boxShadow: selected
          ? '0 0 0 3px rgba(24, 119, 242, 0.3), 0 4px 12px rgba(0,0,0,0.15)'
          : '0 1px 2px rgba(0,0,0,0.1)',
        transition: 'all 0.2s ease',
        transform: selected ? 'scale(1.02)' : 'scale(1)',
        textAlign: 'left',
      }}
    >
      {/* Header - Page info */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        padding: '12px 16px',
        gap: '10px'
      }}>
        {/* Page Avatar */}
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #667eea, #764ba2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 700,
          fontSize: '18px'
        }}>
          {pageName.charAt(0).toUpperCase()}
        </div>

        {/* Page Name & Sponsored */}
        <div style={{ flex: 1 }}>
          <div style={{
            fontWeight: 600,
            fontSize: '14px',
            color: '#050505',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            {pageName}
          </div>
          <div style={{
            fontSize: '12px',
            color: '#65676b',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            Sponsored · <span style={{ fontSize: '10px' }}>🌐</span>
          </div>
        </div>

        {/* More options */}
        <div style={{
          color: '#65676b',
          fontSize: '20px',
          display: 'flex',
          gap: '8px'
        }}>
          <span>···</span>
          <span>✕</span>
        </div>
      </div>

      {/* Primary Text */}
      <div style={{
        padding: '0 16px 12px',
        fontSize: '14px',
        lineHeight: '1.4',
        color: '#050505'
      }}>
        {ad.primaryText}
      </div>

      {/* Image */}
      <div style={{
        position: 'relative',
        width: '100%',
        paddingTop: '100%', // 1:1 aspect ratio
        background: '#f0f2f5',
        overflow: 'hidden'
      }}>
        {ad.imageUrl ? (
          <img
            src={ad.imageUrl}
            alt="Ad creative"
            onLoad={() => setImageLoaded(true)}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              opacity: imageLoaded ? 1 : 0,
              transition: 'opacity 0.3s ease'
            }}
          />
        ) : (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: '#fff'
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', marginBottom: '8px' }}>🖼️</div>
              <div style={{ fontSize: '14px', opacity: 0.8 }}>Generating image...</div>
            </div>
          </div>
        )}

        {/* Loading overlay */}
        {ad.imageUrl && !imageLoaded && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f0f2f5'
          }}>
            <div className="loader" style={{ width: '32px', height: '32px' }}></div>
          </div>
        )}
      </div>

      {/* Link Preview */}
      <div style={{
        background: '#f0f2f5',
        padding: '12px 16px',
        borderTop: '1px solid #dddfe2'
      }}>
        <div style={{
          fontSize: '12px',
          color: '#65676b',
          textTransform: 'uppercase',
          marginBottom: '4px'
        }}>
          {displayUrl}
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '12px'
        }}>
          <div style={{ flex: 1 }}>
            <div style={{
              fontWeight: 600,
              fontSize: '15px',
              color: '#050505',
              marginBottom: '2px',
              lineHeight: '1.3'
            }}>
              {ad.headline}
            </div>
            <div style={{
              fontSize: '13px',
              color: '#65676b',
              lineHeight: '1.3'
            }}>
              {ad.description}
            </div>
          </div>

          {/* CTA Button */}
          <button style={{
            background: '#e4e6eb',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: 600,
            color: '#050505',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            flexShrink: 0
          }}>
            Learn more
          </button>
        </div>
      </div>

      {/* Footer - Like, Comment, Share */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-around',
        padding: '4px 16px 8px',
        borderTop: '1px solid #dddfe2'
      }}>
        {[
          { icon: '👍', label: 'Like' },
          { icon: '💬', label: 'Comment' },
          { icon: '↗️', label: 'Share' }
        ].map((action, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 12px',
              borderRadius: '4px',
              color: '#65676b',
              fontSize: '14px',
              fontWeight: 600
            }}
          >
            <span>{action.icon}</span>
            <span>{action.label}</span>
          </div>
        ))}
      </div>

      {/* Selection indicator */}
      {selected && (
        <div style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          background: '#1877f2',
          color: '#fff',
          borderRadius: '50%',
          width: '28px',
          height: '28px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          fontWeight: 700,
          boxShadow: '0 2px 8px rgba(24, 119, 242, 0.4)'
        }}>
          ✓
        </div>
      )}
    </div>
  )
}

export default MetaAdPreview
