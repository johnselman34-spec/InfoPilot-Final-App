import React from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#6366f1', '#14b8a6', '#f97316'];

/**
 * Stats Summary Cards Component
 */
export const StatsSummaryCards = ({ stats }) => {
  if (!stats) return null;

  const cards = [
    { label: 'Total Searches', value: stats.total_searches || 0, icon: '🔍', color: '#8b5cf6' },
    { label: 'Total Categories', value: stats.total_categories || 0, icon: '📂', color: '#3b82f6' },
    { label: 'Results Found', value: stats.total_results || 0, icon: '📊', color: '#10b981' },
    { label: 'Active Users', value: stats.active_users || 0, icon: '👥', color: '#f59e0b' },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
      gap: 15,
      marginBottom: 25
    }}>
      {cards.map((card, i) => (
        <div key={i} style={{
          background: `linear-gradient(135deg, ${card.color}20, ${card.color}10)`,
          borderRadius: 16,
          padding: 20,
          border: `1px solid ${card.color}30`,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', marginBottom: 8 }}>{card.icon}</div>
          <div style={{ color: card.color, fontSize: '2rem', fontWeight: 700 }}>
            {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.85rem', marginTop: 5 }}>
            {card.label}
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Country Distribution Chart
 */
export const CountryChart = ({ data, title = "Results by Country" }) => {
  if (!data || data.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: 30, 
        color: '#a1a1aa' 
      }}>
        <p>No country data available</p>
      </div>
    );
  }

  return (
    <div style={{
      background: 'rgba(0,0,0,0.2)',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(255,255,255,0.1)'
    }}>
      <h3 style={{ color: '#fff', marginBottom: 20, fontSize: '1.1rem' }}>
        🌍 {title}
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data.slice(0, 10)} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis type="number" stroke="#71717a" tick={{ fill: '#71717a', fontSize: 11 }} />
          <YAxis 
            type="category" 
            dataKey="name" 
            stroke="#71717a" 
            tick={{ fill: '#fff', fontSize: 11 }}
            width={100}
          />
          <Tooltip 
            contentStyle={{ 
              background: 'rgba(0,0,0,0.9)', 
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8
            }}
          />
          <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * Document Types Pie Chart
 */
export const DocumentTypesChart = ({ data, title = "Document Types" }) => {
  if (!data || data.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: 30, 
        color: '#a1a1aa' 
      }}>
        <p>No document type data available</p>
      </div>
    );
  }

  return (
    <div style={{
      background: 'rgba(0,0,0,0.2)',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(255,255,255,0.1)'
    }}>
      <h3 style={{ color: '#fff', marginBottom: 20, fontSize: '1.1rem' }}>
        📄 {title}
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={100}
            dataKey="count"
            nameKey="name"
            label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ 
              background: 'rgba(0,0,0,0.9)', 
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * Top Words Bar Chart
 */
export const TopWordsChart = ({ data, title = "Top 10 Words in Protocols" }) => {
  if (!data || data.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: 30, 
        color: '#a1a1aa' 
      }}>
        <p>No word frequency data available</p>
      </div>
    );
  }

  return (
    <div style={{
      background: 'rgba(0,0,0,0.2)',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(255,255,255,0.1)'
    }}>
      <h3 style={{ color: '#fff', marginBottom: 20, fontSize: '1.1rem' }}>
        📝 {title}
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data.slice(0, 10)}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis 
            dataKey="word" 
            stroke="#71717a" 
            tick={{ fill: '#fff', fontSize: 10, angle: -45 }}
            textAnchor="end"
            height={60}
          />
          <YAxis stroke="#71717a" tick={{ fill: '#71717a', fontSize: 11 }} />
          <Tooltip 
            contentStyle={{ 
              background: 'rgba(0,0,0,0.9)', 
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8
            }}
          />
          <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * Leaderboard Component
 */
export const Leaderboard = ({ 
  data, 
  title, 
  valueLabel = "Value",
  icon = "🏆",
  color = "#fbbf24"
}) => {
  if (!data || data.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: 30, 
        color: '#a1a1aa' 
      }}>
        <p>No data yet</p>
      </div>
    );
  }

  return (
    <div style={{
      background: 'rgba(0,0,0,0.2)',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(255,255,255,0.1)'
    }}>
      <h3 style={{ color: '#fff', marginBottom: 20, fontSize: '1.1rem' }}>
        {icon} {title}
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {data.slice(0, 10).map((item, i) => (
          <div 
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: i < 3 
                ? `linear-gradient(90deg, ${i === 0 ? '#fbbf24' : i === 1 ? '#9ca3af' : '#cd7f32'}15, transparent)`
                : 'rgba(255,255,255,0.03)',
              padding: '12px 15px',
              borderRadius: 10
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                background: i === 0 ? '#fbbf24' : i === 1 ? '#9ca3af' : i === 2 ? '#cd7f32' : 'rgba(255,255,255,0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.8rem',
                fontWeight: 700,
                color: i < 3 ? '#000' : '#fff'
              }}>
                {i + 1}
              </span>
              <span style={{ color: '#fff', fontSize: '0.95rem' }}>
                {item.name || item.username || item.title || `User ${i + 1}`}
              </span>
            </div>
            <span style={{ 
              color: color, 
              fontWeight: 600,
              fontSize: '0.95rem'
            }}>
              {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
              {item.unit && ` ${item.unit}`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
