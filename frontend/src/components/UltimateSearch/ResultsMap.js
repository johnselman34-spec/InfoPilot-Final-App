import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Fix Leaflet default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

/**
 * Results Map Component
 * Displays search results on an interactive map
 */
const ResultsMap = ({
  results = [],
  center = [39.8283, -98.5795], // US Center
  zoom = 4,
  height = 400,
  onMarkerClick,
  markerColor = '#8b5cf6'
}) => {
  // Create custom marker icon
  const createCustomIcon = (color = markerColor) => {
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        background: ${color};
        width: 24px;
        height: 24px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 2px solid #fff;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      "></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 24],
      popupAnchor: [0, -24]
    });
  };

  // Filter results with valid coordinates
  const mappableResults = results.filter(r => 
    r.latitude && r.longitude && 
    !isNaN(parseFloat(r.latitude)) && 
    !isNaN(parseFloat(r.longitude))
  );

  if (mappableResults.length === 0 && results.length > 0) {
    return (
      <div style={{
        background: 'rgba(59, 130, 246, 0.1)',
        borderRadius: 16,
        padding: 30,
        textAlign: 'center',
        border: '1px solid rgba(59, 130, 246, 0.2)',
        height
      }}>
        <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🗺️</div>
        <p style={{ color: '#a1a1aa', margin: 0 }}>
          No mappable results found
        </p>
        <p style={{ color: '#71717a', fontSize: '0.85rem', marginTop: 5 }}>
          {results.length} results without location data
        </p>
      </div>
    );
  }

  // Calculate bounds if we have results
  const bounds = mappableResults.length > 0
    ? L.latLngBounds(mappableResults.map(r => [parseFloat(r.latitude), parseFloat(r.longitude)]))
    : null;

  return (
    <div style={{
      borderRadius: 16,
      overflow: 'hidden',
      border: '1px solid rgba(139, 92, 246, 0.3)',
      height
    }}>
      <MapContainer
        center={bounds ? bounds.getCenter() : center}
        zoom={bounds ? undefined : zoom}
        bounds={bounds}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {mappableResults.map((result, index) => (
          <Marker
            key={result.id || index}
            position={[parseFloat(result.latitude), parseFloat(result.longitude)]}
            icon={createCustomIcon(result.markerColor || markerColor)}
            eventHandlers={{
              click: () => onMarkerClick && onMarkerClick(result)
            }}
          >
            <Popup>
              <div style={{ minWidth: 200 }}>
                <h4 style={{ margin: '0 0 5px 0', color: '#1a1a2e' }}>
                  {result.title || result.name || 'Result'}
                </h4>
                {result.description && (
                  <p style={{ margin: '0 0 8px 0', fontSize: '0.85rem', color: '#4a4a6a' }}>
                    {result.description.slice(0, 100)}
                    {result.description.length > 100 && '...'}
                  </p>
                )}
                {result.url && (
                  <a 
                    href={result.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ 
                      color: '#8b5cf6', 
                      fontSize: '0.8rem',
                      textDecoration: 'none'
                    }}
                  >
                    View Source →
                  </a>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

export default ResultsMap;
