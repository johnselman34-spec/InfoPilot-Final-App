import React, { useState, useEffect, useCallback } from 'react';
import { API } from '../../utils/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

/**
 * CategoryAnalyticsDashboard - Admin dashboard for category analytics
 * Shows category performance, trends, and template popularity
 */
const CategoryAnalyticsDashboard = ({ token, showToast }) => {
  const [analytics, setAnalytics] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDays, setSelectedDays] = useState(30);

  const COLORS = ['#f472b6', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899'];

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const [analyticsRes, trendsRes] = await Promise.all([
        fetch(`${API}/admin/category-analytics?days=${selectedDays}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API}/admin/category-analytics/trends?days=${selectedDays}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (analyticsRes.ok) {
        const data = await analyticsRes.json();
        setAnalytics(data);
      }

      if (trendsRes.ok) {
        const data = await trendsRes.json();
        setTrends(data);
      }
    } catch (e) {
      console.error('Failed to fetch category analytics:', e);
    }
    setLoading(false);
  }, [token, selectedDays]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <div style={{ fontSize: '2rem', marginBottom: 15 }}>📊</div>
        Loading category analytics...
      </div>
    );
  }

  const levelData = analytics?.summary?.categories_by_level ? [
    { name: 'Root (L0)', value: analytics.summary.categories_by_level.level_0, color: '#f472b6' },
    { name: 'Sub (L1)', value: analytics.summary.categories_by_level.level_1, color: '#8b5cf6' },
    { name: 'Sub-Sub (L2)', value: analytics.summary.categories_by_level.level_2, color: '#3b82f6' },
    { name: 'Deep (L3+)', value: analytics.summary.categories_by_level.level_3_plus, color: '#10b981' }
  ].filter(d => d.value > 0) : [];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ color: '#f472b6', margin: 0 }}>📊 Category Analytics Dashboard</h3>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select
            value={selectedDays}
            onChange={(e) => setSelectedDays(parseInt(e.target.value))}
            style={{
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid rgba(124, 58, 237, 0.3)',
              background: 'rgba(30, 20, 50, 0.5)',
              color: '#fff'
            }}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button
            onClick={fetchAnalytics}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              border: '1px solid rgba(124, 58, 237, 0.3)',
              background: 'rgba(124, 58, 237, 0.2)',
              color: '#a78bfa',
              cursor: 'pointer'
            }}
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
        {[
          { label: 'Total Categories', value: analytics?.summary?.total_categories || 0, icon: '📁', color: '#f472b6' },
          { label: 'Total Results', value: analytics?.summary?.total_results?.toLocaleString() || 0, icon: '📄', color: '#3b82f6' },
          { label: 'With Location', value: analytics?.summary?.results_with_location?.toLocaleString() || 0, icon: '📍', color: '#10b981' },
          { label: 'Avg Results/Cat', value: analytics?.summary?.avg_results_per_category || 0, icon: '📈', color: '#f59e0b' },
          { label: 'Public Categories', value: analytics?.summary?.public_categories || 0, icon: '🌐', color: '#8b5cf6' },
          { label: 'Paid Categories', value: analytics?.summary?.paid_categories || 0, icon: '💰', color: '#ef4444' }
        ].map((stat, i) => (
          <div key={i} style={{
            padding: 15,
            background: `linear-gradient(135deg, ${stat.color}15, ${stat.color}05)`,
            borderRadius: 12,
            border: `1px solid ${stat.color}40`,
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '1.5rem', marginBottom: 5 }}>{stat.icon}</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: stat.color }}>{stat.value}</div>
            <div style={{ fontSize: '0.75rem', color: '#a1a1aa' }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 25 }}>
        {/* Top Categories Bar Chart */}
        <div style={{
          padding: 20,
          background: 'rgba(30, 20, 50, 0.4)',
          borderRadius: 12,
          border: '1px solid rgba(124, 58, 237, 0.2)'
        }}>
          <h4 style={{ color: '#a78bfa', margin: '0 0 15px 0' }}>🏆 Top Categories by Results</h4>
          {analytics?.top_categories?.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={analytics.top_categories.slice(0, 8)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis type="number" stroke="#a1a1aa" />
                <YAxis dataKey="name" type="category" width={100} stroke="#a1a1aa" tick={{ fontSize: 11 }} />
                <Tooltip 
                  contentStyle={{ background: 'rgba(30, 20, 50, 0.95)', border: '1px solid #7c3aed', borderRadius: 8 }}
                  labelStyle={{ color: '#f472b6' }}
                />
                <Bar dataKey="result_count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>No data yet</div>
          )}
        </div>

        {/* Category Levels Pie Chart */}
        <div style={{
          padding: 20,
          background: 'rgba(30, 20, 50, 0.4)',
          borderRadius: 12,
          border: '1px solid rgba(124, 58, 237, 0.2)'
        }}>
          <h4 style={{ color: '#a78bfa', margin: '0 0 15px 0' }}>🎯 Category Depth Distribution</h4>
          {levelData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={levelData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {levelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ background: 'rgba(30, 20, 50, 0.95)', border: '1px solid #7c3aed', borderRadius: 8 }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>No data yet</div>
          )}
        </div>
      </div>

      {/* Top Categories Table */}
      <div style={{
        padding: 20,
        background: 'rgba(30, 20, 50, 0.4)',
        borderRadius: 12,
        border: '1px solid rgba(124, 58, 237, 0.2)',
        marginBottom: 25
      }}>
        <h4 style={{ color: '#a78bfa', margin: '0 0 15px 0' }}>📋 Category Performance Details</h4>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <th style={{ padding: '10px 15px', textAlign: 'left', color: '#f472b6' }}>Category</th>
                <th style={{ padding: '10px 15px', textAlign: 'center', color: '#f472b6' }}>Level</th>
                <th style={{ padding: '10px 15px', textAlign: 'center', color: '#f472b6' }}>Results</th>
                <th style={{ padding: '10px 15px', textAlign: 'center', color: '#f472b6' }}>With Location</th>
                <th style={{ padding: '10px 15px', textAlign: 'center', color: '#f472b6' }}>Location %</th>
                <th style={{ padding: '10px 15px', textAlign: 'center', color: '#f472b6' }}>Sub-cats</th>
                <th style={{ padding: '10px 15px', textAlign: 'center', color: '#f472b6' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {analytics?.top_categories?.slice(0, 15).map((cat, i) => (
                <tr key={cat.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '10px 15px', color: '#e2e8f0' }}>
                    {cat.name}
                    {cat.price > 0 && <span style={{ marginLeft: 8, fontSize: '0.7rem', color: '#f59e0b' }}>${cat.price}</span>}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'center', color: '#a1a1aa' }}>
                    L{cat.level}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'center', color: '#3b82f6', fontWeight: 600 }}>
                    {cat.result_count.toLocaleString()}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'center', color: '#10b981' }}>
                    {cat.results_with_location.toLocaleString()}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'center' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: 4,
                      background: cat.location_rate > 50 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                      color: cat.location_rate > 50 ? '#10b981' : '#f59e0b',
                      fontSize: '0.8rem'
                    }}>
                      {cat.location_rate}%
                    </span>
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'center', color: '#a78bfa' }}>
                    {cat.child_count}
                  </td>
                  <td style={{ padding: '10px 15px', textAlign: 'center' }}>
                    {cat.is_public ? (
                      <span style={{ color: '#10b981', fontSize: '0.75rem' }}>🌐 Public</span>
                    ) : (
                      <span style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>🔒 Private</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Empty Categories Warning */}
      {analytics?.empty_categories?.length > 0 && (
        <div style={{
          padding: 20,
          background: 'rgba(245, 158, 11, 0.1)',
          borderRadius: 12,
          border: '1px solid rgba(245, 158, 11, 0.3)',
          marginBottom: 25
        }}>
          <h4 style={{ color: '#f59e0b', margin: '0 0 10px 0' }}>⚠️ Empty Categories ({analytics.empty_categories.length})</h4>
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '0 0 10px 0' }}>
            These categories have no results. Consider adding search results or removing unused categories.
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {analytics.empty_categories.map(cat => (
              <span
                key={cat.id}
                style={{
                  padding: '4px 10px',
                  background: 'rgba(245, 158, 11, 0.2)',
                  borderRadius: 6,
                  color: '#fbbf24',
                  fontSize: '0.8rem'
                }}
              >
                {cat.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Template Popularity */}
      {analytics?.template_popularity?.length > 0 && (
        <div style={{
          padding: 20,
          background: 'rgba(16, 185, 129, 0.1)',
          borderRadius: 12,
          border: '1px solid rgba(16, 185, 129, 0.3)'
        }}>
          <h4 style={{ color: '#10b981', margin: '0 0 15px 0' }}>🛒 Template Popularity in Marketplace</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
            {analytics.template_popularity.map((t, i) => (
              <div key={i} style={{
                padding: 12,
                background: 'rgba(16, 185, 129, 0.1)',
                borderRadius: 8,
                border: '1px solid rgba(16, 185, 129, 0.2)'
              }}>
                <div style={{ fontWeight: 600, color: '#10b981' }}>{t._id || 'Uncategorized'}</div>
                <div style={{ fontSize: '0.85rem', color: '#a1a1aa' }}>
                  {t.count} bundles • {t.total_sales} sales
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generated At */}
      <div style={{ textAlign: 'center', marginTop: 20 }}>
        <span style={{ color: '#71717a', fontSize: '0.75rem' }}>
          Generated: {analytics?.generated_at ? new Date(analytics.generated_at).toLocaleString() : 'N/A'}
        </span>
      </div>
    </div>
  );
};

export default CategoryAnalyticsDashboard;
