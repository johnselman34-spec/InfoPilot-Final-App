/**
 * MapPopup - Enhanced popup component for map markers
 * Features:
 * - Instant show/hide on hover (no fidgeting)
 * - Close button (X) in top-right corner
 * - Maximize button to expand content
 * - Smooth transitions
 * - Works across MapPage, MarketplacePage, and UltimateSearchPage
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';

/**
 * MapPopupProvider - Context for managing popup state across maps
 */
export const useMapPopup = () => {
  const [activePopup, setActivePopup] = useState(null);
  const [isMaximized, setIsMaximized] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const timeoutRef = useRef(null);

  // Clear any pending timeout
  const clearPopupTimeout = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Show popup immediately when hovering a marker
  const showPopup = useCallback((data, position) => {
    clearPopupTimeout();
    setActivePopup(data);
    setPopupPosition(position);
    setIsMaximized(false);
  }, [clearPopupTimeout]);

  // Hide popup - with optional delay for smooth UX
  const hidePopup = useCallback((immediate = false) => {
    clearPopupTimeout();
    if (immediate) {
      setActivePopup(null);
      setIsMaximized(false);
    } else {
      timeoutRef.current = setTimeout(() => {
        setActivePopup(null);
        setIsMaximized(false);
      }, 150);
    }
  }, [clearPopupTimeout]);

  // Cancel hide when hovering the popup itself
  const keepPopupOpen = useCallback(() => {
    clearPopupTimeout();
  }, [clearPopupTimeout]);

  // Toggle maximize state
  const toggleMaximize = useCallback(() => {
    setIsMaximized(prev => !prev);
  }, []);

  // Close popup immediately
  const closePopup = useCallback(() => {
    clearPopupTimeout();
    setActivePopup(null);
    setIsMaximized(false);
  }, [clearPopupTimeout]);

  // Cleanup on unmount
  useEffect(() => {
    return () => clearPopupTimeout();
  }, [clearPopupTimeout]);

  return {
    activePopup,
    isMaximized,
    popupPosition,
    showPopup,
    hidePopup,
    keepPopupOpen,
    toggleMaximize,
    closePopup
  };
};

/**
 * MapPopupContent - The actual popup UI component
 */
