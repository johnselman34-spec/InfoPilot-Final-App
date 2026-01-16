/**
 * Easter Egg Statistics Component
 * Shows Easter Egg catching stats on the Statistics page
 */
import React, { useState, useEffect } from 'react';

const EasterEggStatistics = () => {
  const [stats, setStats] = useState(() => {
    const cached = localStorage.getItem('easterEggStats');
    return cached ? JSON.parse(cached) : { caught: 0, total: 0 };
  });
  
  const [rewards, setRewards] = useState(() => {
    const cached = localStorage.getItem('easterEggRewards');
    return cached ? JSON.parse(cached) : [];
  });
  
  // Calculate reward type breakdown
  const rewardBreakdown = rewards.reduce((acc, reward) => {
    acc[reward.type] = (acc[reward.type] || 0) + 1;
    return acc;
  }, {});
  
  const totalXP = rewards.reduce((sum, r) => sum + (r.xp || 0), 0);
  
  const typeLabels = {
    protocol: { name: 'Protocol Ideas', emoji: '📋', color: '#3b82f6' },
    joke: { name: 'Funny Jokes', emoji: '😂', color: '#f59e0b' },
    pricing: { name: 'Pricing Tips', emoji: '💰', color: '#10b981' },
    motivation: { name: 'Motivation', emoji: '💪', color: '#ec4899' },
    fact: { name: 'Fun Facts', emoji: '🧠', color: '#8b5cf6' },
    secret: { name: 'Secrets', emoji: '🤫', color: '#ef4444' }
  };
  
  // Refresh stats periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const cached = localStorage.getItem('easterEggStats');
      if (cached) setStats(JSON.parse(cached));
      const rewardsCached = localStorage.getItem('easterEggRewards');
      if (rewardsCached) setRewards(JSON.parse(rewardsCached));
    }, 5000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(236, 72, 153, 0.15))',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(124, 58, 237, 0.3)',
      marginBottom: 20
    }} data-testid="easter-egg-statistics">
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 20,
        flexWrap: 'wrap',
        gap: 10
      }}>
        <h3 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          🥚 Easter Egg Hunter Stats
        </h3>
        <div style={{
          background: 'linear-gradient(135deg, #10b981, #059669)',
          padding: '5px 15px',
          borderRadius: 20,
          color: '#fff',
          fontWeight: 700,
          fontSize: '0.9rem'
        }}>
          {totalXP} Total XP
        </div>
      </div>
      
      {/* Main Stats Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: 15,
        marginBottom: 20
      }}>
        <div style={{
          background: 'rgba(0,0,0,0.3)',
          borderRadius: 12,
          padding: 15,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 5 }}>🥚</div>
          <div style={{ color: '#f472b6', fontSize: '2rem', fontWeight: 700 }}>{stats.caught}</div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Eggs Caught</div>
        </div>
        
        <div style={{
          background: 'rgba(0,0,0,0.3)',
          borderRadius: 12,
          padding: 15,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 5 }}>🎯</div>
          <div style={{ color: '#10b981', fontSize: '2rem', fontWeight: 700 }}>
            {stats.total > 0 ? Math.round((stats.caught / stats.total) * 100) : 0}%
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Catch Rate</div>
        </div>
        
        <div style={{
          background: 'rgba(0,0,0,0.3)',
          borderRadius: 12,
          padding: 15,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 5 }}>✨</div>
          <div style={{ color: '#f59e0b', fontSize: '2rem', fontWeight: 700 }}>{rewards.length}</div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Rewards Collected</div>
        </div>
        
        <div style={{
          background: 'rgba(0,0,0,0.3)',
          borderRadius: 12,
          padding: 15,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 5 }}>⭐</div>
          <div style={{ color: '#3b82f6', fontSize: '2rem', fontWeight: 700 }}>
            {Math.floor(totalXP / 100)}
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Egg Hunter Level</div>
        </div>
      </div>
      
      {/* Reward Type Breakdown */}
      <div style={{ marginBottom: 15 }}>
        <h4 style={{ color: '#a78bfa', marginBottom: 10, fontSize: '0.95rem' }}>
          📊 Rewards by Type
        </h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
          {Object.entries(typeLabels).map(([type, info]) => (
            <div
              key={type}
              style={{
                background: `${info.color}20`,
                border: `1px solid ${info.color}40`,
                borderRadius: 10,
                padding: '8px 12px',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                minWidth: 130
              }}
            >
              <span style={{ fontSize: '1.2rem' }}>{info.emoji}</span>
              <div>
                <div style={{ color: info.color, fontWeight: 700, fontSize: '1.1rem' }}>
                  {rewardBreakdown[type] || 0}
                </div>
                <div style={{ color: '#a1a1aa', fontSize: '0.7rem' }}>{info.name}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Recent Catches */}
      {rewards.length > 0 && (
        <div>
          <h4 style={{ color: '#a78bfa', marginBottom: 10, fontSize: '0.95rem' }}>
            🕐 Recent Catches
          </h4>
          <div style={{ 
            display: 'flex', 
            gap: 10, 
            overflowX: 'auto', 
            paddingBottom: 10,
            scrollbarWidth: 'thin'
          }}>
            {rewards.slice(-5).reverse().map((reward, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(0,0,0,0.3)',
                  borderRadius: 10,
                  padding: 12,
                  minWidth: 200,
                  flex: '0 0 auto'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
                  <span style={{ fontSize: '1.2rem' }}>{reward.emoji}</span>
                  <span style={{ color: '#f472b6', fontWeight: 600, fontSize: '0.85rem' }}>
                    {reward.title}
                  </span>
                  <span style={{
                    background: 'rgba(16, 185, 129, 0.2)',
                    color: '#10b981',
                    padding: '2px 6px',
                    borderRadius: 8,
                    fontSize: '0.65rem',
                    marginLeft: 'auto'
                  }}>
                    +{reward.xp} XP
                  </span>
                </div>
                <div style={{ 
                  color: '#a1a1aa', 
                  fontSize: '0.75rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {reward.content?.substring(0, 50)}...
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Tips */}
      {stats.caught === 0 && (
        <div style={{
          background: 'rgba(245, 158, 11, 0.1)',
          borderRadius: 10,
          padding: 15,
          marginTop: 15,
          border: '1px solid rgba(245, 158, 11, 0.3)'
        }}>
          <p style={{ color: '#fbbf24', margin: 0, fontSize: '0.85rem' }}>
            💡 <strong>Tip:</strong> Keep your eyes peeled for colorful Easter eggs floating across the screen! 
            Click them quickly to catch rewards including protocol ideas, funny jokes, and XP! 
            Eggs appear every 45 seconds. 🥚✨
          </p>
        </div>
      )}
    </div>
  );
};

export default EasterEggStatistics;
