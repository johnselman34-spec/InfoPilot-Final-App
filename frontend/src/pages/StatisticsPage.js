import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { PieChart, Pie, Cell, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';

// Fix for leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Funny marketing messages
const FUNNY_STATS_MESSAGES = [
  "📊 These statistics are so accurate, even your math teacher would be impressed!",
  "🎯 Data so hot, it's practically on fire! 🔥",
  "💡 Warning: Viewing these stats may cause sudden urges to buy protocols!",
  "🚀 Our numbers go up like Richard J. Selman's A-4 Skyhawk - FAST!",
  "📈 These charts are more exciting than a supernatural thriller! (Speaking of which...)",
];

const COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#ec4899', '#14b8a6', '#f97316'];

// US State coordinates for the map
const STATE_COORDINATES = {
  'Alabama': [32.806671, -86.791130], 'Alaska': [61.370716, -152.404419],
  'Arizona': [33.729759, -111.431221], 'Arkansas': [34.969704, -92.373123],
  'California': [36.116203, -119.681564], 'Colorado': [39.059811, -105.311104],
  'Connecticut': [41.597782, -72.755371], 'Delaware': [39.318523, -75.507141],
  'Florida': [27.766279, -81.686783], 'Georgia': [33.040619, -83.643074],
  'Hawaii': [21.094318, -157.498337], 'Idaho': [44.240459, -114.478828],
  'Illinois': [40.349457, -88.986137], 'Indiana': [39.849426, -86.258278],
  'Iowa': [42.011539, -93.210526], 'Kansas': [38.526600, -96.726486],
  'Kentucky': [37.668140, -84.670067], 'Louisiana': [31.169546, -91.867805],
  'Maine': [44.693947, -69.381927], 'Maryland': [39.063946, -76.802101],
  'Massachusetts': [42.230171, -71.530106], 'Michigan': [43.326618, -84.536095],
  'Minnesota': [45.694454, -93.900192], 'Mississippi': [32.741646, -89.678696],
  'Missouri': [38.456085, -92.288368], 'Montana': [46.921925, -110.454353],
  'Nebraska': [41.125370, -98.268082], 'Nevada': [38.313515, -117.055374],
  'New Hampshire': [43.452492, -71.563896], 'New Jersey': [40.298904, -74.521011],
  'New Mexico': [34.840515, -106.248482], 'New York': [42.165726, -74.948051],
  'North Carolina': [35.630066, -79.806419], 'North Dakota': [47.528912, -99.784012],
  'Ohio': [40.388783, -82.764915], 'Oklahoma': [35.565342, -96.928917],
  'Oregon': [44.572021, -122.070938], 'Pennsylvania': [40.590752, -77.209755],
  'Rhode Island': [41.680893, -71.511780], 'South Carolina': [33.856892, -80.945007],
  'South Dakota': [44.299782, -99.438828], 'Tennessee': [35.747845, -86.692345],
  'Texas': [31.054487, -97.563461], 'Utah': [40.150032, -111.862434],
  'Vermont': [44.045876, -72.710686], 'Virginia': [37.769337, -78.169968],
  'Washington': [47.400902, -121.490494], 'West Virginia': [38.491226, -80.954456],
  'Wisconsin': [44.268543, -89.616508], 'Wyoming': [42.755966, -107.302490]
};

// Country coordinates
const COUNTRY_COORDINATES = {
  'United States': [39.8283, -98.5795], 'Canada': [56.1304, -106.3468],
  'United Kingdom': [55.3781, -3.4360], 'Germany': [51.1657, 10.4515],
  'France': [46.2276, 2.2137], 'Japan': [36.2048, 138.2529],
  'Australia': [-25.2744, 133.7751], 'Brazil': [-14.2350, -51.9253],
  'India': [20.5937, 78.9629], 'China': [35.8617, 104.1954]
};

const StatisticsPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [leaderboard, setLeaderboard] = useState({ sales: [], revenue: [] });
  const [mostCopied, setMostCopied] = useState({ leaderboard: [], stats: {} });
  const [pollStats, setPollStats] = useState(null);
  const [userPollStats, setUserPollStats] = useState(null);
  const [leaderboardTab, setLeaderboardTab] = useState('sales');
  const [loading, setLoading] = useState(true);
  const [funnyMessage] = useState(() => FUNNY_STATS_MESSAGES[Math.floor(Math.random() * FUNNY_STATS_MESSAGES.length)]);
  const [mapMarkers, setMapMarkers] = useState([]);
  const [selectedStatType, setSelectedStatType] = useState(null);

  useEffect(() => {
    fetchStatistics();
    fetchLeaderboards();
    fetchMostCopied();
    fetchPollStatistics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchPollStatistics = async () => {
    try {
      // Fetch user's poll statistics (everyone has access)
      if (token) {
        const userRes = await fetch(`${API}/polls/user/statistics`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (userRes.ok) {
          const userData = await userRes.json();
          setUserPollStats(userData);
        }
      }
      
      // Fetch admin poll statistics if user is admin
      if (user?.is_admin && token) {
        const adminRes = await fetch(`${API}/polls/admin/statistics`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (adminRes.ok) {
          const adminData = await adminRes.json();
          setPollStats(adminData);
        }
      }
    } catch (error) {
      console.error('Failed to fetch poll statistics:', error);
    }
  };

  const fetchMostCopied = async () => {
    try {
      const res = await fetch(`${API}/statistics/most-copied`);
      if (res.ok) {
        const data = await res.json();
        setMostCopied(data);
      }
    } catch (error) {
      console.error('Failed to fetch most copied:', error);
    }
  };

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

  // Populate map markers when a stat is clicked
  const populateMapForStat = (statType, data) => {
    setSelectedStatType(statType);
    const markers = [];
    
    if (statType === 'countries') {
      // Show country markers
      (data || []).forEach((item, idx) => {
        const coords = COUNTRY_COORDINATES[item.name];
        if (coords) {
          markers.push({
            id: `country-${idx}`,
            position: coords,
            label: item.name,
            value: item.value || item.searches || 0,
            color: COLORS[idx % COLORS.length],
            type: 'country'
          });
        }
      });
    } else if (statType === 'us_states') {
      // Show US state markers
      (data || []).forEach((item, idx) => {
        const coords = STATE_COORDINATES[item.name];
        if (coords) {
          markers.push({
            id: `state-${idx}`,
            position: coords,
            label: item.name,
            value: item.value || item.searches || 0,
            color: COLORS[idx % COLORS.length],
            type: 'state'
          });
        }
      });
    } else if (statType === 'top_sellers') {
      // Show top seller locations (simulated across US)
      (data || []).forEach((item, idx) => {
        // Distribute sellers across different states
        const stateNames = Object.keys(STATE_COORDINATES);
        const randomState = stateNames[idx % stateNames.length];
        const coords = STATE_COORDINATES[randomState];
        if (coords) {
          markers.push({
            id: `seller-${idx}`,
            position: [coords[0] + (Math.random() - 0.5) * 2, coords[1] + (Math.random() - 0.5) * 2],
            label: item.username || item.name,
            value: item.total_sales || item.total_revenue || 0,
            color: COLORS[idx % COLORS.length],
            type: 'seller'
          });
        }
      });
    } else if (statType === 'most_copied') {
      // Show most copied protocol locations
      (mostCopied.leaderboard || []).forEach((item, idx) => {
        const stateNames = Object.keys(STATE_COORDINATES);
        const randomState = stateNames[idx % stateNames.length];
        const coords = STATE_COORDINATES[randomState];
        if (coords) {
          markers.push({
            id: `copied-${idx}`,
            position: [coords[0] + (Math.random() - 0.5) * 2, coords[1] + (Math.random() - 0.5) * 2],
            label: item.name,
            value: item.copy_count || 0,
            color: COLORS[idx % COLORS.length],
            type: 'protocol'
          });
        }
      });
    }
    
    setMapMarkers(markers);
  };

  // Create custom marker icon
  const createStatMarker = (color, size = 20) => L.divIcon({
    className: 'custom-stat-marker',
    html: `<div style="
      background: ${color};
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      border: 2px solid white;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
    popupAnchor: [0, -size/2],
  });

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

      {/* Most Copied Protocols Leaderboard */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
        borderRadius: 20,
        padding: 30,
        marginBottom: 30,
        border: '1px solid rgba(16, 185, 129, 0.3)'
      }}>
        <h2 style={{ 
          color: '#fff', 
          marginBottom: 10,
          display: 'flex',
          alignItems: 'center',
          gap: 15
        }}>
          📋 Most Copied Protocols
          <span style={{
            background: 'linear-gradient(135deg, #10b981 0%, #3b82f6 100%)',
            padding: '5px 15px',
            borderRadius: 20,
            fontSize: '0.8rem',
            fontWeight: 600
          }}>
            HOT 🔥
          </span>
        </h2>
        <p style={{ color: '#71717a', marginBottom: 20, fontSize: '0.9rem' }}>
          {mostCopied.funny_message || "These protocols are spreading faster than memes!"}
        </p>

        {/* Stats Bar */}
        <div style={{ 
          display: 'flex', 
          gap: 20, 
          marginBottom: 20,
          flexWrap: 'wrap'
        }}>
          <div style={{ 
            background: 'rgba(16, 185, 129, 0.2)', 
            padding: '10px 20px', 
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 10
          }}>
            <span style={{ color: '#10b981', fontWeight: 700, fontSize: '1.2rem' }}>
              {mostCopied.stats?.total_copies || 0}
            </span>
            <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Total Copies</span>
          </div>
          <div style={{ 
            background: 'rgba(59, 130, 246, 0.2)', 
            padding: '10px 20px', 
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 10
          }}>
            <span style={{ color: '#3b82f6', fontWeight: 700, fontSize: '1.2rem' }}>
              {mostCopied.stats?.free_percentage || 0}%
            </span>
            <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Free Protocol Copies</span>
          </div>
        </div>

        {/* Leaderboard Grid */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', 
          gap: 15 
        }}>
          {(mostCopied.leaderboard || []).slice(0, 10).map((protocol, i) => (
            <div 
              key={protocol.id || i}
              style={{
                background: i < 3 
                  ? `linear-gradient(135deg, ${i === 0 ? 'rgba(255,215,0,0.2)' : i === 1 ? 'rgba(192,192,192,0.2)' : 'rgba(205,127,50,0.2)'} 0%, rgba(30,20,50,0.5) 100%)`
                  : 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                padding: 15,
                border: `1px solid ${i === 0 ? '#ffd700' : i === 1 ? '#c0c0c0' : i === 2 ? '#cd7f32' : 'rgba(255,255,255,0.1)'}`,
                display: 'flex',
                alignItems: 'center',
                gap: 12
              }}
            >
              {/* Rank Badge */}
              <div style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                background: i === 0 ? 'linear-gradient(135deg, #ffd700, #ffb700)' :
                           i === 1 ? 'linear-gradient(135deg, #c0c0c0, #a8a8a8)' :
                           i === 2 ? 'linear-gradient(135deg, #cd7f32, #b87333)' :
                           'rgba(124, 58, 237, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                color: i < 3 ? '#000' : '#fff',
                fontSize: '1.1rem',
                flexShrink: 0
              }}>
                {protocol.rank}
              </div>
              
              {/* Protocol Info */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 6,
                  marginBottom: 4
                }}>
                  <span style={{ 
                    color: '#f472b6', 
                    fontWeight: 600,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {protocol.name}
                  </span>
                  {protocol.trend && (
                    <span style={{ fontSize: '0.9rem' }}>{protocol.trend}</span>
                  )}
                </div>
                <div style={{ 
                  display: 'flex', 
                  gap: 8, 
                  alignItems: 'center',
                  fontSize: '0.75rem',
                  color: '#71717a'
                }}>
                  <span style={{
                    background: protocol.is_free ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                    color: protocol.is_free ? '#10b981' : '#f59e0b',
                    padding: '2px 6px',
                    borderRadius: 4
                  }}>
                    {protocol.is_free ? '🆓 FREE' : `$${protocol.price?.toFixed(2)}`}
                  </span>
                  <span>{protocol.category}</span>
                </div>
              </div>
              
              {/* Copy Count */}
              <div style={{ 
                textAlign: 'right',
                flexShrink: 0
              }}>
                <div style={{ color: '#10b981', fontWeight: 700, fontSize: '1.1rem' }}>
                  {protocol.copy_count}
                </div>
                <div style={{ color: '#71717a', fontSize: '0.7rem' }}>copies</div>
              </div>
            </div>
          ))}
        </div>

        {(!mostCopied.leaderboard || mostCopied.leaderboard.length === 0) && (
          <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
            <div style={{ fontSize: '3rem', marginBottom: 15 }}>📋</div>
            <p>No copied protocols yet. Be the first to create a viral protocol!</p>
          </div>
        )}
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

      {/* Interactive Statistics Map */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
        borderRadius: 20,
        padding: 30,
        marginBottom: 30,
        border: '1px solid rgba(59, 130, 246, 0.3)'
      }}>
        <h2 style={{ 
          color: '#fff', 
          marginBottom: 15,
          display: 'flex',
          alignItems: 'center',
          gap: 15
        }}>
          🗺️ Statistics Map
          <span style={{
            background: 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)',
            padding: '5px 15px',
            borderRadius: 20,
            fontSize: '0.8rem',
            fontWeight: 600
          }}>
            INTERACTIVE
          </span>
        </h2>
        <p style={{ color: '#a1a1aa', marginBottom: 20, fontSize: '0.9rem' }}>
          Click on any statistic below to visualize it on the map!
        </p>

        {/* Stat Type Buttons */}
        <div style={{ 
          display: 'flex', 
          gap: 10, 
          marginBottom: 20,
          flexWrap: 'wrap'
        }}>
          <button
            onClick={() => populateMapForStat('countries', stats?.countries?.data)}
            style={{
              padding: '10px 20px',
              borderRadius: 25,
              border: 'none',
              background: selectedStatType === 'countries' 
                ? 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)' 
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              cursor: 'pointer',
              fontWeight: 600
            }}
            data-testid="map-countries-btn"
          >
            🌍 Countries
          </button>
          <button
            onClick={() => populateMapForStat('us_states', stats?.us_states?.data)}
            style={{
              padding: '10px 20px',
              borderRadius: 25,
              border: 'none',
              background: selectedStatType === 'us_states' 
                ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' 
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              cursor: 'pointer',
              fontWeight: 600
            }}
            data-testid="map-states-btn"
          >
            🇺🇸 US States
          </button>
          <button
            onClick={() => populateMapForStat('top_sellers', leaderboard.sales)}
            style={{
              padding: '10px 20px',
              borderRadius: 25,
              border: 'none',
              background: selectedStatType === 'top_sellers' 
                ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' 
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              cursor: 'pointer',
              fontWeight: 600
            }}
            data-testid="map-sellers-btn"
          >
            🏆 Top Sellers
          </button>
          <button
            onClick={() => populateMapForStat('most_copied', mostCopied.leaderboard)}
            style={{
              padding: '10px 20px',
              borderRadius: 25,
              border: 'none',
              background: selectedStatType === 'most_copied' 
                ? 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' 
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              cursor: 'pointer',
              fontWeight: 600
            }}
            data-testid="map-copied-btn"
          >
            📋 Most Copied
          </button>
        </div>

        {/* Map Container */}
        <div style={{
          height: 400,
          borderRadius: 15,
          overflow: 'hidden',
          border: '2px solid rgba(59, 130, 246, 0.3)'
        }}>
          <MapContainer
            center={[39.8283, -98.5795]}
            zoom={4}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />
            
            {mapMarkers.map((marker) => (
              <React.Fragment key={marker.id}>
                <Marker 
                  position={marker.position}
                  icon={createStatMarker(marker.color, marker.type === 'country' ? 30 : 24)}
                >
                  <Popup>
                    <div style={{ textAlign: 'center', minWidth: 120 }}>
                      <strong style={{ color: marker.color }}>{marker.label}</strong>
                      <br />
                      <span style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                        {marker.type === 'seller' ? '$' : ''}{marker.value.toLocaleString()}
                      </span>
                      <br />
                      <small style={{ color: '#666' }}>
                        {marker.type === 'country' ? 'searches' : 
                         marker.type === 'state' ? 'searches' :
                         marker.type === 'seller' ? 'revenue' : 'copies'}
                      </small>
                    </div>
                  </Popup>
                </Marker>
                <Circle
                  center={marker.position}
                  radius={Math.max(50000, marker.value * 1000)}
                  pathOptions={{
                    color: marker.color,
                    fillColor: marker.color,
                    fillOpacity: 0.2
                  }}
                />
              </React.Fragment>
            ))}
          </MapContainer>
        </div>

        {mapMarkers.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            padding: 20, 
            color: '#a1a1aa',
            marginTop: 15
          }}>
            <p>👆 Click a button above to populate the map with statistics!</p>
          </div>
        )}

        {mapMarkers.length > 0 && (
          <div style={{ 
            marginTop: 15, 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            color: '#a1a1aa',
            fontSize: '0.85rem'
          }}>
            <span>Showing {mapMarkers.length} data points for {selectedStatType?.replace('_', ' ')}</span>
            <button
              onClick={() => { setMapMarkers([]); setSelectedStatType(null); }}
              style={{
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#ef4444',
                padding: '5px 15px',
                borderRadius: 15,
                cursor: 'pointer',
                fontSize: '0.8rem'
              }}
            >
              Clear Map
            </button>
          </div>
        )}
      </div>

      {/* Poll Statistics Section - Clean & Non-Intrusive */}
      {(userPollStats || pollStats) && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
          borderRadius: 20,
          padding: 25,
          marginBottom: 30,
          border: '1px solid rgba(59, 130, 246, 0.2)'
        }} data-testid="poll-statistics-section">
          <h2 style={{ 
            color: '#fff', 
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            📊 Poll Insights
            <span style={{
              background: 'rgba(16, 185, 129, 0.2)',
              padding: '4px 12px',
              borderRadius: 15,
              fontSize: '0.7rem',
              fontWeight: 600,
              color: '#10b981'
            }}>
              COMMUNITY
            </span>
          </h2>

          {/* User's Poll Stats */}
          {userPollStats && (
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ color: '#a78bfa', fontSize: '1rem', marginBottom: 12 }}>Your Poll Activity</h3>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: 12
              }}>
                {[
                  { label: 'Polls Created', value: userPollStats.polls_created, icon: '📝', color: '#8b5cf6' },
                  { label: 'Active Now', value: userPollStats.active_polls, icon: '🟢', color: '#10b981' },
                  { label: 'Votes Received', value: userPollStats.total_votes_received, icon: '✅', color: '#3b82f6' },
                  { label: 'Polls Voted', value: userPollStats.polls_voted_on, icon: '🗳️', color: '#f59e0b' },
                ].map((stat, i) => (
                  <div key={i} style={{
                    background: 'rgba(0,0,0,0.2)',
                    borderRadius: 12,
                    padding: '12px 15px',
                    textAlign: 'center',
                    border: `1px solid ${stat.color}20`
                  }}>
                    <div style={{ fontSize: '1.3rem', marginBottom: 4 }}>{stat.icon}</div>
                    <div style={{ color: stat.color, fontSize: '1.4rem', fontWeight: 700 }}>{stat.value}</div>
                    <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Admin Poll Stats */}
          {pollStats && user?.is_admin && (
            <div>
              <h3 style={{ 
                color: '#f59e0b', 
                fontSize: '1rem', 
                marginBottom: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                Platform Poll Statistics
                <span style={{
                  background: 'rgba(251, 191, 36, 0.2)',
                  padding: '2px 8px',
                  borderRadius: 10,
                  fontSize: '0.65rem',
                  fontWeight: 700
                }}>
                  ADMIN
                </span>
              </h3>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: 10,
                marginBottom: 15
              }}>
                {[
                  { label: 'Total Polls', value: pollStats.total_polls, color: '#8b5cf6' },
                  { label: 'Active', value: pollStats.active_polls, color: '#10b981' },
                  { label: 'Closed', value: pollStats.closed_polls, color: '#6b7280' },
                  { label: 'Total Votes', value: pollStats.total_votes, color: '#3b82f6' },
                  { label: 'This Week', value: pollStats.polls_this_week, color: '#f59e0b' },
                  { label: 'Avg Votes', value: pollStats.avg_votes_per_poll, color: '#ec4899' },
                ].map((stat, i) => (
                  <div key={i} style={{
                    background: `${stat.color}15`,
                    borderRadius: 8,
                    padding: '10px 12px',
                    textAlign: 'center'
                  }}>
                    <div style={{ color: stat.color, fontSize: '1.2rem', fontWeight: 700 }}>{stat.value}</div>
                    <div style={{ color: '#a1a1aa', fontSize: '0.7rem' }}>{stat.label}</div>
                  </div>
                ))}
              </div>

              {/* Polls by Type Breakdown */}
              {pollStats.polls_by_type && Object.keys(pollStats.polls_by_type).length > 0 && (
                <div style={{
                  background: 'rgba(0,0,0,0.2)',
                  borderRadius: 10,
                  padding: 12,
                  marginBottom: 15
                }}>
                  <div style={{ color: '#a1a1aa', fontSize: '0.8rem', marginBottom: 8 }}>Polls by Location</div>
                  <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap' }}>
                    {Object.entries(pollStats.polls_by_type).map(([type, count]) => (
                      <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{
                          background: type === 'group' ? '#8b5cf6' : type === 'page' ? '#3b82f6' : '#10b981',
                          width: 8,
                          height: 8,
                          borderRadius: '50%'
                        }}></span>
                        <span style={{ color: '#fff', fontSize: '0.85rem' }}>
                          {type.charAt(0).toUpperCase() + type.slice(1)}: {count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Most Active Polls */}
              {pollStats.most_active_polls && pollStats.most_active_polls.length > 0 && (
                <div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.8rem', marginBottom: 8 }}>Top Performing Polls</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {pollStats.most_active_polls.slice(0, 3).map((poll, i) => (
                      <div key={poll.id} style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        background: 'rgba(255,255,255,0.03)',
                        borderRadius: 8,
                        padding: '8px 12px'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <span style={{
                            background: i === 0 ? '#fbbf24' : i === 1 ? '#9ca3af' : '#cd7f32',
                            width: 20,
                            height: 20,
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            color: '#000'
                          }}>{i + 1}</span>
                          <span style={{ color: '#fff', fontSize: '0.85rem' }}>{poll.question}</span>
                        </div>
                        <span style={{ 
                          color: '#10b981', 
                          fontSize: '0.8rem',
                          fontWeight: 600
                        }}>{poll.votes} votes</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

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
