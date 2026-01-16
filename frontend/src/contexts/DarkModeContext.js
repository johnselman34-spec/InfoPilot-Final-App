/**
 * Dark Mode Context & Provider
 * Provides app-wide dark/light theme toggle functionality
 */
import React, { createContext, useContext, useState, useEffect } from 'react';

const DarkModeContext = createContext();

export const useDarkMode = () => {
  const context = useContext(DarkModeContext);
  if (!context) {
    throw new Error('useDarkMode must be used within a DarkModeProvider');
  }
  return context;
};

export const DarkModeProvider = ({ children }) => {
  // Initialize from localStorage or system preference
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) {
      return JSON.parse(saved);
    }
    // Default to dark mode (matches current app theme)
    return true;
  });

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    
    if (isDarkMode) {
      root.classList.add('dark-mode');
      root.classList.remove('light-mode');
      // Dark mode CSS variables
      root.style.setProperty('--bg-primary', '#0f0a1f');
      root.style.setProperty('--bg-secondary', '#1a1035');
      root.style.setProperty('--bg-card', 'rgba(30, 20, 50, 0.8)');
      root.style.setProperty('--bg-hover', 'rgba(124, 58, 237, 0.1)');
      root.style.setProperty('--text-primary', '#e5e7eb');
      root.style.setProperty('--text-secondary', '#a1a1aa');
      root.style.setProperty('--text-muted', '#71717a');
      root.style.setProperty('--border-color', 'rgba(124, 58, 237, 0.3)');
      root.style.setProperty('--accent-primary', '#7c3aed');
      root.style.setProperty('--accent-secondary', '#ec4899');
      root.style.setProperty('--success', '#10b981');
      root.style.setProperty('--warning', '#f59e0b');
      root.style.setProperty('--error', '#ef4444');
    } else {
      root.classList.remove('dark-mode');
      root.classList.add('light-mode');
      // Light mode CSS variables
      root.style.setProperty('--bg-primary', '#f8fafc');
      root.style.setProperty('--bg-secondary', '#ffffff');
      root.style.setProperty('--bg-card', 'rgba(255, 255, 255, 0.95)');
      root.style.setProperty('--bg-hover', 'rgba(124, 58, 237, 0.05)');
      root.style.setProperty('--text-primary', '#1e293b');
      root.style.setProperty('--text-secondary', '#475569');
      root.style.setProperty('--text-muted', '#94a3b8');
      root.style.setProperty('--border-color', 'rgba(124, 58, 237, 0.2)');
      root.style.setProperty('--accent-primary', '#7c3aed');
      root.style.setProperty('--accent-secondary', '#ec4899');
      root.style.setProperty('--success', '#10b981');
      root.style.setProperty('--warning', '#f59e0b');
      root.style.setProperty('--error', '#ef4444');
    }
    
    // Save preference
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(prev => !prev);
  };

  return (
    <DarkModeContext.Provider value={{ isDarkMode, toggleDarkMode, setIsDarkMode }}>
      {children}
    </DarkModeContext.Provider>
  );
};

// Dark Mode Toggle Button Component
export const DarkModeToggle = ({ compact = false }) => {
  const { isDarkMode, toggleDarkMode } = useDarkMode();
  
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
          transition: 'all 0.3s',
        }}
        title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        data-testid="dark-mode-toggle-compact"
      >
        {isDarkMode ? '☀️' : '🌙'}
      </button>
    );
  }
  
  return (
    <button
      onClick={toggleDarkMode}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 20px',
        background: isDarkMode 
          ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(251, 191, 36, 0.2))'
          : 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(139, 92, 246, 0.2))',
        border: `1px solid ${isDarkMode ? 'rgba(245, 158, 11, 0.3)' : 'rgba(124, 58, 237, 0.3)'}`,
        borderRadius: 10,
        cursor: 'pointer',
        transition: 'all 0.3s',
        color: isDarkMode ? '#fbbf24' : '#a78bfa',
        fontSize: '0.9rem',
        fontWeight: 600,
      }}
      data-testid="dark-mode-toggle"
    >
      <span style={{ fontSize: '1.3rem' }}>{isDarkMode ? '☀️' : '🌙'}</span>
      <span>{isDarkMode ? 'Light Mode' : 'Dark Mode'}</span>
    </button>
  );
};

export default DarkModeContext;
