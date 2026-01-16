import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';

// Import refactored components
import { 
  StatsGrid, 
  CountryPieChart, 
  USStatesBarChart, 
  DocumentTypesChart, 
  TopWordsChart,
  PollStatsCard 
} from '../components/Statistics';
import { TopSellersLeaderboard, MostCopiedLeaderboard } from '../components/Statistics';

// Fix for leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Constants
const FUNNY_STATS_MESSAGES = [
  "📊 These statistics are so accurate, even your math teacher would be impressed!",
  "🎯 Data so hot, it's practically on fire! 🔥",
  "💡 Warning: Viewing these stats may cause sudden urges to buy protocols!",
  "🚀 Our numbers go up like Richard J. Selman's A-4 Skyhawk - FAST!",
  "📈 These charts are more exciting than a supernatural thriller! (Speaking of which...)",
];

const COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#ec4899', '#14b8a6', '#f97316'];

// Coordinate maps
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

const COUNTRY_COORDINATES = {
  'United States': [39.8283, -98.5795], 'Canada': [56.1304, -106.3468],
  'United Kingdom': [55.3781, -3.4360], 'Germany': [51.1657, 10.4515],
  'France': [46.2276, 2.2137], 'Japan': [36.2048, 138.2529],
  'Australia': [-25.2744, 133.7751], 'Brazil': [-14.2350, -51.9253],
  'India': [20.5937, 78.9629], 'China': [35.8617, 104.1954]
};

// Sub-components
const HeroBanner = ({ funnyMessage, funnyFact }) => (
  <div style={{
    background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(236, 72, 153, 0.2) 100%)',
    borderRadius: 20, padding: 30, marginBottom: 30,
    border: '1px solid rgba(139, 92, 246, 0.3)'
  }}>
    <h1 style={{ 
      fontSize: '2.5rem', fontWeight: 800, marginBottom: 10,
      background: 'linear-gradient(135deg, #fff 0%, #f472b6 100%)',
      WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
    }}>
      📈 InfoPilot Statistics Central
    </h1>
    <p style={{ color: '#a1a1aa', fontSize: '1.1rem', marginBottom: 15 }}>{funnyMessage}</p>
    {funnyFact && (
      <div style={{ 
        display: 'inline-block', background: 'rgba(16, 185, 129, 0.2)',
        padding: '8px 16px', borderRadius: 20, color: '#10b981', fontSize: '0.9rem'
      }}>
        🎭 {funnyFact}
      </div>
    )}
  </div>
);

const QuickStatsGrid = ({ stats }) => {
  const quickStats = [
    { label: 'Total Users', value: stats?.overview?.total_users || 0, icon: '👥', color: '#8b5cf6' },
    { label: 'Active (7d)', value: stats?.overview?.active_users_7d || 0, icon: '🔥', color: '#ef4444' },
    { label: 'Protocols', value: stats?.overview?.total_protocols || 0, icon: '📋', color: '#3b82f6' },
    { label: 'Searches', value: stats?.overview?.total_searches || 0, icon: '🔍', color: '#10b981' },
    { label: 'Purchases', value: stats?.overview?.total_purchases || 0, icon: '💰', color: '#f59e0b' },
    { label: 'Revenue', value: `$${stats?.overview?.total_revenue || 0}`, icon: '💵', color: '#ec4899' },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginBottom: 30 }}>
      {quickStats.map((stat, i) => (
        <div key={i} style={{
          background: 'rgba(30, 20, 50, 0.6)', borderRadius: 16, padding: 20,
          border: `1px solid ${stat.color}30`, textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', marginBottom: 10 }}>{stat.icon}</div>
          <div style={{ color: stat.color, fontSize: '2rem', fontWeight: 700 }}>{stat.value}</div>
          <div style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>{stat.label}</div>
        </div>
      ))}
    </div>
  );
};

