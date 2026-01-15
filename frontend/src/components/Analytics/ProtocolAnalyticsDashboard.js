import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

/**
 * Protocol Analytics Dashboard
 * Shows creators their protocol performance metrics
 */
const ProtocolAnalyticsDashboard = ({ showToast }) => {
  const { token } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(30);
  const [selectedProtocol, setSelectedProtocol] = useState(null);
  const [protocolDetails, setProtocolDetails] = useState(null);

  const fetchDashboard = useCallback(async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API}/analytics/creator/dashboard?days=${selectedPeriod}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setDashboardData(data);
      }
    } catch (e) {
      console.error('Failed to fetch analytics:', e);
    }
    setLoading(false);
  }, [token, selectedPeriod]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const fetchProtocolDetails = async (protocolId) => {
    try {
      const res = await fetch(`${API}/analytics/protocol/${protocolId}?days=${selectedPeriod}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setProtocolDetails(data);
        setSelectedProtocol(protocolId);
      }
    } catch (e) {
      console.error('Failed to fetch protocol details:', e);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        padding: 60,
        color: '#a1a1aa'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 15, animation: 'pulse 1.5s ease-in-out infinite' }}>
            📊
          </div>
          <p>Loading your analytics...</p>
        </div>
      </div>
    );
  }

  if (!dashboardData || dashboardData.total_protocols === 0) {
    return (
      <div style={{
        background: 'rgba(139, 92, 246, 0.1)',
        borderRadius: 16,
        padding: 40,
        textAlign: 'center',
        border: '1px solid rgba(139, 92, 246, 0.2)'
      }}>
        <div style={{ fontSize: '3rem', marginBottom: 15 }}>📈</div>
        <h3 style={{ color: '#fff', marginBottom: 10 }}>No Marketplace Protocols Yet</h3>
        <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
          List protocols in the marketplace to start tracking their performance!
        </p>
        <button
          onClick={() => window.location.hash = '#marketplace'}
          style={{
            background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
            border: 'none',
            borderRadius: 8,
            padding: '12px 24px',
            color: '#fff',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          Go to Marketplace
        </button>
      </div>
    );
  }

  const { summary, protocols, top_by_views, top_by_conversion, daily_overview } = dashboardData;

  return (
    <div data-testid="protocol-analytics-dashboard">
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 25
      }}>
        <div>
          <h2 style={{ color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            📊 Protocol Analytics
            <span style={{
              background: 'linear-gradient(135deg, #10b981, #059669)',
              padding: '4px 12px',
              borderRadius: 15,
              fontSize: '0.7rem',
              fontWeight: 700
            }}>
              CREATOR DASHBOARD
            </span>
          </h2>
          <p style={{ color: '#a1a1aa', margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Track views, copies, and conversions for your protocols
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: 10 }}>
          {[7, 30, 90].map(days => (
            <button
              key={days}
              onClick={() => setSelectedPeriod(days)}
              style={{
                background: selectedPeriod === days 
                  ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)'
                  : 'rgba(255,255,255,0.1)',
                border: 'none',
                borderRadius: 8,
                padding: '8px 16px',
                color: '#fff',
                fontWeight: selectedPeriod === days ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 15,
        marginBottom: 25
      }}>
        {[
          { label: 'Total Views', value: summary.total_views, icon: '👁️', color: '#3b82f6' },
          { label: 'Total Copies', value: summary.total_copies, icon: '📋', color: '#8b5cf6' },
          { label: 'Total Purchases', value: summary.total_purchases, icon: '💰', color: '#10b981' },
          { label: 'Revenue', value: `$${summary.total_revenue.toFixed(2)}`, icon: '💵', color: '#f59e0b' },
          { label: 'Conversion Rate', value: `${summary.avg_conversion_rate}%`, icon: '📈', color: '#ec4899' },
        ].map((stat, i) => (
          <div key={i} style={{
            background: `linear-gradient(135deg, ${stat.color}15, ${stat.color}08)`,
            borderRadius: 12,
            padding: 18,
            border: `1px solid ${stat.color}30`,
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '1.5rem', marginBottom: 5 }}>{stat.icon}</div>
            <div style={{ color: stat.color, fontSize: '1.6rem', fontWeight: 700 }}>{stat.value}</div>
            <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Daily Trend Chart */}
      {daily_overview && daily_overview.length > 0 && (
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          borderRadius: 16,
          padding: 20,
          marginBottom: 25,
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <h3 style={{ color: '#fff', marginBottom: 20, fontSize: '1rem' }}>
            📈 Daily Performance
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={daily_overview}>
              <defs>
                <linearGradient id="viewsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="copiesGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="date" 
                stroke="#71717a"
                tick={{ fill: '#71717a', fontSize: 11 }}
                tickFormatter={(v) => v.slice(5)}
              />
              <YAxis stroke="#71717a" tick={{ fill: '#71717a', fontSize: 11 }} />
              <Tooltip 
                contentStyle={{ 
                  background: 'rgba(0,0,0,0.9)', 
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8
                }}
                labelStyle={{ color: '#fff' }}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="views" 
                stroke="#3b82f6" 
                fill="url(#viewsGradient)"
                strokeWidth={2}
              />
              <Area 
                type="monotone" 
                dataKey="copies" 
                stroke="#8b5cf6" 
                fill="url(#copiesGradient)"
                strokeWidth={2}
              />
              <Line 
                type="monotone" 
                dataKey="purchases" 
                stroke="#10b981"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top Performers */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: 20,
        marginBottom: 25
      }}>
        {/* Top by Views */}
        <div style={{
          background: 'rgba(59, 130, 246, 0.1)',
          borderRadius: 12,
          padding: 18,
          border: '1px solid rgba(59, 130, 246, 0.2)'
        }}>
          <h4 style={{ color: '#3b82f6', marginBottom: 15, fontSize: '0.95rem' }}>
            👁️ Most Viewed
          </h4>
          {top_by_views && top_by_views.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {top_by_views.slice(0, 5).map((p, i) => (
                <div 
                  key={p.id}
                  onClick={() => fetchProtocolDetails(p.id)}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'rgba(0,0,0,0.2)',
                    padding: '10px 12px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(59, 130, 246, 0.2)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.2)'}
                >
                  <span style={{ color: '#fff', fontSize: '0.85rem' }}>
                    {i + 1}. {p.name.length > 25 ? p.name.slice(0, 25) + '...' : p.name}
                  </span>
                  <span style={{ color: '#3b82f6', fontWeight: 600 }}>{p.views} views</span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>No data yet</p>
          )}
        </div>

        {/* Top by Conversion */}
        <div style={{
          background: 'rgba(16, 185, 129, 0.1)',
          borderRadius: 12,
          padding: 18,
          border: '1px solid rgba(16, 185, 129, 0.2)'
        }}>
          <h4 style={{ color: '#10b981', marginBottom: 15, fontSize: '0.95rem' }}>
            📈 Best Converting
          </h4>
          {top_by_conversion && top_by_conversion.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {top_by_conversion.slice(0, 5).map((p, i) => (
                <div 
                  key={p.id}
                  onClick={() => fetchProtocolDetails(p.id)}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'rgba(0,0,0,0.2)',
                    padding: '10px 12px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(16, 185, 129, 0.2)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.2)'}
                >
                  <span style={{ color: '#fff', fontSize: '0.85rem' }}>
                    {i + 1}. {p.name.length > 25 ? p.name.slice(0, 25) + '...' : p.name}
                  </span>
                  <span style={{ color: '#10b981', fontWeight: 600 }}>{p.conversion_rate}%</span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Need 5+ views to qualify</p>
          )}
        </div>
      </div>

      {/* All Protocols List */}
      <div style={{
        background: 'rgba(0,0,0,0.2)',
        borderRadius: 16,
        padding: 20,
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h3 style={{ color: '#fff', marginBottom: 15, fontSize: '1rem' }}>
          📋 All Your Marketplace Protocols ({dashboardData.total_protocols})
        </h3>
        
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                {['Protocol', 'Price', 'Views', 'Copies', 'Purchases', 'Conv. Rate'].map(h => (
                  <th key={h} style={{
                    textAlign: 'left',
                    padding: '12px 15px',
                    color: '#a1a1aa',
                    fontSize: '0.8rem',
                    fontWeight: 600
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {protocols.map((p, i) => (
                <tr 
                  key={p.id}
                  onClick={() => fetchProtocolDetails(p.id)}
                  style={{ 
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    cursor: 'pointer',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '12px 15px', color: '#fff', fontSize: '0.9rem' }}>
                    {p.name}
                  </td>
                  <td style={{ padding: '12px 15px', color: '#10b981', fontSize: '0.9rem' }}>
                    ${p.price.toFixed(2)}
                  </td>
                  <td style={{ padding: '12px 15px', color: '#3b82f6', fontSize: '0.9rem' }}>
                    {p.views}
                  </td>
                  <td style={{ padding: '12px 15px', color: '#8b5cf6', fontSize: '0.9rem' }}>
                    {p.copies}
                  </td>
                  <td style={{ padding: '12px 15px', color: '#10b981', fontSize: '0.9rem' }}>
                    {p.purchases}
                  </td>
                  <td style={{ padding: '12px 15px' }}>
                    <span style={{
                      background: p.conversion_rate >= 10 
                        ? 'rgba(16, 185, 129, 0.2)' 
                        : p.conversion_rate >= 5 
                        ? 'rgba(251, 191, 36, 0.2)'
                        : 'rgba(107, 114, 128, 0.2)',
                      color: p.conversion_rate >= 10 
                        ? '#10b981' 
                        : p.conversion_rate >= 5 
                        ? '#fbbf24'
                        : '#9ca3af',
                      padding: '4px 10px',
                      borderRadius: 12,
                      fontSize: '0.8rem',
                      fontWeight: 600
                    }}>
                      {p.conversion_rate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Protocol Details Modal */}
      {selectedProtocol && protocolDetails && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20
          }}
          onClick={() => { setSelectedProtocol(null); setProtocolDetails(null); }}
        >
          <div 
            style={{
              background: '#1a1a2e',
              borderRadius: 16,
              padding: 25,
              maxWidth: 700,
              width: '100%',
              maxHeight: '80vh',
              overflow: 'auto',
              border: '1px solid rgba(255,255,255,0.1)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ color: '#fff', margin: 0 }}>{protocolDetails.protocol_name}</h3>
              <button
                onClick={() => { setSelectedProtocol(null); setProtocolDetails(null); }}
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  borderRadius: 8,
                  padding: '6px 12px',
                  color: '#a1a1aa',
                  cursor: 'pointer'
                }}
              >
                ✕ Close
              </button>
            </div>

            {/* Protocol Stats */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
              gap: 12,
              marginBottom: 20
            }}>
              {[
                { label: 'Views', value: protocolDetails.summary.total_views, color: '#3b82f6' },
                { label: 'Copies', value: protocolDetails.summary.total_copies, color: '#8b5cf6' },
                { label: 'Purchases', value: protocolDetails.summary.total_purchases, color: '#10b981' },
                { label: 'Unique Visitors', value: protocolDetails.summary.unique_visitors, color: '#f59e0b' },
                { label: 'Conv. Rate', value: `${protocolDetails.summary.conversion_rate}%`, color: '#ec4899' },
              ].map((stat, i) => (
                <div key={i} style={{
                  background: `${stat.color}15`,
                  borderRadius: 10,
                  padding: 12,
                  textAlign: 'center'
                }}>
                  <div style={{ color: stat.color, fontSize: '1.3rem', fontWeight: 700 }}>{stat.value}</div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>{stat.label}</div>
                </div>
              ))}
            </div>

            {/* Daily Chart */}
            {protocolDetails.daily_data && protocolDetails.daily_data.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <h4 style={{ color: '#a1a1aa', marginBottom: 10, fontSize: '0.9rem' }}>Daily Breakdown</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={protocolDetails.daily_data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#71717a"
                      tick={{ fill: '#71717a', fontSize: 10 }}
                      tickFormatter={(v) => v.slice(5)}
                    />
                    <YAxis stroke="#71717a" tick={{ fill: '#71717a', fontSize: 10 }} />
                    <Tooltip 
                      contentStyle={{ 
                        background: 'rgba(0,0,0,0.9)', 
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 8
                      }}
                    />
                    <Bar dataKey="views" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="copies" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="purchases" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default ProtocolAnalyticsDashboard;
