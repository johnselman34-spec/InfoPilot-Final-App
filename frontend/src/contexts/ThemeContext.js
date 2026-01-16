/**
 * Theme Context & Provider
 * Provides app-wide dark/light theme toggle + accent color customization
 */
import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

// Available accent color themes
export const ACCENT_COLORS = {
  purple: {
    name: 'Royal Purple',
    primary: '#7c3aed',
    secondary: '#ec4899',
    gradient: 'linear-gradient(135deg, #7c3aed, #ec4899)',
    hover: 'rgba(124, 58, 237, 0.1)',
    border: 'rgba(124, 58, 237, 0.3)',
  },
  pink: {
    name: 'Hot Pink',
    primary: '#ec4899',
    secondary: '#f472b6',
    gradient: 'linear-gradient(135deg, #ec4899, #f472b6)',
    hover: 'rgba(236, 72, 153, 0.1)',
    border: 'rgba(236, 72, 153, 0.3)',
  },
  blue: {
    name: 'Ocean Blue',
    primary: '#3b82f6',
    secondary: '#06b6d4',
    gradient: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
    hover: 'rgba(59, 130, 246, 0.1)',
    border: 'rgba(59, 130, 246, 0.3)',
  },
  green: {
    name: 'Forest Green',
    primary: '#10b981',
    secondary: '#34d399',
    gradient: 'linear-gradient(135deg, #10b981, #34d399)',
    hover: 'rgba(16, 185, 129, 0.1)',
    border: 'rgba(16, 185, 129, 0.3)',
  },
  orange: {
    name: 'Sunset Orange',
    primary: '#f59e0b',
    secondary: '#fb923c',
    gradient: 'linear-gradient(135deg, #f59e0b, #fb923c)',
    hover: 'rgba(245, 158, 11, 0.1)',
    border: 'rgba(245, 158, 11, 0.3)',
  },
  red: {
    name: 'Ruby Red',
    primary: '#ef4444',
    secondary: '#f87171',
    gradient: 'linear-gradient(135deg, #ef4444, #f87171)',
    hover: 'rgba(239, 68, 68, 0.1)',
    border: 'rgba(239, 68, 68, 0.3)',
  },
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  // Initialize from localStorage or defaults
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) return JSON.parse(saved);
    return true; // Default to dark mode
  });

  const [accentColor, setAccentColor] = useState(() => {
    const saved = localStorage.getItem('accentColor');
    if (saved && ACCENT_COLORS[saved]) return saved;
    return 'purple'; // Default accent color
  });

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    const accent = ACCENT_COLORS[accentColor];
    
    // Apply accent colors
    root.style.setProperty('--accent-primary', accent.primary);
    root.style.setProperty('--accent-secondary', accent.secondary);
    root.style.setProperty('--accent-gradient', accent.gradient);
    root.style.setProperty('--accent-hover', accent.hover);
    root.style.setProperty('--accent-border', accent.border);
    
    // Also update the CSS custom properties used by components
    root.style.setProperty('--primary-purple', accent.primary);
    root.style.setProperty('--blazing-pink', accent.secondary);
    
    if (isDarkMode) {
      root.classList.add('dark-mode');
      root.classList.remove('light-mode');
      root.style.setProperty('--bg-primary', '#0f0a1f');
      root.style.setProperty('--bg-secondary', '#1a1035');
      root.style.setProperty('--bg-card', 'rgba(30, 20, 50, 0.8)');
      root.style.setProperty('--bg-hover', accent.hover);
      root.style.setProperty('--text-primary', '#e5e7eb');
      root.style.setProperty('--text-secondary', '#a1a1aa');
      root.style.setProperty('--text-muted', '#71717a');
      root.style.setProperty('--border-color', accent.border);
    } else {
      root.classList.remove('dark-mode');
      root.classList.add('light-mode');
      root.style.setProperty('--bg-primary', '#f8fafc');
      root.style.setProperty('--bg-secondary', '#ffffff');
      root.style.setProperty('--bg-card', 'rgba(255, 255, 255, 0.95)');
      root.style.setProperty('--bg-hover', accent.hover);
      root.style.setProperty('--text-primary', '#1e293b');
      root.style.setProperty('--text-secondary', '#475569');
      root.style.setProperty('--text-muted', '#94a3b8');
      root.style.setProperty('--border-color', accent.border);
    }
    
    // Save preferences
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
    localStorage.setItem('accentColor', accentColor);
  }, [isDarkMode, accentColor]);

  const toggleDarkMode = () => setIsDarkMode(prev => !prev);
  const changeAccentColor = (color) => {
    if (ACCENT_COLORS[color]) setAccentColor(color);
  };

  return (
    <ThemeContext.Provider value={{ 
      isDarkMode, 
      toggleDarkMode, 
      setIsDarkMode,
      accentColor,
      changeAccentColor,
      accentColors: ACCENT_COLORS,
      currentAccent: ACCENT_COLORS[accentColor]
    }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Theme Toggle Button Component (combines dark mode + accent color + gallery)
export const ThemeToggle = ({ compact = false, showColorPicker = false, onOpenGallery, onOpenPreview }) => {
  const { isDarkMode, toggleDarkMode, accentColor, changeAccentColor, accentColors, currentAccent } = useTheme();
  const [showColors, setShowColors] = useState(false);
  
  if (compact) {
    return (
      <button
        onClick={toggleDarkMode}
        style={{
          background: 'transparent',
          border: 'none',
          fontSize: '1.2rem',
          cursor: 'pointer',
          padding: 8,
          borderRadius: '50%',
        }}
        title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        data-testid="theme-toggle-compact"
      >
        {isDarkMode ? '☀️' : '🌙'}
      </button>
    );
  }
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {/* Dark/Light Mode Toggle */}
      <button
        onClick={toggleDarkMode}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '10px 16px',
          background: isDarkMode 
            ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(251, 191, 36, 0.2))'
            : `linear-gradient(135deg, ${currentAccent.hover}, ${currentAccent.hover})`,
          border: `1px solid ${isDarkMode ? 'rgba(245, 158, 11, 0.3)' : currentAccent.border}`,
          borderRadius: 10,
          cursor: 'pointer',
          transition: 'all 0.3s',
          color: isDarkMode ? '#fbbf24' : currentAccent.primary,
          fontSize: '0.85rem',
          fontWeight: 600,
          width: '100%',
        }}
        data-testid="dark-mode-toggle"
      >
        <span style={{ fontSize: '1.2rem' }}>{isDarkMode ? '☀️' : '🌙'}</span>
        <span>{isDarkMode ? 'Light Mode' : 'Dark Mode'}</span>
      </button>
      
      {/* Accent Color Picker */}
      {showColorPicker && (
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowColors(!showColors)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 16px',
              background: `linear-gradient(135deg, ${currentAccent.hover}, ${currentAccent.hover})`,
              border: `1px solid ${currentAccent.border}`,
              borderRadius: 10,
              cursor: 'pointer',
              transition: 'all 0.3s',
              color: currentAccent.primary,
              fontSize: '0.85rem',
              fontWeight: 600,
              width: '100%',
            }}
            data-testid="accent-color-toggle"
          >
            <span style={{ 
              width: 18, 
              height: 18, 
              borderRadius: '50%', 
              background: currentAccent.gradient,
              border: '2px solid white',
            }} />
            <span>{currentAccent.name}</span>
            <span style={{ marginLeft: 'auto' }}>{showColors ? '▲' : '▼'}</span>
          </button>
          
          {showColors && (
            <div style={{
              position: 'absolute',
              bottom: '100%',
              left: 0,
              right: 0,
              background: isDarkMode ? 'rgba(30, 20, 50, 0.98)' : 'rgba(255, 255, 255, 0.98)',
              border: `1px solid ${currentAccent.border}`,
              borderRadius: 10,
              padding: 10,
              marginBottom: 5,
              boxShadow: '0 -4px 20px rgba(0,0,0,0.3)',
              zIndex: 1000,
            }}>
              <div style={{ 
                fontSize: '0.75rem', 
                color: isDarkMode ? '#a1a1aa' : '#64748b', 
                marginBottom: 8,
                fontWeight: 600 
              }}>
                🎨 Choose Accent Color
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
                {Object.entries(accentColors).map(([key, color]) => (
                  <button
                    key={key}
                    onClick={() => { changeAccentColor(key); setShowColors(false); }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      padding: '8px 10px',
                      background: accentColor === key 
                        ? color.hover 
                        : 'transparent',
                      border: accentColor === key 
                        ? `2px solid ${color.primary}` 
                        : '1px solid transparent',
                      borderRadius: 8,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                    data-testid={`accent-color-${key}`}
                  >
                    <span style={{ 
                      width: 16, 
                      height: 16, 
                      borderRadius: '50%', 
                      background: color.gradient,
                      flexShrink: 0,
                    }} />
                    <span style={{ 
                      fontSize: '0.7rem', 
                      color: isDarkMode ? '#d1d5db' : '#374151',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}>
                      {color.name.split(' ')[0]}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Theme Gallery & Preview Buttons */}
      <div style={{ display: 'flex', gap: 8 }}>
        {onOpenGallery && (
          <button
            onClick={onOpenGallery}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              padding: '8px 12px',
              background: `linear-gradient(135deg, ${currentAccent.hover}, ${currentAccent.hover})`,
              border: `1px solid ${currentAccent.border}`,
              borderRadius: 8,
              cursor: 'pointer',
              color: currentAccent.primary,
              fontSize: '0.75rem',
              fontWeight: 600,
            }}
            data-testid="open-theme-gallery"
          >
            🎨 Gallery
          </button>
        )}
        {onOpenPreview && (
          <button
            onClick={onOpenPreview}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              padding: '8px 12px',
              background: `linear-gradient(135deg, ${currentAccent.hover}, ${currentAccent.hover})`,
              border: `1px solid ${currentAccent.border}`,
              borderRadius: 8,
              cursor: 'pointer',
              color: currentAccent.primary,
              fontSize: '0.75rem',
              fontWeight: 600,
            }}
            data-testid="open-theme-preview"
          >
            👁️ Preview
          </button>
        )}
      </div>
    </div>
  );
};

// Re-export for backward compatibility
export const DarkModeProvider = ThemeProvider;
export const useDarkMode = useTheme;
export const DarkModeToggle = ThemeToggle;

export default ThemeContext;
