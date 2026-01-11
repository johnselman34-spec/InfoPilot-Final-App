import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import L from 'leaflet';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { extractHashtags } from '../utils/hashtags';
import { HashtagDisplay } from '../components/shared';

const MapPage = ({ showToast, setCurrentPage }) => {
  const { token } = useAuth();
  const [mapResults, setMapResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hoveredResult, setHoveredResult] = useState(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  const mapContainerRef = useRef(null);

  // Known locations for context-based geocoding
  const KNOWN_LOCATIONS = {
    'texas': { lat: 31.9686, lng: -99.9018 },
    'california': { lat: 36.7783, lng: -119.4179 },
    'new york': { lat: 40.7128, lng: -74.0060 },
    'florida': { lat: 27.6648, lng: -81.5158 },
    'washington': { lat: 47.7511, lng: -120.7401 },
    'washington dc': { lat: 38.9072, lng: -77.0369 },
    'virginia': { lat: 37.4316, lng: -78.6569 },
    'houston': { lat: 29.7604, lng: -95.3698 },
    'midland': { lat: 31.9973, lng: -102.0779 },
    'new haven': { lat: 41.3083, lng: -72.9279 },
    'yale': { lat: 41.3163, lng: -72.9223 },
    'gettysburg': { lat: 39.8309, lng: -77.2311 },
    'united states': { lat: 39.8283, lng: -98.5795 },
    'usa': { lat: 39.8283, lng: -98.5795 },
    'america': { lat: 39.8283, lng: -98.5795 },
    'england': { lat: 51.5074, lng: -0.1278 },
    'france': { lat: 46.2276, lng: 2.2137 },
    'germany': { lat: 51.1657, lng: 10.4515 },
    'air force': { lat: 38.8719, lng: -77.0563 },
    'pentagon': { lat: 38.8719, lng: -77.0563 },
    'white house': { lat: 38.8977, lng: -77.0365 },
  };

  const extractLocation = useCallback((text, title) => {
    if (!text && !title) return null;
    const combined = `${title || ''} ${text || ''}`.toLowerCase();
    for (const [place, coords] of Object.entries(KNOWN_LOCATIONS)) {
      if (combined.includes(place)) {
        return {
          lat: coords.lat + (Math.random() - 0.5) * 1.5,
          lng: coords.lng + (Math.random() - 0.5) * 1.5,
          place: place
        };
      }
    }
    return null;
  }, []);

  const fetchMapResults = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/ultimate-search?limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const resultsWithLocation = data.results
          .map((r) => {
            if (r.latitude && r.longitude && 
                r.latitude >= -90 && r.latitude <= 90 &&
                r.longitude >= -180 && r.longitude <= 180) {
              return { ...r, hasRealLocation: true, hashtags: extractHashtags(r.title, r.snippet, r.article_type) };
            }
            const extracted = extractLocation(r.content || r.snippet, r.title);
            if (extracted) {
              return { 
                ...r, 
                latitude: extracted.lat, 
                longitude: extracted.lng, 
                extractedPlace: extracted.place,
                hashtags: extractHashtags(r.title, r.snippet, r.article_type)
              };
            }
            return null;
          })
          .filter(r => r !== null);
        setMapResults(resultsWithLocation);
      }
    } catch (e) {
      console.error('Failed to fetch map results:', e);
    }
    setLoading(false);
  }, [token, extractLocation]);

  useEffect(() => {
    fetchMapResults();
  }, [fetchMapResults]);

  const fetchMapResults = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/ultimate-search?limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const resultsWithLocation = data.results
          .map((r, idx) => {
            if (r.latitude && r.longitude && 
                r.latitude >= -90 && r.latitude <= 90 &&
                r.longitude >= -180 && r.longitude <= 180) {
              return { ...r, hasRealLocation: true, hashtags: extractHashtags(r.title, r.snippet, r.article_type) };
            }
            const extracted = extractLocation(r.content || r.snippet, r.title);
            if (extracted) {
              return { 
                ...r, 
                latitude: extracted.lat, 
                longitude: extracted.lng, 
                extractedPlace: extracted.place,
                hashtags: extractHashtags(r.title, r.snippet, r.article_type)
              };
            }
            return null;
          })
          .filter(r => r !== null);
        setMapResults(resultsWithLocation);
      }
    } catch (e) {
      console.error('Failed to fetch map results:', e);
    }
    setLoading(false);
  };

  const getMarkerColor = (articleType) => {
    const colors = {
      'News Article': '#ef4444',
      'Blog Post': '#f97316',
      'Academic Paper': '#3b82f6',
      'Wiki': '#10b981',
      'Forum': '#8b5cf6',
      'Government': '#06b6d4',
      'Video': '#ec4899',
      'Unknown': '#6b7280'
    };
    return colors[articleType] || colors['Unknown'];
  };

  // Create custom colored marker icon
  const createCustomIcon = (color) => {
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        width: 24px;
        height: 24px;
        background: ${color};
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 0 10px ${color}, 0 2px 6px rgba(0,0,0,0.4);
        cursor: pointer;
      "></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
      popupAnchor: [0, -12]
    });
  };

  // Handle marker click - open URL in new tab
  const handleMarkerClick = (result) => {
    if (result.url) {
      window.open(result.url, '_blank', 'noopener,noreferrer');
    }
  };

  // Handle marker hover
  const handleMarkerHover = (result, event) => {
    if (mapContainerRef.current) {
      const rect = mapContainerRef.current.getBoundingClientRect();
      const x = event.originalEvent.clientX - rect.left;
      const y = event.originalEvent.clientY - rect.top;
      setHoverPosition({ x, y });
    }
    setHoveredResult(result);
  };

  return (
    <div className="card" data-testid="map-page">
      <div className="card-header">
        <h2>🗺️ Interactive World Map</h2>
        <span style={{ color: '#10b981', fontSize: '0.9rem' }}>
          {mapResults.length} results mapped • Click markers to open articles
        </span>
      </div>

      {/* Legend */}
      <div style={{ 
        display: 'flex', gap: 15, flexWrap: 'wrap', marginBottom: 15,
        padding: 10, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10
      }}>
        {[
          { type: 'News Article', color: '#ef4444' },
          { type: 'Blog Post', color: '#f97316' },
          { type: 'Academic Paper', color: '#3b82f6' },
          { type: 'Wiki', color: '#10b981' },
          { type: 'Forum', color: '#8b5cf6' },
          { type: 'Government', color: '#06b6d4' }
        ].map(({ type, color }) => (
          <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: color, boxShadow: `0 0 5px ${color}` }} />
            <span style={{ fontSize: '0.75rem', color: '#a1a1aa' }}>{type}</span>
          </div>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <div className="loading-spinner"><div className="spinner"></div></div>
          <p style={{ color: '#a1a1aa', marginTop: 15 }}>Loading map data...</p>
        </div>
      ) : mapResults.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <p style={{ color: '#a1a1aa', fontSize: '1.1rem' }}>
            No mapped results yet. Search and collate content to see results on the map!
          </p>
          <button className="btn btn-primary" style={{ marginTop: 15 }} onClick={() => setCurrentPage('search')}>
            Go to Ultimate Search
          </button>
        </div>
      ) : (
        <>
          {/* React-Leaflet Map with hover popups */}
          <div 
            ref={mapContainerRef}
            style={{ 
              height: 450, borderRadius: 12, overflow: 'hidden',
              border: '2px solid rgba(124, 58, 237, 0.3)',
              position: 'relative'
            }}
          >
            <MapContainer
              center={[39.8283, -98.5795]}
              zoom={4}
              style={{ height: '100%', width: '100%' }}
              scrollWheelZoom={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mapResults.slice(0, 50).map((result, idx) => (
                <Marker
                  key={result.id || `marker-${idx}`}
                  position={[result.latitude, result.longitude]}
                  icon={createCustomIcon(getMarkerColor(result.article_type))}
                  eventHandlers={{
                    click: () => handleMarkerClick(result),
                    mouseover: (e) => handleMarkerHover(result, e),
                    mouseout: () => setHoveredResult(null)
                  }}
                />
              ))}
            </MapContainer>

            {/* Hover Popup Window */}
            {hoveredResult && (
              <div 
                style={{
                  position: 'absolute',
                  left: Math.min(hoverPosition.x + 15, mapContainerRef.current?.clientWidth - 320 || 0),
                  top: Math.max(hoverPosition.y - 150, 10),
                  width: 300,
                  background: 'rgba(15, 10, 35, 0.98)',
                  borderRadius: 12,
                  border: `2px solid ${getMarkerColor(hoveredResult.article_type)}`,
                  boxShadow: `0 8px 32px rgba(0,0,0,0.6), 0 0 20px ${getMarkerColor(hoveredResult.article_type)}40`,
                  zIndex: 1000,
                  pointerEvents: 'auto',
                  overflow: 'hidden'
                }}
              >
                {/* Header */}
                <div style={{
                  padding: '10px 12px',
                  background: `linear-gradient(135deg, ${getMarkerColor(hoveredResult.article_type)}30, transparent)`,
                  borderBottom: '1px solid rgba(255,255,255,0.1)'
                }}>
                  <span style={{
                    background: getMarkerColor(hoveredResult.article_type),
                    padding: '3px 8px', borderRadius: 10,
                    fontSize: '0.65rem', fontWeight: 600, color: '#fff'
                  }}>
                    {hoveredResult.article_type}
                  </span>
                  {hoveredResult.extractedPlace && (
                    <span style={{ color: '#10b981', fontSize: '0.7rem', marginLeft: 8 }}>
                      📍 {hoveredResult.extractedPlace.charAt(0).toUpperCase() + hoveredResult.extractedPlace.slice(1)}
                    </span>
                  )}
                </div>
                
                {/* Content */}
                <div style={{ padding: 12 }}>
                  <h4 style={{ color: '#fff', margin: '0 0 8px 0', fontSize: '0.85rem', lineHeight: 1.3 }}>
                    {hoveredResult.title?.substring(0, 70) || 'Untitled'}...
                  </h4>
                  <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: '0 0 8px 0', lineHeight: 1.4 }}>
                    {hoveredResult.snippet?.substring(0, 120) || 'No description'}...
                  </p>
                  
                  {/* Hashtags */}
                  {hoveredResult.hashtags && (
                    <HashtagDisplay hashtags={hoveredResult.hashtags} small={true} />
                  )}
                  
                  {/* Click instruction */}
                  <div style={{ 
                    marginTop: 10, padding: '6px 10px', 
                    background: `${getMarkerColor(hoveredResult.article_type)}30`,
                    borderRadius: 6, textAlign: 'center'
                  }}>
                    <span style={{ color: '#fff', fontSize: '0.7rem', fontWeight: 600 }}>
                      🖱️ Click marker to open article
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results list with hashtags */}
          <div style={{ marginTop: 20 }}>
            <h3 style={{ color: '#f472b6', marginBottom: 15 }}>📍 Mapped Results ({mapResults.length})</h3>
            <div style={{ 
              display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: 12, maxHeight: 400, overflowY: 'auto'
            }}>
              {mapResults.slice(0, 20).map((result, idx) => (
                <div 
                  key={result.id || `result-${idx}`}
                  data-testid={`map-result-${idx}`}
                  style={{
                    padding: 12,
                    background: 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 10,
                    border: '1px solid rgba(124, 58, 237, 0.2)',
                    cursor: 'pointer', transition: 'all 0.2s'
                  }}
                  onClick={() => window.open(result.url, '_blank', 'noopener,noreferrer')}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = getMarkerColor(result.article_type)}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = 'rgba(124, 58, 237, 0.2)'}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <div style={{
                      width: 10, height: 10, borderRadius: '50%',
                      background: getMarkerColor(result.article_type),
                      boxShadow: `0 0 6px ${getMarkerColor(result.article_type)}`
                    }} />
                    <span style={{ color: getMarkerColor(result.article_type), fontSize: '0.7rem', fontWeight: 600 }}>
                      {result.article_type}
                    </span>
                    {result.extractedPlace && (
                      <span style={{ color: '#10b981', fontSize: '0.65rem', marginLeft: 'auto' }}>
                        📍 {result.extractedPlace.charAt(0).toUpperCase() + result.extractedPlace.slice(1)}
                      </span>
                    )}
                  </div>
                  <div style={{ color: '#fff', fontWeight: 600, fontSize: '0.85rem', marginBottom: 5, lineHeight: 1.3 }}>
                    {result.title?.substring(0, 60) || 'Untitled'}...
                  </div>
                  <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: '0 0 8px 0', lineHeight: 1.4 }}>
                    {result.snippet?.substring(0, 80) || ''}...
                  </p>
                  {/* Hashtags */}
                  {result.hashtags && <HashtagDisplay hashtags={result.hashtags} small={true} />}
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      <p style={{ marginTop: 20, color: '#a1a1aa', fontSize: '0.85rem', textAlign: 'center' }}>
        💡 Hover over markers to preview details. Click any marker to open the article in a new tab!
      </p>
    </div>
  );
};

export default MapPage;
