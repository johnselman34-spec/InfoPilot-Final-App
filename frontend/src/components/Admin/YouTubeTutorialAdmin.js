import React, { useState, useEffect, useCallback } from 'react';
import { API } from '../../utils/api';

/**
 * YouTubeTutorialAdmin - Admin interface for managing YouTube tutorials
 */
const YouTubeTutorialAdmin = ({ token, showToast }) => {
  const [tutorials, setTutorials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [newTutorial, setNewTutorial] = useState({
    title: '',
    description: '',
    category: 'getting-started',
    video_url: ''
  });
  const [showAddForm, setShowAddForm] = useState(false);

  const categories = [
    { id: 'getting-started', label: '🚀 Getting Started', color: '#10b981' },
    { id: 'search', label: '🔍 Search & Protocols', color: '#3b82f6' },
    { id: 'marketplace', label: '🛒 Marketplace', color: '#f59e0b' },
    { id: 'social', label: '👥 Social Features', color: '#ec4899' },
    { id: 'advanced', label: '⚡ Advanced', color: '#8b5cf6' },
    { id: 'mobile', label: '📱 Mobile & Extension', color: '#14b8a6' }
  ];

  const fetchTutorials = useCallback(async () => {
    try {
      const res = await fetch(`${API}/tutorials`);
      if (res.ok) {
        const data = await res.json();
        setTutorials(data.tutorials || []);
      }
    } catch (e) {
      console.error('Failed to fetch tutorials:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTutorials();
  }, [fetchTutorials]);

  const extractVideoId = (url) => {
    if (!url) return null;
    const match = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
    return match ? match[1] : null;
  };

  const updateTutorialVideo = async (tutorialId) => {
    const videoId = extractVideoId(videoUrl);
    
    try {
      const res = await fetch(`${API}/tutorials/admin/${tutorialId}/video`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          video_url: videoUrl,
          video_id: videoId
        })
      });

      if (res.ok) {
        showToast('Video updated successfully! 🎬', 'success');
        setEditingId(null);
        setVideoUrl('');
        fetchTutorials();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to update video', 'error');
      }
    } catch (e) {
      showToast('Error updating video', 'error');
    }
  };

  const removeTutorialVideo = async (tutorialId) => {
    if (!window.confirm('Remove video from this tutorial?')) return;

    try {
      const res = await fetch(`${API}/tutorials/admin/${tutorialId}/video`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        showToast('Video removed! 🗑️', 'success');
        fetchTutorials();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to remove video', 'error');
      }
    } catch (e) {
      showToast('Error removing video', 'error');
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>Loading tutorials...</div>;
  }

  return (
    <div>
      <h3 style={{ marginBottom: 20, color: '#f472b6' }}>🎬 YouTube Tutorial Management</h3>
      <p style={{ color: '#a1a1aa', marginBottom: 25 }}>
        Add, update, or remove YouTube videos from tutorials. Videos will be displayed alongside text content.
      </p>

      {/* Quick Stats */}
      <div style={{ 
        display: 'flex', 
        gap: 15, 
        marginBottom: 25,
        flexWrap: 'wrap'
      }}>
        <div style={{ 
          background: 'rgba(16, 185, 129, 0.2)', 
          padding: '15px 25px', 
          borderRadius: 12,
          border: '1px solid rgba(16, 185, 129, 0.3)'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981' }}>
            {tutorials.length}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#a1a1aa' }}>Total Tutorials</div>
        </div>
        <div style={{ 
          background: 'rgba(239, 68, 68, 0.2)', 
          padding: '15px 25px', 
          borderRadius: 12,
          border: '1px solid rgba(239, 68, 68, 0.3)'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#ef4444' }}>
            {tutorials.filter(t => t.video_url || t.video_id).length}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#a1a1aa' }}>With Videos</div>
        </div>
        <div style={{ 
          background: 'rgba(124, 58, 237, 0.2)', 
          padding: '15px 25px', 
          borderRadius: 12,
          border: '1px solid rgba(124, 58, 237, 0.3)'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#8b5cf6' }}>
            {categories.length}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#a1a1aa' }}>Categories</div>
        </div>
      </div>

      {/* Tutorial List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        {tutorials.map((tutorial) => {
          const category = categories.find(c => c.id === tutorial.category);
          const hasVideo = tutorial.video_url || tutorial.video_id;
          const isEditing = editingId === tutorial.id;

          return (
            <div 
              key={tutorial.id}
              style={{
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                padding: 20,
                border: `1px solid ${hasVideo ? 'rgba(16, 185, 129, 0.3)' : 'rgba(124, 58, 237, 0.2)'}`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 5 }}>
                    <h4 style={{ margin: 0, color: '#e2e8f0' }}>{tutorial.title}</h4>
                    {hasVideo && (
                      <span style={{ 
                        background: 'rgba(239, 68, 68, 0.2)', 
                        color: '#ef4444', 
                        padding: '2px 8px', 
                        borderRadius: 10, 
                        fontSize: '0.7rem' 
                      }}>
                        📹 Video
                      </span>
                    )}
                  </div>
                  <span style={{ 
                    background: `${category?.color}20`, 
                    color: category?.color, 
                    padding: '3px 10px', 
                    borderRadius: 15, 
                    fontSize: '0.75rem' 
                  }}>
                    {category?.label}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  {hasVideo ? (
                    <>
                      <button
                        className="btn btn-secondary"
                        onClick={() => { setEditingId(tutorial.id); setVideoUrl(tutorial.video_url || ''); }}
                        style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                      >
                        ✏️ Edit
                      </button>
                      <button
                        className="btn"
                        onClick={() => removeTutorialVideo(tutorial.id)}
                        style={{ 
                          padding: '6px 12px', 
                          fontSize: '0.8rem',
                          background: 'rgba(239, 68, 68, 0.2)',
                          color: '#ef4444',
                          border: '1px solid rgba(239, 68, 68, 0.3)'
                        }}
                      >
                        🗑️
                      </button>
                    </>
                  ) : (
                    <button
                      className="btn btn-primary"
                      onClick={() => { setEditingId(tutorial.id); setVideoUrl(''); }}
                      style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                    >
                      ➕ Add Video
                    </button>
                  )}
                </div>
              </div>

              <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '10px 0' }}>
                {tutorial.description}
              </p>

              {hasVideo && !isEditing && (
                <div style={{ 
                  background: 'rgba(0, 0, 0, 0.3)', 
                  padding: 10, 
                  borderRadius: 8, 
                  marginTop: 10,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10
                }}>
                  <span style={{ color: '#ef4444' }}>📹</span>
                  <a 
                    href={tutorial.video_url || `https://youtube.com/watch?v=${tutorial.video_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: '#3b82f6', fontSize: '0.85rem', wordBreak: 'break-all' }}
                  >
                    {tutorial.video_url || `https://youtube.com/watch?v=${tutorial.video_id}`}
                  </a>
                </div>
              )}

              {isEditing && (
                <div style={{ 
                  background: 'rgba(124, 58, 237, 0.1)', 
                  padding: 15, 
                  borderRadius: 10, 
                  marginTop: 15,
                  border: '1px solid rgba(124, 58, 237, 0.3)'
                }}>
                  <label style={{ color: '#a78bfa', fontWeight: 600, display: 'block', marginBottom: 8 }}>
                    YouTube Video URL
                  </label>
                  <div style={{ display: 'flex', gap: 10 }}>
                    <input
                      type="text"
                      value={videoUrl}
                      onChange={(e) => setVideoUrl(e.target.value)}
                      placeholder="https://youtube.com/watch?v=... or https://youtu.be/..."
                      className="input-field"
                      style={{ flex: 1 }}
                    />
                    <button
                      className="btn btn-primary"
                      onClick={() => updateTutorialVideo(tutorial.id)}
                      disabled={!videoUrl.trim()}
                    >
                      💾 Save
                    </button>
                    <button
                      className="btn btn-secondary"
                      onClick={() => { setEditingId(null); setVideoUrl(''); }}
                    >
                      ✕
                    </button>
                  </div>
                  {videoUrl && extractVideoId(videoUrl) && (
                    <div style={{ marginTop: 10 }}>
                      <p style={{ color: '#10b981', fontSize: '0.8rem', margin: '0 0 10px 0' }}>
                        ✅ Valid YouTube ID: {extractVideoId(videoUrl)}
                      </p>
                      <div style={{ 
                        position: 'relative', 
                        paddingBottom: '56.25%', 
                        height: 0, 
                        overflow: 'hidden',
                        borderRadius: 8
                      }}>
                        <iframe
                          src={`https://www.youtube.com/embed/${extractVideoId(videoUrl)}`}
                          title="Video Preview"
                          style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            border: 'none'
                          }}
                          allowFullScreen
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Help Section */}
      <div style={{ 
        marginTop: 25, 
        padding: 20, 
        background: 'rgba(59, 130, 246, 0.1)', 
        borderRadius: 12,
        border: '1px solid rgba(59, 130, 246, 0.3)'
      }}>
        <h4 style={{ color: '#60a5fa', margin: '0 0 10px 0' }}>💡 Tips for Great Tutorial Videos</h4>
        <ul style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: 0, paddingLeft: 20, lineHeight: 1.8 }}>
          <li>Keep videos under 10 minutes for better engagement</li>
          <li>Start with a brief overview of what users will learn</li>
          <li>Use screen recordings to show actual features</li>
          <li>Add captions for accessibility (YouTube auto-generates them)</li>
          <li>Include a call-to-action at the end (e.g., &quot;Try it yourself!&quot;)</li>
        </ul>
      </div>
    </div>
  );
};

export default YouTubeTutorialAdmin;
