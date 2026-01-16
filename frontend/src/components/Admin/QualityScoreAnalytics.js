/**
 * QualityScoreAnalytics - Admin component for viewing content quality score distribution
 * Shows distribution charts, top domains, improvement opportunities, and trends
 * Includes Domain Blocklist Management functionality
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

const QualityScoreAnalytics = ({ showToast }) => {
  const { token } = useAuth();
  const { isDarkMode } = useTheme();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [blockedDomains, setBlockedDomains] = useState([]);
  const [blockingDomain, setBlockingDomain] = useState(null);
  const [showBlockedList, setShowBlockedList] = useState(false);
  
  const bgColor = isDarkMode ? 'rgba(15, 10, 35, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const cardBg = isDarkMode ? 'rgba(30, 20, 50, 0.7)' : 'rgba(248, 250, 252, 0.9)';
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  
  const fetchAnalytics = useCallback(async () => {
    if (!token) return;
    
    try {
      const res = await fetch(`${API}/analytics/quality-scores`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      } else {
        showToast('Failed to load quality analytics', 'error');
      }
    } catch (e) {
      console.error('Failed to fetch quality analytics:', e);
      showToast('Failed to load quality analytics', 'error');
    }
    setLoading(false);
  }, [token, showToast]);
  
  useEffect(() => {
    const load = async () => {
      await fetchAnalytics();
    };
    load();
  }, [fetchAnalytics]);
  
  if (loading) {
    return (
      <div style={{ padding: 30, textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto' }} />
        <p style={{ color: mutedColor, marginTop: 15 }}>Loading quality score analytics...</p>
      </div>
    );
  }
  
  if (!analytics) {
    return (
      <div style={{ padding: 30, textAlign: 'center', color: mutedColor }}>
        <p>Unable to load analytics. Please try again.</p>
        <button className="btn btn-primary" onClick={fetchAnalytics} style={{ marginTop: 15 }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ background: bgColor, borderRadius: 16, padding: 25 }} data-testid="quality-score-analytics">
      {/* Header */}
      <div style={{ marginBottom: 25 }}>
        <h2 style={{ color: '#10b981', margin: 0, display: 'flex', alignItems: 'center', gap: 12 }}>
          📊 Content Quality Analytics
        </h2>
        <p style={{ color: mutedColor, margin: '8px 0 0 0', fontSize: '0.9rem' }}>
          Distribution and insights for content quality scores across {analytics.total_results.toLocaleString()} search results
        </p>
      </div>
      
      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15, marginBottom: 25 }}>
        <div style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05))', borderRadius: 12, padding: 20, border: '1px solid rgba(16, 185, 129, 0.3)', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#10b981' }}>
            {analytics.average_score}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.85rem' }}>Average Quality Score</div>
        </div>
        
        <div style={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.05))', borderRadius: 12, padding: 20, border: '1px solid rgba(59, 130, 246, 0.3)', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#3b82f6' }}>
            {analytics.insights?.high_quality_percentage || 0}%
          </div>
          <div style={{ color: mutedColor, fontSize: '0.85rem' }}>High Quality+ Content</div>
        </div>
        
        <div style={{ background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.05))', borderRadius: 12, padding: 20, border: '1px solid rgba(245, 158, 11, 0.3)', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#f59e0b' }}>
            {analytics.total_results.toLocaleString()}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.85rem' }}>Total Results</div>
        </div>
        
        <div style={{ background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05))', borderRadius: 12, padding: 20, border: '1px solid rgba(239, 68, 68, 0.3)', textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', fontWeight: 700, color: '#ef4444' }}>
            {analytics.insights?.needs_improvement_count?.toLocaleString() || 0}
          </div>
          <div style={{ color: mutedColor, fontSize: '0.85rem' }}>Needs Improvement</div>
        </div>
      </div>
      
      {/* Distribution Chart */}
      <div style={{ background: cardBg, borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <h3 style={{ color: textColor, margin: '0 0 20px 0', fontSize: '1.1rem' }}>
          📈 Quality Score Distribution
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {analytics.distribution?.map((range, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
              <div style={{ width: 140, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: '1.2rem' }}>{range.emoji}</span>
                <span style={{ color: range.color, fontWeight: 600, fontSize: '0.9rem' }}>{range.name}</span>
              </div>
              <div style={{ flex: 1, height: 28, background: 'rgba(0,0,0,0.2)', borderRadius: 14, overflow: 'hidden', position: 'relative' }}>
                <div 
                  style={{ 
                    width: `${range.percentage}%`, 
                    height: '100%', 
                    background: `linear-gradient(90deg, ${range.color}, ${range.color}90)`,
                    borderRadius: 14,
                    transition: 'width 0.5s ease'
                  }} 
                />
                <span style={{ 
                  position: 'absolute', 
                  right: 10, 
                  top: '50%', 
                  transform: 'translateY(-50%)',
                  color: textColor,
                  fontSize: '0.8rem',
                  fontWeight: 600
                }}>
                  {range.count.toLocaleString()} ({range.percentage}%)
                </span>
              </div>
              <div style={{ width: 80, textAlign: 'right', color: mutedColor, fontSize: '0.8rem' }}>
                {range.min_score}-{range.max_score}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Two Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20, marginBottom: 20 }}>
        {/* Top Quality Domains */}
        <div style={{ background: cardBg, borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#10b981', margin: '0 0 15px 0', fontSize: '1rem' }}>
            🏆 Top Quality Domains
          </h3>
          {analytics.top_quality_domains?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {analytics.top_quality_domains.map((domain, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ color: '#fbbf24', fontWeight: 700, width: 24 }}>#{idx + 1}</span>
                    <span style={{ color: textColor, fontSize: '0.9rem' }}>{domain.domain}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
                    <span style={{ color: '#10b981', fontWeight: 600 }}>{domain.avg_score}</span>
                    <span style={{ color: mutedColor, fontSize: '0.75rem' }}>({domain.count} results)</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: mutedColor, margin: 0, fontSize: '0.9rem' }}>No domain data available</p>
          )}
        </div>
        
        {/* Improvement Opportunities */}
        <div style={{ background: cardBg, borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#ef4444', margin: '0 0 15px 0', fontSize: '1rem' }}>
            ⚠️ Improvement Opportunities
          </h3>
          {analytics.improvement_opportunities?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {analytics.improvement_opportunities.map((domain, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ color: '#f97316', fontWeight: 700, width: 24 }}>#{idx + 1}</span>
                    <span style={{ color: textColor, fontSize: '0.9rem' }}>{domain.domain}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
                    <span style={{ color: '#ef4444', fontWeight: 600 }}>{domain.avg_score}</span>
                    <span style={{ color: mutedColor, fontSize: '0.75rem' }}>({domain.count} results)</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: mutedColor, margin: 0, fontSize: '0.9rem' }}>All content meets quality standards!</p>
          )}
        </div>
      </div>
      
      {/* Article Type Quality */}
      <div style={{ background: cardBg, borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <h3 style={{ color: textColor, margin: '0 0 15px 0', fontSize: '1rem' }}>
          📑 Quality by Article Type
        </h3>
        {analytics.article_type_quality?.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            {analytics.article_type_quality.map((type, idx) => (
              <div 
                key={idx} 
                style={{ 
                  background: type.avg_score >= 65 ? 'rgba(16, 185, 129, 0.15)' : type.avg_score >= 50 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  border: `1px solid ${type.avg_score >= 65 ? 'rgba(16, 185, 129, 0.3)' : type.avg_score >= 50 ? 'rgba(245, 158, 11, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                  borderRadius: 10,
                  padding: '10px 15px',
                  textAlign: 'center'
                }}
              >
                <div style={{ color: type.avg_score >= 65 ? '#10b981' : type.avg_score >= 50 ? '#f59e0b' : '#ef4444', fontWeight: 700, fontSize: '1.2rem' }}>
                  {type.avg_score}
                </div>
                <div style={{ color: textColor, fontSize: '0.8rem', fontWeight: 500 }}>{type.type}</div>
                <div style={{ color: mutedColor, fontSize: '0.7rem' }}>{type.count} results</div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: mutedColor, margin: 0, fontSize: '0.9rem' }}>No article type data available</p>
        )}
      </div>
      
      {/* Quality Trend */}
      {analytics.quality_trend?.length > 0 && (
        <div style={{ background: cardBg, borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: textColor, margin: '0 0 15px 0', fontSize: '1rem' }}>
            📅 Quality Trend (Last 7 Days)
          </h3>
          <div style={{ display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 10 }}>
            {analytics.quality_trend.map((day, idx) => (
              <div 
                key={idx} 
                style={{ 
                  flex: '1 0 auto',
                  minWidth: 80,
                  background: 'rgba(124, 58, 237, 0.1)',
                  border: '1px solid rgba(124, 58, 237, 0.3)',
                  borderRadius: 10,
                  padding: '12px 15px',
                  textAlign: 'center'
                }}
              >
                <div style={{ color: '#a78bfa', fontWeight: 700, fontSize: '1.3rem' }}>
                  {day.avg_score}
                </div>
                <div style={{ color: mutedColor, fontSize: '0.75rem', marginTop: 5 }}>
                  {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </div>
                <div style={{ color: mutedColor, fontSize: '0.7rem' }}>
                  {day.count} new
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Tips Section */}
      <div style={{
        marginTop: 20,
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(236, 72, 153, 0.1))',
        borderRadius: 12,
        padding: 20,
        border: '1px dashed rgba(124, 58, 237, 0.3)'
      }}>
        <h4 style={{ color: '#a78bfa', margin: '0 0 12px 0' }}>💡 Content Curation Tips</h4>
        <ul style={{ color: mutedColor, margin: 0, paddingLeft: 20, fontSize: '0.9rem', lineHeight: 1.8 }}>
          <li><strong>Premium Content (80+):</strong> Prioritize authoritative sources like .edu, .gov, and reputable news sites</li>
          <li><strong>Improve Low Scores:</strong> Review domains in the improvement list and consider filtering them out</li>
          <li><strong>Quality Keywords:</strong> Results with research, study, analysis score higher automatically</li>
          <li><strong>Content Length:</strong> Longer, more detailed articles receive higher quality scores</li>
        </ul>
      </div>
      
      <p style={{ color: mutedColor, fontSize: '0.75rem', marginTop: 15, textAlign: 'right' }}>
        Last updated: {new Date(analytics.last_updated).toLocaleString()}
      </p>
    </div>
  );
};

export default QualityScoreAnalytics;