const InteractiveStatsMap = ({ mapMarkers, selectedStatType, onClearMap, onSelectStat, stats, leaderboard, mostCopied }) => {
  const createStatMarker = (color, size = 20) => L.divIcon({
    className: 'custom-stat-marker',
    html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>`,
    iconSize: [size, size], iconAnchor: [size/2, size/2], popupAnchor: [0, -size/2],
  });

  return (
    <div style={{
      background: 'rgba(30, 20, 50, 0.6)', borderRadius: 16, padding: 25,
      marginBottom: 30, border: '1px solid rgba(139, 92, 246, 0.2)'
    }} data-testid="interactive-stats-map">
      <h3 style={{ color: '#fff', marginBottom: 15 }}>🗺️ Interactive Statistics Map</h3>
      <div style={{ display: 'flex', gap: 10, marginBottom: 15, flexWrap: 'wrap' }}>
        {[
          { type: 'countries', label: '🌍 Countries', data: stats?.countries?.countries },
          { type: 'us_states', label: '🇺🇸 US States', data: stats?.us_states?.states },
          { type: 'top_sellers', label: '🏆 Top Sellers', data: leaderboard?.sales },
          { type: 'most_copied', label: '📋 Most Copied', data: mostCopied?.leaderboard },
        ].map(btn => (
          <button
            key={btn.type}
            onClick={() => onSelectStat(btn.type, btn.data)}
            className={`btn ${selectedStatType === btn.type ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 16px', fontSize: '0.85rem' }}
          >
            {btn.label}
          </button>
        ))}
        {mapMarkers.length > 0 && (
          <button onClick={onClearMap} className="btn btn-secondary" style={{ marginLeft: 'auto', padding: '8px 16px' }}>
            Clear Map
          </button>
        )}
      </div>
      
      <div style={{ height: 400, borderRadius: 12, overflow: 'hidden' }}>
        <MapContainer center={[39.8283, -98.5795]} zoom={4} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
          {mapMarkers.map((marker, idx) => (
            <React.Fragment key={marker.id}>
              <Marker position={marker.position} icon={createStatMarker(marker.color, 24)}>
                <Popup>
                  <div style={{ textAlign: 'center' }}>
                    <strong style={{ color: marker.color }}>{marker.label}</strong>
                    <br />
                    <span>{marker.type === 'seller' ? 'Sales' : marker.type === 'protocol' ? 'Copies' : 'Count'}: {marker.value}</span>
                  </div>
                </Popup>
              </Marker>
              <Circle center={marker.position} radius={marker.value * 1000} pathOptions={{ color: marker.color, fillColor: marker.color, fillOpacity: 0.2 }} />
            </React.Fragment>
          ))}
        </MapContainer>
      </div>
      
      {mapMarkers.length === 0 && (
        <p style={{ textAlign: 'center', padding: 20, color: '#a1a1aa' }}>👆 Click a button above to populate the map!</p>
      )}
    </div>
  );
};

