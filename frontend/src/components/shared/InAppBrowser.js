/**
 * InAppBrowser - Opens external links within the application
 * Features:
 * - Iframe-based browser for external URLs
 * - Navigation controls (back, forward, refresh)
 * - URL display bar
 * - Close button to return to app
 * - Fullscreen toggle
 */
import React, { useState, useRef, useEffect } from 'react';

export const InAppBrowser = ({ 
  url, 
  onClose, 
  title = 'External Link',
  initialFullscreen = false 
}) => {
  const [currentUrl, setCurrentUrl] = useState(url);
  const [isFullscreen, setIsFullscreen] = useState(initialFullscreen);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const iframeRef = useRef(null);

  useEffect(() => {
    setCurrentUrl(url);
    setIsLoading(true);
    setLoadError(false);
  }, [url]);

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = () => {
    setIsLoading(false);
    setLoadError(true);
  };

  const openExternal = () => {
    window.open(currentUrl, '_blank', 'noopener,noreferrer');
  };

  const refreshPage = () => {
    setIsLoading(true);
    setLoadError(false);
    if (iframeRef.current) {
      iframeRef.current.src = currentUrl;
    }
  };

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.9)',
        zIndex: 10000,
        display: 'flex',
        flexDirection: 'column'
      }}
      data-testid="in-app-browser"
    >
      {/* Browser Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
        padding: '10px 15px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        borderBottom: '1px solid rgba(124, 58, 237, 0.3)'
      }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            background: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid rgba(239, 68, 68, 0.5)',
            color: '#ef4444',
            padding: '8px 12px',
            borderRadius: 8,
            cursor: 'pointer',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 5
          }}
          data-testid="browser-close-btn"
        >
          ← Back to App
        </button>

        {/* URL Bar */}
        <div style={{
          flex: 1,
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 20,
          padding: '8px 15px',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <span style={{ color: '#10b981', fontSize: '0.8rem' }}>🔒</span>
          <span style={{ 
            color: '#a1a1aa', 
            fontSize: '0.85rem', 
            overflow: 'hidden', 
            textOverflow: 'ellipsis', 
            whiteSpace: 'nowrap',
            flex: 1
          }}>
            {currentUrl}
          </span>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={refreshPage}
            style={{
              background: 'rgba(59, 130, 246, 0.2)',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              color: '#3b82f6',
              padding: '8px 12px',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
            title="Refresh"
            data-testid="browser-refresh-btn"
          >
            🔄
          </button>
          <button
            onClick={openExternal}
            style={{
              background: 'rgba(16, 185, 129, 0.2)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              color: '#10b981',
              padding: '8px 12px',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
            title="Open in new tab"
            data-testid="browser-external-btn"
          >
            ↗️
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            style={{
              background: 'rgba(139, 92, 246, 0.2)',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              color: '#8b5cf6',
              padding: '8px 12px',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            data-testid="browser-fullscreen-btn"
          >
            {isFullscreen ? '⊟' : '⊞'}
          </button>
        </div>
      </div>

      {/* Loading Indicator */}
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          zIndex: 10001
        }}>
          <div className="spinner" style={{ margin: '0 auto 15px' }} />
          <p style={{ color: '#a1a1aa' }}>Loading {title}...</p>
        </div>
      )}

      {/* Error State */}
      {loadError && (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 20
        }}>
          <div style={{ fontSize: '4rem' }}>🚫</div>
          <h2 style={{ color: '#ef4444' }}>Unable to load page</h2>
          <p style={{ color: '#a1a1aa', textAlign: 'center', maxWidth: 400 }}>
            This page couldn't be displayed in the in-app browser due to security restrictions.
          </p>
          <button
            onClick={openExternal}
            style={{
              background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
              border: 'none',
              color: '#fff',
              padding: '12px 24px',
              borderRadius: 25,
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '1rem'
            }}
          >
            ↗️ Open in New Tab Instead
          </button>
        </div>
      )}

      {/* Iframe */}
      <iframe
        ref={iframeRef}
        src={currentUrl}
        onLoad={handleLoad}
        onError={handleError}
        style={{
          flex: 1,
          border: 'none',
          width: '100%',
          display: loadError ? 'none' : 'block'
        }}
        title={title}
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        data-testid="browser-iframe"
      />
    </div>
  );
};

/**
 * useInAppBrowser - Hook to manage in-app browser state
 */
export const useInAppBrowser = () => {
  const [browserState, setBrowserState] = useState({
    isOpen: false,
    url: '',
    title: ''
  });

  const openInAppBrowser = (url, title = 'External Link') => {
    setBrowserState({
      isOpen: true,
      url,
      title
    });
  };

  const closeInAppBrowser = () => {
    setBrowserState({
      isOpen: false,
      url: '',
      title: ''
    });
  };

  return {
    browserState,
    openInAppBrowser,
    closeInAppBrowser,
    InAppBrowserComponent: browserState.isOpen ? (
      <InAppBrowser
        url={browserState.url}
        title={browserState.title}
        onClose={closeInAppBrowser}
      />
    ) : null
  };
};

export default InAppBrowser;
