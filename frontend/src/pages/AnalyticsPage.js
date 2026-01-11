import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons } from '../components/shared';

const AnalyticsPage = ({ showToast }) => {
  const { token } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trendsDays, setTrendsDays] = useState(7);

  const fetchAnalytics = useCallback(async () => {
    try {
      const res = await fetch(`${API}/analytics/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to load analytics', 'error');
      }
    } catch (e) {
      showToast('Failed to load analytics', 'error');
    }
    setLoading(false);
  }, [token, showToast]);

  const fetchTrends = useCallback(async () => {
    try {
      const res = await fetch(`${API}/analytics/search-trends?days=${trendsDays}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTrends(data.trends || []);
      }
    } catch (e) {
      console.error('Failed to fetch trends');
    }
  }, [token, trendsDays]);

  useEffect(() => {
    fetchAnalytics();
    fetchTrends();
  }, [fetchAnalytics, fetchTrends]);

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 60 }}>
        <div className="spinner" style={{ margin: '0 auto' }}></div>
        <p style={{ color: '#a1a1aa', marginTop: 20 }}>Loading analytics...</p>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 60 }}>
        <p style={{ color: '#ef4444' }}>Failed to load analytics. Admin access required.</p>
      </div>
    );
  }

  const StatCard = ({ icon, value, label, color, trend }) => (
    <div style={{
      background: `linear-gradient(135deg, ${color}20, ${color}10)`,
      borderRadius: 16,
      padding: 20,
      border: `1px solid ${color}30`,
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '2rem', marginBottom: 8 }}>{icon}</div>
      <div style={{ fontSize: '2rem', fontWeight: 700, color: color }}>{(value || 0).toLocaleString()}</div>
      <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>{label}</div>
      {trend !== undefined && trend !== null && (
        <div style={{ 
          marginTop: 8, 
          fontSize: '0.8rem', 
          color: trend >= 0 ? '#10b981' : '#ef4444' 
        }}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)} this week
        </div>
      )}
    </div>
  );

  // Safe access helpers
  const users = analytics?.users || {};
  const searches = analytics?.searches || {};
  const protocols = analytics?.protocols || {};
  const marketplace = analytics?.marketplace || {};
  const engagement = analytics?.engagement || {};
  const popularTerms = analytics?.popular_search_terms || [];

  const maxSearches = Math.max(...(trends.length > 0 ? trends.map(t => t.searches || 0) : [1]), 1);

  return (
    <div className="card" data-testid="analytics-page">
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Chart />
          Analytics Dashboard
        </h2>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Platform insights and metrics • Generated {analytics?.generated_at ? new Date(analytics.generated_at).toLocaleString() : 'now'}
        </p>
      </div>

      {/* Key Metrics Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
        gap: 16, 
        marginBottom: 30 
      }}>
        <StatCard 
          icon="👥" 
          value={users.total} 
          label="Total Users" 
          color="#a78bfa"
          trend={users.new_this_week}
        />
        <StatCard 
          icon="🔍" 
          value={searches.total} 
          label="Total Searches" 
          color="#f472b6"
          trend={searches.this_week}
        />
        <StatCard 
          icon="📝" 
          value={protocols.total} 
          label="Protocols Created" 
          color="#10b981"
        />
        <StatCard 
          icon="🛒" 
          value={marketplace.active_listings} 
          label="Marketplace Listings" 
          color="#fbbf24"
        />
        <StatCard 
          icon="💰" 
          value={marketplace.total_purchases} 
          label="Protocol Purchases" 
          color="#3b82f6"
        />
        <StatCard 
          icon="🏘️" 
          value={engagement.total_groups} 
          label="Groups" 
          color="#ec4899"
        />
      </div>

      {/* Search Trends Chart */}
      <div style={{
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 16,
        padding: 20,
        marginBottom: 25
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h3 style={{ color: '#f472b6' }}>📊 Search Activity</h3>
          <div style={{ display: 'flex', gap: 10 }}>
            {[7, 14, 30].map(days => (
              <button
                key={days}
                className={`btn ${trendsDays === days ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setTrendsDays(days)}
                style={{ padding: '6px 12px', fontSize: '0.8rem' }}
              >
                {days}d
              </button>
            ))}
          </div>
        </div>

        {/* Simple Bar Chart */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'flex-end', 
          gap: 8, 
          height: 200,
          padding: '20px 0'
        }}>
          {trends.map((day, idx) => {
            const height = (day.searches / maxSearches) * 100;
            return (
              <div 
                key={day.date}
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8
                }}
              >
                <span style={{ color: '#fff', fontSize: '0.75rem', fontWeight: 600 }}>
                  {day.searches}
                </span>
                <div style={{
                  width: '100%',
                  maxWidth: 40,
                  height: `${Math.max(height, 5)}%`,
                  background: `linear-gradient(to top, #f472b6, #a78bfa)`,
                  borderRadius: '6px 6px 0 0',
                  minHeight: 10,
                  transition: 'height 0.3s ease'
                }} />
                <span style={{ 
                  color: '#6b7280', 
                  fontSize: '0.65rem',
                  transform: 'rotate(-45deg)',
                  whiteSpace: 'nowrap'
                }}>
                  {day.date.slice(5)}
                </span>
              </div>
            );
          })}
        </div>

        {trends.length === 0 && (
          <p style={{ color: '#a1a1aa', textAlign: 'center', padding: 30 }}>
            No search activity data for this period.
          </p>
        )}
      </div>

      {/* Popular Search Terms */}
      <div style={{
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 16,
        padding: 20,
        marginBottom: 25
      }}>
        <h3 style={{ color: '#f472b6', marginBottom: 15 }}>🔥 Popular Search Terms</h3>
        {popularTerms.length === 0 ? (
          <p style={{ color: '#a1a1aa' }}>No recent search data available.</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            {popularTerms.map((term, idx) => (
              <div
                key={term.term || idx}
                style={{
                  background: `rgba(244, 114, 182, ${0.3 - idx * 0.02})`,
                  border: '1px solid rgba(244, 114, 182, 0.3)',
                  borderRadius: 20,
                  padding: '8px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8
                }}
              >
                <span style={{ color: '#fff' }}>{term.term}</span>
                <span style={{ 
                  background: 'rgba(0,0,0,0.3)', 
                  padding: '2px 8px', 
                  borderRadius: 10,
                  fontSize: '0.75rem',
                  color: '#a1a1aa'
                }}>
                  {term.count}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Today's Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 20 }}>
        <div style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 16,
          padding: 20
        }}>
          <h4 style={{ color: '#10b981', marginBottom: 15 }}>📅 Today's Activity</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#a1a1aa' }}>New Users</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{users.new_today || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#a1a1aa' }}>Searches</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{searches.today || 0}</span>
            </div>
          </div>
        </div>

        <div style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 16,
          padding: 20
        }}>
          <h4 style={{ color: '#3b82f6', marginBottom: 15 }}>📈 Platform Health</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#a1a1aa' }}>Public Protocols</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{protocols.public || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#a1a1aa' }}>Total Posts</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{engagement.total_posts || 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#a1a1aa' }}>Total Pages</span>
              <span style={{ color: '#fff', fontWeight: 600 }}>{engagement.total_pages || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
