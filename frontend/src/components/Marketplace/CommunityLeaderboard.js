/**
 * Community Leaderboard
 * Highlights top protocol creators, most downloaded protocols, and rising stars
 * Encourages engagement and competition in the marketplace
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

const CommunityLeaderboard = ({ showToast }) => {
  const { token } = useAuth();
  const { isDarkMode, currentAccent } = useTheme();
  const [leaderboard, setLeaderboard] = useState({
    topCreators: [],
    topProtocols: [],
    risingStars: [],
    monthlyChampions: []
  });
  const [activeTab, setActiveTab] = useState('creators');
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('all'); // all, month, week
  
  const bgColor = isDarkMode ? 'rgba(15, 10, 35, 0.95)' : 'rgba(255, 255, 255, 0.98)';
  const cardBg = isDarkMode ? 'rgba(30, 20, 50, 0.7)' : 'rgba(248, 250, 252, 0.9)';
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b';
  const mutedColor = isDarkMode ? '#a1a1aa' : '#64748b';
  const accentColor = currentAccent?.primary || '#7c3aed';
  
  // Fetch leaderboard data
  const fetchLeaderboard = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/marketplace/leaderboard?timeRange=${timeRange}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setLeaderboard(data);
      }
    } catch (e) {
      console.error('Failed to fetch leaderboard:', e);
      // Use mock data for display if API fails
      setLeaderboard({
        topCreators: [
          { rank: 1, username: 'InfoPilotPro', protocols: 25, downloads: 1250, revenue: 2499.99, badge: '🏆' },
          { rank: 2, username: 'SearchMaster', protocols: 18, downloads: 890, revenue: 1799.50, badge: '🥈' },
          { rank: 3, username: 'DataHunter', protocols: 15, downloads: 720, revenue: 1450.00, badge: '🥉' },
          { rank: 4, username: 'ProtocolKing', protocols: 12, downloads: 580, revenue: 1150.00 },
          { rank: 5, username: 'WebWizard', protocols: 10, downloads: 450, revenue: 899.99 },
        ],
        topProtocols: [
          { rank: 1, name: 'AI News Tracker Pro', creator: 'InfoPilotPro', downloads: 450, rating: 4.9, price: 4.99 },
          { rank: 2, name: 'Financial Markets Bundle', creator: 'SearchMaster', downloads: 380, rating: 4.8, price: 9.99 },
          { rank: 3, name: 'Research Paper Finder', creator: 'DataHunter', downloads: 320, rating: 4.7, price: 2.99 },
          { rank: 4, name: 'Tech Startup News', creator: 'ProtocolKing', downloads: 280, rating: 4.6, price: 1.99 },
          { rank: 5, name: 'Health & Wellness Guide', creator: 'WebWizard', downloads: 240, rating: 4.5, price: 3.99 },
        ],
        risingStars: [
          { rank: 1, username: 'NewbieNinja', joinedDays: 14, protocols: 5, downloads: 120, growth: '+340%', badge: '🌟' },
          { rank: 2, username: 'FreshFinder', joinedDays: 21, protocols: 4, downloads: 85, growth: '+280%', badge: '⭐' },
          { rank: 3, username: 'RookieRiser', joinedDays: 30, protocols: 3, downloads: 65, growth: '+220%', badge: '✨' },
        ],
        monthlyChampions: [
          { month: 'January 2026', username: 'InfoPilotPro', downloads: 450, revenue: 899.99 },
          { month: 'December 2025', username: 'SearchMaster', downloads: 380, revenue: 759.50 },
          { month: 'November 2025', username: 'DataHunter', downloads: 320, revenue: 640.00 },
        ]
      });
    } finally {
      setLoading(false);
    }
  }, [token, timeRange]);
  
  useEffect(() => {
    fetchLeaderboard();
  }, [fetchLeaderboard]);
  
  // Rank badge colors
  const getRankStyle = (rank) => {
    switch(rank) {
      case 1: return { bg: 'linear-gradient(135deg, #ffd700, #ffb800)', color: '#1a1a1a', shadow: '0 0 20px rgba(255, 215, 0, 0.5)' };
      case 2: return { bg: 'linear-gradient(135deg, #c0c0c0, #a0a0a0)', color: '#1a1a1a', shadow: '0 0 15px rgba(192, 192, 192, 0.4)' };
      case 3: return { bg: 'linear-gradient(135deg, #cd7f32, #b8860b)', color: '#fff', shadow: '0 0 15px rgba(205, 127, 50, 0.4)' };
      default: return { bg: cardBg, color: textColor, shadow: 'none' };
    }
  };
  
  const tabs = [
    { id: 'creators', name: '👑 Top Creators', icon: '👑' },
    { id: 'protocols', name: '📋 Top Protocols', icon: '📋' },
    { id: 'rising', name: '🌟 Rising Stars', icon: '🌟' },
    { id: 'champions', name: '🏆 Hall of Fame', icon: '🏆' }
  ];
  
  if (loading) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <div className="spinner" style={{ margin: '0 auto' }} />
        <p style={{ color: mutedColor, marginTop: 15 }}>Loading leaderboard...</p>
      </div>
    );
  }
  
  return (
    <div style={{ background: bgColor, borderRadius: 20, padding: 25 }} data-testid="community-leaderboard">
      {/* Header */}
      <div style={{ marginBottom: 25 }}>
        <h2 style={{ 
          color: '#f472b6', 
          margin: '0 0 10px 0',
          fontSize: '1.8rem',
          display: 'flex',
          alignItems: 'center',
          gap: 12
        }}>
          🏆 Community Leaderboard
        </h2>
        <p style={{ color: mutedColor, margin: 0, fontSize: '0.95rem' }}>
          Celebrating our top protocol creators and rising stars!
        </p>
      </div>
      
      {/* Time Range Filter */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        {['all', 'month', 'week'].map(range => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            style={{
              background: timeRange === range ? accentColor : 'transparent',
              border: `1px solid ${accentColor}40`,
              borderRadius: 20,
              padding: '6px 16px',
              color: timeRange === range ? '#fff' : mutedColor,
              fontSize: '0.8rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {range === 'all' ? 'All Time' : range === 'month' ? 'This Month' : 'This Week'}
          </button>
        ))}
      </div>
      
      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 25, flexWrap: 'wrap' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: activeTab === tab.id 
                ? 'linear-gradient(135deg, #7c3aed, #ec4899)'
                : cardBg,
              border: activeTab === tab.id ? 'none' : `1px solid ${accentColor}30`,
              borderRadius: 12,
              padding: '12px 20px',
              color: activeTab === tab.id ? '#fff' : textColor,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
              fontSize: '0.9rem'
            }}
            data-testid={`leaderboard-tab-${tab.id}`}
          >
            {tab.name}
          </button>
        ))}
      </div>
      
      {/* Top Creators */}
      {activeTab === 'creators' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {leaderboard.topCreators.map((creator, idx) => {
            const rankStyle = getRankStyle(creator.rank);
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 15,
                  padding: 16,
                  background: cardBg,
                  borderRadius: 16,
                  border: creator.rank <= 3 ? `2px solid ${rankStyle.bg.includes('#ffd700') ? '#ffd700' : rankStyle.bg.includes('#c0c0c0') ? '#c0c0c0' : '#cd7f32'}` : `1px solid ${accentColor}20`,
                  boxShadow: rankStyle.shadow
                }}
                data-testid={`creator-rank-${creator.rank}`}
              >
                {/* Rank */}
                <div style={{
                  width: 50,
                  height: 50,
                  borderRadius: '50%',
                  background: rankStyle.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: rankStyle.color,
                  fontWeight: 900,
                  fontSize: '1.2rem',
                  flexShrink: 0
                }}>
                  {creator.badge || `#${creator.rank}`}
                </div>
                
                {/* Info */}
                <div style={{ flex: 1 }}>
                  <div style={{ color: textColor, fontWeight: 700, fontSize: '1.1rem', marginBottom: 4 }}>
                    {creator.username}
                  </div>
                  <div style={{ color: mutedColor, fontSize: '0.85rem' }}>
                    📋 {creator.protocols} protocols • 📥 {creator.downloads.toLocaleString()} downloads
                  </div>
                </div>
                
                {/* Revenue */}
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#10b981', fontWeight: 700, fontSize: '1.2rem' }}>
                    ${creator.revenue.toLocaleString()}
                  </div>
                  <div style={{ color: mutedColor, fontSize: '0.75rem' }}>total earned</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      {/* Top Protocols */}
      {activeTab === 'protocols' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {leaderboard.topProtocols.map((protocol, idx) => {
            const rankStyle = getRankStyle(protocol.rank);
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 15,
                  padding: 16,
                  background: cardBg,
                  borderRadius: 16,
                  border: protocol.rank <= 3 ? `2px solid ${rankStyle.bg.includes('#ffd700') ? '#ffd700' : rankStyle.bg.includes('#c0c0c0') ? '#c0c0c0' : '#cd7f32'}` : `1px solid ${accentColor}20`
                }}
              >
                <div style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: rankStyle.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: rankStyle.color,
                  fontWeight: 700,
                  flexShrink: 0
                }}>
                  #{protocol.rank}
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ color: textColor, fontWeight: 600, fontSize: '1rem', marginBottom: 4 }}>
                    {protocol.name}
                  </div>
                  <div style={{ color: mutedColor, fontSize: '0.8rem' }}>
                    by {protocol.creator} • ⭐ {protocol.rating}
                  </div>
                </div>
                
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#3b82f6', fontWeight: 600 }}>
                    📥 {protocol.downloads.toLocaleString()}
                  </div>
                  <div style={{ 
                    color: protocol.price > 0 ? '#10b981' : '#f59e0b',
                    fontSize: '0.85rem',
                    fontWeight: 600
                  }}>
                    {protocol.price > 0 ? `$${protocol.price}` : 'FREE'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      {/* Rising Stars */}
      {activeTab === 'rising' && (
        <div>
          <p style={{ color: '#f59e0b', marginBottom: 15, fontSize: '0.9rem' }}>
            🌟 New creators making waves in the past 30 days!
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {leaderboard.risingStars.map((star, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 15,
                  padding: 16,
                  background: `linear-gradient(135deg, ${cardBg}, rgba(251, 191, 36, 0.1))`,
                  borderRadius: 16,
                  border: '2px solid rgba(251, 191, 36, 0.3)'
                }}
              >
                <div style={{ fontSize: '2rem' }}>{star.badge}</div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ color: textColor, fontWeight: 600, fontSize: '1rem', marginBottom: 4 }}>
                    {star.username}
                  </div>
                  <div style={{ color: mutedColor, fontSize: '0.8rem' }}>
                    Joined {star.joinedDays} days ago • {star.protocols} protocols
                  </div>
                </div>
                
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#10b981', fontWeight: 700, fontSize: '1.1rem' }}>
                    {star.growth}
                  </div>
                  <div style={{ color: mutedColor, fontSize: '0.75rem' }}>
                    {star.downloads} downloads
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Hall of Fame */}
      {activeTab === 'champions' && (
        <div>
          <p style={{ color: '#ec4899', marginBottom: 15, fontSize: '0.9rem' }}>
            🏆 Monthly champions who dominated the marketplace!
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {leaderboard.monthlyChampions.map((champ, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 15,
                  padding: 16,
                  background: `linear-gradient(135deg, ${cardBg}, rgba(236, 72, 153, 0.1))`,
                  borderRadius: 16,
                  border: '2px solid rgba(236, 72, 153, 0.3)'
                }}
              >
                <div style={{
                  width: 50,
                  height: 50,
                  borderRadius: 12,
                  background: 'linear-gradient(135deg, #ec4899, #7c3aed)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.5rem'
                }}>
                  🏆
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ color: '#f472b6', fontWeight: 600, fontSize: '0.9rem', marginBottom: 4 }}>
                    {champ.month}
                  </div>
                  <div style={{ color: textColor, fontWeight: 700, fontSize: '1.1rem' }}>
                    {champ.username}
                  </div>
                </div>
                
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#3b82f6', fontWeight: 600 }}>
                    📥 {champ.downloads.toLocaleString()}
                  </div>
                  <div style={{ color: '#10b981', fontWeight: 600 }}>
                    💰 ${champ.revenue.toLocaleString()}
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

export default CommunityLeaderboard;
