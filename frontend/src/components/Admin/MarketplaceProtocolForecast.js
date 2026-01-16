import React, { useState, useEffect, useCallback } from 'react';
import { API } from '../../utils/api';

const MarketplaceProtocolForecast = ({ token, showToast }) => {
  const [forecast, setForecast] = useState(null);
  const [topCreators, setTopCreators] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchForecast = useCallback(async () => {
    try {
      const res = await fetch(`${API}/protocol-analytics/admin/marketplace-forecast`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setForecast(data.marketplace_forecast);
      }
    } catch (e) {
      console.error('Failed to fetch forecast:', e);
    }
    setLoading(false);
  }, [token]);

  const fetchTopCreators = useCallback(async () => {
    try {
      const res = await fetch(`${API}/protocol-analytics/admin/top-creators?limit=10`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTopCreators(data.top_creators || []);
      }
    } catch (e) {
      console.error('Failed to fetch top creators:', e);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchForecast();
      fetchTopCreators();
    }
  }, [token, fetchForecast, fetchTopCreators]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
        <div style={{ fontSize: '2rem', marginBottom: 15 }}>📊</div>
        Loading marketplace forecast...
      </div>
    );
  }

  return (
    <div data-testid="marketplace-protocol-forecast">
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.1))',
        borderRadius: 16,
        padding: 20,
        marginBottom: 25,
        border: '1px solid rgba(16, 185, 129, 0.3)'
      }}>
        <h2 style={{ color: '#10b981', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          🔮 Marketplace Protocol Forecast
          <span style={{
            background: 'rgba(16, 185, 129, 0.2)',
            color: '#10b981',
            padding: '4px 12px',
            borderRadius: 20,
            fontSize: '0.75rem',
            fontWeight: 600
          }}>
            ADMIN
          </span>
        </h2>
        <p style={{ color: '#a1a1aa', margin: '10px 0 0 0', fontSize: '0.9rem' }}>
          Predict top-performing protocols and track marketplace trends 📈
        </p>
      </div>

      {forecast ? (
        <>
          {/* Key Metrics */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
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
              <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: 5 }}>Week Revenue</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, color: '#10b981' }}>
                ${forecast.week_revenue.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#71717a' }}>{forecast.week_sales} sales</div>
            </div>
            
            <div style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(124, 58, 237, 0.05))',
              borderRadius: 16,
              padding: 20,
              textAlign: 'center',
              border: '1px solid rgba(124, 58, 237, 0.3)'
            }}>
              <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: 5 }}>Month Revenue</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, color: '#a78bfa' }}>
                ${forecast.month_revenue.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#71717a' }}>{forecast.month_sales} sales</div>
            </div>
            
            <div style={{
              background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.05))',
              borderRadius: 16,
              padding: 20,
              textAlign: 'center',
              border: '1px solid rgba(251, 191, 36, 0.3)'
            }}>
              <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: 5 }}>Next Month Projection</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, color: '#fbbf24' }}>
                ${forecast.projected_next_month.toFixed(2)}
              </div>
            </div>
            
            <div style={{
              background: forecast.wow_growth_percent >= 0 
                ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.05))'
                : 'linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.05))',
              borderRadius: 16,
              padding: 20,
              textAlign: 'center',
              border: forecast.wow_growth_percent >= 0 
                ? '1px solid rgba(16, 185, 129, 0.3)'
                : '1px solid rgba(239, 68, 68, 0.3)'
            }}>
              <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginBottom: 5 }}>Week-over-Week</div>
              <div style={{ 
                fontSize: '2.2rem', 
                fontWeight: 700, 
                color: forecast.wow_growth_percent >= 0 ? '#10b981' : '#ef4444' 
              }}>
                {forecast.wow_growth_percent >= 0 ? '+' : ''}{forecast.wow_growth_percent}%
              </div>
              <div style={{ fontSize: '0.75rem', color: '#71717a' }}>growth</div>
            </div>
          </div>

          {/* Top Performing Protocols */}
          {forecast.top_performing_protocols?.length > 0 && (
            <div style={{
              background: 'rgba(30, 20, 50, 0.5)',
              borderRadius: 16,
              padding: 20,
              marginBottom: 25,
              border: '1px solid rgba(124, 58, 237, 0.2)'
            }}>
              <h3 style={{ color: '#f472b6', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 10 }}>
                🏆 Top Performing Protocols
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {forecast.top_performing_protocols.map((protocol, index) => (
                  <div
                    key={protocol.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: 15,
                      background: index === 0 ? 'rgba(251, 191, 36, 0.1)' : 'rgba(0,0,0,0.2)',
                      borderRadius: 12,
                      border: index === 0 ? '1px solid rgba(251, 191, 36, 0.3)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
                      <div style={{
                        width: 35,
                        height: 35,
                        borderRadius: '50%',
                        background: index === 0 ? '#fbbf24' : index === 1 ? '#a1a1aa' : index === 2 ? '#cd7f32' : '#71717a',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        color: index < 3 ? '#000' : '#fff',
                        fontSize: '0.9rem'
                      }}>
                        {index + 1}
                      </div>
                      <div>
                        <div style={{ color: '#fff', fontWeight: 600 }}>{protocol.name}</div>
                        <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{protocol.category}</div>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ color: '#10b981', fontWeight: 700, fontSize: '1.1rem' }}>
                        ${protocol.revenue.toFixed(2)}
                      </div>
                      <div style={{ color: '#71717a', fontSize: '0.75rem' }}>
                        {protocol.sales} sales
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
          No forecast data available yet. Make some sales first! 💰
        </div>
      )}

      {/* Top Creators */}
      {topCreators.length > 0 && (
        <div style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 16,
          padding: 20,
          border: '1px solid rgba(236, 72, 153, 0.2)'
        }}>
          <h3 style={{ color: '#ec4899', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 10 }}>
            👑 Top Protocol Creators
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {topCreators.map((creator, index) => (
              <div
                key={creator.user_id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: 15,
                  background: 'rgba(0,0,0,0.2)',
                  borderRadius: 12
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #ec4899, #f472b6)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    color: '#fff',
                    fontSize: '1rem'
                  }}>
                    {creator.username.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div style={{ color: '#fff', fontWeight: 600 }}>{creator.username}</div>
                    <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{creator.protocols_count} protocols</div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#10b981', fontWeight: 700, fontSize: '1.1rem' }}>
                    ${creator.total_revenue.toFixed(2)}
                  </div>
                  <div style={{ color: '#71717a', fontSize: '0.75rem' }}>
                    {creator.total_sales} total sales
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketplaceProtocolForecast;
