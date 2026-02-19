/**
 * Facebook In-App Browser Compatibility
 * Detects and handles Facebook's in-app browser quirks
 * 
 * Known issues with FB in-app browser:
 * - Limited localStorage/sessionStorage support
 * - Different window.open behavior
 * - Cookie handling differences
 * - OAuth redirect issues
 */

// Detect Facebook in-app browser
export const isFacebookInAppBrowser = () => {
  const ua = navigator.userAgent || navigator.vendor || window.opera;
  return /FBAN|FBAV|FB_IAB|FB4A|FBIOS|Instagram/i.test(ua);
};

// Detect any in-app browser
export const isInAppBrowser = () => {
  const ua = navigator.userAgent || navigator.vendor || window.opera;
  const inAppPatterns = [
    /FBAN|FBAV|FB_IAB|FB4A|FBIOS/i,  // Facebook
    /Instagram/i,                      // Instagram  
    /Twitter/i,                        // Twitter/X
    /LinkedIn/i,                       // LinkedIn
    /Pinterest/i,                      // Pinterest
    /Snapchat/i,                       // Snapchat
    /TikTok/i,                         // TikTok
    /WebView/i,                        // Generic WebView
  ];
  return inAppPatterns.some(pattern => pattern.test(ua));
};

// Get browser name for in-app browsers
export const getInAppBrowserName = () => {
  const ua = navigator.userAgent || '';
  if (/FBAN|FBAV|FB_IAB|FB4A|FBIOS/i.test(ua)) return 'Facebook';
  if (/Instagram/i.test(ua)) return 'Instagram';
  if (/Twitter/i.test(ua)) return 'Twitter/X';
  if (/LinkedIn/i.test(ua)) return 'LinkedIn';
  if (/Pinterest/i.test(ua)) return 'Pinterest';
  if (/Snapchat/i.test(ua)) return 'Snapchat';
  if (/TikTok/i.test(ua)) return 'TikTok';
  return 'In-App Browser';
};

// Safe storage wrapper that falls back gracefully
export const safeStorage = {
  getItem: (key) => {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      // In-app browsers may block localStorage
      try {
        return sessionStorage.getItem(key);
      } catch (e2) {
        console.warn('Storage not available:', e2);
        return null;
      }
    }
  },
  
  setItem: (key, value) => {
    try {
      localStorage.setItem(key, value);
    } catch (e) {
      try {
        sessionStorage.setItem(key, value);
      } catch (e2) {
        console.warn('Storage not available:', e2);
      }
    }
  },
  
  removeItem: (key) => {
    try {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    } catch (e) {
      console.warn('Storage not available:', e);
    }
  }
};

// Safe window.open that handles in-app browser restrictions
export const safeOpenLink = (url, target = '_blank') => {
  if (isFacebookInAppBrowser()) {
    // Facebook in-app browser may block window.open
    // Try different approaches
    try {
      // Method 1: Direct location change for same window
      if (target === '_self') {
        window.location.href = url;
        return true;
      }
      
      // Method 2: Try window.open
      const newWindow = window.open(url, target);
      if (newWindow) {
        return true;
      }
      
      // Method 3: Create a temporary link and click it
      const link = document.createElement('a');
      link.href = url;
      link.target = target;
      link.rel = 'noopener noreferrer';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      return true;
    } catch (e) {
      console.error('Failed to open link:', e);
      // Last resort: show the URL to user
      alert(`Please copy this link and open it in your browser:\n\n${url}`);
      return false;
    }
  } else {
    // Standard browser
    window.open(url, target, 'noopener,noreferrer');
    return true;
  }
};

// Component to show in-app browser warning
export const InAppBrowserWarning = ({ onDismiss }) => {
  if (!isInAppBrowser()) return null;
  
  const browserName = getInAppBrowserName();
  
  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      background: 'linear-gradient(135deg, #f59e0b, #d97706)',
      padding: '15px 20px',
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 15,
      flexWrap: 'wrap'
    }}>
      <div style={{ flex: 1, minWidth: 200 }}>
        <strong style={{ color: '#fff', display: 'block', marginBottom: 4 }}>
          📱 {browserName} Browser Detected
        </strong>
        <span style={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.85rem' }}>
          For the best experience, open InfoPilot in Safari, Chrome, or your default browser.
        </span>
      </div>
      
      <div style={{ display: 'flex', gap: 10 }}>
        <button
          onClick={() => {
            // Try to open in system browser
            safeOpenLink(window.location.href, '_system');
          }}
          style={{
            background: '#fff',
            color: '#d97706',
            border: 'none',
            padding: '8px 16px',
            borderRadius: 20,
            fontWeight: 600,
            cursor: 'pointer',
            fontSize: '0.85rem'
          }}
        >
          Open in Browser
        </button>
        
        {onDismiss && (
          <button
            onClick={onDismiss}
            style={{
              background: 'rgba(0,0,0,0.2)',
              color: '#fff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: 20,
              cursor: 'pointer',
              fontSize: '0.85rem'
            }}
          >
            Continue Anyway
          </button>
        )}
      </div>
    </div>
  );
};

// Hook for in-app browser detection
export const useInAppBrowser = () => {
  const isInApp = isInAppBrowser();
  const isFacebook = isFacebookInAppBrowser();
  const browserName = isInApp ? getInAppBrowserName() : null;
  
  return {
    isInApp,
    isFacebook,
    browserName,
    safeStorage,
    safeOpenLink
  };
};

export default {
  isFacebookInAppBrowser,
  isInAppBrowser,
  getInAppBrowserName,
  safeStorage,
  safeOpenLink,
  InAppBrowserWarning,
  useInAppBrowser
};
