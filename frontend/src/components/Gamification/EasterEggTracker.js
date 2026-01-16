/**
 * InfoPilot Explorer - Easter Egg Tracker Component
 * Displays and tracks hidden Easter eggs discovered by users
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

// Rarity colors
const RARITY_COLORS = {
  common: { bg: 'rgba(156, 163, 175, 0.2)', border: '#9ca3af', text: '#9ca3af' },
  uncommon: { bg: 'rgba(34, 197, 94, 0.2)', border: '#22c55e', text: '#22c55e' },
  rare: { bg: 'rgba(59, 130, 246, 0.2)', border: '#3b82f6', text: '#3b82f6' },
  epic: { bg: 'rgba(168, 85, 247, 0.2)', border: '#a855f7', text: '#a855f7' },
  legendary: { bg: 'rgba(245, 158, 11, 0.2)', border: '#f59e0b', text: '#f59e0b' }
};

export const EasterEggTracker = () => {
  const { token, user } = useAuth();
  const [discoveries, setDiscoveries] = useState({ discovered: [], undiscovered: [] });
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('my-eggs');
  const [celebrationEgg, setCelebrationEgg] = useState(null);
  
  const fetchDiscoveries = useCallback(async () => {
    if (!token) return;
    
    try {
      const [discResp, leaderResp] = await Promise.all([
        fetch(`${API}/api/easter-eggs/my-discoveries`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API}/api/easter-eggs/leaderboard`)
      ]);
      
      if (discResp.ok) {
        const data = await discResp.json();
        setDiscoveries(data);
      }
      
      if (leaderResp.ok) {
        const data = await leaderResp.json();
        setLeaderboard(data.leaderboard || []);
      }
    } catch (e) {
      console.error('Failed to fetch Easter egg data:', e);
    } finally {
      setLoading(false);
    }
  }, [token]);
  
  useEffect(() => {
    fetchDiscoveries();
  }, [fetchDiscoveries]);
  
  // Listen for Easter egg discovery events from other components
  useEffect(() => {
    const handleEasterEggDiscovery = (event) => {
      const { egg } = event.detail;
      setCelebrationEgg(egg);
      fetchDiscoveries();
      
      // Auto-dismiss celebration after 5 seconds
      setTimeout(() => setCelebrationEgg(null), 5000);
    };
    
    window.addEventListener('easterEggDiscovered', handleEasterEggDiscovery);
    return () => window.removeEventListener('easterEggDiscovered', handleEasterEggDiscovery);
  }, [fetchDiscoveries]);
  
  const getRarityBadge = (rarity) => {
    const colors = RARITY_COLORS[rarity] || RARITY_COLORS.common;
    return (
      <span style={{
        fontSize: '0.65rem',
        padding: '2px 6px',
        borderRadius: 4,
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        color: colors.text,
        textTransform: 'uppercase',
        fontWeight: 600
      }}>
        {rarity}
      </span>
    );
  };
  
  if (loading) {
    return (
      <div style={{ padding: 20, textAlign: 'center' }}>
        <span className="loading-spinner"></span>
        <p style={{ color: '#a1a1aa', marginTop: 10 }}>Searching for eggs... 🥚</p>
      </div>
    );
  }
  
  return (
    <div className="card" style={{ marginTop: 20 }} data-testid="easter-egg-tracker">
      <h2 style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 10,
        marginBottom: 15,
        color: '#f59e0b'
      }}>
        🥚 Easter Egg Hunt 
        <span style={{ 
          fontSize: '0.7rem', 
          background: 'linear-gradient(135deg, #f59e0b, #ec4899)', 
          padding: '4px 10px', 
          borderRadius: 20,
          color: '#fff'
        }}>
          {discoveries.discovered_count || 0}/{discoveries.total_eggs || 15} Found
        </span>
      </h2>
      
      {/* Celebration Modal */}
      {celebrationEgg && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          animation: 'fadeIn 0.3s ease-out'
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
            borderRadius: 20,
            padding: 40,
            textAlign: 'center',
            maxWidth: 400,
            border: `3px solid ${RARITY_COLORS[celebrationEgg.rarity]?.border || '#f59e0b'}`,
            animation: 'bounceIn 0.5s ease-out'
          }}>
            <div style={{ fontSize: '4rem', marginBottom: 15 }}>{celebrationEgg.icon}</div>
            <h2 style={{ color: '#f59e0b', marginBottom: 10 }}>🎉 Easter Egg Found!</h2>
            <h3 style={{ color: '#fff', marginBottom: 10 }}>{celebrationEgg.name}</h3>
            <p style={{ color: '#a1a1aa', marginBottom: 15 }}>{celebrationEgg.description}</p>
            {getRarityBadge(celebrationEgg.rarity)}
            <div style={{ 
              marginTop: 20, 
              fontSize: '1.5rem', 
              color: '#10b981',
              fontWeight: 700
            }}>
              +{celebrationEgg.xp} XP!
            </div>
            <button 
              onClick={() => setCelebrationEgg(null)}
              className="btn btn-primary"
              style={{ marginTop: 20 }}
            >
              Awesome! 🎉
            </button>
          </div>
        </div>
      )}
      
      {/* Progress Bar */}
      <div style={{ 
        background: 'rgba(39, 39, 42, 0.5)', 
        borderRadius: 10, 
        padding: 15,
        marginBottom: 20
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: 8,
          fontSize: '0.85rem',
          color: '#a1a1aa'
        }}>
          <span>🥚 Egg Hunter Progress</span>
          <span>{discoveries.completion_percentage || 0}% Complete</span>
        </div>
        <div style={{ 
          background: 'rgba(63, 63, 70, 0.5)', 
          borderRadius: 8, 
          height: 12,
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${discoveries.completion_percentage || 0}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #10b981, #3b82f6, #a855f7, #f59e0b)',
            borderRadius: 8,
            transition: 'width 0.5s ease-out'
          }}></div>
        </div>
        <div style={{ 
          marginTop: 10, 
          display: 'flex', 
          justifyContent: 'space-between',
          fontSize: '0.8rem'
        }}>
          <span style={{ color: '#10b981' }}>
            ✨ {discoveries.total_xp_earned || 0} XP Earned
          </span>
          <span style={{ color: '#a1a1aa' }}>
            {(discoveries.total_eggs || 15) - (discoveries.discovered_count || 0)} eggs remaining
          </span>
        </div>
      </div>
      
      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        {[
          { id: 'my-eggs', label: '🥚 My Eggs', count: discoveries.discovered_count },
          { id: 'leaderboard', label: '🏆 Hunters', count: leaderboard.length },
          { id: 'hints', label: '💡 Hints', count: discoveries.undiscovered?.length }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`btn ${activeTab === tab.id ? 'btn-primary' : ''}`}
            style={{
              flex: 1,
              opacity: activeTab === tab.id ? 1 : 0.6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6
            }}
            data-testid={`tab-${tab.id}`}
          >
            {tab.label}
            <span style={{
              fontSize: '0.7rem',
              background: 'rgba(255,255,255,0.2)',
              padding: '2px 6px',
              borderRadius: 10
            }}>{tab.count}</span>
          </button>
        ))}
      </div>
      
      {/* Tab Content */}
      {activeTab === 'my-eggs' && (
        <div style={{ display: 'grid', gap: 12 }}>
          {discoveries.discovered?.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: 40, 
              color: '#a1a1aa',
              background: 'rgba(39, 39, 42, 0.3)',
              borderRadius: 12
            }}>
              <div style={{ fontSize: '3rem', marginBottom: 10 }}>🔍</div>
              <p>No eggs discovered yet!</p>
              <p style={{ fontSize: '0.85rem', marginTop: 5 }}>
                Start exploring InfoPilot to find hidden Easter eggs...
              </p>
            </div>
          ) : (
            discoveries.discovered?.map((egg, i) => (
              <div 
                key={egg.id || i}
                style={{
                  background: RARITY_COLORS[egg.rarity]?.bg || 'rgba(39, 39, 42, 0.5)',
                  border: `1px solid ${RARITY_COLORS[egg.rarity]?.border || '#3f3f46'}`,
                  borderRadius: 12,
                  padding: 15,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 15
                }}
                data-testid={`discovered-egg-${egg.id}`}
              >
                <div style={{ fontSize: '2.5rem' }}>{egg.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <strong style={{ color: '#fff' }}>{egg.name}</strong>
                    {getRarityBadge(egg.rarity)}
                  </div>
                  <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '4px 0' }}>
                    {egg.description}
                  </p>
                  <span style={{ color: '#10b981', fontSize: '0.75rem' }}>
                    +{egg.xp_earned || egg.xp} XP
                    {egg.discovered_at && ` • Found ${new Date(egg.discovered_at).toLocaleDateString()}`}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
      
      {activeTab === 'leaderboard' && (
        <div>
          <h4 style={{ color: '#f59e0b', marginBottom: 15, textAlign: 'center' }}>
            🏆 Hall of Egg-cellent Hunters 🏆
          </h4>
          {leaderboard.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#a1a1aa' }}>
              No hunters yet! Be the first to find an egg!
            </p>
          ) : (
            <div style={{ display: 'grid', gap: 8 }}>
              {leaderboard.map((hunter, i) => (
                <div 
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: 12,
                    background: i < 3 ? 'rgba(245, 158, 11, 0.1)' : 'rgba(39, 39, 42, 0.3)',
                    borderRadius: 10,
                    border: i === 0 ? '1px solid #f59e0b' : 'none'
                  }}
                  data-testid={`leaderboard-rank-${i + 1}`}
                >
                  <div style={{
                    width: 35,
                    height: 35,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: i < 3 ? '1.2rem' : '0.9rem',
                    background: i === 0 ? 'linear-gradient(135deg, #f59e0b, #fbbf24)' :
                              i === 1 ? 'linear-gradient(135deg, #9ca3af, #d1d5db)' :
                              i === 2 ? 'linear-gradient(135deg, #b45309, #d97706)' :
                              'rgba(63, 63, 70, 0.5)',
                    color: i < 3 ? '#fff' : '#a1a1aa'
                  }}>
                    {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <strong style={{ color: '#fff' }}>{hunter.username}</strong>
                      <span style={{ 
                        fontSize: '0.7rem', 
                        color: '#a1a1aa',
                        background: 'rgba(63, 63, 70, 0.5)',
                        padding: '2px 6px',
                        borderRadius: 4
                      }}>
                        {hunter.title}
                      </span>
                    </div>
                    <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                      🥚 {hunter.eggs_found} eggs • ✨ {hunter.total_xp} XP
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'hints' && (
        <div style={{ display: 'grid', gap: 12 }}>
          <p style={{ 
            color: '#a1a1aa', 
            fontSize: '0.9rem', 
            textAlign: 'center',
            marginBottom: 10,
            fontStyle: 'italic'
          }}>
            💡 Hints for undiscovered eggs...
          </p>
          {discoveries.undiscovered?.map((egg, i) => (
            <div 
              key={i}
              style={{
                background: 'rgba(39, 39, 42, 0.5)',
                borderRadius: 12,
                padding: 15,
                display: 'flex',
                alignItems: 'center',
                gap: 15,
                border: '1px dashed rgba(63, 63, 70, 0.8)'
              }}
              data-testid={`hint-${i}`}
            >
              <div style={{ 
                fontSize: '2rem', 
                filter: 'grayscale(1)', 
                opacity: 0.5 
              }}>🔒</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <strong style={{ color: '#71717a' }}>{egg.name}</strong>
                  {getRarityBadge(egg.rarity)}
                </div>
                <p style={{ 
                  color: '#f59e0b', 
                  fontSize: '0.85rem', 
                  margin: '4px 0',
                  fontStyle: 'italic'
                }}>
                  💡 {egg.hint}
                </p>
                <span style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>
                  Reward: +{egg.xp} XP
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Fun Stats */}
      <div style={{ 
        marginTop: 20, 
        padding: 15, 
        background: 'rgba(16, 185, 129, 0.1)', 
        borderRadius: 10,
        border: '1px solid rgba(16, 185, 129, 0.3)',
        textAlign: 'center'
      }}>
        <p style={{ color: '#10b981', fontSize: '0.9rem', margin: 0 }}>
          🎮 <strong>Fun Fact:</strong> The Konami Code still works... somewhere! 
          <span style={{ opacity: 0.6 }}> (↑ ↑ ↓ ↓ ← → ← → B A)</span>
        </p>
      </div>
    </div>
  );
};

// Export a helper function for triggering Easter egg discoveries from anywhere
export const triggerEasterEggDiscovery = async (eggId, token, trigger = 'automatic') => {
  try {
    const response = await fetch(`${API}/api/easter-eggs/discover`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ egg_id: eggId, trigger })
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.celebration) {
        // Dispatch event for EasterEggTracker to show celebration
        window.dispatchEvent(new CustomEvent('easterEggDiscovered', { 
          detail: { egg: data.egg } 
        }));
        showToast(data.message, 'success');
      }
      return data;
    }
  } catch (e) {
    console.error('Easter egg discovery failed:', e);
  }
  return null;
};

export default EasterEggTracker;
