import React, { useState, useEffect, useCallback } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

const ContentQualityReport = ({ showToast }) => {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const token = localStorage.getItem('token');

  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/admin/content-quality-report?days=${days}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setReportData(data);
      } else {
        showToast('Failed to load content quality report', 'error');
      }
    } catch (e) {
      console.error('Error fetching report:', e);
      showToast('Error loading report', 'error');
    }
    setLoading(false);
  }, [token, days, showToast]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <div className="loading-spinner"><div className="spinner"></div></div>
        <p style={{ color: '#a1a1aa', marginTop: 15 }}>Loading content quality report...</p>
      </div>
    );
  }

  if (!reportData) {
    return (
      <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
        <p style={{ color: '#a1a1aa' }}>No report data available</p>
        <button className="btn btn-primary" onClick={fetchReport} style={{ marginTop: 15 }}>
          Retry
        </button>
      </div>
    );
  }

  const { total_violations, unique_violators, banned_words_count, violations_by_type, 
          top_offending_words, quality_distribution, violation_trend, recent_violations } = reportData;

  // Calculate quality scores for visualization
  const totalQuality = Object.values(quality_distribution).reduce((a, b) => a + b, 0);
  const qualityColors = {
    poor: '#ef4444',
    fair: '#f59e0b',
    good: '#3b82f6',
    high: '#10b981',
    premium: '#a855f7'
  };

  return (
    <div data-testid="content-quality-report">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          📊 Content Quality Report
          <span style={{ 
            fontSize: '0.75rem', 
            background: 'rgba(244, 114, 182, 0.2)', 
            padding: '4px 12px', 
            borderRadius: 20 
          }}>
            Last {days} days
          </span>
        </h3>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            style={{
              background: 'rgba(124, 58, 237, 0.2)',
              border: '1px solid rgba(124, 58, 237, 0.3)',
              color: '#a78bfa',
              padding: '8px 12px',
              borderRadius: 8
            }}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button 
            onClick={fetchReport}
            className="btn btn-secondary"
            style={{ padding: '8px 16px' }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
        gap: 15, 
        marginBottom: 25 
      }}>
        <div style={{
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.1))',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(239, 68, 68, 0.3)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#ef4444' }}>
            {total_violations}
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Total Violations</div>
        </div>
        
        <div style={{
          background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.1))',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(251, 191, 36, 0.3)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#fbbf24' }}>
            {unique_violators}
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Unique Violators</div>
        </div>
        
        <div style={{
          background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(168, 85, 247, 0.1))',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(168, 85, 247, 0.3)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#a855f7' }}>
            {banned_words_count}
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Banned Words</div>
        </div>
        
        <div style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(16, 185, 129, 0.3)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#10b981' }}>
            {totalQuality > 0 ? Math.round((quality_distribution.high + quality_distribution.premium) / totalQuality * 100) : 0}%
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>High Quality Content</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 25 }}>
        {/* Violations by Type */}
        <div style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(124, 58, 237, 0.2)'
        }}>
          <h4 style={{ color: '#f472b6', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
            🛡️ Violations by Content Type
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {Object.entries(violations_by_type).map(([type, count]) => (
              <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 100, color: '#a1a1aa', textTransform: 'capitalize' }}>{type}</div>
                <div style={{ flex: 1, background: 'rgba(0,0,0,0.3)', borderRadius: 4, height: 20, overflow: 'hidden' }}>
                  <div 
                    style={{
                      width: `${total_violations > 0 ? (count / total_violations) * 100 : 0}%`,
                      height: '100%',
                      background: type === 'category' ? '#f472b6' : type === 'protocol' ? '#8b5cf6' : type === 'marketplace' ? '#3b82f6' : '#71717a',
                      borderRadius: 4,
                      transition: 'width 0.5s ease'
                    }}
                  />
                </div>
                <div style={{ width: 50, textAlign: 'right', color: '#fff', fontWeight: 600 }}>{count}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Quality Distribution */}
        <div style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(124, 58, 237, 0.2)'
        }}>
          <h4 style={{ color: '#10b981', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
            📊 Content Quality Distribution
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {Object.entries(quality_distribution).map(([level, count]) => (
              <div key={level} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 80, color: qualityColors[level], textTransform: 'capitalize', fontWeight: 500 }}>{level}</div>
                <div style={{ flex: 1, background: 'rgba(0,0,0,0.3)', borderRadius: 4, height: 20, overflow: 'hidden' }}>
                  <div 
                    style={{
                      width: `${totalQuality > 0 ? (count / totalQuality) * 100 : 0}%`,
                      height: '100%',
                      background: qualityColors[level],
                      borderRadius: 4,
                      transition: 'width 0.5s ease'
                    }}
                  />
                </div>
                <div style={{ width: 60, textAlign: 'right', color: '#fff', fontWeight: 600 }}>{count}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Offending Words */}
      {top_offending_words && top_offending_words.length > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05))',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(239, 68, 68, 0.3)',
          marginBottom: 25
        }}>
          <h4 style={{ color: '#ef4444', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
            ⚠️ Most Frequently Violated Words
          </h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            {top_offending_words.map((item, idx) => (
              <div 
                key={idx}
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 20,
                  padding: '8px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8
                }}
              >
                <span style={{ color: '#fca5a5' }}>{item.word}</span>
                <span style={{
                  background: 'rgba(239, 68, 68, 0.3)',
                  padding: '2px 8px',
                  borderRadius: 10,
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: '#ef4444'
                }}>
                  {item.count}x
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Violation Trend */}
      {violation_trend && violation_trend.length > 0 && (
        <div style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(124, 58, 237, 0.2)',
          marginBottom: 25
        }}>
          <h4 style={{ color: '#a78bfa', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
            📈 Violation Trend (Last 7 Days)
          </h4>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 100 }}>
            {violation_trend.reverse().map((item, idx) => {
              const maxViolations = Math.max(...violation_trend.map(t => t.violations), 1);
              const height = (item.violations / maxViolations) * 80;
              return (
                <div 
                  key={idx}
                  style={{ 
                    flex: 1, 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center',
                    gap: 5
                  }}
                >
                  <span style={{ fontSize: '0.7rem', color: '#a78bfa', fontWeight: 600 }}>
                    {item.violations}
                  </span>
                  <div 
                    style={{
                      width: '100%',
                      height: Math.max(height, 4),
                      background: item.violations > 0 
                        ? 'linear-gradient(180deg, #a78bfa, #7c3aed)' 
                        : 'rgba(124, 58, 237, 0.2)',
                      borderRadius: '4px 4px 0 0',
                      transition: 'height 0.3s ease'
                    }}
                  />
                  <span style={{ fontSize: '0.65rem', color: '#71717a' }}>
                    {item.date.slice(5)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Violations */}
      {recent_violations && recent_violations.length > 0 && (
        <div style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(124, 58, 237, 0.2)'
        }}>
          <h4 style={{ color: '#f472b6', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
            🕐 Recent Violations
          </h4>
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {recent_violations.map((violation, idx) => (
              <div 
                key={violation.id || idx}
                style={{
                  padding: 12,
                  background: 'rgba(0,0,0,0.2)',
                  borderRadius: 8,
                  marginBottom: 8,
                  borderLeft: `3px solid ${violation.content_type === 'category' ? '#f472b6' : violation.content_type === 'protocol' ? '#8b5cf6' : '#3b82f6'}`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <span style={{
                      background: 'rgba(239, 68, 68, 0.2)',
                      color: '#ef4444',
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: '0.75rem',
                      fontWeight: 600
                    }}>
                      {violation.word}
                    </span>
                    <span style={{
                      background: 'rgba(124, 58, 237, 0.2)',
                      color: '#a78bfa',
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: '0.7rem',
                      textTransform: 'capitalize'
                    }}>
                      {violation.content_type}
                    </span>
                  </div>
                  <span style={{ color: '#71717a', fontSize: '0.7rem' }}>
                    {new Date(violation.created_at).toLocaleString()}
                  </span>
                </div>
                <p style={{ 
                  color: '#a1a1aa', 
                  fontSize: '0.8rem', 
                  margin: 0,
                  fontFamily: 'monospace',
                  background: 'rgba(0,0,0,0.2)',
                  padding: '6px 10px',
                  borderRadius: 4
                }}>
                  {violation.attempted_text}...
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {total_violations === 0 && (
        <div style={{ 
          textAlign: 'center', 
          padding: 40, 
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05))',
          borderRadius: 12,
          border: '1px solid rgba(16, 185, 129, 0.3)'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: 15 }}>✨</div>
          <h3 style={{ color: '#10b981', marginBottom: 10 }}>No Violations Detected!</h3>
          <p style={{ color: '#a1a1aa' }}>
            Your community is maintaining high content quality standards. Keep it up!
          </p>
        </div>
      )}
    </div>
  );
};

export default ContentQualityReport;
