/**
 * Smart Search Suggestions Component
 * AI-powered search suggestions based on user patterns and trending topics
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

const SmartSearchSuggestions = ({ query, onSuggestionClick, showToast }) => {
  const { token } = useAuth();
  const { isDarkMode } = useTheme();
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isAiPowered, setIsAiPowered] = useState(false);
  const [visible, setVisible] = useState(true);
  
  const bgColor = isDarkMode ? 'rgba(30, 20, 50, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  
  const typeColors = {
    completion: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6', icon: '✨' },
    related: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', icon: '🔗' },
    trending: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', icon: '🔥' }
  };
  
  const fetchSuggestions = useCallback(async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API}/ai/smart-suggestions?query=${encodeURIComponent(query || '')}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions || []);
        setIsAiPowered(data.ai_powered || false);
      }
    } catch (e) {
      console.error('Failed to fetch smart suggestions:', e);
    }
    setLoading(false);
  }, [token, query]);
  
  useEffect(() => {
    // Debounce the fetch
    const timer = setTimeout(() => {
      fetchSuggestions();
    }, 500);
    
    return () => clearTimeout(timer);
  }, [fetchSuggestions]);
  
  const handleSuggestionClick = (suggestion) => {
    if (onSuggestionClick) {
      onSuggestionClick(suggestion.suggestion);
    }
    showToast && showToast(`Applied: ${suggestion.suggestion}`, 'success');
  };
  
  if (!visible || suggestions.length === 0) return null;
  
  return (
    <div 
      style={{
        background: bgColor,
        borderRadius: 12,
        padding: 15,
        marginBottom: 15,
        border: '1px solid rgba(124, 58, 237, 0.2)',
        position: 'relative'
      }}
      data-testid="smart-search-suggestions"
    >
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 12 
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.1rem' }}>💡</span>
          <span style={{ color: '#7c3aed', fontWeight: 600, fontSize: '0.9rem' }}>
            Smart Suggestions
          </span>
          {isAiPowered && (
            <span style={{
              background: 'linear-gradient(135deg, #10b981, #06b6d4)',
              padding: '2px 8px',
              borderRadius: 10,
              fontSize: '0.6rem',
              color: '#fff',
              fontWeight: 700
            }}>
              🧠 AI
            </span>
          )}
          {loading && (
            <span style={{ fontSize: '0.7rem', color: mutedColor }}>Loading...</span>
          )}
        </div>
        <button
          onClick={() => setVisible(false)}
          style={{
            background: 'transparent',
            border: 'none',
            color: mutedColor,
            cursor: 'pointer',
            fontSize: '0.8rem'
          }}
        >
          ✕
        </button>
      </div>
      
      {/* Suggestions */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {suggestions.map((suggestion, idx) => {
          const type = suggestion.type || 'related';
          const colors = typeColors[type] || typeColors.related;
          
          return (
            <button
              key={idx}
              onClick={() => handleSuggestionClick(suggestion)}
              style={{
                background: colors.bg,
                border: `1px solid ${colors.text}30`,
                borderRadius: 20,
                padding: '6px 14px',
                color: colors.text,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                transition: 'all 0.2s'
              }}
              title={suggestion.reason || 'Click to search'}
              data-testid={`suggestion-${idx}`}
            >
              <span>{colors.icon}</span>
              {suggestion.suggestion}
            </button>
          );
        })}
      </div>
      
      {/* Footer hint */}
      <p style={{ 
        margin: '10px 0 0 0', 
        fontSize: '0.7rem', 
        color: mutedColor,
        textAlign: 'center'
      }}>
        {isAiPowered 
          ? '🤖 Suggestions powered by GPT-5.2 based on your search patterns'
          : '📊 Popular searches and trending topics'}
      </p>
    </div>
  );
};

export default SmartSearchSuggestions;