export const MapPopupContent = ({
  data,
  position,
  isMaximized,
  onClose,
  onMaximize,
  onMouseEnter,
  onMouseLeave,
  containerWidth = 800,
  getMarkerColor,
  HashtagDisplay,
  onOpenUrl
}) => {
  if (!data) return null;

  const markerColor = getMarkerColor ? getMarkerColor(data.article_type) : '#7c3aed';
  
  // Calculate popup position to stay within bounds
  const popupWidth = isMaximized ? 450 : 320;
  const popupHeight = isMaximized ? 400 : 220;
  
  let left = position.x;
  let top = position.y;
  
  // Ensure popup stays within container
  if (left + popupWidth > containerWidth - 20) {
    left = Math.max(20, containerWidth - popupWidth - 20);
  }
  if (left < 20) left = 20;
  if (top < 20) top = 20;

  return (
    <div
      data-testid="map-popup-content"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      style={{
        position: 'absolute',
        left: left,
        top: top,
        width: popupWidth,
        maxHeight: popupHeight,
        background: 'linear-gradient(145deg, rgba(20, 10, 40, 0.98), rgba(30, 15, 50, 0.98))',
        borderRadius: 12,
        padding: 0,
        boxShadow: `0 8px 32px rgba(0, 0, 0, 0.5), 0 0 20px ${markerColor}40`,
        border: `2px solid ${markerColor}60`,
        zIndex: 1000,
        backdropFilter: 'blur(10px)',
        transition: 'all 0.2s ease-out',
        overflow: 'hidden',
        animation: 'popupFadeIn 0.15s ease-out'
      }}
    >
      {/* Header with Close and Maximize buttons */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 12px',
        background: `linear-gradient(90deg, ${markerColor}30, transparent)`,
        borderBottom: `1px solid ${markerColor}30`
      }}>
        {/* Article type badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: markerColor,
            boxShadow: `0 0 8px ${markerColor}`
          }} />
          <span style={{ 
            color: markerColor, 
            fontSize: '0.75rem', 
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            {data.article_type || 'Article'}
          </span>
        </div>
        
        {/* Control buttons */}
        <div style={{ display: 'flex', gap: 4 }}>
          {/* Maximize button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onMaximize && onMaximize();
            }}
            data-testid="popup-maximize-btn"
            style={{
              width: 24,
              height: 24,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(255,255,255,0.1)',
              border: 'none',
              borderRadius: 4,
              color: '#a1a1aa',
              cursor: 'pointer',
              fontSize: '0.8rem',
              transition: 'all 0.15s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
              e.currentTarget.style.color = '#fff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
              e.currentTarget.style.color = '#a1a1aa';
            }}
            title={isMaximized ? 'Minimize' : 'Maximize'}
          >
            {isMaximized ? '⊟' : '⊞'}
          </button>
          
          {/* Close button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClose && onClose();
            }}
            data-testid="popup-close-btn"
            style={{
              width: 24,
              height: 24,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(239, 68, 68, 0.2)',
              border: 'none',
              borderRadius: 4,
              color: '#ef4444',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 'bold',
              transition: 'all 0.15s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.4)';
              e.currentTarget.style.color = '#fff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)';
              e.currentTarget.style.color = '#ef4444';
            }}
            title="Close"
          >
            ×
          </button>
        </div>
      </div>

      {/* Content area */}
      <div style={{ 
        padding: 12,
        overflowY: 'auto',
        maxHeight: isMaximized ? 340 : 160
      }}>
        {/* Location badge if available */}
        {data.extractedPlace && (
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            padding: '3px 8px',
            background: 'rgba(16, 185, 129, 0.2)',
            borderRadius: 4,
            marginBottom: 8,
            fontSize: '0.7rem',
            color: '#10b981'
          }}>
            📍 {data.extractedPlace.charAt(0).toUpperCase() + data.extractedPlace.slice(1)}
          </div>
        )}

        {/* Title */}
        <h4 style={{ 
          color: '#fff', 
          fontWeight: 600, 
          fontSize: isMaximized ? '1rem' : '0.85rem', 
          lineHeight: 1.3,
          margin: '0 0 8px 0'
        }}>
          {isMaximized 
            ? data.title || 'Untitled'
            : (data.title?.substring(0, 70) || 'Untitled') + (data.title?.length > 70 ? '...' : '')}
        </h4>

        {/* Snippet */}
        <p style={{ 
          color: '#a1a1aa', 
          fontSize: '0.75rem', 
          margin: '0 0 10px 0', 
          lineHeight: 1.5
        }}>
          {isMaximized 
            ? data.snippet || 'No description available'
            : (data.snippet?.substring(0, 120) || 'No description') + (data.snippet?.length > 120 ? '...' : '')}
        </p>

        {/* Categories if available */}
        {data.categories && data.categories.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
            {data.categories.slice(0, isMaximized ? 10 : 3).map((cat, idx) => (
              <span
                key={idx}
                style={{
                  background: 'rgba(124, 58, 237, 0.2)',
                  color: '#a78bfa',
                  padding: '2px 8px',
                  borderRadius: 10,
                  fontSize: '0.65rem',
                  fontWeight: 500
                }}
              >
                {cat}
              </span>
            ))}
            {!isMaximized && data.categories.length > 3 && (
              <span style={{ color: '#71717a', fontSize: '0.65rem' }}>
                +{data.categories.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Hashtags */}
        {HashtagDisplay && data.hashtags && (
          <HashtagDisplay hashtags={data.hashtags} small={true} />
        )}

        {/* Action button */}
        <div style={{ 
          marginTop: 10, 
          padding: '8px 12px', 
          background: `${markerColor}20`,
          borderRadius: 8, 
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s'
        }}
        onClick={() => onOpenUrl && onOpenUrl(data.url)}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = `${markerColor}40`;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = `${markerColor}20`;
        }}
        >
          <span style={{ color: '#fff', fontSize: '0.75rem', fontWeight: 600 }}>
            🔗 {isMaximized ? 'Open Article in New Tab' : 'Click to Open Article'}
          </span>
        </div>
      </div>

      {/* CSS Animation */}
      <style>{`
        @keyframes popupFadeIn {
          from {
            opacity: 0;
            transform: translateY(-10px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>
    </div>
  );
};

/**
 * EnhancedMarker - A marker component with improved hover behavior
 */
export const EnhancedMarker = ({
  result,
  index,
  getMarkerColor,
  onHover,
  onLeave,
  isActive,
  onClick
}) => {
  const markerColor = getMarkerColor ? getMarkerColor(result.article_type) : '#7c3aed';
  
  return (
    <div
      data-testid={`map-marker-${index}`}
      onMouseEnter={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const parentRect = e.currentTarget.closest('[data-map-container]')?.getBoundingClientRect() || { left: 0, top: 0 };
        onHover(result, {
          x: rect.left - parentRect.left + 20,
          y: rect.top - parentRect.top + 30
        });
      }}
      onMouseLeave={() => onLeave()}
      onClick={() => onClick && onClick(result)}
      style={{
        position: 'absolute',
        left: `${result._mapX || 50}%`,
        top: `${result._mapY || 50}%`,
        transform: 'translate(-50%, -50%)',
        cursor: 'pointer',
        zIndex: isActive ? 100 : 10,
        transition: 'transform 0.15s ease-out, z-index 0.15s'
      }}
    >
      <div
        style={{
          width: isActive ? 20 : 14,
          height: isActive ? 20 : 14,
          borderRadius: '50%',
          background: markerColor,
          border: `2px solid ${isActive ? '#fff' : 'rgba(255,255,255,0.8)'}`,
          boxShadow: isActive 
            ? `0 0 20px ${markerColor}, 0 0 40px ${markerColor}60`
            : `0 0 10px ${markerColor}80`,
          transition: 'all 0.15s ease-out',
          animation: isActive ? 'markerPulse 1s infinite' : 'none'
        }}
      />
      <style>{`
        @keyframes markerPulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.2); }
        }
      `}</style>
    </div>
  );
};

export default {
  useMapPopup,
  MapPopupContent,
  EnhancedMarker
};
