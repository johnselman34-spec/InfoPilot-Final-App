import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { PieChart, Pie, Cell, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Funny marketing messages
const FUNNY_STATS_MESSAGES = [
  "📊 These statistics are so accurate, even your math teacher would be impressed!",
  "🎯 Data so hot, it's practically on fire! 🔥",
  "💡 Warning: Viewing these stats may cause sudden urges to buy protocols!",
  "🚀 Our numbers go up like Richard J. Selman's A-4 Skyhawk - FAST!",
  "📈 These charts are more exciting than a supernatural thriller! (Speaking of which...)",
];

const COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#ec4899', '#14b8a6', '#f97316'];

const StatisticsPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [leaderboard, setLeaderboard] = useState({ sales: [], revenue: [] });
  const [leaderboardTab, setLeaderboardTab] = useState('sales');
  const [loading, setLoading] = useState(true);
  const [funnyMessage] = useState(() => FUNNY_STATS_MESSAGES[Math.floor(Math.random() * FUNNY_STATS_MESSAGES.length)]);

  useEffect(() => {
    fetchStatistics();
    fetchLeaderboards();
  }, []);

  const fetchStatistics = async () => {
    try {
      const res = await fetch(`${API}/statistics/dashboard`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLeaderboards = async () => {
    try {
      const [salesRes, revenueRes] = await Promise.all([
        fetch(`${API}/marketplace/leaderboard/sales`),
        fetch(`${API}/marketplace/leaderboard/revenue`)
      ]);
      
      if (salesRes.ok && revenueRes.ok) {
        const salesData = await salesRes.json();
        const revenueData = await revenueRes.json();
        setLeaderboard({
          sales: salesData.leaderboard || [],
          revenue: revenueData.leaderboard || []
        });
      }
    } catch (error) {
      console.error('Failed to fetch leaderboards:', error);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '50vh',
        color: '#fff'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: 20 }}>📊</div>
          <p>Crunching numbers faster than a squirrel hoards acorns...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 0' }}>
      {/* Hero Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(236, 72, 153, 0.2) 100%)',
        borderRadius: 20,
        padding: 30,
        marginBottom: 30,
        border: '1px solid rgba(139, 92, 246, 0.3)'
      }}>
        <h1 style={{ 
          fontSize: '2.5rem', 
          fontWeight: 800, 
          marginBottom: 10,
          background: 'linear-gradient(135deg, #fff 0%, #f472b6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          📈 InfoPilot Statistics Central
        </h1>
        <p style={{ color: '#a1a1aa', fontSize: '1.1rem', marginBottom: 15 }}>
          {funnyMessage}
        </p>
        <div style={{ 
          display: 'inline-block',
          background: 'rgba(16, 185, 129, 0.2)',
          padding: '8px 16px',
          borderRadius: 20,
          color: '#10b981',
          fontSize: '0.9rem'
        }}>
          🎭 {stats?.funny_fact}
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 20,
        marginBottom: 30
      }}>
        {[
          { label: 'Total Users', value: stats?.overview?.total_users || 0, icon: '👥', color: '#8b5cf6' },
          { label: 'Active (7d)', value: stats?.overview?.active_users_7d || 0, icon: '🔥', color: '#ef4444' },
          { label: 'Protocols', value: stats?.overview?.total_protocols || 0, icon: '📋', color: '#3b82f6' },
          { label: 'Searches', value: stats?.overview?.total_searches || 0, icon: '🔍', color: '#10b981' },
          { label: 'Purchases', value: stats?.overview?.total_purchases || 0, icon: '💰', color: '#f59e0b' },
          { label: 'Revenue', value: `$${stats?.overview?.total_revenue || 0}`, icon: '💵', color: '#ec4899' },
        ].map((stat, i) => (
          <div key={i} style={{
            background: 'rgba(30, 20, 50, 0.6)',
            borderRadius: 16,
            padding: 20,
            border: `1px solid ${stat.color}30`,
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '2rem', marginBottom: 10 }}>{stat.icon}</div>
            <div style={{ color: stat.color, fontSize: '2rem', fontWeight: 700 }}>{stat.value}</div>
            <div style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 25, marginBottom: 30 }}>
        {/* Countries Pie Chart */}
        <div style={{
          background: 'rgba(30, 20, 50, 0.6)',
          borderRadius: 16,
          padding: 25,
          border: '1px solid rgba(139, 92, 246, 0.2)'
        }}>
          <h3 style={{ color: '#fff', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
            🌍 Results by Country
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats?.countries?.countries || []}
                dataKey="count"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percentage }) => `${name}: ${percentage}%`}
              >
                {(stats?.countries?.countries || []).map((entry, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* US States Bar Chart */}
        <div style={{
          background: 'rgba(30, 20, 50, 0.6)',
          borderRadius: 16,
          padding: 25,
          border: '1px solid rgba(139, 92, 246, 0.2)'
        }}>
          <h3 style={{ color: '#fff', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
            🇺🇸 US States Breakdown
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats?.us_states?.states || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="code" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip 
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Document Types */}
        <div style={{
          background: 'rgba(30, 20, 50, 0.6)',
          borderRadius: 16,
          padding: 25,
          border: '1px solid rgba(139, 92, 246, 0.2)'
        }}>
          <h3 style={{ color: '#fff', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
            📄 Document Types
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats?.document_types?.document_types || []}
                dataKey="count"
                nameKey="label"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                label={({ label, percentage }) => `${label}: ${percentage}%`}
              >
                {(stats?.document_types?.document_types || []).map((entry, index) => (
                  <Cell key={index} fill={entry.color || COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Words */}
        <div style={{
          background: 'rgba(30, 20, 50, 0.6)',
          borderRadius: 16,
          padding: 25,
          border: '1px solid rgba(139, 92, 246, 0.2)'
        }}>
          <h3 style={{ color: '#fff', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
            🔤 Top 10 Words in Protocols
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats?.top_words?.top_words || []} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis type="number" stroke="#888" />
              <YAxis dataKey="word" type="category" stroke="#888" width={80} />
              <Tooltip 
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }}
              />
              <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Sellers Leaderboard */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
        borderRadius: 20,
        padding: 30,
        marginBottom: 30,
        border: '1px solid rgba(245, 158, 11, 0.3)'
      }}>
        <h2 style={{ 
          color: '#fff', 
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 15
        }}>
          🏆 Top Sellers Leaderboard
          <span style={{
            background: 'linear-gradient(135deg, #f59e0b 0%, #ec4899 100%)',
            padding: '5px 15px',
            borderRadius: 20,
            fontSize: '0.8rem',
            fontWeight: 600
          }}>
            LIVE
          </span>
        </h2>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
          <button
            onClick={() => setLeaderboardTab('sales')}
            style={{
              padding: '10px 25px',
              borderRadius: 10,
              border: 'none',
              background: leaderboardTab === 'sales' 
                ? 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)' 
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            📊 By Sales Count
          </button>
          <button
            onClick={() => setLeaderboardTab('revenue')}
            style={{
              padding: '10px 25px',
              borderRadius: 10,
              border: 'none',
              background: leaderboardTab === 'revenue' 
                ? 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)' 
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            💰 By Revenue
          </button>
        </div>

        {/* Leaderboard Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid rgba(255,255,255,0.1)' }}>
                <th style={{ padding: 15, textAlign: 'left', color: '#a1a1aa' }}>Rank</th>
                <th style={{ padding: 15, textAlign: 'left', color: '#a1a1aa' }}>Seller</th>
                <th style={{ padding: 15, textAlign: 'left', color: '#a1a1aa' }}>Title</th>
                <th style={{ padding: 15, textAlign: 'center', color: '#a1a1aa' }}>
                  {leaderboardTab === 'sales' ? 'Total Sales' : 'Total Revenue'}
                </th>
                <th style={{ padding: 15, textAlign: 'center', color: '#a1a1aa' }}>Protocols</th>
                <th style={{ padding: 15, textAlign: 'center', color: '#a1a1aa' }}>Badge</th>
              </tr>
            </thead>
            <tbody>
              {(leaderboardTab === 'sales' ? leaderboard.sales : leaderboard.revenue).map((seller, i) => (
                <tr 
                  key={i}
                  style={{ 
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    background: i < 3 ? `rgba(${i === 0 ? '255,215,0' : i === 1 ? '192,192,192' : '205,127,50'},0.1)` : 'transparent'
                  }}
                >
                  <td style={{ padding: 15, color: '#fff' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 35,
                      height: 35,
                      borderRadius: '50%',
                      background: i === 0 ? 'linear-gradient(135deg, #ffd700 0%, #ffb700 100%)' :
                                 i === 1 ? 'linear-gradient(135deg, #c0c0c0 0%, #a8a8a8 100%)' :
                                 i === 2 ? 'linear-gradient(135deg, #cd7f32 0%, #b87333 100%)' :
                                 'rgba(255,255,255,0.1)',
                      fontWeight: 700,
                      color: i < 3 ? '#000' : '#fff'
                    }}>
                      {seller.rank}
                    </span>
                  </td>
                  <td style={{ padding: 15, color: '#fff', fontWeight: 600 }}>
                    {seller.creator_name}
                  </td>
                  <td style={{ padding: 15, color: '#f59e0b' }}>
                    {seller.title}
                  </td>
                  <td style={{ padding: 15, textAlign: 'center', color: '#10b981', fontWeight: 700 }}>
                    {leaderboardTab === 'sales' 
                      ? seller.total_sales 
                      : `$${seller.total_revenue?.toFixed(2)}`
                    }
                  </td>
                  <td style={{ padding: 15, textAlign: 'center', color: '#8b5cf6' }}>
                    {seller.protocol_count}
                  </td>
                  <td style={{ padding: 15, textAlign: 'center', fontSize: '1.5rem' }}>
                    {seller.badge}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(leaderboardTab === 'sales' ? leaderboard.sales : leaderboard.revenue).length === 0 && (
          <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
            <div style={{ fontSize: '3rem', marginBottom: 15 }}>🏆</div>
            <p>Be the first to claim the throne! Start selling protocols now!</p>
          </div>
        )}
      </div>

      {/* Book Promo */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
        borderRadius: 20,
        padding: 30,
        border: '1px solid rgba(236, 72, 153, 0.3)',
        textAlign: 'center'
      }}>
        <h3 style={{ color: '#f472b6', marginBottom: 15, fontSize: '1.5rem' }}>
          📚 Speaking of Statistics...
        </h3>
        <p style={{ color: '#fff', fontSize: '1.1rem', marginBottom: 15, maxWidth: 600, margin: '0 auto 15px' }}>
          Did you know that &quot;Letters to Evelyn&quot; by John Selman has been read by approximately{' '}
          <span style={{ color: '#f59e0b', fontWeight: 700 }}>∞</span> ghosts? 
          (Source: The ghosts themselves, during a séance that got WAY out of hand)
        </p>
        <p style={{ color: '#a1a1aa', marginBottom: 20, fontStyle: 'italic' }}>
          &quot;A supernatural thriller comedy that&apos;s funnier than your accountant explaining 
          tax deductions during an audit!&quot; - Totally Real Book Review
        </p>
        <button 
          onClick={() => window.open('https://www.amazon.com/dp/B0DC735Q4W', '_blank')}
          style={{
            background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
            color: '#fff',
            border: 'none',
            padding: '15px 40px',
            borderRadius: 30,
            fontWeight: 700,
            fontSize: '1.1rem',
            cursor: 'pointer'
          }}
        >
          📖 Get &quot;Letters to Evelyn&quot; - Only $2.99!
        </button>
        <p style={{ color: '#10b981', marginTop: 15, fontSize: '0.9rem' }}>
          💡 Plot twist: The book costs less than your morning coffee but lasts WAY longer!
        </p>
      </div>
    </div>
  );
};

export default StatisticsPage;
