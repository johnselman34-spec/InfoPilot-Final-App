import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons } from '../components/shared';

const AchievementsPage = ({ showToast }) => {
  const { token } = useAuth();
  const [profile, setProfile] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [allBadges, setAllBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile'); // profile, badges, leaderboard

  const fetchData = useCallback(async () => {
    try {
      const [profileRes, leaderboardRes, badgesRes] = await Promise.all([
        fetch(`${API}/gamification/profile`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/gamification/leaderboard`),
        fetch(`${API}/gamification/badges`)
      ]);

      const profileData = await profileRes.json();
      const leaderboardData = await leaderboardRes.json();
      const badgesData = await badgesRes.json();

      setProfile(profileData);
      setLeaderboard(leaderboardData.leaderboard || []);
      setAllBadges(badgesData.badges || []);

      // Show new badges notification
      if (profileData.new_badges?.length > 0) {
        profileData.new_badges.forEach(badge => {
          showToast(`🎉 New Badge Earned: ${badge.icon} ${badge.name}!`, 'success');
        });
      }
    } catch (e) {
      console.error('Failed to fetch gamification data:', e);
    }
    setLoading(false);
  }, [token, showToast]);

  const trackLogin = useCallback(async () => {
    try {
      await fetch(`${API}/gamification/track-login`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (e) {
      console.error('Failed to track login');
    }
  }, [token]);

  useEffect(() => {
    fetchData();
    trackLogin();
  }, [fetchData, trackLogin]);

  const getRarityColor = (rarity) => {
    switch (rarity) {
      case 'legendary': return 'linear-gradient(135deg, #fbbf24, #f59e0b)';
      case 'rare': return 'linear-gradient(135deg, #a78bfa, #7c3aed)';
      case 'uncommon': return 'linear-gradient(135deg, #34d399, #10b981)';
      default: return 'linear-gradient(135deg, #94a3b8, #64748b)';
    }
  };

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 60 }}>
        <div className="spinner" style={{ margin: '0 auto' }}></div>
        <p style={{ color: '#a1a1aa', marginTop: 20 }}>Loading achievements...</p>
      </div>
    );
  }

  return (
    <div className="card" data-testid="achievements-page">
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Trophy />
          Achievements & Rewards
        </h2>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Earn badges, gain XP, and climb the leaderboard!
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 25 }}>
        {['profile', 'badges', 'leaderboard'].map(tab => (
          <button
            key={tab}
            className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab(tab)}
            data-testid={`achievements-tab-${tab}`}
          >
            {tab === 'profile' && '👤 My Progress'}
            {tab === 'badges' && '🏅 All Badges'}
            {tab === 'leaderboard' && '🏆 Leaderboard'}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && profile && (
        <div>
          {/* Level & XP Card */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.3), rgba(236, 72, 153, 0.3))',
            borderRadius: 16,
            padding: 25,
            marginBottom: 25,
            border: '1px solid rgba(124, 58, 237, 0.5)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
              <div>
                <h3 style={{ color: '#fff', fontSize: '1.8rem', marginBottom: 5 }}>
                  Level {profile.level?.level || 1}
                </h3>
                <p style={{ color: '#a1a1aa' }}>{profile.username}</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: '#fbbf24', fontSize: '1.5rem', fontWeight: 700 }}>
                  {profile.level?.total_xp || 0} XP
                </div>
                <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                  Rank #{profile.rank?.position || '?'} (Top {profile.rank?.percentile || 0}%)
                </p>
              </div>
            </div>

            {/* XP Progress Bar */}
            <div style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#a1a1aa', marginBottom: 5 }}>
                <span>Progress to Level {(profile.level?.level || 1) + 1}</span>
                <span>{profile.level?.current_xp || 0} / {profile.level?.xp_for_next_level || 100} XP</span>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 10, height: 12, overflow: 'hidden' }}>
                <div style={{
                  background: 'linear-gradient(90deg, #f472b6, #a78bfa)',
                  height: '100%',
                  width: `${profile.level?.progress_percent || 0}%`,
                  borderRadius: 10,
                  transition: 'width 0.5s ease'
                }} />
              </div>
            </div>

            {/* Login Streak */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 15 }}>
              <span style={{ fontSize: '1.2rem' }}>🔥</span>
              <span style={{ color: '#ef4444', fontWeight: 600 }}>{profile.stats?.login_streak || 0} day streak</span>
            </div>
          </div>

          {/* Stats Grid */}
          <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Your Stats</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 25 }}>
            {[
              { label: 'Searches', value: profile.stats?.searches || 0, icon: '🔍' },
              { label: 'Protocols Created', value: profile.stats?.protocols_created || 0, icon: '📝' },
              { label: 'Protocols Sold', value: profile.stats?.protocols_sold || 0, icon: '💰' },
              { label: 'Protocols Bought', value: profile.stats?.protocols_purchased || 0, icon: '🛒' },
              { label: 'Friends', value: profile.stats?.friends || 0, icon: '👥' },
              { label: 'Reviews', value: profile.stats?.reviews || 0, icon: '⭐' }
            ].map(stat => (
              <div key={stat.label} style={{
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                padding: 15,
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '1.5rem', marginBottom: 5 }}>{stat.icon}</div>
                <div style={{ color: '#fff', fontSize: '1.3rem', fontWeight: 700 }}>{stat.value}</div>
                <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>{stat.label}</div>
              </div>
            ))}
          </div>

          {/* My Badges */}
          <h3 style={{ color: '#f472b6', marginBottom: 15 }}>My Badges ({profile.badges?.length || 0})</h3>
          {profile.badges?.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 30, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa' }}>No badges yet. Start exploring to earn your first badge!</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
              {profile.badges?.map(badge => (
                <div
                  key={badge.id}
                  style={{
                    background: getRarityColor(badge.rarity),
                    borderRadius: 12,
                    padding: '12px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    minWidth: 180
                  }}
                  title={badge.description}
                >
                  <span style={{ fontSize: '1.5rem' }}>{badge.icon}</span>
                  <div>
                    <div style={{ color: '#fff', fontWeight: 600, fontSize: '0.9rem' }}>{badge.name}</div>
                    <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.7rem', textTransform: 'uppercase' }}>{badge.rarity}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* All Badges Tab */}
      {activeTab === 'badges' && (
        <div>
          <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
            Collect all badges by completing various activities on InfoPilot!
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 15 }}>
            {allBadges.map(badge => {
              const isEarned = profile?.badges?.some(b => b.id === badge.id);
              return (
                <div
                  key={badge.id}
                  style={{
                    background: isEarned ? getRarityColor(badge.rarity) : 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 12,
                    padding: 20,
                    opacity: isEarned ? 1 : 0.6,
                    border: isEarned ? 'none' : '1px dashed rgba(124, 58, 237, 0.3)',
                    position: 'relative'
                  }}
                >
                  {isEarned && (
                    <span style={{
                      position: 'absolute',
                      top: -8,
                      right: -8,
                      background: '#10b981',
                      color: '#fff',
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.8rem'
                    }}>✓</span>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: '2rem', filter: isEarned ? 'none' : 'grayscale(1)' }}>{badge.icon}</span>
                    <div>
                      <div style={{ color: '#fff', fontWeight: 600 }}>{badge.name}</div>
                      <div style={{ color: isEarned ? 'rgba(255,255,255,0.8)' : '#71717a', fontSize: '0.8rem', marginTop: 3 }}>
                        {badge.description}
                      </div>
                      <div style={{ 
                        color: isEarned ? 'rgba(255,255,255,0.6)' : '#52525b', 
                        fontSize: '0.7rem', 
                        textTransform: 'uppercase',
                        marginTop: 5
                      }}>
                        {badge.rarity}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div>
          <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
            Top InfoPilot users ranked by XP
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {leaderboard.map((entry, index) => {
              const isCurrentUser = entry.user_id === profile?.user_id;
              return (
                <div
                  key={entry.user_id}
                  style={{
                    background: isCurrentUser 
                      ? 'linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(124, 58, 237, 0.3))'
                      : 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 12,
                    padding: '15px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 15,
                    border: isCurrentUser ? '2px solid #f472b6' : '1px solid rgba(124, 58, 237, 0.2)'
                  }}
                >
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '1.1rem',
                    background: index === 0 ? '#fbbf24' : index === 1 ? '#94a3b8' : index === 2 ? '#cd7f32' : 'rgba(124, 58, 237, 0.3)',
                    color: index < 3 ? '#000' : '#fff'
                  }}>
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : entry.rank}
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#fff', fontWeight: 600 }}>
                      {entry.username}
                      {isCurrentUser && <span style={{ color: '#f472b6', marginLeft: 8, fontSize: '0.8rem' }}>(You)</span>}
                    </div>
                    <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                      Level {entry.level} • {entry.badge_count} badges
                    </div>
                  </div>
                  
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: '#fbbf24', fontWeight: 700 }}>{entry.xp.toLocaleString()} XP</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default AchievementsPage;
