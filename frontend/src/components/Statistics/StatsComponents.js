import React from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#ec4899', '#14b8a6', '#f97316'];

/**
 * StatsGrid - Quick statistics cards grid
 */
export const StatsGrid = ({ stats }) => {
  const quickStats = [
    { label: 'Total Users', value: stats?.total_users || 0, icon: '👥', color: '#8b5cf6' },
    { label: 'Active (7d)', value: stats?.active_users_7d || 0, icon: '🔥', color: '#ef4444' },
    { label: 'Protocols', value: stats?.total_protocols || 0, icon: '📋', color: '#10b981' },
    { label: 'Searches', value: stats?.total_searches || 0, icon: '🔍', color: '#3b82f6' },
    { label: 'Purchases', value: stats?.total_purchases || 0, icon: '💰', color: '#f59e0b' },
    { label: 'Revenue', value: `$${(stats?.total_revenue || 0).toFixed(2)}`, icon: '💎', color: '#ec4899' }
  ];

  return (
    <div className="card" style={{ marginBottom: 25 }}>
      <h3 style={{ color: '#f472b6', marginBottom: 20 }}>⚡ Quick Stats</h3>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
        gap: 15 
      }}>
        {quickStats.map((stat, idx) => (
          <div key={idx} style={{
            background: 'rgba(30, 20, 50, 0.5)',
            borderRadius: 12,
            padding: 20,
            textAlign: 'center',
            border: `1px solid ${stat.color}30`
          }}>
            <div style={{ fontSize: '2rem', marginBottom: 10 }}>{stat.icon}</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: stat.color }}>
              {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
            </div>
            <div style={{ fontSize: '0.85rem', color: '#a1a1aa', marginTop: 5 }}>
              {stat.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * CountryPieChart - Countries distribution pie chart
 */
export const CountryPieChart = ({ data, onSelect }) => {
  const chartData = (data || []).map((item, idx) => ({
    name: item.name || `Country ${idx + 1}`,
    value: item.value || item.searches || 0
  }));

  return (
    <div className="card" style={{ marginBottom: 25 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
        <h3 style={{ color: '#f472b6', margin: 0 }}>🌍 By Country</h3>
        <button
          className="btn btn-secondary"
          onClick={() => onSelect('countries', data)}
          style={{ padding: '6px 12px', fontSize: '0.8rem' }}
        >
          📍 Show on Map
        </button>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * USStatesBarChart - US States bar chart
 */
export const USStatesBarChart = ({ data, onSelect }) => {
  const chartData = (data || []).slice(0, 10).map((item) => ({
    name: item.name?.length > 10 ? item.name.substring(0, 10) + '...' : item.name,
    fullName: item.name,
    value: item.value || item.searches || 0
  }));

  return (
    <div className="card" style={{ marginBottom: 25 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
        <h3 style={{ color: '#f472b6', margin: 0 }}>🇺🇸 Top US States</h3>
        <button
          className="btn btn-secondary"
          onClick={() => onSelect('us_states', data)}
          style={{ padding: '6px 12px', fontSize: '0.8rem' }}
        >
          📍 Show on Map
        </button>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 60, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis type="number" stroke="#888" />
          <YAxis dataKey="name" type="category" stroke="#888" width={80} />
          <Tooltip 
            contentStyle={{ background: '#1e1b4b', border: '1px solid #7c3aed', borderRadius: 8 }}
            formatter={(value, name, props) => [value, props.payload.fullName]}
          />
          <Bar dataKey="value" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
      {data?.some(s => s.name === 'Maine') && (
        <p style={{ color: '#10b981', fontSize: '0.85rem', marginTop: 10, textAlign: 'center' }}>
          🦞 Maine representing! Home of Maestro Bistro's famous Beef Rouladen!
        </p>
      )}
    </div>
  );
};

/**
 * DocumentTypesChart - Document types donut chart
 */
export const DocumentTypesChart = ({ data }) => {
  const chartData = Object.entries(data || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="card" style={{ marginBottom: 25 }}>
      <h3 style={{ color: '#f472b6', marginBottom: 15 }}>📄 Document Types</h3>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            fill="#8884d8"
            paddingAngle={5}
            dataKey="value"
            label={({ name }) => name}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * TopWordsChart - Top words in protocols
 */
export const TopWordsChart = ({ data }) => {
  const chartData = (data || []).slice(0, 10);

  return (
    <div className="card" style={{ marginBottom: 25 }}>
      <h3 style={{ color: '#f472b6', marginBottom: 15 }}>🔤 Top 10 Words in Protocols</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis type="number" stroke="#888" />
          <YAxis dataKey="word" type="category" stroke="#888" width={70} />
          <Tooltip contentStyle={{ background: '#1e1b4b', border: '1px solid #7c3aed', borderRadius: 8 }} />
          <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * PollStatsCard - Poll statistics card
 */
export const PollStatsCard = ({ userStats, adminStats, isAdmin }) => {
  if (!userStats && !adminStats) return null;

  return (
    <div className="card" style={{ marginBottom: 25 }}>
      <h3 style={{ color: '#f472b6', marginBottom: 20 }}>📊 Poll Statistics</h3>
      
      {/* User Stats */}
      {userStats && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ color: '#a78bfa', marginBottom: 15 }}>Your Poll Activity</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10 }}>
            <StatBox label="Created" value={userStats.polls_created || 0} icon="📝" />
            <StatBox label="Voted" value={userStats.polls_voted || 0} icon="🗳️" />
            <StatBox label="Total Votes" value={userStats.total_votes_received || 0} icon="✅" />
          </div>
        </div>
      )}

      {/* Admin Stats */}
      {isAdmin && adminStats && (
        <div style={{ borderTop: '1px solid rgba(124, 58, 237, 0.3)', paddingTop: 20 }}>
          <h4 style={{ color: '#f472b6', marginBottom: 15 }}>📊 Platform Poll Stats (Admin)</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10 }}>
            <StatBox label="Total Polls" value={adminStats.total_polls || 0} icon="📊" color="#8b5cf6" />
            <StatBox label="Active" value={adminStats.active_polls || 0} icon="🟢" color="#10b981" />
            <StatBox label="Total Votes" value={adminStats.total_votes || 0} icon="🗳️" color="#3b82f6" />
            <StatBox label="Avg Votes" value={(adminStats.avg_votes_per_poll || 0).toFixed(1)} icon="📈" color="#f59e0b" />
          </div>
        </div>
      )}
    </div>
  );
};

const StatBox = ({ label, value, icon, color = '#a78bfa' }) => (
  <div style={{
    background: 'rgba(30, 20, 50, 0.5)',
    borderRadius: 10,
    padding: 15,
    textAlign: 'center'
  }}>
    <div style={{ fontSize: '1.5rem', marginBottom: 5 }}>{icon}</div>
    <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color }}>{value}</div>
    <div style={{ fontSize: '0.75rem', color: '#a1a1aa' }}>{label}</div>
  </div>
);
