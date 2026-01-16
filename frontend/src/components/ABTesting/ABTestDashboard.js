import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell
} from 'recharts';

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ec4899'];

/**
 * A/B Testing Dashboard Component
 * Admin interface for viewing and managing A/B tests
 */
const ABTestDashboard = ({ showToast }) => {
  const { token } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [selectedTest, setSelectedTest] = useState(null);
  const [testResults, setTestResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/ab-testing/dashboard?days=${period}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDashboard(data);
      }
    } catch (e) {
      console.error('Failed to fetch A/B dashboard:', e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period]);

  const fetchTestResults = async (testName) => {
    try {
      const res = await fetch(`${API}/ab-testing/results/${testName}?days=${period}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTestResults(data);
        setSelectedTest(testName);
      }
    } catch (e) {
      console.error('Failed to fetch test results:', e);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 60, color: '#a1a1aa' }}>
        <div style={{ fontSize: '2rem', animation: 'pulse 1.5s ease-in-out infinite' }}>🧪</div>
        <p>Loading A/B Testing Dashboard...</p>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div style={{ textAlign: 'center', padding: 60, color: '#a1a1aa' }}>
        <p>Failed to load dashboard</p>
      </div>
    );
  }

  return (
    <div data-testid="ab-testing-dashboard">
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 25
      }}>
        <div>
          <h2 style={{ color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            🧪 A/B Testing Dashboard
            <span style={{
              background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
              padding: '4px 12px',
              borderRadius: 15,
              fontSize: '0.7rem',
              fontWeight: 700
            }}>
              CONVERSION OPTIMIZATION
            </span>
          </h2>
          <p style={{ color: '#a1a1aa', margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Track and optimize UI elements for better conversions
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          {[7, 30, 90].map(days => (
            <button
              key={days}
              onClick={() => setPeriod(days)}
              style={{
                background: period === days 
                  ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)'
                  : 'rgba(255,255,255,0.1)',
                border: 'none',
                borderRadius: 8,
                padding: '8px 16px',
                color: '#fff',
                fontWeight: period === days ? 600 : 400,
                cursor: 'pointer'
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
          { label: 'Active Tests', value: dashboard.active_tests, icon: '🧪', color: '#8b5cf6' },
          { label: 'Total Impressions', value: dashboard.total_impressions.toLocaleString(), icon: '👁️', color: '#3b82f6' },
          { label: 'Total Conversions', value: dashboard.total_conversions.toLocaleString(), icon: '✅', color: '#10b981' },
          { label: 'Overall Conv. Rate', value: `${dashboard.overall_conversion_rate}%`, icon: '📈', color: '#f59e0b' },
        ].map((stat, i) => (
          <div key={i} style={{
            background: `linear-gradient(135deg, ${stat.color}20, ${stat.color}10)`,
            borderRadius: 12,
            padding: 18,
            border: `1px solid ${stat.color}30`,
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '1.5rem', marginBottom: 5 }}>{stat.icon}</div>
            <div style={{ color: stat.color, fontSize: '1.5rem', fontWeight: 700 }}>{stat.value}</div>
            <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Tests List */}
      <div style={{
        background: 'rgba(0,0,0,0.2)',
        borderRadius: 16,
        padding: 20,
        marginBottom: 25,
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        <h3 style={{ color: '#fff', marginBottom: 15 }}>Active A/B Tests</h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {dashboard.tests.map((test, i) => (
            <div 
              key={test.name}
              onClick={() => fetchTestResults(test.name)}
              style={{
                background: selectedTest === test.name 
                  ? 'rgba(139, 92, 246, 0.2)' 
                  : 'rgba(255,255,255,0.03)',
                borderRadius: 12,
                padding: 15,
                cursor: 'pointer',
                border: selectedTest === test.name 
                  ? '1px solid rgba(139, 92, 246, 0.5)'
                  : '1px solid transparent',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (selectedTest !== test.name) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                }
              }}
              onMouseLeave={(e) => {
                if (selectedTest !== test.name) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                }
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4 style={{ color: '#fff', margin: '0 0 5px 0', fontSize: '1rem' }}>
                    {test.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </h4>
                  <p style={{ color: '#a1a1aa', margin: 0, fontSize: '0.85rem' }}>
                    {test.description || `Testing ${test.target_element}`}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: '#3b82f6', fontSize: '0.9rem' }}>
                      {test.total_events.toLocaleString()} events
                    </div>
                    <div style={{ color: '#71717a', fontSize: '0.8rem' }}>
                      {test.variant_count} variants
                    </div>
                  </div>
                  <span style={{
                    background: test.is_active ? 'rgba(16, 185, 129, 0.2)' : 'rgba(107, 114, 128, 0.2)',
                    color: test.is_active ? '#10b981' : '#9ca3af',
                    padding: '4px 10px',
                    borderRadius: 15,
                    fontSize: '0.75rem',
                    fontWeight: 600
                  }}>
                    {test.is_active ? 'Active' : 'Paused'}
                  </span>
                  {test.leading_variant && (
                    <span style={{
                      background: 'rgba(251, 191, 36, 0.2)',
                      color: '#fbbf24',
                      padding: '4px 10px',
                      borderRadius: 15,
                      fontSize: '0.75rem'
                    }}>
                      Leading: {test.leading_variant}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Test Results Detail */}
      {testResults && (
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(139, 92, 246, 0.3)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3 style={{ color: '#fff', margin: 0 }}>
              Results: {testResults.test_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </h3>
            <button
              onClick={() => { setSelectedTest(null); setTestResults(null); }}
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

          {/* Winner Banner */}
          {testResults.winner && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))',
              borderRadius: 12,
              padding: 15,
              marginBottom: 20,
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: 15
            }}>
              <span style={{ fontSize: '2rem' }}>🏆</span>
              <div>
                <h4 style={{ color: '#10b981', margin: 0 }}>
                  Winner: Variant {testResults.winner} ({testResults.winner_name})
                </h4>
                <p style={{ color: '#a1a1aa', margin: '5px 0 0 0', fontSize: '0.9rem' }}>
                  {testResults.recommendation}
                </p>
              </div>
            </div>
          )}

          {!testResults.is_statistically_significant && (
            <div style={{
              background: 'rgba(251, 191, 36, 0.1)',
              borderRadius: 12,
              padding: 15,
              marginBottom: 20,
              border: '1px solid rgba(251, 191, 36, 0.3)'
            }}>
              <p style={{ color: '#fbbf24', margin: 0, fontSize: '0.9rem' }}>
                ⚠️ Need at least 1,000 impressions for statistical significance. 
                Currently at {testResults.total_impressions.toLocaleString()}.
              </p>
            </div>
          )}

          {/* Variant Comparison Chart */}
          <div style={{ marginBottom: 20 }}>
            <h4 style={{ color: '#a1a1aa', marginBottom: 10, fontSize: '0.9rem' }}>
              Conversion Rate by Variant
            </h4>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={testResults.variants}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis 
                  dataKey="variant_name" 
                  stroke="#71717a"
                  tick={{ fill: '#fff', fontSize: 11 }}
                />
                <YAxis 
                  stroke="#71717a" 
                  tick={{ fill: '#71717a', fontSize: 11 }}
                  unit="%"
                />
                <Tooltip 
                  contentStyle={{ 
                    background: 'rgba(0,0,0,0.9)', 
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 8
                  }}
                  formatter={(value) => [`${value}%`, 'Conversion Rate']}
                />
                <Bar dataKey="conversion_rate" radius={[4, 4, 0, 0]}>
                  {testResults.variants.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.variant_id === testResults.winner ? '#10b981' : COLORS[index % COLORS.length]} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Variant Stats Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                  {['Variant', 'Impressions', 'Clicks', 'Conversions', 'Click Rate', 'Conv. Rate'].map(h => (
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
                {testResults.variants.map((v, i) => (
                  <tr 
                    key={v.variant_id}
                    style={{ 
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                      background: v.variant_id === testResults.winner ? 'rgba(16, 185, 129, 0.1)' : 'transparent'
                    }}
                  >
                    <td style={{ padding: '12px 15px', color: '#fff' }}>
                      <span style={{ fontWeight: 600 }}>{v.variant_id}</span>
                      <span style={{ color: '#a1a1aa', marginLeft: 8 }}>({v.variant_name})</span>
                      {v.variant_id === testResults.winner && (
                        <span style={{ marginLeft: 8 }}>🏆</span>
                      )}
                    </td>
                    <td style={{ padding: '12px 15px', color: '#3b82f6' }}>
                      {v.impressions.toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 15px', color: '#8b5cf6' }}>
                      {v.clicks.toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 15px', color: '#10b981' }}>
                      {v.conversions.toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 15px', color: '#f59e0b' }}>
                      {v.click_rate}%
                    </td>
                    <td style={{ padding: '12px 15px' }}>
                      <span style={{
                        background: v.variant_id === testResults.winner 
                          ? 'rgba(16, 185, 129, 0.3)' 
                          : 'rgba(139, 92, 246, 0.2)',
                        padding: '4px 10px',
                        borderRadius: 12,
                        color: v.variant_id === testResults.winner ? '#10b981' : '#a78bfa',
                        fontWeight: 600
                      }}>
                        {v.conversion_rate}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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

export default ABTestDashboard;
