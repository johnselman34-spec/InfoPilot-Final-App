import React, { useState } from 'react';

/**
 * YouTube Video Player Component
 * Embeds YouTube videos with responsive sizing and loading states
 */
const YouTubePlayer = ({ 
  videoId, 
  videoUrl, 
  title = "Tutorial Video",
  aspectRatio = "16/9" 
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  // Extract video ID from URL if not provided directly
  const getVideoId = () => {
    if (videoId) return videoId;
    if (!videoUrl) return null;
    
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
    ];
    
    for (const pattern of patterns) {
      const match = videoUrl.match(pattern);
      if (match) return match[1];
    }
    return null;
  };

  const finalVideoId = getVideoId();

  if (!finalVideoId) {
    return (
      <div 
        style={{
          background: 'rgba(107, 114, 128, 0.2)',
          borderRadius: 12,
          padding: 40,
          textAlign: 'center',
          border: '1px dashed rgba(107, 114, 128, 0.3)'
        }}
        data-testid="youtube-placeholder"
      >
        <div style={{ fontSize: '3rem', marginBottom: 15, opacity: 0.5 }}>🎬</div>
        <p style={{ color: '#9ca3af', margin: 0, fontSize: '0.9rem' }}>
          Video coming soon!
        </p>
        <p style={{ color: '#6b7280', margin: '5px 0 0 0', fontSize: '0.8rem' }}>
          Check back later for video tutorial
        </p>
      </div>
    );
  }

  return (
    <div 
      style={{
        position: 'relative',
        width: '100%',
        aspectRatio: aspectRatio,
        borderRadius: 12,
        overflow: 'hidden',
        background: '#000',
        border: '1px solid rgba(255,255,255,0.1)'
      }}
      data-testid="youtube-player"
    >
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(0,0,0,0.8)',
          zIndex: 1
        }}>
          <div style={{ textAlign: 'center', color: '#fff' }}>
            <div style={{ fontSize: '2rem', animation: 'pulse 1.5s ease-in-out infinite' }}>▶️</div>
            <p style={{ marginTop: 10, fontSize: '0.9rem' }}>Loading video...</p>
          </div>
        </div>
      )}

      {error ? (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(239, 68, 68, 0.1)',
          flexDirection: 'column'
        }}>
          <span style={{ fontSize: '2rem', marginBottom: 10 }}>⚠️</span>
          <p style={{ color: '#f87171', margin: 0 }}>Failed to load video</p>
          <a 
            href={`https://www.youtube.com/watch?v=${finalVideoId}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: '#3b82f6',
              marginTop: 10,
              fontSize: '0.9rem'
            }}
          >
            Watch on YouTube →
          </a>
        </div>
      ) : (
        <iframe
          src={`https://www.youtube.com/embed/${finalVideoId}?rel=0&modestbranding=1`}
          title={title}
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          onLoad={() => setIsLoading(false)}
          onError={() => { setError(true); setIsLoading(false); }}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%'
          }}
        />
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

/**
 * Video URL Input Component for Admin
 * Allows admins to add/update YouTube URLs for tutorials
 */
export const VideoUrlInput = ({ 
  tutorialId, 
  currentVideoUrl, 
  onUpdate, 
  token 
}) => {
  const [videoUrl, setVideoUrl] = useState(currentVideoUrl || '');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const handleSave = async () => {
    if (!videoUrl.trim()) {
      setMessage({ type: 'error', text: 'Please enter a YouTube URL' });
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const API = process.env.REACT_APP_BACKEND_URL;
      const res = await fetch(`${API}/api/tutorials/admin/${tutorialId}/video`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ video_url: videoUrl })
      });

      if (res.ok) {
        const data = await res.json();
        setMessage({ type: 'success', text: 'Video URL saved!' });
        if (onUpdate) onUpdate(data);
      } else {
        const error = await res.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to save' });
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Connection error' });
    }

    setSaving(false);
  };

  const handleRemove = async () => {
    if (!window.confirm('Remove video from this tutorial?')) return;

    setSaving(true);
    try {
      const API = process.env.REACT_APP_BACKEND_URL;
      const res = await fetch(`${API}/api/tutorials/admin/${tutorialId}/video`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        setVideoUrl('');
        setMessage({ type: 'success', text: 'Video removed' });
        if (onUpdate) onUpdate(null);
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to remove' });
    }
    setSaving(false);
  };

  return (
    <div style={{
      background: 'rgba(251, 191, 36, 0.1)',
      borderRadius: 10,
      padding: 15,
      border: '1px solid rgba(251, 191, 36, 0.2)',
      marginBottom: 15
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 8, 
        marginBottom: 10 
      }}>
        <span style={{ fontSize: '1.1rem' }}>🎬</span>
        <span style={{ color: '#fbbf24', fontWeight: 600, fontSize: '0.9rem' }}>
          Video URL (Admin)
        </span>
      </div>

      <div style={{ display: 'flex', gap: 10 }}>
        <input
          type="text"
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.target.value)}
          placeholder="https://youtube.com/watch?v=..."
          style={{
            flex: 1,
            background: 'rgba(0,0,0,0.3)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 8,
            padding: '10px 12px',
            color: '#fff',
            fontSize: '0.9rem'
          }}
        />
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            background: 'linear-gradient(135deg, #10b981, #059669)',
            border: 'none',
            borderRadius: 8,
            padding: '10px 16px',
            color: '#fff',
            fontWeight: 600,
            cursor: saving ? 'wait' : 'pointer',
            opacity: saving ? 0.7 : 1
          }}
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
        {currentVideoUrl && (
          <button
            onClick={handleRemove}
            disabled={saving}
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 8,
              padding: '10px 16px',
              color: '#f87171',
              fontWeight: 600,
              cursor: saving ? 'wait' : 'pointer'
            }}
          >
            Remove
          </button>
        )}
      </div>

      {message && (
        <p style={{
          margin: '10px 0 0 0',
          color: message.type === 'success' ? '#10b981' : '#f87171',
          fontSize: '0.85rem'
        }}>
          {message.text}
        </p>
      )}

      <p style={{ 
        margin: '10px 0 0 0', 
        color: '#71717a', 
        fontSize: '0.75rem' 
      }}>
        Supports YouTube URLs like youtube.com/watch?v=... or youtu.be/...
      </p>
    </div>
  );
};

export default YouTubePlayer;
