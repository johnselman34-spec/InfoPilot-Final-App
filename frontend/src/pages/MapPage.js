import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import L from 'leaflet';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { extractHashtags } from '../utils/hashtags';
import { HashtagDisplay } from '../components/shared';
import CustomMapStyling from '../components/Map/CustomMapStyling';

// Auto-refresh interval for map (30 seconds)
const MAP_REFRESH_INTERVAL = 30000;

// Category colors for color-coded dots
const CATEGORY_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#22c55e', 
  '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6',
  '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e'
];

const MapPage = ({ showToast, setCurrentPage }) => {
  const { token, user } = useAuth();
  const [mapResults, setMapResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hoveredResult, setHoveredResult] = useState(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [containerWidth, setContainerWidth] = useState(800); // Default width
  const [showMapStyling, setShowMapStyling] = useState(false);
  const [mapStyle, setMapStyle] = useState(() => {
    const cached = localStorage.getItem('mapStylePreferences');
    return cached ? JSON.parse(cached) : { preset: 'default', tileUrl: null };
  });
  const mapContainerRef = useRef(null);
  const refreshIntervalRef = useRef(null);
  
  // Category filtering state
  const [categories, setCategories] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [showCategoryFilter, setShowCategoryFilter] = useState(true);
  const [categoryColorMap, setCategoryColorMap] = useState({});
  
  // Update container width when ref changes
  useEffect(() => {
    const updateWidth = () => {
      if (mapContainerRef.current) {
        setContainerWidth(mapContainerRef.current.clientWidth);
      }
    };
    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);
  
  // Fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      const res = await fetch(`${API}/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data || []);
        // Assign colors to categories
        const colorMap = {};
        (data || []).forEach((cat, idx) => {
          colorMap[cat.name] = CATEGORY_COLORS[idx % CATEGORY_COLORS.length];
        });
        setCategoryColorMap(colorMap);
      }
    } catch (e) {
      console.error('Failed to fetch categories:', e);
    }
  }, [token]);
  
  useEffect(() => {
    if (token) {
      fetchCategories();
    }
  }, [token, fetchCategories]);
  
  // AI Search state
  const [aiSearchQuery, setAiSearchQuery] = useState('');
  const [aiSearchLoading, setAiSearchLoading] = useState(false);
  const [aiSearchMode, setAiSearchMode] = useState('comprehensive');
  const [dbSearchLoading, setDbSearchLoading] = useState(false);
  const [dbSearchMode, setDbSearchMode] = useState('smart');

  // Toggle category selection
  const toggleCategory = (categoryName) => {
    setSelectedCategories(prev => {
      if (prev.includes(categoryName)) {
        return prev.filter(c => c !== categoryName);
      } else {
        return [...prev, categoryName];
      }
    });
  };
  
  // Get color for a result based on its categories
  const getResultCategoryColor = (result) => {
    if (result.categories && result.categories.length > 0) {
      const firstCat = result.categories[0];
      return categoryColorMap[firstCat] || '#6b7280';
    }
    return getMarkerColor(result.article_type);
  };
  
  // Filter map results by selected categories
  const filteredMapResults = selectedCategories.length > 0
    ? mapResults.filter(result => 
        result.categories && result.categories.some(cat => selectedCategories.includes(cat))
      )
    : mapResults;

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

  const fetchMapResults = useCallback(async (showLoadingState = true) => {
    if (showLoadingState) setLoading(true);
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
        setLastUpdate(new Date());
      }
    } catch (e) {
      console.error('Failed to fetch map results:', e);
    }
    if (showLoadingState) setLoading(false);
  }, [token, extractLocation]);

  // Export map data as CSV or JSON
  const exportMapData = (format) => {
    if (mapResults.length === 0) {
      showToast('No data to export', 'error');
      return;
    }
    
    const exportData = mapResults.map(r => ({
      title: r.title || 'Untitled',
      url: r.url || '',
      latitude: r.latitude,
      longitude: r.longitude,
      article_type: r.article_type || 'Unknown',
      location: r.extractedPlace || 'Unknown',
      snippet: (r.snippet || '').substring(0, 200),
      hashtags: (r.hashtags || []).join(', ')
    }));
    
    let content, filename, mimeType;
    
    if (format === 'csv') {
      // Create CSV content
      const headers = ['Title', 'URL', 'Latitude', 'Longitude', 'Article Type', 'Location', 'Snippet', 'Hashtags'];
      const csvRows = [
        headers.join(','),
        ...exportData.map(row => [
          `"${(row.title || '').replace(/"/g, '""')}"`,
          `"${row.url}"`,
          row.latitude,
          row.longitude,
          `"${row.article_type}"`,
          `"${row.location}"`,
          `"${(row.snippet || '').replace(/"/g, '""')}"`,
          `"${row.hashtags}"`
        ].join(','))
      ];
      content = csvRows.join('\n');
      filename = `infopilot_map_export_${new Date().toISOString().slice(0,10)}.csv`;
      mimeType = 'text/csv';
    } else {
      // JSON format
      content = JSON.stringify(exportData, null, 2);
      filename = `infopilot_map_export_${new Date().toISOString().slice(0,10)}.json`;
      mimeType = 'application/json';
    }
    
    // Create download
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    showToast(`📊 Exported ${exportData.length} results as ${format.toUpperCase()}!`, 'success');
  };

  // AI Intelligent Search for Map
  const aiSearchForMap = async () => {
    if (!aiSearchQuery.trim()) {
      showToast('Please enter a search query', 'error');
      return;
    }
    
    setAiSearchLoading(true);
    
    try {
      const res = await fetch(`${API}/ai-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ 
          query: aiSearchQuery,
          mode: aiSearchMode,
          auto_categorize: true
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`🤖 ${data.message}`, 'success');
        // Refresh map to show new results
        fetchMapResults(true);
      } else {
        const error = await res.json();
        showToast(error.detail || 'AI Search failed', 'error');
      }
    } catch (e) {
      showToast('AI Search failed', 'error');
    }
    
    setAiSearchLoading(false);
  };

  // Auto-Categorize Search for Map
  const autoCategorizeSearc = async () => {
    if (!aiSearchQuery.trim()) {
      showToast('Please enter a search query', 'error');
      return;
    }
    
    setAiSearchLoading(true);
    
    try {
      const res = await fetch(`${API}/auto-categorize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query: aiSearchQuery })
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`🎯 ${data.message}`, 'success');
        // Refresh map to show new results
        fetchMapResults(true);
      } else {
        const error = await res.json();
        showToast(error.detail || 'Auto-categorization failed', 'error');
      }
    } catch (e) {
      showToast('Auto-categorization failed', 'error');
    }
    
    setAiSearchLoading(false);
  };

  // Database Text Search for Map
  const databaseSearchForMap = async () => {
    if (!aiSearchQuery.trim()) {
      showToast('Please enter a search query', 'error');
      return;
    }
    
    setDbSearchLoading(true);
    
    try {
      const res = await fetch(`${API}/database-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ 
          query: aiSearchQuery,
          mode: dbSearchMode,
          limit: 100
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`📚 ${data.message}`, 'success');
        // Refresh map to show results
        fetchMapResults(true);
      } else {
        const error = await res.json();
        showToast(error.detail || 'Database search failed', 'error');
      }
    } catch (e) {
      showToast('Database search failed', 'error');
    }
    
    setDbSearchLoading(false);
  };

  useEffect(() => {
    fetchMapResults();
  }, [fetchMapResults]);

  // Auto-refresh map data
  useEffect(() => {
    if (autoRefresh && token) {
      refreshIntervalRef.current = setInterval(() => {
        fetchMapResults(false); // Silent refresh (no loading state)
      }, MAP_REFRESH_INTERVAL);
    }
    
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [autoRefresh, token, fetchMapResults]);

  // Listen for custom events to trigger map refresh
  useEffect(() => {
    const handleMapRefresh = () => {
      fetchMapResults(false);
    };
    
    window.addEventListener('infopilot-data-changed', handleMapRefresh);
    
    return () => {
      window.removeEventListener('infopilot-data-changed', handleMapRefresh);
    };
  }, [fetchMapResults]);

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
        <div style={{ display: 'flex', alignItems: 'center', gap: 15, flexWrap: 'wrap' }}>
          <span style={{ color: '#10b981', fontSize: '0.9rem' }}>
            {mapResults.length} results mapped • Click markers to open articles
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button 
              onClick={() => fetchMapResults(true)} 
              className="btn btn-secondary"
              style={{ padding: '4px 12px', fontSize: '0.8rem' }}
              data-testid="map-refresh-btn"
            >
              🔄 Refresh
            </button>
            <label style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer', fontSize: '0.8rem', color: '#a1a1aa' }}>
              <input 
                type="checkbox" 
                checked={autoRefresh} 
                onChange={(e) => setAutoRefresh(e.target.checked)}
                style={{ accentColor: '#10b981' }}
              />
              Auto-refresh
            </label>
            {lastUpdate && (
              <span style={{ fontSize: '0.75rem', color: '#71717a' }}>
                Last: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={() => setShowMapStyling(!showMapStyling)}
              className="btn btn-secondary"
              style={{ 
                padding: '4px 12px', 
                fontSize: '0.8rem',
                background: showMapStyling ? 'linear-gradient(135deg, #7c3aed, #3b82f6)' : undefined
              }}
              data-testid="toggle-map-styling-btn"
            >
              🎨 {showMapStyling ? 'Hide Styling' : 'Map Style'}
            </button>
          </div>
        </div>
      </div>
      
      {/* Custom Map Styling Panel */}
      {showMapStyling && (
        <div style={{ marginBottom: 15 }}>
          <CustomMapStyling 
            onStyleChange={(style) => {
              setMapStyle(style);
              localStorage.setItem('mapStylePreferences', JSON.stringify(style));
            }}
            currentStyle={mapStyle}
            showToast={showToast}
          />
        </div>
      )}
      
      {/* AI Search Section */}
      <div style={{ 
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(236, 72, 153, 0.15))',
        borderRadius: 12,
        padding: 15,
        marginBottom: 15,
        border: '1px solid rgba(124, 58, 237, 0.3)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <input
            type="text"
            value={aiSearchQuery}
            onChange={(e) => setAiSearchQuery(e.target.value)}
            placeholder="Enter search query for AI-powered search..."
            style={{
              flex: 1,
              minWidth: 200,
              padding: '10px 15px',
              background: 'rgba(30, 20, 50, 0.8)',
              border: '1px solid rgba(124, 58, 237, 0.4)',
              borderRadius: 8,
              color: '#fff'
            }}
            onKeyPress={(e) => e.key === 'Enter' && aiSearchForMap()}
            data-testid="map-ai-search-input"
          />
          <button
            onClick={autoCategorizeSearc}
            disabled={aiSearchLoading || !aiSearchQuery.trim()}
            className="btn"
            style={{
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              color: '#fff',
              padding: '10px 15px',
              opacity: (!aiSearchQuery.trim() || aiSearchLoading) ? 0.5 : 1
            }}
            data-testid="map-auto-categorize-btn"
          >
            {aiSearchLoading ? '⏳' : '🎯'} Auto-Categorize
          </button>
          <button
            onClick={aiSearchForMap}
            disabled={aiSearchLoading || !aiSearchQuery.trim()}
            className="btn"
            style={{
              background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
              color: '#fff',
              padding: '10px 15px',
              opacity: (!aiSearchQuery.trim() || aiSearchLoading) ? 0.5 : 1
            }}
            data-testid="map-ai-search-btn"
          >
            {aiSearchLoading ? '🤖 Searching...' : '🤖 AI Search'}
          </button>
          <select
            value={aiSearchMode}
            onChange={(e) => setAiSearchMode(e.target.value)}
            style={{
              background: 'rgba(124, 58, 237, 0.3)',
              border: '1px solid rgba(124, 58, 237, 0.4)',
              color: '#a78bfa',
              padding: '8px 12px',
              borderRadius: 8,
              fontSize: '0.85rem'
            }}
          >
            <option value="comprehensive">📊 Comprehensive</option>
            <option value="news">📰 News</option>
            <option value="research">🔬 Research</option>
          </select>
          <button
            onClick={databaseSearchForMap}
            disabled={dbSearchLoading || !aiSearchQuery.trim()}
            className="btn"
            style={{
              background: 'linear-gradient(135deg, #06b6d4, #0891b2)',
              color: '#fff',
              padding: '10px 15px',
              opacity: (!aiSearchQuery.trim() || dbSearchLoading) ? 0.5 : 1
            }}
            data-testid="map-database-search-btn"
          >
            {dbSearchLoading ? '📚 Searching...' : '📚 DB Search'}
          </button>
          <select
            value={dbSearchMode}
            onChange={(e) => setDbSearchMode(e.target.value)}
            style={{
              background: 'rgba(6, 182, 212, 0.3)',
              border: '1px solid rgba(6, 182, 212, 0.4)',
              color: '#22d3ee',
              padding: '8px 12px',
              borderRadius: 8,
              fontSize: '0.85rem'
            }}
          >
            <option value="smart">🧠 Smart</option>
            <option value="exact">🎯 Exact</option>
            <option value="fuzzy">🔍 Fuzzy</option>
          </select>
        </div>
        <p style={{ color: '#a1a1aa', fontSize: '0.75rem', marginTop: 8, marginBottom: 0 }}>
          💡 <strong>AI Search:</strong> Google, Bing, DuckDuckGo, Brave with GPT keyword expansion. <strong>DB Search:</strong> Search your already collated results.
        </p>
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
                url={mapStyle.tileUrl || "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"}
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
                  left: Math.min(hoverPosition.x + 15, containerWidth - 320),
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

      {/* Premium Map Export Section */}
      {mapResults.length > 0 && (
        <div style={{
          marginTop: 25,
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(236, 72, 153, 0.15))',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(245, 158, 11, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 15
        }} data-testid="map-export-section">
          <div style={{ flex: 1, minWidth: 200 }}>
            <h3 style={{ color: '#f59e0b', margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ 
                background: 'linear-gradient(135deg, #f59e0b, #ec4899)', 
                padding: '2px 8px', 
                borderRadius: 6, 
                fontSize: '0.65rem', 
                color: '#fff' 
              }}>PREMIUM</span>
              📊 Export Map Data
            </h3>
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: 0 }}>
              Download your mapped results as CSV or JSON for analysis and research!
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button 
              onClick={() => exportMapData('csv')}
              className="btn btn-primary"
              style={{ 
                background: 'linear-gradient(135deg, #10b981, #06b6d4)',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
              data-testid="export-csv-btn"
            >
              📄 Export CSV
            </button>
            <button 
              onClick={() => exportMapData('json')}
              className="btn btn-primary"
              style={{ 
                background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
              data-testid="export-json-btn"
            >
              📋 Export JSON
            </button>
          </div>
        </div>
      )}

      <p style={{ marginTop: 20, color: '#a1a1aa', fontSize: '0.85rem', textAlign: 'center' }}>
        💡 Hover over markers to preview details. Click any marker to open the article in a new tab!
      </p>
    </div>
  );
};

export default MapPage;
