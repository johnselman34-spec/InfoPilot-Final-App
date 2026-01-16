/**
 * Custom Map Styling Component (Premium Feature)
 * Allows users to customize map appearance with different themes and styles
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

// Predefined map style presets
const MAP_STYLE_PRESETS = [
  {
    id: 'default',
    name: 'Default',
    description: 'Standard map with balanced colors',
    preview: '🗺️',
    free: true,
    style: null // Uses default Leaflet tiles
  },
  {
    id: 'dark',
    name: 'Dark Mode',
    description: 'Dark theme for night viewing',
    preview: '🌙',
    free: true,
    tileUrl: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
  },
  {
    id: 'satellite',
    name: 'Satellite',
    description: 'Satellite imagery view',
    preview: '🛰️',
    free: false,
    tileUrl: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
  },
  {
    id: 'terrain',
    name: 'Terrain',
    description: 'Topographic with elevation',
    preview: '⛰️',
    free: false,
    tileUrl: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png'
  },
  {
    id: 'watercolor',
    name: 'Watercolor',
    description: 'Artistic watercolor style',
    preview: '🎨',
    free: false,
    tileUrl: 'https://stamen-tiles.a.ssl.fastly.net/watercolor/{z}/{x}/{y}.jpg'
  },
  {
    id: 'vintage',
    name: 'Vintage',
    description: 'Classic vintage map look',
    preview: '📜',
    free: false,
    tileUrl: 'https://stamen-tiles.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}{r}.png'
  },
  {
    id: 'neon',
    name: 'Neon Glow',
    description: 'Cyberpunk neon aesthetic',
    preview: '💜',
    free: false,
    tileUrl: 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png'
  },
  {
    id: 'minimal',
    name: 'Minimal',
    description: 'Clean, minimal design',
    preview: '⚪',
    free: false,
    tileUrl: 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png'
  }
];

// Custom marker color options
const MARKER_COLORS = [
  { id: 'default', name: 'Category Colors', color: 'auto', free: true },
  { id: 'blue', name: 'Ocean Blue', color: '#3b82f6', free: true },
  { id: 'green', name: 'Forest Green', color: '#10b981', free: true },
  { id: 'purple', name: 'Royal Purple', color: '#8b5cf6', free: false },
  { id: 'pink', name: 'Hot Pink', color: '#ec4899', free: false },
  { id: 'gold', name: 'Gold', color: '#f59e0b', free: false },
  { id: 'red', name: 'Ruby Red', color: '#ef4444', free: false },
  { id: 'cyan', name: 'Cyber Cyan', color: '#06b6d4', free: false },
  { id: 'rainbow', name: 'Rainbow', color: 'rainbow', free: false }
];

// Cluster style options
const CLUSTER_STYLES = [
  { id: 'default', name: 'Standard Circles', free: true },
  { id: 'gradient', name: 'Gradient Glow', free: false },
  { id: 'pulse', name: 'Pulsing Dots', free: false },
  { id: 'hexagon', name: 'Hexagon Grid', free: false }
];

const CustomMapStyling = ({ onStyleChange, currentStyle, showToast }) => {
  const { user, token } = useAuth();
  const [selectedPreset, setSelectedPreset] = useState(currentStyle?.preset || 'default');
  const [markerColor, setMarkerColor] = useState(currentStyle?.markerColor || 'default');
  const [clusterStyle, setClusterStyle] = useState(currentStyle?.clusterStyle || 'default');
  const [showLabels, setShowLabels] = useState(currentStyle?.showLabels !== false);
  const [animateMarkers, setAnimateMarkers] = useState(currentStyle?.animateMarkers || false);
  const [saving, setSaving] = useState(false);
  
  const isPremium = user?.subscription_tier === 'premium' || user?.is_admin;
  
  // Save map style preferences
  const saveStylePreferences = async () => {
    const styleConfig = {
      preset: selectedPreset,
      markerColor,
      clusterStyle,
      showLabels,
      animateMarkers,
      tileUrl: MAP_STYLE_PRESETS.find(p => p.id === selectedPreset)?.tileUrl || null
    };
    
    setSaving(true);
    try {
      const res = await fetch(`${API}/api/user/map-preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(styleConfig)
      });
      
      if (res.ok) {
        showToast('Map style saved!', 'success');
        onStyleChange?.(styleConfig);
      } else {
        showToast('Failed to save style', 'error');
      }
    } catch (e) {
      // Save locally if API fails
      localStorage.setItem('mapStylePreferences', JSON.stringify(styleConfig));
      showToast('Style saved locally', 'info');
      onStyleChange?.(styleConfig);
    }
    setSaving(false);
  };
  
  // Apply style immediately on change
  useEffect(() => {
    const styleConfig = {
      preset: selectedPreset,
      markerColor,
      clusterStyle,
      showLabels,
      animateMarkers,
      tileUrl: MAP_STYLE_PRESETS.find(p => p.id === selectedPreset)?.tileUrl || null
    };
    onStyleChange?.(styleConfig);
  }, [selectedPreset, markerColor, clusterStyle, showLabels, animateMarkers, onStyleChange]);

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(59, 130, 246, 0.1))',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(124, 58, 237, 0.3)'
    }} data-testid="custom-map-styling">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          🎨 Custom Map Styling
          {!isPremium && (
            <span style={{
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              padding: '3px 10px',
              borderRadius: 10,
              fontSize: '0.7rem',
              color: '#fff'
            }}>
              PREMIUM
            </span>
          )}
        </h3>
        <button
          onClick={saveStylePreferences}
          disabled={saving}
          className="btn btn-primary"
          style={{ fontSize: '0.85rem' }}
          data-testid="save-map-style-btn"
        >
          {saving ? '⏳ Saving...' : '💾 Save Style'}
        </button>
      </div>
      
      {/* Map Style Presets */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 10, display: 'block' }}>
          Map Theme
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 10 }}>
          {MAP_STYLE_PRESETS.map(preset => {
            const isLocked = !preset.free && !isPremium;
            return (
              <button
                key={preset.id}
                onClick={() => !isLocked && setSelectedPreset(preset.id)}
                disabled={isLocked}
                style={{
                  background: selectedPreset === preset.id 
                    ? 'linear-gradient(135deg, #7c3aed, #3b82f6)' 
                    : 'rgba(30, 20, 50, 0.5)',
                  border: selectedPreset === preset.id 
                    ? '2px solid #a78bfa' 
                    : '1px solid rgba(124, 58, 237, 0.3)',
                  borderRadius: 10,
                  padding: 12,
                  cursor: isLocked ? 'not-allowed' : 'pointer',
                  opacity: isLocked ? 0.5 : 1,
                  textAlign: 'center',
                  transition: 'all 0.2s'
                }}
                data-testid={`map-preset-${preset.id}`}
              >
                <div style={{ fontSize: '1.5rem', marginBottom: 5 }}>{preset.preview}</div>
                <div style={{ color: '#e5e7eb', fontSize: '0.8rem', fontWeight: 600 }}>{preset.name}</div>
                <div style={{ color: '#71717a', fontSize: '0.65rem' }}>{preset.description}</div>
                {isLocked && <div style={{ color: '#f59e0b', fontSize: '0.6rem', marginTop: 5 }}>🔒 Premium</div>}
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Marker Colors */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 10, display: 'block' }}>
          Marker Colors
        </label>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {MARKER_COLORS.map(mc => {
            const isLocked = !mc.free && !isPremium;
            return (
              <button
                key={mc.id}
                onClick={() => !isLocked && setMarkerColor(mc.id)}
                disabled={isLocked}
                title={mc.name}
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  background: mc.color === 'auto' 
                    ? 'conic-gradient(#7c3aed, #3b82f6, #10b981, #f59e0b, #ef4444, #7c3aed)'
                    : mc.color === 'rainbow'
                    ? 'linear-gradient(135deg, red, orange, yellow, green, blue, purple)'
                    : mc.color,
                  border: markerColor === mc.id ? '3px solid #fff' : '2px solid rgba(255,255,255,0.2)',
                  cursor: isLocked ? 'not-allowed' : 'pointer',
                  opacity: isLocked ? 0.4 : 1,
                  boxShadow: markerColor === mc.id ? '0 0 15px rgba(124, 58, 237, 0.5)' : 'none',
                  position: 'relative'
                }}
                data-testid={`marker-color-${mc.id}`}
              >
                {isLocked && <span style={{ position: 'absolute', top: -5, right: -5, fontSize: '0.6rem' }}>🔒</span>}
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Cluster Style */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 10, display: 'block' }}>
          Cluster Style
        </label>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {CLUSTER_STYLES.map(cs => {
            const isLocked = !cs.free && !isPremium;
            return (
              <button
                key={cs.id}
                onClick={() => !isLocked && setClusterStyle(cs.id)}
                disabled={isLocked}
                style={{
                  padding: '8px 15px',
                  background: clusterStyle === cs.id 
                    ? 'linear-gradient(135deg, #7c3aed, #3b82f6)' 
                    : 'rgba(30, 20, 50, 0.5)',
                  border: clusterStyle === cs.id 
                    ? '2px solid #a78bfa' 
                    : '1px solid rgba(124, 58, 237, 0.3)',
                  borderRadius: 8,
                  color: clusterStyle === cs.id ? '#fff' : '#a1a1aa',
                  fontSize: '0.8rem',
                  cursor: isLocked ? 'not-allowed' : 'pointer',
                  opacity: isLocked ? 0.5 : 1
                }}
                data-testid={`cluster-style-${cs.id}`}
              >
                {cs.name} {isLocked && '🔒'}
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Toggle Options */}
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={showLabels}
            onChange={(e) => setShowLabels(e.target.checked)}
            style={{ width: 18, height: 18, accentColor: '#7c3aed' }}
          />
          <span style={{ color: '#d1d5db', fontSize: '0.85rem' }}>Show Map Labels</span>
        </label>
        
        <label style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 8, 
          cursor: isPremium ? 'pointer' : 'not-allowed',
          opacity: isPremium ? 1 : 0.5
        }}>
          <input
            type="checkbox"
            checked={animateMarkers}
            onChange={(e) => isPremium && setAnimateMarkers(e.target.checked)}
            disabled={!isPremium}
            style={{ width: 18, height: 18, accentColor: '#7c3aed' }}
          />
          <span style={{ color: '#d1d5db', fontSize: '0.85rem' }}>
            Animate Markers {!isPremium && '🔒'}
          </span>
        </label>
      </div>
      
      {/* Premium Upgrade Prompt */}
      {!isPremium && (
        <div style={{
          marginTop: 20,
          padding: 15,
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(234, 88, 12, 0.15))',
          borderRadius: 10,
          border: '1px solid rgba(245, 158, 11, 0.3)',
          textAlign: 'center'
        }}>
          <p style={{ color: '#fbbf24', margin: 0, fontSize: '0.85rem' }}>
            ⭐ <strong>Upgrade to Premium</strong> to unlock all map styles, marker colors, and animations!
          </p>
        </div>
      )}
    </div>
  );
};

export default CustomMapStyling;