const PollStatsSection = ({ userPollStats, pollStats, isAdmin }) => {
  if (!userPollStats && !pollStats) return null;

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
      borderRadius: 20, padding: 25, marginBottom: 30,
      border: '1px solid rgba(59, 130, 246, 0.2)'
    }} data-testid="poll-statistics-section">
      <h2 style={{ color: '#fff', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 12 }}>
        📊 Poll Insights
        <span style={{ background: 'rgba(16, 185, 129, 0.2)', padding: '4px 12px', borderRadius: 15, fontSize: '0.7rem', fontWeight: 600, color: '#10b981' }}>COMMUNITY</span>
      </h2>

      {userPollStats && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ color: '#a78bfa', fontSize: '1rem', marginBottom: 12 }}>Your Poll Activity</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
            {[
              { label: 'Polls Created', value: userPollStats.polls_created, icon: '📝', color: '#8b5cf6' },
              { label: 'Active Now', value: userPollStats.active_polls, icon: '🟢', color: '#10b981' },
              { label: 'Votes Received', value: userPollStats.total_votes_received, icon: '✅', color: '#3b82f6' },
              { label: 'Polls Voted', value: userPollStats.polls_voted_on, icon: '🗳️', color: '#f59e0b' },
            ].map((stat, i) => (
              <div key={i} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: '12px 15px', textAlign: 'center', border: `1px solid ${stat.color}20` }}>
                <div style={{ fontSize: '1.3rem', marginBottom: 4 }}>{stat.icon}</div>
                <div style={{ color: stat.color, fontSize: '1.4rem', fontWeight: 700 }}>{stat.value}</div>
                <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {isAdmin && pollStats && (
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: 20 }}>
          <h3 style={{ color: '#f472b6', fontSize: '1rem', marginBottom: 12 }}>Platform Stats (Admin)</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
            {[
              { label: 'Total Polls', value: pollStats.total_polls, icon: '📊', color: '#f472b6' },
              { label: 'Total Votes', value: pollStats.total_votes, icon: '🗳️', color: '#8b5cf6' },
              { label: 'Avg Votes/Poll', value: pollStats.avg_votes_per_poll?.toFixed(1), icon: '📈', color: '#10b981' },
              { label: 'Unique Voters', value: pollStats.unique_voters, icon: '👥', color: '#3b82f6' },
            ].map((stat, i) => (
              <div key={i} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: '12px 15px', textAlign: 'center', border: `1px solid ${stat.color}20` }}>
                <div style={{ fontSize: '1.3rem', marginBottom: 4 }}>{stat.icon}</div>
                <div style={{ color: stat.color, fontSize: '1.4rem', fontWeight: 700 }}>{stat.value}</div>
                <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const BookPromo = () => (
  <div style={{
    background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%)',
    borderRadius: 20, padding: 25, marginTop: 30,
    border: '1px solid rgba(236, 72, 153, 0.3)'
  }}>
    <h2 style={{ color: '#f472b6', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 10 }}>
      📚 Speaking of Statistics...
    </h2>
    <p style={{ color: '#e2e8f0', marginBottom: 15, lineHeight: 1.6 }}>
      <strong>&quot;Letters to Evelyn&quot;</strong> by John Selman has <strong style={{ color: '#10b981' }}>19 Five-Star Reviews</strong> on Readers&apos; Favorite! 
      That&apos;s a 100% satisfaction rate - better stats than most protocols! 🚀
    </p>
    <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap' }}>
      <a href="https://a.co/d/gsRLapf" target="_blank" rel="noopener noreferrer" className="btn btn-primary" style={{ padding: '10px 20px' }}>
        📖 Get eBook ($2.99)
      </a>
      <a href="https://a.co/d/g0aeHkI" target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ padding: '10px 20px' }}>
        📕 Hardcover ($250)
      </a>
    </div>
  </div>
);

