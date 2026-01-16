/**
 * Performance Insights Component
 * Shows protocol creators their trending data and engagement metrics
 * Week-over-week changes and actionable insights
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

const PerformanceInsights = ({ showToast }) => {
  const { token } = useAuth();
  const { isDarkMode, currentAccent } = useTheme();
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const bgColor = isDarkMode ? 'rgba(15, 10, 35, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const cardBg = isDarkMode ? 'rgba(30, 20, 50, 0.7)' : 'rgba(248, 250, 252, 0.9)';
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  const accentColor = currentAccent?.primary || '#7c3aed';
  
  const fetchInsights = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    
    try {
      const res = await fetch(`${API}/marketplace/performance-insights`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setInsights(data);
      }
    } catch (e) {
      console.error('Failed to fetch insights:', e);
    }
    setLoading(false);
  }, [token]);
  
  useEffect(() => {
    const load = async () => {
      await fetchInsights();
    };
    load();
  }, [fetchInsights]);
  
  if (loading) {
    return (
      <div style={{ padding: 30, textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto' }} />
        <p style={{ color: mutedColor, marginTop: 15 }}>Loading your insights...</p>
      </div>
    );
  }
  
  if (!token) {
    return (
      <div style={{ 
        background: cardBg, 
        borderRadius: 16, 
        padding: 30, 
        textAlign: 'center',
        border: `1px solid ${accentColor}30`
      }}>
        <div style={{ fontSize: '3rem', marginBottom: 15 }}>🔐</div>
        <h3 style={{ color: textColor, marginBottom: 10 }}>Sign in to see your insights</h3>
        <p style={{ color: mutedColor }}>Track your protocol performance and discover growth opportunities!</p>
      </div>
    );
  }
  
  if (!insights?.has_protocols) {
    return (
      <div style={{ 
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1))',
        borderRadius: 16, 
        padding: 30, 
        textAlign: 'center',
        border: '1px solid rgba(16, 185, 129, 0.3)'
      }}>
        <div style={{ fontSize: '3rem', marginBottom: 15 }}>🚀</div>
        <h3 style={{ color: '#10b981', marginBottom: 10 }}>Ready to Start Earning?</h3>
        <p style={{ color: mutedColor, marginBottom: 20 }}>
          {insights?.message || 'List your first protocol to start tracking performance!'}
        </p>
        <div style={{
          background: cardBg,
          borderRadius: 12,
          padding: 20,
          textAlign: 'left'
        }}>
          <h4 style={{ color: textColor, marginBottom: 10 }}>💡 Quick Start Tips:</h4>
          <ul style={{ color: mutedColor, margin: 0, paddingLeft: 20, lineHeight: 1.8 }}>
            <li>Start with a FREE protocol to build reputation</li>
            <li>Use descriptive names that attract buyers</li>
            <li>Price competitively - $0.99 to $4.99 sells best</li>
            <li>Bundle related protocols for higher value</li>
          </ul>
        </div>
      </div>
    );
  }
  
  const getTrendColor = (trend) => {
    if (trend === 'up') return '#10b981';
    if (trend === 'down') return '#ef4444';
    return mutedColor;
  };
  
  const getTrendArrow = (trend) => {
    if (trend === 'up') return '↑';
    if (trend === 'down') return '↓';
    return '→';
  };

  return (
    <div style={{ background: bgColor, borderRadius: 20, padding: 25 }} data-testid="performance-insights">
      {/* Header */}
      <div style={{ marginBottom: 25 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <h2 style={{ 
            color: '#f472b6', 
            margin: 0,
            fontSize: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            📊 Performance Insights
          </h2>
          <span style={{
            background: insights.overall_trend === 'up' 
              ? 'rgba(16, 185, 129, 0.2)' 
              : insights.overall_trend === 'down' 
                ? 'rgba(239, 68, 68, 0.2)' 
                : 'rgba(156, 163, 175, 0.2)',
            color: getTrendColor(insights.overall_trend),
            padding: '6px 12px',
            borderRadius: 20,
            fontSize: '0.85rem',
            fontWeight: 600
          }}>
            {insights.overall_trend === 'up' ? '🚀 Trending Up!' : 
             insights.overall_trend === 'down' ? '📉 Needs Attention' : '➡️ Steady'}
          </span>
        </div>
        <p style={{ color: mutedColor, margin: 0, fontSize: '0.9rem' }}>
          Track your protocol performance and discover growth opportunities
        </p>
      </div>
      
      {/* Quick Stats */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
        gap: 15, 
        marginBottom: 25 
      }}>
        <div style={{ background: cardBg, borderRadius: 12, padding: 15, textAlign: 'center' }}>
          <div style={{ color: '#3b82f6', fontSize: '1.8rem', fontWeight: 700 }}>
            {insights.stats?.this_week?.views || 0}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.8rem' }}>Views This Week</div>
          {insights.stats?.changes?.views !== 0 && (
            <div style={{ 
              color: getTrendColor(insights.stats?.changes?.views > 0 ? 'up' : 'down'),
              fontSize: '0.75rem',
              marginTop: 5
            }}>
              {getTrendArrow(insights.stats?.changes?.views > 0 ? 'up' : 'down')} {Math.abs(insights.stats?.changes?.views || 0)}%
            </div>
          )}
        </div>
        
        <div style={{ background: cardBg, borderRadius: 12, padding: 15, textAlign: 'center' }}>
          <div style={{ color: '#10b981', fontSize: '1.8rem', fontWeight: 700 }}>
            {insights.stats?.this_week?.copies || 0}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.8rem' }}>Copies This Week</div>
          {insights.stats?.changes?.copies !== 0 && (
            <div style={{ 
              color: getTrendColor(insights.stats?.changes?.copies > 0 ? 'up' : 'down'),
              fontSize: '0.75rem',
              marginTop: 5
            }}>
              {getTrendArrow(insights.stats?.changes?.copies > 0 ? 'up' : 'down')} {Math.abs(insights.stats?.changes?.copies || 0)}%
            </div>
          )}
        </div>
        
        <div style={{ background: cardBg, borderRadius: 12, padding: 15, textAlign: 'center' }}>
          <div style={{ color: '#f59e0b', fontSize: '1.8rem', fontWeight: 700 }}>
            {insights.stats?.this_week?.purchases || 0}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.8rem' }}>Sales This Week</div>
        </div>
        
        <div style={{ background: cardBg, borderRadius: 12, padding: 15, textAlign: 'center' }}>
          <div style={{ color: '#ec4899', fontSize: '1.8rem', fontWeight: 700 }}>
            ${(insights.monthly_earnings || 0).toFixed(2)}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.8rem' }}>Monthly Earnings</div>
        </div>
      </div>
      
      {/* Insights Cards */}
      <div style={{ marginBottom: 25 }}>
        <h3 style={{ color: textColor, marginBottom: 15, fontSize: '1.1rem' }}>
          💡 Your Insights
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {insights.insights?.map((insight, idx) => (
            <div
              key={idx}
              style={{
                background: insight.trend === 'up' 
                  ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05))'
                  : insight.trend === 'down'
                    ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05))'
                    : cardBg,
                borderRadius: 12,
                padding: 15,
                border: `1px solid ${getTrendColor(insight.trend)}30`,
                display: 'flex',
                alignItems: 'center',
                gap: 15
              }}
              data-testid={`insight-${insight.type}`}
            >
              <div style={{ fontSize: '2rem' }}>{insight.icon}</div>
              <div style={{ flex: 1 }}>
                <p style={{ color: textColor, margin: 0, fontWeight: 500 }}>
                  {insight.message}
                </p>
              </div>
              {insight.change !== 0 && (
                <div style={{
                  background: getTrendColor(insight.trend) + '20',
                  color: getTrendColor(insight.trend),
                  padding: '6px 12px',
                  borderRadius: 20,
                  fontSize: '0.85rem',
                  fontWeight: 600
                }}>
                  {insight.change > 0 ? '+' : ''}{insight.change}%
                </div>
              )}
            </div>
          ))}
          
          {(!insights.insights || insights.insights.length === 0) && (
            <div style={{ 
              background: cardBg, 
              borderRadius: 12, 
              padding: 20, 
              textAlign: 'center' 
            }}>
              <p style={{ color: mutedColor, margin: 0 }}>
                Keep selling to unlock performance insights!
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Tips Section */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(236, 72, 153, 0.1))',
        borderRadius: 16,
        padding: 20,
        border: '1px dashed rgba(251, 191, 36, 0.3)'
      }}>
        <h4 style={{ color: '#f59e0b', margin: '0 0 12px 0' }}>🎯 Pro Tips to Boost Performance</h4>
        <ul style={{ color: mutedColor, margin: 0, paddingLeft: 20, fontSize: '0.9rem', lineHeight: 1.8 }}>
          <li><strong>Share on social:</strong> Twitter and LinkedIn drive 3x more sales</li>
          <li><strong>Bundle power:</strong> Bundles convert 40% better than singles</li>
          <li><strong>Update regularly:</strong> Fresh protocols rank higher in search</li>
          <li><strong>Engage community:</strong> Reply to comments for +25% repeat buyers</li>
        </ul>
      </div>
    </div>
  );
};

export default PerformanceInsights;
