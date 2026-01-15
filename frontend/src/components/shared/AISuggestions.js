import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

/**
 * AI-Powered Protocol Suggestions Component
 * Non-intrusive component that displays personalized protocol recommendations
 */
const AISuggestions = ({ showToast, onViewProtocol, compact = false }) => {
  const { token } = useAuth();
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAIPowered, setIsAIPowered] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchSuggestions = useCallback(async (forceRefresh = false) => {
    if (!token) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const endpoint = forceRefresh 
        ? `${API}/ai/suggestions/refresh`
        : `${API}/ai/suggestions?limit=5`;
      
      const res = await fetch(endpoint, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions || []);
        setIsAIPowered(data.ai_powered || false);
      } else {
        setError('Could not load suggestions');
      }
    } catch (e) {
      console.error('Failed to fetch AI suggestions:', e);
      setError('Connection error');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [token]);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchSuggestions(true);
  };

  if (!token) return null;

  // Compact version for sidebar or small spaces
  if (compact) {
    return (
      <div 
        style={{
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
          borderRadius: 12,
          padding: 15,
          border: '1px solid rgba(139, 92, 246, 0.2)'
        }}
        data-testid="ai-suggestions-compact"
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
          <span style={{ fontSize: '1.2rem' }}>✨</span>
          <span style={{ color: '#a78bfa', fontWeight: 600, fontSize: '0.85rem' }}>
            {isAIPowered ? 'AI Picks' : 'Trending'}
          </span>
        </div>
        
        {loading ? (
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Loading...</div>
        ) : suggestions.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {suggestions.slice(0, 3).map((s, i) => (
              <div 
                key={s.protocol_id}
                onClick={() => onViewProtocol && onViewProtocol(s.protocol_id)}
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  padding: '8px 10px',
                  borderRadius: 8,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.target.style.background = 'rgba(139, 92, 246, 0.2)'}
                onMouseLeave={(e) => e.target.style.background = 'rgba(255,255,255,0.05)'}
                data-testid={`ai-suggestion-compact-${i}`}
              >
                <div style={{ color: '#fff', fontSize: '0.8rem', fontWeight: 500 }}>
                  {s.title.length > 25 ? s.title.substring(0, 25) + '...' : s.title}
                </div>
                <div style={{ color: '#10b981', fontSize: '0.75rem' }}>
                  ${s.price?.toFixed(2) || 'Free'}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>No suggestions yet</div>
        )}
      </div>
    );
  }

  // Full version
  return (
    <div 
      style={{
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%)',
        borderRadius: 16,
        padding: isExpanded ? 20 : 15,
        marginBottom: 20,
        border: '1px solid rgba(139, 92, 246, 0.3)',
        transition: 'all 0.3s ease'
      }}
      data-testid="ai-suggestions-panel"
    >
      {/* Header */}
      <div 
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          cursor: 'pointer'
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            background: 'linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%)',
            borderRadius: 10,
            padding: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <span style={{ fontSize: '1.3rem' }}>✨</span>
          </div>
          <div>
            <h3 style={{ 
              color: '#fff', 
              margin: 0, 
              fontSize: '1.1rem',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}>
              {isAIPowered ? 'AI-Powered Recommendations' : 'Recommended Protocols'}
              {isAIPowered && (
                <span style={{
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  padding: '3px 8px',
                  borderRadius: 12,
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  textTransform: 'uppercase'
                }}>
                  GPT-5.2
                </span>
              )}
            </h3>
            <p style={{ color: '#a1a1aa', margin: 0, fontSize: '0.8rem', marginTop: 2 }}>
              {isAIPowered 
                ? 'Personalized based on your search history' 
                : 'Popular protocols from the marketplace'}
            </p>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isExpanded && (
            <button
              onClick={(e) => { e.stopPropagation(); handleRefresh(); }}
              disabled={isRefreshing}
              style={{
                background: 'rgba(255,255,255,0.1)',
                border: 'none',
                borderRadius: 8,
                padding: '6px 12px',
                color: '#a1a1aa',
                cursor: isRefreshing ? 'wait' : 'pointer',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: 5
              }}
              data-testid="ai-refresh-btn"
            >
              <span style={{ 
                display: 'inline-block',
                animation: isRefreshing ? 'spin 1s linear infinite' : 'none'
              }}>🔄</span>
              Refresh
            </button>
          )}
          <span style={{ 
            color: '#a1a1aa', 
            fontSize: '1.2rem',
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.3s'
          }}>▼</span>
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div style={{ marginTop: 20 }}>
          {loading ? (
            <div style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              padding: 30,
              color: '#a1a1aa'
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: 10, animation: 'pulse 1.5s ease-in-out infinite' }}>
                  ✨
                </div>
                <p>Analyzing your interests...</p>
              </div>
            </div>
          ) : error ? (
            <div style={{ 
              textAlign: 'center', 
              padding: 20, 
              color: '#f87171',
              background: 'rgba(239, 68, 68, 0.1)',
              borderRadius: 10
            }}>
              <p>{error}</p>
              <button
                onClick={handleRefresh}
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#f87171',
                  padding: '8px 16px',
                  borderRadius: 8,
                  cursor: 'pointer',
                  marginTop: 10
                }}
              >
                Try Again
              </button>
            </div>
          ) : suggestions.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: 30, 
              color: '#a1a1aa' 
            }}>
              <p style={{ fontSize: '2rem', marginBottom: 10 }}>🔍</p>
              <p>Keep searching to get personalized recommendations!</p>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: 15
            }}>
              {suggestions.map((suggestion, index) => (
                <div
                  key={suggestion.protocol_id}
                  style={{
                    background: 'rgba(0,0,0,0.3)',
                    borderRadius: 12,
                    padding: 15,
                    border: '1px solid rgba(139, 92, 246, 0.2)',
                    transition: 'all 0.3s',
                    cursor: 'pointer'
                  }}
                  onClick={() => onViewProtocol && onViewProtocol(suggestion.protocol_id)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-3px)';
                    e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.2)';
                  }}
                  data-testid={`ai-suggestion-${index}`}
                >
                  {/* Match Score Badge */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'flex-start',
                    marginBottom: 10
                  }}>
                    <span style={{
                      background: suggestion.match_score >= 0.9 
                        ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                        : suggestion.match_score >= 0.7
                        ? 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)'
                        : 'rgba(255,255,255,0.1)',
                      padding: '4px 10px',
                      borderRadius: 20,
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      color: '#fff'
                    }}>
                      {Math.round(suggestion.match_score * 100)}% Match
                    </span>
                    <span style={{
                      color: '#10b981',
                      fontWeight: 700,
                      fontSize: '1.1rem'
                    }}>
                      {suggestion.price > 0 ? `$${suggestion.price.toFixed(2)}` : 'FREE'}
                    </span>
                  </div>

                  {/* Title */}
                  <h4 style={{ 
                    color: '#fff', 
                    margin: '0 0 8px 0',
                    fontSize: '1rem',
                    fontWeight: 600
                  }}>
                    {suggestion.title}
                  </h4>

                  {/* Description */}
                  <p style={{ 
                    color: '#a1a1aa', 
                    margin: '0 0 10px 0',
                    fontSize: '0.8rem',
                    lineHeight: 1.4,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}>
                    {suggestion.description || 'A powerful search protocol'}
                  </p>

                  {/* AI Reason */}
                  {isAIPowered && suggestion.reason && (
                    <div style={{
                      background: 'rgba(139, 92, 246, 0.1)',
                      borderRadius: 8,
                      padding: 8,
                      marginBottom: 10
                    }}>
                      <p style={{ 
                        color: '#a78bfa', 
                        margin: 0, 
                        fontSize: '0.75rem',
                        fontStyle: 'italic'
                      }}>
                        💡 {suggestion.reason}
                      </p>
                    </div>
                  )}

                  {/* Footer */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    borderTop: '1px solid rgba(255,255,255,0.1)',
                    paddingTop: 10,
                    marginTop: 'auto'
                  }}>
                    <span style={{ color: '#71717a', fontSize: '0.75rem' }}>
                      by {suggestion.creator}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewProtocol && onViewProtocol(suggestion.protocol_id);
                      }}
                      style={{
                        background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                        border: 'none',
                        borderRadius: 6,
                        padding: '6px 12px',
                        color: '#fff',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                      data-testid={`view-suggestion-${index}`}
                    >
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Animation Styles */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default AISuggestions;
