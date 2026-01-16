/**
 * Theme Preset Gallery
 * Save, share, and browse community theme presets
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme, ACCENT_COLORS } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

const ThemePresetGallery = ({ showToast, onClose }) => {
  const { token, user } = useAuth();
  const { isDarkMode, accentColor, setIsDarkMode, changeAccentColor } = useTheme();
  const [presets, setPresets] = useState({ public_presets: [], my_presets: [] });
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPreset, setNewPreset] = useState({
    name: '',
    description: '',
    is_public: false
  });
  const [activeTab, setActiveTab] = useState('browse');

  // Fetch presets
  const fetchPresets = useCallback(async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API}/theme-presets`, { headers });
      if (res.ok) {
        const data = await res.json();
        setPresets(data);
      }
    } catch (e) {
      console.error('Failed to fetch presets:', e);
    }
    setLoading(false);
  }, [token]);

  useEffect(() => {
    fetchPresets();
  }, [fetchPresets]);

  // Create preset
  const createPreset = async () => {
    if (!newPreset.name.trim()) {
      showToast('Please enter a preset name', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/theme-presets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...newPreset,
          is_dark: isDarkMode,
          accent_color: accentColor
        })
      });

      if (res.ok) {
        showToast('Theme preset saved!', 'success');
        setShowCreateForm(false);
        setNewPreset({ name: '', description: '', is_public: false });
        fetchPresets();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to save preset', 'error');
      }
    } catch (e) {
      showToast('Failed to save preset', 'error');
    }
  };

  // Apply preset
  const applyPreset = (preset) => {
    setIsDarkMode(preset.is_dark);
    changeAccentColor(preset.accent_color);
    showToast(`Applied "${preset.name}" theme!`, 'success');
  };

  // Like preset
  const likePreset = async (presetId) => {
    if (!token) {
      showToast('Please log in to like presets', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/theme-presets/${presetId}/like`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchPresets();
      }
    } catch (e) {
      console.error('Failed to like preset:', e);
    }
  };

  // Delete preset
  const deletePreset = async (presetId) => {
    if (!window.confirm('Delete this preset?')) return;

    try {
      const res = await fetch(`${API}/theme-presets/${presetId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Preset deleted', 'success');
        fetchPresets();
      }
    } catch (e) {
      showToast('Failed to delete preset', 'error');
    }
  };

  // Render preset card
  const PresetCard = ({ preset }) => {
    const accent = ACCENT_COLORS[preset.accent_color] || ACCENT_COLORS.purple;
    
    return (
      <div
        style={{
          background: preset.is_dark 
            ? 'rgba(30, 20, 50, 0.8)' 
            : 'rgba(255, 255, 255, 0.95)',
          borderRadius: 12,
          padding: 15,
          border: `2px solid ${accent.primary}`,
          position: 'relative',
          transition: 'transform 0.2s',
          cursor: 'pointer'
        }}
        onClick={() => applyPreset(preset)}
        data-testid={`preset-card-${preset.id}`}
      >
        {/* Preview */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          marginBottom: 10
        }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 8,
            background: accent.gradient,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 700
          }}>
            {preset.is_dark ? '🌙' : '☀️'}
          </div>
          <div style={{ flex: 1 }}>
            <h4 style={{ 
              color: preset.is_dark ? '#f472b6' : '#7c3aed', 
              margin: '0 0 2px 0',
              fontSize: '0.95rem'
            }}>
              {preset.name}
            </h4>
            <span style={{
              fontSize: '0.7rem',
              color: preset.is_dark ? '#a1a1aa' : '#64748b'
            }}>
              by {preset.author}
            </span>
          </div>
        </div>

        {/* Description */}
        {preset.description && (
          <p style={{ 
            color: preset.is_dark ? '#a1a1aa' : '#64748b', 
            fontSize: '0.8rem',
            margin: '0 0 10px 0',
            lineHeight: 1.4
          }}>
            {preset.description}
          </p>
        )}

        {/* Actions */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          borderTop: `1px solid ${preset.is_dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
          paddingTop: 10,
          marginTop: 5
        }}>
          <button
            onClick={(e) => { e.stopPropagation(); likePreset(preset.id); }}
            style={{
              background: 'transparent',
              border: 'none',
              color: preset.is_dark ? '#f472b6' : '#ec4899',
              cursor: 'pointer',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: 4
            }}
          >
            ❤️ {preset.likes}
          </button>
          
          <div style={{ display: 'flex', gap: 5 }}>
            <span style={{
              background: accent.hover,
              color: accent.primary,
              padding: '2px 8px',
              borderRadius: 8,
              fontSize: '0.7rem'
            }}>
              {ACCENT_COLORS[preset.accent_color]?.name || preset.accent_color}
            </span>
            
            {preset.is_mine && (
              <button
                onClick={(e) => { e.stopPropagation(); deletePreset(preset.id); }}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: 'none',
                  color: '#ef4444',
                  padding: '2px 8px',
                  borderRadius: 8,
                  fontSize: '0.7rem',
                  cursor: 'pointer'
                }}
              >
                🗑️
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10000,
      padding: 20
    }} data-testid="theme-preset-gallery">
      <div style={{
        background: isDarkMode ? 'rgba(15, 10, 31, 0.98)' : 'rgba(248, 250, 252, 0.98)',
        borderRadius: 20,
        maxWidth: 800,
        maxHeight: '85vh',
        width: '100%',
        overflow: 'hidden',
        border: `1px solid ${ACCENT_COLORS[accentColor].border}`
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 25px',
          borderBottom: `1px solid ${isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ 
              color: isDarkMode ? '#f472b6' : '#7c3aed', 
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 10
            }}>
              🎨 Theme Gallery
            </h2>
            <p style={{ 
              color: isDarkMode ? '#a1a1aa' : '#64748b', 
              margin: '5px 0 0 0',
              fontSize: '0.85rem'
            }}>
              Browse and share community themes
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: isDarkMode ? '#a1a1aa' : '#64748b',
              fontSize: '1.5rem',
              cursor: 'pointer'
            }}
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div style={{ 
          display: 'flex', 
          gap: 5, 
          padding: '15px 25px',
          borderBottom: `1px solid ${isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'}`
        }}>
          {['browse', 'my-presets', 'create'].map(tab => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                if (tab === 'create') setShowCreateForm(true);
              }}
              style={{
                padding: '8px 16px',
                background: activeTab === tab 
                  ? ACCENT_COLORS[accentColor].gradient
                  : 'transparent',
                border: activeTab === tab 
                  ? 'none'
                  : `1px solid ${ACCENT_COLORS[accentColor].border}`,
                borderRadius: 8,
                color: activeTab === tab ? '#fff' : (isDarkMode ? '#a1a1aa' : '#64748b'),
                cursor: 'pointer',
                fontWeight: activeTab === tab ? 600 : 400,
                fontSize: '0.85rem'
              }}
              data-testid={`tab-${tab}`}
            >
              {tab === 'browse' && '🌐 Browse'}
              {tab === 'my-presets' && '📁 My Presets'}
              {tab === 'create' && '✨ Create New'}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ 
          padding: 25, 
          maxHeight: 'calc(85vh - 180px)',
          overflowY: 'auto'
        }}>
          {loading ? (
            <p style={{ color: isDarkMode ? '#a1a1aa' : '#64748b', textAlign: 'center' }}>
              Loading themes...
            </p>
          ) : activeTab === 'create' || showCreateForm ? (
            /* Create Form */
            <div style={{ maxWidth: 500, margin: '0 auto' }}>
              <h3 style={{ color: isDarkMode ? '#f472b6' : '#7c3aed', marginBottom: 20 }}>
                Save Current Theme
              </h3>
              
              {/* Preview */}
              <div style={{
                background: isDarkMode ? 'rgba(30, 20, 50, 0.5)' : 'rgba(255,255,255,0.8)',
                borderRadius: 12,
                padding: 15,
                marginBottom: 20,
                border: `2px solid ${ACCENT_COLORS[accentColor].primary}`,
                display: 'flex',
                alignItems: 'center',
                gap: 15
              }}>
                <div style={{
                  width: 50,
                  height: 50,
                  borderRadius: 10,
                  background: ACCENT_COLORS[accentColor].gradient
                }} />
                <div>
                  <div style={{ color: isDarkMode ? '#fff' : '#1e293b', fontWeight: 600 }}>
                    {isDarkMode ? '🌙 Dark Mode' : '☀️ Light Mode'}
                  </div>
                  <div style={{ color: isDarkMode ? '#a1a1aa' : '#64748b', fontSize: '0.85rem' }}>
                    {ACCENT_COLORS[accentColor].name}
                  </div>
                </div>
              </div>

              <input
                type="text"
                placeholder="Preset Name *"
                value={newPreset.name}
                onChange={(e) => setNewPreset({ ...newPreset, name: e.target.value })}
                className="input"
                style={{ marginBottom: 15 }}
                data-testid="preset-name-input"
              />
              
              <textarea
                placeholder="Description (optional)"
                value={newPreset.description}
                onChange={(e) => setNewPreset({ ...newPreset, description: e.target.value })}
                className="input"
                rows={3}
                style={{ marginBottom: 15 }}
              />

              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                color: isDarkMode ? '#a1a1aa' : '#64748b',
                marginBottom: 20,
                cursor: 'pointer'
              }}>
                <input
                  type="checkbox"
                  checked={newPreset.is_public}
                  onChange={(e) => setNewPreset({ ...newPreset, is_public: e.target.checked })}
                  style={{ accentColor: ACCENT_COLORS[accentColor].primary }}
                />
                Share with community (public)
              </label>

              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  onClick={createPreset}
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  data-testid="save-preset-btn"
                >
                  💾 Save Preset
                </button>
                <button
                  onClick={() => { setShowCreateForm(false); setActiveTab('browse'); }}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : activeTab === 'my-presets' ? (
            /* My Presets */
            <div>
              {presets.my_presets?.length > 0 ? (
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                  gap: 15
                }}>
                  {presets.my_presets.map(preset => (
                    <PresetCard key={preset.id} preset={preset} />
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <p style={{ color: isDarkMode ? '#71717a' : '#94a3b8', marginBottom: 15 }}>
                    No saved presets yet
                  </p>
                  <button
                    onClick={() => setActiveTab('create')}
                    className="btn btn-primary"
                  >
                    ✨ Create Your First Preset
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* Browse Public Presets */
            <div>
              {presets.public_presets?.length > 0 ? (
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                  gap: 15
                }}>
                  {presets.public_presets.map(preset => (
                    <PresetCard key={preset.id} preset={preset} />
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <p style={{ color: isDarkMode ? '#71717a' : '#94a3b8' }}>
                    No community presets yet. Be the first to share!
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ThemePresetGallery;