// Main Component
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
  
  // Easter Egg Statistics state
  const [easterEggStats, setEasterEggStats] = useState(null);
  const [userEasterEggStats, setUserEasterEggStats] = useState(null);
  const [easterEggLeaderboard, setEasterEggLeaderboard] = useState([]);
  
  // AI Search state
  const [aiSearchQuery, setAiSearchQuery] = useState('');
  const [aiSearchLoading, setAiSearchLoading] = useState(false);
  const [aiSearchMode, setAiSearchMode] = useState('comprehensive');
  const [dbSearchLoading, setDbSearchLoading] = useState(false);
  const [dbSearchMode, setDbSearchMode] = useState('smart');

  // AI Intelligent Search for Statistics
  const aiSearchFromStats = async () => {
    if (!aiSearchQuery.trim()) {
      showToast('Please enter a search query', 'error');
      return;
    }
    
    setAiSearchLoading(true);
    
    try {
      const res = await fetch(`${API}/ai-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ 
          query: aiSearchQuery,
          mode: aiSearchMode,
          auto_categorize: true
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`🤖 ${data.message}`, 'success');
        // Refresh statistics
        fetchStatistics();
      } else {
        const error = await res.json();
        showToast(error.detail || 'AI Search failed', 'error');
      }
    } catch (e) {
      showToast('AI Search failed', 'error');
    }
    
    setAiSearchLoading(false);
  };

  // Auto-Categorize Search from Statistics
  const autoCategorizeFroStats = async () => {
    if (!aiSearchQuery.trim()) {
      showToast('Please enter a search query', 'error');
      return;
    }
    
    setAiSearchLoading(true);
    
    try {
      const res = await fetch(`${API}/auto-categorize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query: aiSearchQuery })
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`🎯 ${data.message}`, 'success');
        // Refresh statistics
        fetchStatistics();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Auto-categorization failed', 'error');
      }
    } catch (e) {
      showToast('Auto-categorization failed', 'error');
    }
    
    setAiSearchLoading(false);
  };

  // Database Text Search from Statistics
  const databaseSearchFromStats = async () => {
    if (!aiSearchQuery.trim()) {
      showToast('Please enter a search query', 'error');
      return;
    }
    
    setDbSearchLoading(true);
    
    try {
      const res = await fetch(`${API}/database-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ 
          query: aiSearchQuery,
          mode: dbSearchMode,
          limit: 100
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`📚 ${data.message}`, 'success');
      } else {
        const error = await res.json();
        showToast(error.detail || 'Database search failed', 'error');
      }
    } catch (e) {
      showToast('Database search failed', 'error');
    }
    
    setDbSearchLoading(false);
  };

  useEffect(() => {
    fetchStatistics();
    fetchLeaderboards();
    fetchMostCopied();
    fetchPollStatistics();
  }, []);

  const fetchPollStatistics = async () => {
    try {
      if (token) {
        const userRes = await fetch(`${API}/polls/user/statistics`, { headers: { Authorization: `Bearer ${token}` } });
        if (userRes.ok) setUserPollStats(await userRes.json());
      }
      if (user?.is_admin && token) {
        const adminRes = await fetch(`${API}/polls/admin/statistics`, { headers: { Authorization: `Bearer ${token}` } });
        if (adminRes.ok) setPollStats(await adminRes.json());
      }
    } catch (error) { console.error('Failed to fetch poll statistics:', error); }
  };

  const fetchMostCopied = async () => {
    try {
      const res = await fetch(`${API}/statistics/most-copied`);
      if (res.ok) setMostCopied(await res.json());
    } catch (error) { console.error('Failed to fetch most copied:', error); }
  };

  const fetchStatistics = async () => {
    try {
      const res = await fetch(`${API}/statistics/dashboard`);
      if (res.ok) setStats(await res.json());
    } catch (error) { console.error('Failed to fetch statistics:', error); }
    finally { setLoading(false); }
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
        setLeaderboard({ sales: salesData.leaderboard || [], revenue: revenueData.leaderboard || [] });
      }
    } catch (error) { console.error('Failed to fetch leaderboards:', error); }
  };

  const populateMapForStat = (statType, data) => {
    setSelectedStatType(statType);
    const markers = [];
    
    if (statType === 'countries') {
      (data || []).forEach((item, idx) => {
        const coords = COUNTRY_COORDINATES[item.name];
        if (coords) markers.push({ id: `country-${idx}`, position: coords, label: item.name, value: item.count || item.value || 0, color: COLORS[idx % COLORS.length], type: 'country' });
      });
    } else if (statType === 'us_states') {
      (data || []).forEach((item, idx) => {
        const coords = STATE_COORDINATES[item.name];
        if (coords) markers.push({ id: `state-${idx}`, position: coords, label: item.name, value: item.count || item.value || 0, color: COLORS[idx % COLORS.length], type: 'state' });
      });
    } else if (statType === 'top_sellers') {
      const stateNames = Object.keys(STATE_COORDINATES);
      (data || []).forEach((item, idx) => {
        const coords = STATE_COORDINATES[stateNames[idx % stateNames.length]];
        if (coords) markers.push({ id: `seller-${idx}`, position: [coords[0] + (Math.random() - 0.5) * 2, coords[1] + (Math.random() - 0.5) * 2], label: item.username || item.name, value: item.total_sales || 0, color: COLORS[idx % COLORS.length], type: 'seller' });
      });
    } else if (statType === 'most_copied') {
      const stateNames = Object.keys(STATE_COORDINATES);
      (mostCopied.leaderboard || []).forEach((item, idx) => {
        const coords = STATE_COORDINATES[stateNames[idx % stateNames.length]];
        if (coords) markers.push({ id: `copied-${idx}`, position: [coords[0] + (Math.random() - 0.5) * 2, coords[1] + (Math.random() - 0.5) * 2], label: item.name, value: item.copy_count || 0, color: COLORS[idx % COLORS.length], type: 'protocol' });
      });
    }
    
    setMapMarkers(markers);
  };

  const clearMap = () => { setMapMarkers([]); setSelectedStatType(null); };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh', color: '#fff' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: 20 }}>📊</div>
          <p>Crunching numbers faster than a squirrel hoards acorns...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 0' }} data-testid="statistics-page">
      <HeroBanner funnyMessage={funnyMessage} funnyFact={stats?.funny_fact} />
      
      {/* AI Search Section */}
      <div style={{ 
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(236, 72, 153, 0.15))',
        borderRadius: 16,
        padding: 20,
        marginBottom: 30,
        border: '1px solid rgba(124, 58, 237, 0.3)'
      }}>
        <h3 style={{ color: '#a78bfa', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
          🤖 AI-Powered Search
          <span style={{ fontSize: '0.7rem', background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', padding: '3px 8px', borderRadius: 6 }}>
            Search Google, Bing, DuckDuckGo, Brave & More
          </span>
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
          <input
            type="text"
            value={aiSearchQuery}
            onChange={(e) => setAiSearchQuery(e.target.value)}
            placeholder="Enter search query for AI-powered intelligent search..."
            style={{
              flex: 1,
              minWidth: 250,
              padding: '12px 15px',
              background: 'rgba(30, 20, 50, 0.8)',
              border: '1px solid rgba(124, 58, 237, 0.4)',
              borderRadius: 10,
              color: '#fff',
              fontSize: '1rem'
            }}
            onKeyPress={(e) => e.key === 'Enter' && aiSearchFromStats()}
            data-testid="stats-ai-search-input"
          />
          <button
            onClick={autoCategorizeFroStats}
            disabled={aiSearchLoading || !aiSearchQuery.trim()}
            className="btn"
            style={{
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              color: '#fff',
              padding: '12px 20px',
              fontWeight: 600,
              opacity: (!aiSearchQuery.trim() || aiSearchLoading) ? 0.5 : 1
            }}
            data-testid="stats-auto-categorize-btn"
          >
            {aiSearchLoading ? '⏳' : '🎯'} Search & Auto-Categorize
          </button>
          <button
            onClick={aiSearchFromStats}
            disabled={aiSearchLoading || !aiSearchQuery.trim()}
            className="btn"
            style={{
              background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
              color: '#fff',
              padding: '12px 20px',
              fontWeight: 600,
              opacity: (!aiSearchQuery.trim() || aiSearchLoading) ? 0.5 : 1
            }}
            data-testid="stats-ai-search-btn"
          >
            {aiSearchLoading ? '🤖 Searching...' : '🤖 AI Intelligent Search'}
          </button>
          <select
            value={aiSearchMode}
            onChange={(e) => setAiSearchMode(e.target.value)}
            style={{
              background: 'rgba(124, 58, 237, 0.3)',
              border: '1px solid rgba(124, 58, 237, 0.4)',
              color: '#a78bfa',
              padding: '10px 15px',
              borderRadius: 8,
              fontSize: '0.9rem'
            }}
          >
            <option value="comprehensive">📊 Comprehensive</option>
            <option value="news">📰 News Focus</option>
            <option value="research">🔬 Research Focus</option>
          </select>
        </div>
        {/* Database Search Row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <button
            onClick={databaseSearchFromStats}
            disabled={dbSearchLoading || !aiSearchQuery.trim()}
            className="btn"
            style={{
              background: 'linear-gradient(135deg, #06b6d4, #0891b2)',
              color: '#fff',
              padding: '12px 20px',
              fontWeight: 600,
              opacity: (!aiSearchQuery.trim() || dbSearchLoading) ? 0.5 : 1
            }}
            data-testid="stats-database-search-btn"
          >
            {dbSearchLoading ? '📚 Searching...' : '📚 Database Text Search'}
          </button>
          <select
            value={dbSearchMode}
            onChange={(e) => setDbSearchMode(e.target.value)}
            style={{
              background: 'rgba(6, 182, 212, 0.3)',
              border: '1px solid rgba(6, 182, 212, 0.4)',
              color: '#22d3ee',
              padding: '10px 15px',
              borderRadius: 8,
              fontSize: '0.9rem'
            }}
          >
            <option value="smart">🧠 Smart Match</option>
            <option value="exact">🎯 Exact Phrase</option>
            <option value="fuzzy">🔍 Fuzzy Match</option>
          </select>
        </div>
        <p style={{ color: '#a1a1aa', fontSize: '0.8rem', marginTop: 10, marginBottom: 0 }}>
          💡 <strong>AI Search:</strong> Searches Google, Bing, DuckDuckGo, Brave with GPT keyword expansion. <strong>Database Search:</strong> Finds content in your already collated results.
        </p>
      </div>
      
      <QuickStatsGrid stats={stats} />

      {/* Charts Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 25, marginBottom: 30 }}>
        {/* Countries Pie Chart */}
        <div style={{ background: 'rgba(30, 20, 50, 0.6)', borderRadius: 16, padding: 25, border: '1px solid rgba(139, 92, 246, 0.2)' }}>
          <h3 style={{ color: '#fff', marginBottom: 20 }}>🌍 Results by Country</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={stats?.countries?.countries || []} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, percentage }) => `${name}: ${percentage}%`}>
                {(stats?.countries?.countries || []).map((entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* US States Bar Chart */}
        <div style={{ background: 'rgba(30, 20, 50, 0.6)', borderRadius: 16, padding: 25, border: '1px solid rgba(139, 92, 246, 0.2)' }}>
          <h3 style={{ color: '#fff', marginBottom: 20 }}>🇺🇸 US States Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats?.us_states?.states || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="code" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} labelStyle={{ color: '#fff' }} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Document Types */}
        <div style={{ background: 'rgba(30, 20, 50, 0.6)', borderRadius: 16, padding: 25, border: '1px solid rgba(139, 92, 246, 0.2)' }}>
          <h3 style={{ color: '#fff', marginBottom: 20 }}>📄 Document Types</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={stats?.document_types?.types || []} dataKey="count" nameKey="type" cx="50%" cy="50%" innerRadius={50} outerRadius={100} paddingAngle={5} label={({ type }) => type}>
                {(stats?.document_types?.types || []).map((entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Words */}
        <div style={{ background: 'rgba(30, 20, 50, 0.6)', borderRadius: 16, padding: 25, border: '1px solid rgba(139, 92, 246, 0.2)' }}>
          <h3 style={{ color: '#fff', marginBottom: 20 }}>🔤 Top 10 Protocol Words</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats?.top_words?.words || []} layout="vertical" margin={{ left: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis type="number" stroke="#888" />
              <YAxis dataKey="word" type="category" stroke="#888" width={60} />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
              <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Interactive Map */}
      <InteractiveStatsMap 
        mapMarkers={mapMarkers}
        selectedStatType={selectedStatType}
        onClearMap={clearMap}
        onSelectStat={populateMapForStat}
        stats={stats}
        leaderboard={leaderboard}
        mostCopied={mostCopied}
      />

      {/* Poll Statistics */}
      <PollStatsSection userPollStats={userPollStats} pollStats={pollStats} isAdmin={user?.is_admin} />

      {/* Leaderboards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 25, marginBottom: 30 }}>
        <TopSellersLeaderboard 
          leaderboard={leaderboard}
          activeTab={leaderboardTab}
          setActiveTab={setLeaderboardTab}
          onShowOnMap={populateMapForStat}
        />
        <MostCopiedLeaderboard 
          data={mostCopied}
          onShowOnMap={populateMapForStat}
        />
      </div>

      {/* Book Promo */}
      <BookPromo />
    </div>
  );
};

export default StatisticsPage;
