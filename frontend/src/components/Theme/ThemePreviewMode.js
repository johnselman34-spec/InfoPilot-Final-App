/**
 * Visual Theme Preview Mode
 * Split-screen comparison showing dark vs light mode with different accent colors
 */
import React, { useState } from 'react';
import { useTheme, ACCENT_COLORS } from '../../contexts/ThemeContext';

const ThemePreviewMode = ({ onClose, showToast }) => {
  const { isDarkMode, accentColor, setIsDarkMode, changeAccentColor } = useTheme();
  const [leftTheme, setLeftTheme] = useState({ isDark: true, accent: 'purple' });
  const [rightTheme, setRightTheme] = useState({ isDark: false, accent: 'blue' });
  const [selectedSide, setSelectedSide] = useState(null);

  // Apply theme
  const applyTheme = (theme) => {
    setIsDarkMode(theme.isDark);
    changeAccentColor(theme.accent);
    showToast?.(`Applied ${theme.isDark ? 'Dark' : 'Light'} mode with ${ACCENT_COLORS[theme.accent].name}!`, 'success');
    onClose();
  };

  // Preview panel content
  const PreviewContent = ({ theme, side }) => {
    const accent = ACCENT_COLORS[theme.accent];
    const bgPrimary = theme.isDark ? '#0f0a1f' : '#f8fafc';
    const bgCard = theme.isDark ? 'rgba(30, 20, 50, 0.8)' : 'rgba(255, 255, 255, 0.95)';
    const textPrimary = theme.isDark ? '#e5e7eb' : '#1e293b';
    const textSecondary = theme.isDark ? '#a1a1aa' : '#64748b';
    
    return (
      <div
        onClick={() => setSelectedSide(side)}
        style={{
          flex: 1,
          background: bgPrimary,
          padding: 20,
          borderRadius: 16,
          border: selectedSide === side 
            ? `3px solid ${accent.primary}` 
            : '2px solid transparent',
          cursor: 'pointer',
          transition: 'all 0.3s',
          transform: selectedSide === side ? 'scale(1.02)' : 'scale(1)',
          boxShadow: selectedSide === side 
            ? `0 0 30px ${accent.primary}40` 
            : 'none',
        }}
        data-testid={`preview-${side}`}
      >
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: 15,
          paddingBottom: 10,
          borderBottom: `1px solid ${theme.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: '1.3rem' }}>{theme.isDark ? '🌙' : '☀️'}</span>
            <span style={{ color: textPrimary, fontWeight: 700 }}>
              {theme.isDark ? 'Dark Mode' : 'Light Mode'}
            </span>
          </div>
          <div style={{
            width: 24,
            height: 24,
            borderRadius: '50%',
            background: accent.gradient,
            border: '2px solid white'
          }} />
        </div>

        {/* Mock Sidebar */}
        <div style={{
          background: bgCard,
          borderRadius: 10,
          padding: 12,
          marginBottom: 12,
          border: `1px solid ${accent.border}`
        }}>
          <div style={{ color: accent.primary, fontWeight: 700, marginBottom: 8, fontSize: '0.9rem' }}>
            📊 InfoPilot Explorer
          </div>
          {['Dashboard', 'Search', 'Statistics', 'Marketplace'].map((item, i) => (
            <div key={i} style={{
              padding: '6px 10px',
              marginBottom: 4,
              borderRadius: 6,
              background: i === 0 ? accent.hover : 'transparent',
              color: i === 0 ? accent.primary : textSecondary,
              fontSize: '0.8rem'
            }}>
              {item}
            </div>
          ))}
        </div>

        {/* Mock Card */}
        <div style={{
          background: bgCard,
          borderRadius: 10,
          padding: 15,
          border: `1px solid ${accent.border}`
        }}>
          <h3 style={{ color: accent.primary, margin: '0 0 10px 0', fontSize: '1rem' }}>
            🎯 Sample Protocol Card
          </h3>
          <p style={{ color: textSecondary, fontSize: '0.8rem', margin: '0 0 12px 0', lineHeight: 1.4 }}>
            This is how your content would look with this theme combination...
          </p>
          <div style={{ display: 'flex', gap: 8 }}>
            <span style={{
              background: accent.hover,
              color: accent.primary,
              padding: '4px 10px',
              borderRadius: 15,
              fontSize: '0.7rem'
            }}>
              Technology
            </span>
            <span style={{
              background: 'rgba(16, 185, 129, 0.2)',
              color: '#10b981',
              padding: '4px 10px',
              borderRadius: 15,
              fontSize: '0.7rem'
            }}>
              🆓 FREE
            </span>
          </div>
          <button style={{
            marginTop: 12,
            width: '100%',
            padding: '8px 15px',
            background: accent.gradient,
            border: 'none',
            borderRadius: 8,
            color: '#fff',
            fontWeight: 600,
            fontSize: '0.8rem',
            cursor: 'pointer'
          }}>
            ✨ Action Button
          </button>
        </div>

        {/* Apply Button */}
        <button
          onClick={(e) => { e.stopPropagation(); applyTheme(theme); }}
          style={{
            marginTop: 15,
            width: '100%',
            padding: '12px 20px',
            background: selectedSide === side ? accent.gradient : 'transparent',
            border: `2px solid ${accent.primary}`,
            borderRadius: 10,
            color: selectedSide === side ? '#fff' : accent.primary,
            fontWeight: 700,
            fontSize: '0.9rem',
            cursor: 'pointer',
            transition: 'all 0.3s'
          }}
          data-testid={`apply-${side}-theme`}
        >
          {selectedSide === side ? '✓ Apply This Theme' : 'Select to Apply'}
        </button>
      </div>
    );
  };

  // Theme selector dropdown
  const ThemeSelector = ({ theme, setTheme, label }) => (
    <div style={{ marginBottom: 15 }}>
      <label style={{ 
        color: isDarkMode ? '#a1a1aa' : '#64748b', 
        fontSize: '0.85rem', 
        display: 'block', 
        marginBottom: 8 
      }}>
        {label}
      </label>
      <div style={{ display: 'flex', gap: 10 }}>
        {/* Mode Toggle */}
        <button
          onClick={() => setTheme({ ...theme, isDark: !theme.isDark })}
          style={{
            padding: '8px 15px',
            background: theme.isDark 
              ? 'linear-gradient(135deg, #1e1b4b, #312e81)' 
              : 'linear-gradient(135deg, #fef3c7, #fde68a)',
            border: 'none',
            borderRadius: 8,
            color: theme.isDark ? '#fff' : '#92400e',
            fontWeight: 600,
            fontSize: '0.8rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6
          }}
        >
          {theme.isDark ? '🌙 Dark' : '☀️ Light'}
        </button>
        
        {/* Color Selector */}
        <div style={{ display: 'flex', gap: 5 }}>
          {Object.entries(ACCENT_COLORS).map(([key, color]) => (
            <button
              key={key}
              onClick={() => setTheme({ ...theme, accent: key })}
              style={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                background: color.gradient,
                border: theme.accent === key ? '3px solid white' : '2px solid transparent',
                cursor: 'pointer',
                boxShadow: theme.accent === key ? `0 0 10px ${color.primary}` : 'none',
                transition: 'all 0.2s'
              }}
              title={color.name}
            />
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.9)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10000,
      padding: 20
    }} data-testid="theme-preview-mode">
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        width: '100%',
        maxWidth: 1200,
        marginBottom: 20
      }}>
        <div>
          <h1 style={{ 
            color: '#fff', 
            margin: 0,
            fontSize: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: 10
          }}>
            👁️ Visual Theme Preview
          </h1>
          <p style={{ color: '#a1a1aa', margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Compare themes side-by-side and click to select
          </p>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'rgba(255,255,255,0.1)',
            border: 'none',
            color: '#fff',
            fontSize: '1.5rem',
            width: 40,
            height: 40,
            borderRadius: '50%',
            cursor: 'pointer'
          }}
        >
          ×
        </button>
      </div>

      {/* Theme Selectors */}
      <div style={{
        display: 'flex',
        gap: 40,
        width: '100%',
        maxWidth: 1200,
        marginBottom: 20
      }}>
        <div style={{ flex: 1 }}>
          <ThemeSelector theme={leftTheme} setTheme={setLeftTheme} label="Left Preview" />
        </div>
        <div style={{ flex: 1 }}>
          <ThemeSelector theme={rightTheme} setTheme={setRightTheme} label="Right Preview" />
        </div>
      </div>

      {/* Split Screen Preview */}
      <div style={{
        display: 'flex',
        gap: 20,
        width: '100%',
        maxWidth: 1200,
        height: 'calc(100vh - 280px)',
        minHeight: 400
      }}>
        <PreviewContent theme={leftTheme} side="left" />
        <PreviewContent theme={rightTheme} side="right" />
      </div>

      {/* Instructions */}
      <div style={{ 
        marginTop: 20, 
        color: '#71717a', 
        fontSize: '0.85rem',
        textAlign: 'center'
      }}>
        💡 Click a preview to select it, then click "Apply This Theme" to use it
      </div>
    </div>
  );
};

export default ThemePreviewMode;
