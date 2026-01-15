import React, { useState, useEffect } from 'react';
import { API } from '../../utils/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts';

/**
 * RevenueForecastAdmin - AI-powered revenue forecasting dashboard
 */
const RevenueForecastAdmin = ({ token, showToast }) => {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const summaryRes = await fetch(`${API}/revenue-forecast/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setSummary(data);
      }
    } catch (e) {
      console.error('Failed to fetch revenue data:', e);
    }
    setLoading(false);
  };

  const generateForecast = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API}/revenue-forecast/forecast?history_days=30&forecast_days=30`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setForecast(data);
        showToast('🔮 AI Forecast Generated!', 'success');
      }
    } catch (e) {
      showToast('Failed to generate forecast', 'error');
    }
    setGenerating(false);
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>Loading revenue data...</div>;
  }

  return (
    <div>
      <h3 style={{ marginBottom: 10, color: '#f472b6' }}>📈 Revenue Forecasting</h3>
      <p style={{ color: '#a1a1aa', marginBottom: 25 }}>
        AI-powered revenue predictions based on A/B test performance trends. See where your profits are headed! 💰🔮
      </p>

      {/* Revenue Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 15,
        marginBottom: 25
      }}>
        {/* Weekly Revenue */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2))',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(16, 185, 129, 0.3)'
        }}>
          <div style={{ fontSize: '0.85rem', color: '#10b981', marginBottom: 8, fontWeight: 600 }}>
            📅 This Week
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
            ${(summary?.weekly?.revenue || 0).toFixed(2)}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 5 }}>
            {summary?.weekly?.conversions || 0} conversions
          </div>
        </div>

        {/* Monthly Revenue */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.2))',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(59, 130, 246, 0.3)'
        }}>
          <div style={{ fontSize: '0.85rem', color: '#3b82f6', marginBottom: 8, fontWeight: 600 }}>
            📆 This Month
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
            ${(summary?.monthly?.revenue || 0).toFixed(2)}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 5 }}>
            {summary?.monthly?.conversions || 0} conversions
          </div>
        </div>

        {/* Projected Monthly */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(219, 39, 119, 0.2))',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(236, 72, 153, 0.3)'
        }}>
          <div style={{ fontSize: '0.85rem', color: '#ec4899', marginBottom: 8, fontWeight: 600 }}>
            🔮 Projected Monthly
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ec4899' }}>
            ${(summary?.projected_monthly || 0).toFixed(2)}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 5 }}>
            Based on current trend
          </div>
        </div>

        {/* Trend */}
        <div style={{
          background: summary?.trend === 'up' 
            ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2))'
            : summary?.trend === 'down'
            ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2))'
            : 'linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.2))',
          borderRadius: 16,
          padding: 20,
          border: `1px solid ${summary?.trend === 'up' ? 'rgba(16, 185, 129, 0.3)' : summary?.trend === 'down' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
        }}>
          <div style={{ fontSize: '0.85rem', color: summary?.trend === 'up' ? '#10b981' : summary?.trend === 'down' ? '#ef4444' : '#f59e0b', marginBottom: 8, fontWeight: 600 }}>
            📊 Trend
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: summary?.trend === 'up' ? '#10b981' : summary?.trend === 'down' ? '#ef4444' : '#f59e0b' }}>
            {summary?.trend === 'up' ? '📈' : summary?.trend === 'down' ? '📉' : '➡️'} {Math.abs(summary?.trend_percent || 0).toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 5 }}>
            vs last month avg
          </div>
        </div>
      </div>

      {/* Generate Forecast Button */}
      <div style={{ marginBottom: 25 }}>
        <button
          className="btn btn-primary"
          onClick={generateForecast}
          disabled={generating}
          style={{
            padding: '15px 30px',
            background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
            fontSize: '1rem'
          }}
        >
          {generating ? '🔮 Consulting the AI Oracle...' : '🤖 Generate AI Forecast'}
        </button>
      </div>

      {/* AI Forecast Results */}
      {forecast && (
        <div style={{
          background: 'rgba(124, 58, 237, 0.1)',
          border: '1px solid rgba(124, 58, 237, 0.3)',
          borderRadius: 16,
          padding: 25,
          marginBottom: 25
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <span style={{ fontSize: '1.5rem' }}>🔮</span>
            <h4 style={{ color: '#a78bfa', margin: 0 }}>AI Revenue Forecast (Next 30 Days)</h4>
            {forecast.forecast?.ai_generated && (
              <span style={{
                padding: '4px 10px',
                background: 'rgba(16, 185, 129, 0.2)',
                color: '#10b981',
                borderRadius: 15,
                fontSize: '0.7rem'
              }}>
                🤖 GPT-5.2 Generated
              </span>
            )}
          </div>

          {/* Revenue Scenarios */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 15,
            marginBottom: 20
          }}>
            <div style={{
              padding: 15,
              background: 'rgba(245, 158, 11, 0.1)',
              borderRadius: 12,
              textAlign: 'center',
              border: '1px solid rgba(245, 158, 11, 0.3)'
            }}>
              <div style={{ fontSize: '0.8rem', color: '#f59e0b', marginBottom: 5 }}>🐢 Conservative</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f59e0b' }}>
                ${(forecast.forecast?.conservative_revenue || 0).toFixed(2)}
              </div>
            </div>
            <div style={{
              padding: 15,
              background: 'rgba(16, 185, 129, 0.1)',
              borderRadius: 12,
              textAlign: 'center',
              border: '2px solid rgba(16, 185, 129, 0.5)'
            }}>
              <div style={{ fontSize: '0.8rem', color: '#10b981', marginBottom: 5 }}>🎯 Expected</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#10b981' }}>
                ${(forecast.forecast?.expected_revenue || 0).toFixed(2)}
              </div>
            </div>
            <div style={{
              padding: 15,
              background: 'rgba(236, 72, 153, 0.1)',
              borderRadius: 12,
              textAlign: 'center',
              border: '1px solid rgba(236, 72, 153, 0.3)'
            }}>
              <div style={{ fontSize: '0.8rem', color: '#ec4899', marginBottom: 5 }}>🚀 Optimistic</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#ec4899' }}>
                ${(forecast.forecast?.optimistic_revenue || 0).toFixed(2)}
              </div>
            </div>
          </div>

          {/* Weekly Breakdown Chart */}
          {forecast.forecast?.weekly_breakdown && forecast.forecast.weekly_breakdown.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <h5 style={{ color: '#a1a1aa', marginBottom: 10 }}>📊 Weekly Projection</h5>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={forecast.forecast.weekly_breakdown}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="week" stroke="#888" tickFormatter={(v) => `Week ${v}`} />
                  <YAxis stroke="#888" tickFormatter={(v) => `$${v}`} />
                  <Tooltip 
                    contentStyle={{ background: '#1e1b4b', border: '1px solid #7c3aed', borderRadius: 8 }}
                    formatter={(value) => [`$${value.toFixed(2)}`, 'Projected Revenue']}
                    labelFormatter={(label) => `Week ${label}`}
                  />
                  <Bar dataKey="projected" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Key Factors */}
          {forecast.forecast?.key_factors && (
            <div style={{ marginBottom: 20 }}>
              <h5 style={{ color: '#a1a1aa', marginBottom: 10 }}>🔑 Key Factors</h5>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                {forecast.forecast.key_factors.map((factor, idx) => (
                  <span key={idx} style={{
                    padding: '6px 12px',
                    background: 'rgba(59, 130, 246, 0.2)',
                    color: '#60a5fa',
                    borderRadius: 20,
                    fontSize: '0.8rem'
                  }}>
                    {factor}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* AI Recommendation */}
          {forecast.forecast?.recommendation && (
            <div style={{
              padding: 15,
              background: 'rgba(16, 185, 129, 0.1)',
              borderRadius: 12,
              border: '1px solid rgba(16, 185, 129, 0.3)',
              marginBottom: 15
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span>💡</span>
                <span style={{ color: '#10b981', fontWeight: 600 }}>AI Recommendation</span>
              </div>
              <p style={{ color: '#e2e8f0', margin: 0, lineHeight: 1.6 }}>
                {forecast.forecast.recommendation}
              </p>
            </div>
          )}

          {/* Funny Insight */}
          {forecast.forecast?.funny_insight && (
            <div style={{
              padding: 15,
              background: 'rgba(236, 72, 153, 0.1)',
              borderRadius: 12,
              border: '1px solid rgba(236, 72, 153, 0.3)',
              textAlign: 'center'
            }}>
              <p style={{ color: '#f472b6', margin: 0, fontStyle: 'italic', fontSize: '0.95rem' }}>
                "{forecast.forecast.funny_insight}"
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tips */}
      <div style={{
        padding: 20,
        background: 'rgba(59, 130, 246, 0.1)',
        borderRadius: 12,
        border: '1px solid rgba(59, 130, 246, 0.3)'
      }}>
        <h4 style={{ color: '#60a5fa', margin: '0 0 10px 0' }}>💡 Tips to Maximize Revenue</h4>
        <ul style={{ color: '#a1a1aa', fontSize: '0.9rem', margin: 0, paddingLeft: 20, lineHeight: 1.8 }}>
          <li><strong>Optimize A/B Tests:</strong> Use the Auto-Optimizer to automatically disable losing variants</li>
          <li><strong>Price Testing:</strong> Experiment with different price points for your protocols</li>
          <li><strong>Conversion Focus:</strong> Improve your CTAs based on A/B test winners</li>
          <li><strong>Scale Winners:</strong> Once you find a winner, increase traffic to that variant</li>
          <li><strong>Regular Monitoring:</strong> Check forecasts weekly to catch trends early</li>
        </ul>
      </div>
    </div>
  );
};

export default RevenueForecastAdmin;
