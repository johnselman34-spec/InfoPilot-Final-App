import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import DailyLaughGoal from '../components/Gamification/DailyLaughGoal';
import { LaughOMeterWidget, BadgeShowcase } from '../components/Gamification/LaughOMeter';

const AchievementsPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [achievements, setAchievements] = useState({ earned: [], unearned: [], total_points: 0, level: 1 });
  const [allAchievements, setAllAchievements] = useState([]);
  const [weeklyLeaderboard, setWeeklyLeaderboard] = useState([]);
  const [allTimeLeaderboard, setAllTimeLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('my-achievements');
  const [shareModal, setShareModal] = useState(null);
  const [checkingNew, setCheckingNew] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      const [allRes, weeklyRes, allTimeRes] = await Promise.all([
        fetch(`${API}/gamification/achievements`),
        fetch(`${API}/gamification/leaderboard/weekly`),
        fetch(`${API}/gamification/leaderboard/all-time`)
      ]);

      if (allRes.ok) {
        const allData = await allRes.json();
        setAllAchievements(allData.achievements || []);
      }
      if (weeklyRes.ok) {
        const weeklyData = await weeklyRes.json();
        setWeeklyLeaderboard(weeklyData.leaderboard || []);
      }
      if (allTimeRes.ok) {
        const allTimeData = await allTimeRes.json();
        setAllTimeLeaderboard(allTimeData.leaderboard || []);
      }

      // Fetch user's achievements if logged in
      if (token) {
        const myRes = await fetch(`${API}/gamification/my-achievements`, { headers });
        if (myRes.ok) {
          const myData = await myRes.json();
          setAchievements(myData);
        }
      }
    } catch (e) {
      console.error('Failed to fetch gamification data:', e);
    }
    setLoading(false);
  }, [token]);

  const checkNewAchievements = async () => {
    if (!token) return;
    setCheckingNew(true);
    try {
      const res = await fetch(`${API}/gamification/check-achievements`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.new_achievements?.length > 0) {
          data.new_achievements.forEach(achievement => {
            showToast(`🏆 Achievement Unlocked: ${achievement.icon} ${achievement.name}!`, 'success');
          });
          fetchData();
        } else {
          showToast(data.message || 'Keep going! More achievements await!', 'info');
        }
      }
    } catch (e) {
      showToast('Failed to check achievements', 'error');
    }
    setCheckingNew(false);
  };

  const handleShareAchievement = async (achievementId) => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/gamification/share-achievement/${achievementId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setShareModal(data);
      }
    } catch (e) {
      showToast('Failed to generate share link', 'error');
    }
  };

  const copyShareText = async () => {
    if (shareModal?.share_message) {
      try {
        await navigator.clipboard.writeText(shareModal.share_message);
        showToast('Copied to clipboard!', 'success');
      } catch (e) {
        showToast('Failed to copy', 'error');
      }
    }
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh', color: '#fff' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: 20 }}>🏆</div>
          <p>Loading your glorious achievements...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 0' }}>
      {/* Hero Section */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.3) 0%, rgba(139, 92, 246, 0.2) 100%)',
        borderRadius: 20,
        padding: 30,
        marginBottom: 30,
        border: '1px solid rgba(245, 158, 11, 0.3)',
        textAlign: 'center'
      }}>
        <h1 style={{ 
          fontSize: '2.5rem', 
          fontWeight: 800, 
          marginBottom: 10,
          background: 'linear-gradient(135deg, #f59e0b 0%, #ec4899 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          🏆 Achievement Center
        </h1>
        <p style={{ color: '#a1a1aa', fontSize: '1.1rem', marginBottom: 20 }}>
          Collect badges, climb leaderboards, and prove you&apos;re the ultimate InfoPilot!
        </p>
        
        {/* User Stats */}
        {token && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: 30, flexWrap: 'wrap' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', color: '#f59e0b', fontWeight: 700 }}>{achievements.total_points}</div>
              <div style={{ color: '#a1a1aa' }}>Total Points</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', color: '#8b5cf6', fontWeight: 700 }}>Lv.{achievements.level}</div>
              <div style={{ color: '#a1a1aa' }}>{achievements.level_name}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', color: '#10b981', fontWeight: 700 }}>{achievements.earned?.length || 0}</div>
              <div style={{ color: '#a1a1aa' }}>Achievements</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', color: '#ec4899', fontWeight: 700 }}>{achievements.completion_percentage || 0}%</div>
              <div style={{ color: '#a1a1aa' }}>Complete</div>
            </div>
          </div>
        )}
        
        {token && (
          <button 
            onClick={checkNewAchievements}
            disabled={checkingNew}
            style={{
              marginTop: 20,
              padding: '12px 30px',
              background: checkingNew ? 'rgba(255,255,255,0.1)' : 'linear-gradient(135deg, #f59e0b 0%, #ec4899 100%)',
              border: 'none',
              borderRadius: 30,
              color: '#fff',
              fontWeight: 600,
              cursor: checkingNew ? 'wait' : 'pointer'
            }}
          >
            {checkingNew ? '🔍 Checking...' : '🎯 Check for New Achievements'}
          </button>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 25, flexWrap: 'wrap' }}>
        {['my-achievements', 'all-achievements', 'weekly-leaderboard', 'all-time-leaderboard'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 20px',
              borderRadius: 10,
              border: 'none',
              background: activeTab === tab 
                ? 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)' 
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            {tab === 'my-achievements' && '🏅 My Achievements'}
            {tab === 'all-achievements' && '📋 All Achievements'}
            {tab === 'weekly-leaderboard' && '📊 Weekly Top'}
            {tab === 'all-time-leaderboard' && '🌟 All-Time Legends'}
          </button>
        ))}
      </div>

      {/* My Achievements Tab */}
      {activeTab === 'my-achievements' && (
        <div>
          {!token ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
              <div style={{ fontSize: '3rem', marginBottom: 15 }}>🔐</div>
              <p>Log in to track your achievements!</p>
            </div>
          ) : (
            <>
              <h2 style={{ color: '#10b981', marginBottom: 20 }}>✅ Earned ({achievements.earned?.length || 0})</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 15, marginBottom: 30 }}>
                {achievements.earned?.map((achievement, i) => (
                  <div key={i} style={{
                    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(139, 92, 246, 0.1))',
                    borderRadius: 15,
                    padding: 20,
                    border: '1px solid rgba(16, 185, 129, 0.3)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 15, marginBottom: 10 }}>
                      <span style={{ fontSize: '2rem' }}>{achievement.icon}</span>
                      <div>
                        <div style={{ color: '#fff', fontWeight: 600 }}>{achievement.name}</div>
                        <div style={{ color: '#10b981', fontSize: '0.8rem' }}>+{achievement.points} pts</div>
                      </div>
                    </div>
                    <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 10 }}>{achievement.description}</p>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#71717a', fontSize: '0.75rem' }}>
                        Earned: {new Date(achievement.earned_at).toLocaleDateString()}
                      </span>
                      <button 
                        onClick={() => handleShareAchievement(achievement.id)}
                        style={{
                          padding: '5px 12px',
                          background: 'rgba(255,255,255,0.1)',
                          border: 'none',
                          borderRadius: 15,
                          color: '#8b5cf6',
                          fontSize: '0.8rem',
                          cursor: 'pointer'
                        }}
                      >
                        📤 Share
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <h2 style={{ color: '#f59e0b', marginBottom: 20 }}>🎯 Not Yet Earned ({achievements.unearned?.length || 0})</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 15 }}>
                {achievements.unearned?.map((achievement, i) => (
                  <div key={i} style={{
                    background: 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 15,
                    padding: 20,
                    border: '1px solid rgba(255,255,255,0.1)',
                    opacity: 0.7
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 15, marginBottom: 10 }}>
                      <span style={{ fontSize: '2rem', filter: 'grayscale(100%)' }}>{achievement.icon}</span>
                      <div>
                        <div style={{ color: '#fff', fontWeight: 600 }}>{achievement.name}</div>
                        <div style={{ color: '#f59e0b', fontSize: '0.8rem' }}>+{achievement.points} pts</div>
                      </div>
                    </div>
                    <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>{achievement.description}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* All Achievements Tab */}
      {activeTab === 'all-achievements' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 15 }}>
          {allAchievements.map((achievement, i) => (
            <div key={i} style={{
              background: 'rgba(30, 20, 50, 0.6)',
              borderRadius: 15,
              padding: 20,
              border: '1px solid rgba(139, 92, 246, 0.2)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 15, marginBottom: 10 }}>
                <span style={{ fontSize: '2rem' }}>{achievement.icon}</span>
                <div>
                  <div style={{ color: '#fff', fontWeight: 600 }}>{achievement.name}</div>
                  <div style={{ color: '#8b5cf6', fontSize: '0.8rem' }}>+{achievement.points} pts • {achievement.category}</div>
                </div>
              </div>
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>{achievement.description}</p>
            </div>
          ))}
        </div>
      )}

      {/* Weekly Leaderboard Tab */}
      {activeTab === 'weekly-leaderboard' && (
        <div style={{
          background: 'rgba(30, 20, 50, 0.6)',
          borderRadius: 20,
          padding: 25,
          border: '1px solid rgba(245, 158, 11, 0.2)'
        }}>
          <h2 style={{ color: '#f59e0b', marginBottom: 20 }}>📊 This Week&apos;s Top Sellers</h2>
          {weeklyLeaderboard.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
              <div style={{ fontSize: '3rem', marginBottom: 15 }}>🏆</div>
              <p>No sales yet this week. Be the first to claim the crown!</p>
            </div>
          ) : (
            <div>
              {weeklyLeaderboard.map((entry, i) => (
                <div key={i} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 20,
                  padding: 15,
                  background: i === 0 ? 'rgba(255, 215, 0, 0.1)' : 'transparent',
                  borderRadius: 10,
                  marginBottom: 10,
                  border: i === 0 ? '1px solid rgba(255, 215, 0, 0.3)' : 'none'
                }}>
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: i === 0 ? '#ffd700' : i === 1 ? '#c0c0c0' : i === 2 ? '#cd7f32' : 'rgba(255,255,255,0.1)',
                    color: i < 3 ? '#000' : '#fff',
                    fontWeight: 700
                  }}>
                    {entry.rank}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#fff', fontWeight: 600 }}>{entry.username}</div>
                    <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                      {entry.weekly_sales} sales • ${entry.weekly_revenue?.toFixed(2)} earned
                    </div>
                  </div>
                  {i === 0 && <span style={{ fontSize: '1.5rem' }}>👑</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* All-Time Leaderboard Tab */}
      {activeTab === 'all-time-leaderboard' && (
        <div style={{
          background: 'rgba(30, 20, 50, 0.6)',
          borderRadius: 20,
          padding: 25,
          border: '1px solid rgba(139, 92, 246, 0.2)'
        }}>
          <h2 style={{ color: '#8b5cf6', marginBottom: 20 }}>🌟 All-Time Achievement Legends</h2>
          {allTimeLeaderboard.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
              <div style={{ fontSize: '3rem', marginBottom: 15 }}>🏆</div>
              <p>Start earning achievements to climb the leaderboard!</p>
            </div>
          ) : (
            <div>
              {allTimeLeaderboard.map((entry, i) => (
                <div key={i} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 20,
                  padding: 15,
                  background: i === 0 ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
                  borderRadius: 10,
                  marginBottom: 10,
                  border: i === 0 ? '1px solid rgba(139, 92, 246, 0.3)' : 'none'
                }}>
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: i === 0 ? 'linear-gradient(135deg, #8b5cf6, #ec4899)' : 'rgba(255,255,255,0.1)',
                    color: '#fff',
                    fontWeight: 700
                  }}>
                    {entry.rank}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#fff', fontWeight: 600 }}>{entry.username}</div>
                    <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                      {entry.total_points} points • {entry.achievement_count} achievements • {entry.level_name}
                    </div>
                  </div>
                  {i === 0 && <span style={{ fontSize: '1.5rem' }}>🏆</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Share Modal */}
      {shareModal && (
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
          zIndex: 1000
        }} onClick={() => setShareModal(null)}>
          <div style={{
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            borderRadius: 20,
            padding: 30,
            maxWidth: 500,
            width: '90%',
            border: '1px solid rgba(139, 92, 246, 0.3)'
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ color: '#fff', marginBottom: 20 }}>📤 Share Your Achievement!</h3>
            <div style={{
              background: 'rgba(0,0,0,0.3)',
              padding: 15,
              borderRadius: 10,
              marginBottom: 20
            }}>
              <p style={{ color: '#e0e0e0', fontSize: '0.9rem', whiteSpace: 'pre-wrap' }}>
                {shareModal.share_message}
              </p>
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button 
                onClick={copyShareText}
                style={{
                  flex: 1,
                  padding: '12px 20px',
                  background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                  border: 'none',
                  borderRadius: 10,
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                📋 Copy Text
              </button>
              <a 
                href={shareModal.platforms?.twitter}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  flex: 1,
                  padding: '12px 20px',
                  background: '#1da1f2',
                  border: 'none',
                  borderRadius: 10,
                  color: '#fff',
                  fontWeight: 600,
                  textDecoration: 'none',
                  textAlign: 'center'
                }}
              >
                🐦 Twitter
              </a>
              <button 
                onClick={() => setShareModal(null)}
                style={{
                  padding: '12px 20px',
                  background: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  borderRadius: 10,
                  color: '#fff',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Book Promo */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
        borderRadius: 20,
        padding: 30,
        marginTop: 30,
        border: '1px solid rgba(236, 72, 153, 0.3)',
        textAlign: 'center'
      }}>
        <h3 style={{ color: '#f472b6', marginBottom: 15, fontSize: '1.3rem' }}>
          📚 Achievement Unlocked: Book Reader!
        </h3>
        <p style={{ color: '#fff', fontSize: '1rem', marginBottom: 15, maxWidth: 600, margin: '0 auto 15px' }}>
          Want the ultimate achievement? Read &quot;Letters to Evelyn&quot; - a supernatural thriller comedy 
          so good, even the ghosts wrote 5-star reviews! (Well, they would have if they had Amazon accounts...)
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
            fontSize: '1rem',
            cursor: 'pointer'
          }}
        >
          📖 Unlock the Book Achievement - Only $2.99!
        </button>
      </div>
    </div>
  );
};

export default AchievementsPage;
