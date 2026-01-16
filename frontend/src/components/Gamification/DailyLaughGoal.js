/**
 * Daily Laugh Goal - Track your daily humor intake!
 * Features streak bonuses, progress tracking, and MAXIMUM FUN!
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

// Streak bonus tiers
const STREAK_BONUSES = {
  3: { xp: 25, emoji: '🔥', message: '3-Day Streak! You are on FIRE!' },
  7: { xp: 75, emoji: '🌟', message: '1-Week Streak! A whole week of laughs!' },
  14: { xp: 150, emoji: '💪', message: '2-Week Streak! Unstoppable!' },
  30: { xp: 400, emoji: '👑', message: 'MONTHLY STREAK! You are ROYALTY!' },
  100: { xp: 1000, emoji: '⚡', message: '100-DAY STREAK! LEGENDARY STATUS!' },
};

// Motivational messages
const MOTIVATIONAL_MESSAGES = [
  "Every laugh brings you closer to your goal! 😄",
  "Keep the giggles coming! You got this! 🎯",
  "Laughter is the best medicine AND XP! 💊",
  "Your smile is powering up! ⚡",
  "The comedy gods are watching - make them proud! 🏆",
];

const DailyLaughGoal = ({ compact = false }) => {
  const { token } = useAuth();
  const [goalData, setGoalData] = useState({
    daily_goal: 10,
    current_progress: 0,
    streak_days: 0,
    longest_streak: 0,
    goal_completed_today: false,
  });
  const [loading, setLoading] = useState(true);
  const [settingGoal, setSettingGoal] = useState(false);
  const [newGoal, setNewGoal] = useState(10);
  const [showCelebration, setShowCelebration] = useState(false);

  const fetchGoalData = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/api/gamification/daily-laugh-goal`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setGoalData(data);
        setNewGoal(data.daily_goal);
      }
    } catch (e) {
      console.error('Failed to fetch laugh goal:', e);
    }
    setLoading(false);
  }, [token]);

  useEffect(() => {
    fetchGoalData();
  }, [fetchGoalData]);

  const handleSetGoal = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/gamification/daily-laugh-goal/set`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ goal: newGoal })
      });
      if (res.ok) {
        fetchGoalData();
        setSettingGoal(false);
      }
    } catch (e) {
      console.error('Failed to set goal:', e);
    }
  };

  const progress = Math.min((goalData.current_progress / goalData.daily_goal) * 100, 100);
  const nextStreakBonus = Object.entries(STREAK_BONUSES).find(
    ([days]) => parseInt(days) > goalData.streak_days
  );

  if (loading) {
    return <div style={{ padding: 20, textAlign: 'center', color: '#a1a1aa' }}>Loading your laugh goal...</div>;
  }

  if (compact) {
    return (
      <div 
        data-testid="daily-laugh-goal-compact"
        style={{
          background: goalData.goal_completed_today 
            ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2))'
            : 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(236, 72, 153, 0.2))',
          borderRadius: 12,
          padding: '12px 15px',
          border: goalData.goal_completed_today 
            ? '2px solid rgba(16, 185, 129, 0.4)'
            : '2px solid rgba(124, 58, 237, 0.3)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: '1.5rem' }}>
            {goalData.goal_completed_today ? '✅' : '🎯'}
          </span>
          <div style={{ flex: 1 }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              marginBottom: 5 
            }}>
              <span style={{ color: '#f472b6', fontWeight: 600, fontSize: '0.9rem' }}>
                Daily Goal
              </span>
              <span style={{ color: '#10b981', fontSize: '0.85rem' }}>
                {goalData.current_progress}/{goalData.daily_goal}
              </span>
            </div>
            <div style={{
              background: 'rgba(0, 0, 0, 0.3)',
              borderRadius: 10,
              height: 8,
              overflow: 'hidden'
            }}>
              <div style={{
                background: goalData.goal_completed_today 
                  ? 'linear-gradient(135deg, #10b981, #06b6d4)'
                  : 'linear-gradient(135deg, #7c3aed, #ec4899)',
                height: '100%',
                width: `${progress}%`,
                borderRadius: 10,
                transition: 'width 0.5s ease'
              }} />
            </div>
          </div>
          {goalData.streak_days > 0 && (
            <div style={{
              background: 'rgba(245, 158, 11, 0.2)',
              padding: '4px 10px',
              borderRadius: 10,
              display: 'flex',
              alignItems: 'center',
              gap: 5
            }}>
              <span>🔥</span>
              <span style={{ color: '#f59e0b', fontWeight: 700, fontSize: '0.85rem' }}>
                {goalData.streak_days}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div 
      data-testid="daily-laugh-goal"
      style={{
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(236, 72, 153, 0.15))',
        borderRadius: 16,
        padding: 20,
        border: '1px solid rgba(124, 58, 237, 0.3)'
      }}
    >
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 15 
      }}>
        <h3 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          🎯 Daily Laugh Goal
          {goalData.goal_completed_today && (
            <span style={{
              background: 'linear-gradient(135deg, #10b981, #06b6d4)',
              color: '#fff',
              padding: '4px 12px',
              borderRadius: 20,
              fontSize: '0.7rem',
              fontWeight: 700
            }}>
              ✅ COMPLETE!
            </span>
          )}
        </h3>
        <button
          onClick={() => setSettingGoal(!settingGoal)}
          style={{
            background: 'rgba(124, 58, 237, 0.3)',
            border: 'none',
            borderRadius: 8,
            padding: '6px 12px',
            color: '#a78bfa',
            cursor: 'pointer',
            fontSize: '0.8rem'
          }}
        >
          ⚙️ Set Goal
        </button>
      </div>

      {/* Goal Setting Modal */}
      {settingGoal && (
        <div style={{
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 12,
          padding: 15,
          marginBottom: 15
        }}>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 10, display: 'block' }}>
            Set your daily laugh goal (5-100):
          </label>
          <div style={{ display: 'flex', gap: 10 }}>
            <input
              type="number"
              min="5"
              max="100"
              value={newGoal}
              onChange={(e) => setNewGoal(Math.max(5, Math.min(100, parseInt(e.target.value) || 10)))}
              style={{
                flex: 1,
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid rgba(124, 58, 237, 0.3)',
                borderRadius: 8,
                padding: '8px 12px',
                color: '#fff',
                fontSize: '1rem'
              }}
            />
            <button
              onClick={handleSetGoal}
              className="btn btn-primary"
              style={{ padding: '8px 16px' }}
            >
              Save
            </button>
          </div>
        </div>
      )}

      {/* Progress */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginBottom: 8 
        }}>
          <span style={{ color: '#e2e8f0', fontWeight: 600 }}>
            {goalData.current_progress} / {goalData.daily_goal} laughs
          </span>
          <span style={{ color: '#10b981', fontWeight: 700 }}>
            {Math.round(progress)}%
          </span>
        </div>
        <div style={{
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 12,
          height: 16,
          overflow: 'hidden',
          position: 'relative'
        }}>
          <div style={{
            background: goalData.goal_completed_today 
              ? 'linear-gradient(135deg, #10b981, #06b6d4)'
              : 'linear-gradient(135deg, #7c3aed, #ec4899)',
            height: '100%',
            width: `${progress}%`,
            borderRadius: 12,
            transition: 'width 0.5s ease'
          }} />
          {/* Goal markers */}
          <div style={{
            position: 'absolute',
            right: 5,
            top: '50%',
            transform: 'translateY(-50%)',
            fontSize: '0.8rem'
          }}>
            🎯
          </div>
        </div>
        <p style={{ color: '#71717a', fontSize: '0.8rem', margin: '8px 0 0 0', fontStyle: 'italic' }}>
          {MOTIVATIONAL_MESSAGES[Math.floor(Math.random() * MOTIVATIONAL_MESSAGES.length)]}
        </p>
      </div>

      {/* Streak Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 15 }}>
        <div style={{
          background: 'rgba(245, 158, 11, 0.15)',
          borderRadius: 12,
          padding: 15,
          textAlign: 'center',
          border: '1px solid rgba(245, 158, 11, 0.3)'
        }}>
          <div style={{ fontSize: '2rem' }}>🔥</div>
          <div style={{ color: '#f59e0b', fontSize: '1.5rem', fontWeight: 800 }}>
            {goalData.streak_days}
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>Current Streak</div>
        </div>
        <div style={{
          background: 'rgba(124, 58, 237, 0.15)',
          borderRadius: 12,
          padding: 15,
          textAlign: 'center',
          border: '1px solid rgba(124, 58, 237, 0.3)'
        }}>
          <div style={{ fontSize: '2rem' }}>🏆</div>
          <div style={{ color: '#a78bfa', fontSize: '1.5rem', fontWeight: 800 }}>
            {goalData.longest_streak}
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>Best Streak</div>
        </div>
      </div>

      {/* Next Streak Bonus */}
      {nextStreakBonus && !goalData.goal_completed_today && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px dashed rgba(16, 185, 129, 0.4)',
          borderRadius: 12,
          padding: 12,
          textAlign: 'center'
        }}>
          <p style={{ color: '#10b981', margin: 0, fontSize: '0.85rem' }}>
            {nextStreakBonus[1].emoji} {parseInt(nextStreakBonus[0]) - goalData.streak_days} more days until <strong>+{nextStreakBonus[1].xp} XP</strong> bonus!
          </p>
        </div>
      )}

      {/* Stats */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-around', 
        marginTop: 15,
        paddingTop: 15,
        borderTop: '1px solid rgba(124, 58, 237, 0.2)'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#10b981', fontWeight: 700 }}>
            {goalData.total_goals_completed || 0}
          </div>
          <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Goals Hit</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#f472b6', fontWeight: 700 }}>
            {goalData.streak_xp_earned || 0}
          </div>
          <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Streak XP</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#f59e0b', fontWeight: 700 }}>
            {goalData.next_streak_bonus || '???'}
          </div>
          <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Next Bonus</div>
        </div>
      </div>
    </div>
  );
};

export default DailyLaughGoal;
