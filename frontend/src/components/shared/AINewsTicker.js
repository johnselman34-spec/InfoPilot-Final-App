/**
 * AI News Ticker Component
 * Displays top 10 AI-generated news headlines across different topics
 * Positioned in upper-right corner with bright, colorful fonts
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

// Color palette for different news topics
const TOPIC_COLORS = {
  technology: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6', border: 'rgba(59, 130, 246, 0.4)' },
  science: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', border: 'rgba(16, 185, 129, 0.4)' },
  business: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', border: 'rgba(245, 158, 11, 0.4)' },
  health: { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444', border: 'rgba(239, 68, 68, 0.4)' },
  politics: { bg: 'rgba(139, 92, 246, 0.15)', text: '#8b5cf6', border: 'rgba(139, 92, 246, 0.4)' },
  environment: { bg: 'rgba(34, 197, 94, 0.15)', text: '#22c55e', border: 'rgba(34, 197, 94, 0.4)' },
  space: { bg: 'rgba(99, 102, 241, 0.15)', text: '#6366f1', border: 'rgba(99, 102, 241, 0.4)' },
  finance: { bg: 'rgba(236, 72, 153, 0.15)', text: '#ec4899', border: 'rgba(236, 72, 153, 0.4)' },
  education: { bg: 'rgba(14, 165, 233, 0.15)', text: '#0ea5e9', border: 'rgba(14, 165, 233, 0.4)' },
  sports: { bg: 'rgba(249, 115, 22, 0.15)', text: '#f97316', border: 'rgba(249, 115, 22, 0.4)' },
  default: { bg: 'rgba(124, 58, 237, 0.15)', text: '#7c3aed', border: 'rgba(124, 58, 237, 0.4)' }
};

const AINewsTicker = ({ compact = false }) => {
  const { token } = useAuth();
  const { isDarkMode } = useTheme();
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAiPowered, setIsAiPowered] = useState(false);
  const [expanded, setExpanded] = useState(!compact);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const bgColor = isDarkMode ? 'rgba(15, 10, 35, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  
  const fetchNews = useCallback(async () => {
    try {
      const res = await fetch(`${API}/ai/news`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      
      if (res.ok) {
        const data = await res.json();
        setNews(data.articles || []);
        setIsAiPowered(data.ai_powered || false);
      }
    } catch (e) {
      console.error('Failed to fetch AI news:', e);
    }
    setLoading(false);
  }, [token]);
  
  useEffect(() => {
    // Initial fetch and refresh interval
    let mounted = true;
    const loadNews = async () => {
      if (mounted) await fetchNews();
    };
    loadNews();
    const interval = setInterval(loadNews, 30 * 60 * 1000);
    return () => { 
      mounted = false;
      clearInterval(interval); 
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // Auto-scroll through headlines when compact
  useEffect(() => {
    if (compact && news.length > 0) {
      const interval = setInterval(() => {
        setCurrentIndex(prev => (prev + 1) % news.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [compact, news.length]);
  
  const getTopicColor = (topic) => {
    const key = (topic || '').toLowerCase();
    return TOPIC_COLORS[key] || TOPIC_COLORS.default;
  };
  
  if (loading) {
    return (
      <div style={{
        position: compact ? 'relative' : 'fixed',
        top: compact ? 0 : 80,
        right: compact ? 0 : 20,
        width: compact ? '100%' : 320,
        padding: 15,
        background: bgColor,
        borderRadius: 16,
        border: '1px solid rgba(124, 58, 237, 0.3)',
        zIndex: 100,
        textAlign: 'center'
      }}>
        <div className="spinner" style={{ margin: '0 auto', width: 24, height: 24 }} />
        <p style={{ color: mutedColor, fontSize: '0.8rem', margin: '8px 0 0 0' }}>
          🤖 Loading AI News...
        </p>
      </div>
    );
  }
  
  // Compact ticker mode
  if (compact) {
    const currentNews = news[currentIndex];
    const colors = currentNews ? getTopicColor(currentNews.topic) : TOPIC_COLORS.default;
    
    return (
      <div 
        style={{
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(236, 72, 153, 0.1))',
          borderRadius: 12,
          padding: '10px 15px',
          border: '1px solid rgba(124, 58, 237, 0.2)',
          cursor: 'pointer'
        }}
        onClick={() => setExpanded(true)}
        data-testid="ai-news-ticker-compact"
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ 
            background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
            padding: '3px 8px',
            borderRadius: 20,
            fontSize: '0.65rem',
            color: '#fff',
            fontWeight: 700
          }}>
            🤖 AI NEWS
          </span>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <p style={{
              margin: 0,
              fontSize: '0.85rem',
              color: colors.text,
              fontWeight: 600,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              animation: 'fadeInSlide 0.5s ease'
            }}>
              {currentNews?.emoji} {currentNews?.headline || 'Loading...'}
            </p>
          </div>
          <span style={{ fontSize: '0.7rem', color: mutedColor }}>
            {currentIndex + 1}/{news.length}
          </span>
        </div>
      </div>
    );
  }
  
  // Full expanded mode
  return (
    <div 
      style={{
        position: 'fixed',
        top: 80,
        right: 20,
        width: 340,
        maxHeight: expanded ? '80vh' : 60,
        overflow: 'hidden',
        background: bgColor,
        borderRadius: 16,
        border: '2px solid rgba(124, 58, 237, 0.3)',
        boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
        zIndex: 100,
        transition: 'all 0.3s ease'
      }}
      data-testid="ai-news-ticker"
    >
      {/* Header */}
      <div 
        style={{
          background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
          padding: '12px 15px',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.2rem' }}>📰</span>
          <span style={{ color: '#fff', fontWeight: 700, fontSize: '0.95rem' }}>
            AI News Headlines
          </span>
          {isAiPowered && (
            <span style={{
              background: 'rgba(255,255,255,0.2)',
              padding: '2px 8px',
              borderRadius: 10,
              fontSize: '0.6rem',
              color: '#fff'
            }}>
              🧠 LIVE
            </span>
          )}
        </div>
        <span style={{ color: '#fff', fontSize: '0.8rem' }}>
          {expanded ? '▲' : '▼'}
        </span>
      </div>
      
      {/* News List */}
      {expanded && (
        <div style={{ 
          maxHeight: 'calc(80vh - 60px)', 
          overflowY: 'auto',
          padding: '10px'
        }}>
          {news.map((article, idx) => {
            const colors = getTopicColor(article.topic);
            return (
              <div
                key={idx}
                style={{
                  background: colors.bg,
                  borderRadius: 12,
                  padding: 12,
                  marginBottom: 10,
                  border: `1px solid ${colors.border}`,
                  transition: 'all 0.2s',
                  cursor: 'default'
                }}
                data-testid={`news-article-${idx}`}
              >
                {/* Topic Badge */}
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  marginBottom: 8 
                }}>
                  <span style={{
                    background: colors.text,
                    color: '#fff',
                    padding: '3px 10px',
                    borderRadius: 20,
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    textTransform: 'uppercase'
                  }}>
                    {article.emoji} {article.topic}
                  </span>
                  <span style={{ 
                    color: mutedColor, 
                    fontSize: '0.65rem' 
                  }}>
                    #{idx + 1}
                  </span>
                </div>
                
                {/* Headline */}
                <h4 style={{
                  color: colors.text,
                  margin: '0 0 6px 0',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  lineHeight: 1.3
                }}>
                  {article.headline}
                </h4>
                
                {/* Summary */}
                <p style={{
                  color: mutedColor,
                  margin: 0,
                  fontSize: '0.75rem',
                  lineHeight: 1.4
                }}>
                  {article.summary}
                </p>
              </div>
            );
          })}
          
          {/* Footer */}
          <div style={{
            textAlign: 'center',
            padding: '10px 0',
            borderTop: '1px solid rgba(124, 58, 237, 0.2)',
            marginTop: 10
          }}>
            <button
              onClick={fetchNews}
              style={{
                background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
                border: 'none',
                borderRadius: 20,
                padding: '8px 20px',
                color: '#fff',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.8rem'
              }}
              data-testid="refresh-news-btn"
            >
              🔄 Refresh Headlines
            </button>
            <p style={{ 
              color: mutedColor, 
              fontSize: '0.7rem', 
              margin: '8px 0 0 0' 
            }}>
              {isAiPowered ? '🤖 Powered by GPT-5.2' : '📚 Curated headlines'}
            </p>
          </div>
        </div>
      )}
      
      {/* CSS Animations */}
      <style>{`
        @keyframes fadeInSlide {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default AINewsTicker;
