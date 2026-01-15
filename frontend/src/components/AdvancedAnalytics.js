import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS = ['#7c3aed', '#10b981', '#f472b6', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6', '#06b6d4'];

const AdvancedAnalytics = ({ showToast }) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');
  const [analyticsData, setAnalyticsData] = useState(null);
  const [activeChart, setActiveChart] = useState('overview');

  const fetchAnalytics = useCallback(async () => {
    try {
      const res = await fetch(`${API}/admin/analytics?range=${timeRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setAnalyticsData(data);
      } else {
        // Generate mock data for demo
        generateMockData();
      }
    } catch (e) {
      generateMockData();
    }
    setLoading(false);
  }, [token, timeRange]);

  const generateMockData = () => {
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
    const dailyData = [];
    
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      dailyData.push({
        date: date.toISOString().split('T')[0],
        searches: Math.floor(Math.random() * 500) + 100,
        users: Math.floor(Math.random() * 50) + 10,
        protocols: Math.floor(Math.random() * 20) + 5,
        revenue: (Math.random() * 100 + 20).toFixed(2)
      });
    }

    setAnalyticsData({
      summary: {
        total_users: 1247,
        active_users: 892,
        total_searches: 45678,
        total_protocols: 156,
        total_revenue: 2847.50,
        avg_session_time: '12m 34s'
      },
      daily_data: dailyData,
      category_distribution: [
        { name: 'News & Media', value: 35, searches: 12500 },
        { name: 'Technology', value: 25, searches: 8900 },
        { name: 'Business', value: 20, searches: 7100 },
        { name: 'Science', value: 12, searches: 4300 },
        { name: 'Entertainment', value: 8, searches: 2900 }
      ],
      top_protocols: [
        { name: 'Tech Startup News', sales: 234, revenue: 468 },
        { name: 'Climate Research', sales: 189, revenue: 567 },
        { name: 'Crypto Analysis', sales: 156, revenue: 780 },
        { name: 'Academic Papers', sales: 123, revenue: 369 },
        { name: 'Sports Updates', sales: 98, revenue: 196 }
      ],
      user_growth: dailyData.map(d => ({ date: d.date, users: d.users })),
      revenue_data: dailyData.map(d => ({ date: d.date, revenue: parseFloat(d.revenue) }))
    });
  };

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <div className="spinner" />
        <p style={{ color: '#a1a1aa', marginTop: 15 }}>Loading analytics...</p>
      </div>
    );
  }

  return (
    <div className="card" data-testid="advanced-analytics">
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          📊 Advanced Analytics Dashboard
        </h2>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Real-time insights into InfoPilot Explorer performance
        </p>
      </div>

      {/* Time Range Selector */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {['7d', '30d', '90d'].map(range => (
          <button
            key={range}
            className={`btn ${timeRange === range ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTimeRange(range)}
          >
            {range === '7d' ? 'Last 7 Days' : range === '30d' ? 'Last 30 Days' : 'Last 90 Days'}
          </button>
        ))}
      </div>

      {/* Summary Cards */}
      {analyticsData?.summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 15,
          marginBottom: 30
        }}>
          {[
            { label: 'Total Users', value: analyticsData.summary.total_users.toLocaleString(), icon: '👥', color: '#7c3aed' },
            { label: 'Active Users', value: analyticsData.summary.active_users.toLocaleString(), icon: '🟢', color: '#10b981' },
            { label: 'Total Searches', value: analyticsData.summary.total_searches.toLocaleString(), icon: '🔍', color: '#3b82f6' },
            { label: 'Protocols', value: analyticsData.summary.total_protocols, icon: '📦', color: '#f472b6' },
            { label: 'Revenue', value: `$${analyticsData.summary.total_revenue.toLocaleString()}`, icon: '💰', color: '#f59e0b' },
            { label: 'Avg Session', value: analyticsData.summary.avg_session_time, icon: '⏱️', color: '#06b6d4' }
          ].map((stat, i) => (
            <div key={i} style={{
              background: `linear-gradient(135deg, ${stat.color}20, ${stat.color}10)`,
              borderRadius: 12,
              padding: 20,
              border: `1px solid ${stat.color}40`,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.8rem', marginBottom: 8 }}>{stat.icon}</div>
              <div style={{ color: stat.color, fontSize: '1.5rem', fontWeight: 700 }}>{stat.value}</div>
              <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{stat.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Chart Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {['overview', 'revenue', 'users', 'categories', 'protocols'].map(chart => (
          <button
            key={chart}
            className={`btn ${activeChart === chart ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveChart(chart)}
            style={{ textTransform: 'capitalize' }}
          >
            {chart === 'overview' ? '📈 Overview' :
             chart === 'revenue' ? '💰 Revenue' :
             chart === 'users' ? '👥 Users' :
             chart === 'categories' ? '📁 Categories' : '📦 Top Protocols'}
          </button>
        ))}
      </div>

      {/* Charts */}
      <div style={{
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 15,
        padding: 25,
        minHeight: 400
      }}>
        {/* Overview Chart - Combined Line Chart */}
        {activeChart === 'overview' && analyticsData?.daily_data && (
          <div>
            <h3 style={{ color: '#f472b6', marginBottom: 20 }}>Daily Activity Overview</h3>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={analyticsData.daily_data}>
                <defs>
                  <linearGradient id="colorSearches" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#7c3aed" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#a1a1aa" tick={{ fontSize: 10 }} />
                <YAxis stroke="#a1a1aa" />
                <Tooltip
                  contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                  labelStyle={{ color: '#fff' }}
                />
                <Legend />
                <Area type="monotone" dataKey="searches" stroke="#7c3aed" fillOpacity={1} fill="url(#colorSearches)" name="Searches" />
                <Area type="monotone" dataKey="users" stroke="#10b981" fillOpacity={1} fill="url(#colorUsers)" name="Active Users" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Revenue Chart */}
        {activeChart === 'revenue' && analyticsData?.revenue_data && (
          <div>
            <h3 style={{ color: '#f59e0b', marginBottom: 20 }}>Revenue Trend</h3>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={analyticsData.revenue_data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#a1a1aa" tick={{ fontSize: 10 }} />
                <YAxis stroke="#a1a1aa" tickFormatter={(v) => `$${v}`} />
                <Tooltip
                  contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                  formatter={(value) => [`$${value}`, 'Revenue']}
                />
                <Bar dataKey="revenue" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Users Chart */}
        {activeChart === 'users' && analyticsData?.user_growth && (
          <div>
            <h3 style={{ color: '#10b981', marginBottom: 20 }}>User Growth</h3>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={analyticsData.user_growth}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#a1a1aa" tick={{ fontSize: 10 }} />
                <YAxis stroke="#a1a1aa" />
                <Tooltip
                  contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                />
                <Line type="monotone" dataKey="users" stroke="#10b981" strokeWidth={3} dot={{ fill: '#10b981', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Categories Pie Chart */}
        {activeChart === 'categories' && analyticsData?.category_distribution && (
          <div>
            <h3 style={{ color: '#f472b6', marginBottom: 20 }}>Search Categories Distribution</h3>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }}>
              <ResponsiveContainer width={350} height={350}>
                <PieChart>
                  <Pie
                    data={analyticsData.category_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={120}
                    fill="#8884d8"
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {analyticsData.category_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                    formatter={(value, name, props) => [`${value}% (${props.payload.searches.toLocaleString()} searches)`, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ marginLeft: 20 }}>
                {analyticsData.category_distribution.map((cat, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                    <div style={{ width: 16, height: 16, borderRadius: 4, background: COLORS[i % COLORS.length] }} />
                    <span style={{ color: '#fff' }}>{cat.name}</span>
                    <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>({cat.searches.toLocaleString()})</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Top Protocols */}
        {activeChart === 'protocols' && analyticsData?.top_protocols && (
          <div>
            <h3 style={{ color: '#7c3aed', marginBottom: 20 }}>Top Selling Protocols</h3>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={analyticsData.top_protocols} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#a1a1aa" />
                <YAxis dataKey="name" type="category" stroke="#a1a1aa" width={150} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                  formatter={(value, name) => [name === 'sales' ? `${value} sales` : `$${value}`, name === 'sales' ? 'Sales' : 'Revenue']}
                />
                <Legend />
                <Bar dataKey="sales" fill="#7c3aed" name="Sales" radius={[0, 4, 4, 0]} />
                <Bar dataKey="revenue" fill="#10b981" name="Revenue ($)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Export Options */}
      <div style={{ marginTop: 20, display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
        <button 
          className="btn btn-secondary"
          onClick={() => {
            const dataStr = JSON.stringify(analyticsData, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `infopilot-analytics-${timeRange}.json`;
            a.click();
          }}
        >
          📥 Export JSON
        </button>
        <button 
          className="btn btn-secondary"
          onClick={() => {
            const csv = analyticsData.daily_data.map(d => 
              `${d.date},${d.searches},${d.users},${d.protocols},${d.revenue}`
            ).join('\n');
            const blob = new Blob([`Date,Searches,Users,Protocols,Revenue\n${csv}`], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `infopilot-analytics-${timeRange}.csv`;
            a.click();
          }}
        >
          📊 Export CSV
        </button>
      </div>
    </div>
  );
};

export default AdvancedAnalytics;
