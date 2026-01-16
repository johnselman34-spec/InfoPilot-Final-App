import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

const ProtocolAnalyticsDashboard = ({ showToast }) => {
  const { token, user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  const fetchAnalytics = useCallback(async () => {
    try {
      const res = await fetch(`${API}/protocol-analytics/my-protocols?days=${selectedPeriod}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
    } catch (e) {
      console.error('Failed to fetch analytics:', e);
    }
    setLoading(false);
  }, [token, selectedPeriod]);

  const fetchForecast = useCallback(async () => {
    try {
      const res = await fetch(`${API}/protocol-analytics/my-forecast?days=${selectedPeriod}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setForecast(data.forecast);
      }
    } catch (e) {
      console.error('Failed to fetch forecast:', e);
    }
  }, [token, selectedPeriod]);

  useEffect(() => {
    if (token) {
      fetchAnalytics();
      fetchForecast();
    }
  }, [token, fetchAnalytics, fetchForecast]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
        <div style={{ fontSize: '2rem', marginBottom: 15 }}>📊</div>
        Loading your protocol analytics...
      </div>
    );
  }

  if (!analytics || analytics.total_protocols === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <div style={{ fontSize: '4rem', marginBottom: 20 }}>📈</div>
        <h3 style={{ color: '#f472b6', marginBottom: 10 }}>No Protocols Yet</h3>
        <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
          Start selling protocols in the Marketplace to see your analytics here!
        </p>
      </div>
    );
  }

  return (
    <div data-testid="protocol-analytics-dashboard">
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 25,
        flexWrap: 'wrap',
        gap: 15
      }}>
        <div>
          <h2 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            📊 Protocol Analytics
            <span style={{
              background: 'linear-gradient(135deg, #10b981, #059669)',
              color: '#fff',
              padding: '4px 12px',
              borderRadius: 20,
              fontSize: '0.75rem',
              fontWeight: 700
            }}>
              {analytics.total_protocols} Protocols
            </span>
          </h2>
          <p style={{ color: '#a1a1aa', margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Track your protocol performance and optimize for more revenue! 💰
          </p>
        </div>
        
        <select
          value={selectedPeriod}
          onChange={(e) => setSelectedPeriod(Number(e.target.value))}
          className="input"
          style={{ width: 'auto', minWidth: 150 }}
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 15,
        marginBottom: 25
      }}>
        <div style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.05))',
          borderRadius: 16,
          padding: 20,
          textAlign: 'center',
          border: '1px solid rgba(16, 185, 129, 0.3)'
        }}>
          <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: 5 }}>Total Revenue</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#10b981' }}>
            ${analytics.summary.total_revenue.toFixed(2)}
          </div>
        </div>
        
        <div style={{
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(124, 58, 237, 0.05))',
          borderRadius: 16,
          padding: 20,
          textAlign: 'center',
          border: '1px solid rgba(124, 58, 237, 0.3)'
        }}>
          <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: 5 }}>Total Views</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#a78bfa' }}>
            {analytics.summary.total_views.toLocaleString()}
          </div>
        </div>
        
        <div style={{
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.05))',
          borderRadius: 16,
          padding: 20,
          textAlign: 'center',
          border: '1px solid rgba(59, 130, 246, 0.3)'
        }}>
          <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: 5 }}>Total Copies</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#3b82f6' }}>
            {analytics.summary.total_copies.toLocaleString()}
          </div>
        </div>
        
        <div style={{
          background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.05))',
          borderRadius: 16,
          padding: 20,
          textAlign: 'center',
          border: '1px solid rgba(251, 191, 36, 0.3)'
        }}>
          <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: 5 }}>Avg Conversion</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#fbbf24' }}>
            {analytics.summary.avg_conversion_rate}%
          </div>
        </div>
        
        <div style={{
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(236, 72, 153, 0.05))',
          borderRadius: 16,
          padding: 20,
          textAlign: 'center',
          border: '1px solid rgba(236, 72, 153, 0.3)'
        }}>
          <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: 5 }}>Avg Rating</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: '#f472b6' }}>
            {'★'.repeat(Math.round(analytics.summary.avg_rating))}
          </div>
        </div>
      </div>

      {/* Forecast Section */}
      {forecast && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1))',
          borderRadius: 16,
          padding: 20,
          marginBottom: 25,
          border: '1px solid rgba(16, 185, 129, 0.2)'
        }}>
          <h3 style={{ color: '#10b981', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 10 }}>
            🔮 Revenue Forecast
            <span style={{ fontSize: '0.75rem', color: '#a1a1aa', fontWeight: 400 }}>Based on {selectedPeriod}-day trends</span>
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15 }}>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Next Week Projection</div>
              <div style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700 }}>${forecast.next_week_revenue}</div>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Next Month Projection</div>
              <div style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700 }}>${forecast.next_month_revenue}</div>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Daily Avg Copies</div>
              <div style={{ color: '#3b82f6', fontSize: '1.5rem', fontWeight: 700 }}>{forecast.daily_average_copies}</div>
            </div>
          </div>

          {forecast.top_performer && (
            <div style={{ marginTop: 15, padding: 15, background: 'rgba(251, 191, 36, 0.1)', borderRadius: 12, border: '1px solid rgba(251, 191, 36, 0.3)' }}>
              <div style={{ color: '#fbbf24', fontWeight: 600, marginBottom: 5 }}>🏆 Top Performer</div>
              <div style={{ color: '#fff' }}>{forecast.top_performer.name}</div>
              <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                ${forecast.top_performer.revenue} revenue • {forecast.top_performer.conversion_rate}% conversion
              </div>
            </div>
          )}

          {forecast.growth_potential?.length > 0 && (
            <div style={{ marginTop: 15 }}>
              <div style={{ color: '#f472b6', fontWeight: 600, marginBottom: 10 }}>💡 Growth Opportunities</div>
              {forecast.growth_potential.map((p, i) => (
                <div key={i} style={{ padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8, marginBottom: 8 }}>
                  <div style={{ color: '#fff', fontWeight: 500 }}>{p.name}</div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{p.potential_increase}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Individual Protocol Analytics */}
      <h3 style={{ color: '#f472b6', marginBottom: 15 }}>📋 Protocol Performance</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        {analytics.analytics.map((protocol, index) => (
          <div
            key={protocol.id}
            style={{
              background: 'rgba(30, 20, 50, 0.5)',
              borderRadius: 16,
              padding: 20,
              border: index === 0 ? '2px solid rgba(251, 191, 36, 0.5)' : '1px solid rgba(124, 58, 237, 0.2)',
              position: 'relative'
            }}
          >
            {index === 0 && (
              <span style={{
                position: 'absolute',
                top: -10,
                right: 15,
                background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
                color: '#fff',
                padding: '4px 12px',
                borderRadius: 15,
                fontSize: '0.7rem',
                fontWeight: 700
              }}>
                🏆 TOP PERFORMER
              </span>
            )}
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 15 }}>
              <div>
                <h4 style={{ color: '#fff', margin: 0, marginBottom: 5 }}>{protocol.name}</h4>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <span style={{ background: 'rgba(124, 58, 237, 0.2)', color: '#a78bfa', padding: '2px 10px', borderRadius: 15, fontSize: '0.75rem' }}>
                    {protocol.category}
                  </span>
                  <span style={{
                    background: protocol.is_free ? 'rgba(16, 185, 129, 0.2)' : 'rgba(251, 191, 36, 0.2)',
                    color: protocol.is_free ? '#10b981' : '#fbbf24',
                    padding: '2px 10px',
                    borderRadius: 15,
                    fontSize: '0.75rem'
                  }}>
                    {protocol.is_free ? '🆓 FREE' : `$${protocol.price.toFixed(2)}`}
                  </span>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700 }}>${protocol.revenue.toFixed(2)}</div>
                <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>revenue</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10 }}>
              <div style={{ textAlign: 'center', padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ color: '#a78bfa', fontSize: '1.2rem', fontWeight: 600 }}>{protocol.views}</div>
                <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Views</div>
              </div>
              <div style={{ textAlign: 'center', padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ color: '#3b82f6', fontSize: '1.2rem', fontWeight: 600 }}>{protocol.copies}</div>
                <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Copies</div>
              </div>
              <div style={{ textAlign: 'center', padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ color: '#10b981', fontSize: '1.2rem', fontWeight: 600 }}>{protocol.sales}</div>
                <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Sales</div>
              </div>
              <div style={{ textAlign: 'center', padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ color: '#fbbf24', fontSize: '1.2rem', fontWeight: 600 }}>{protocol.conversion_rate}%</div>
                <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Conversion</div>
              </div>
              <div style={{ textAlign: 'center', padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8 }}>
                <div style={{ color: '#f472b6', fontSize: '1.2rem', fontWeight: 600 }}>{'★'.repeat(Math.round(protocol.rating))}</div>
                <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Rating ({protocol.review_count})</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProtocolAnalyticsDashboard;
