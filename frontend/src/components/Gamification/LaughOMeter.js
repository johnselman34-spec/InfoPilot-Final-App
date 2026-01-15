/**
 * InfoPilot Explorer - Laugh-O-Meter Gamification System
 * Tracks funny messages seen, awards badges for encountering Easter eggs
 * Designed for MAXIMUM LAUGHTER and user engagement! 🎉
 */
import React, { useState, useEffect, createContext, useContext } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';

// Laugh-O-Meter Context
const LaughContext = createContext();

// Laugh badges and achievements
const LAUGH_BADGES = [
  { id: 'first_giggle', name: '😄 First Giggle', description: 'Saw your first funny message!', threshold: 1, xp: 10 },
  { id: 'chuckle_champion', name: '😂 Chuckle Champion', description: 'Encountered 25 funny moments!', threshold: 25, xp: 50 },
  { id: 'laugh_legend', name: '🤣 Laugh Legend', description: 'Discovered 100 hilarious gems!', threshold: 100, xp: 100 },
  { id: 'comedy_king', name: '👑 Comedy King', description: 'Found 250 jokes - you ARE the party!', threshold: 250, xp: 250 },
  { id: 'humor_master', name: '🎭 Humor Master', description: '500 laughs! You have mastered comedy!', threshold: 500, xp: 500 },
  { id: 'giggle_god', name: '⚡ Giggle God', description: '1000 laughs! Transcended to comedy deity!', threshold: 1000, xp: 1000 },
];

const EASTER_EGG_BADGES = [
  { id: 'egg_hunter', name: '🥚 Egg Hunter', description: 'Found your first Easter egg!', rare: true, xp: 100 },
  { id: 'night_owl_laugh', name: '🦉 Night Owl Giggler', description: 'Found a joke after midnight!', rare: true, xp: 75 },
  { id: 'early_bird_smile', name: '🐦 Early Bird Smiler', description: 'Started the day with a laugh before 6 AM!', rare: true, xp: 75 },
  { id: 'rapid_fire', name: '🔥 Rapid Fire Laugher', description: 'Saw 10 jokes in under a minute!', rare: true, xp: 150 },
  { id: 'joke_collector', name: '📚 Joke Collector', description: 'Copied a joke to share with friends!', rare: true, xp: 50 },
  { id: 'bundle_comedian', name: '📦 Bundle Comedian', description: 'Bought a bundle and laughed at the tagline!', rare: true, xp: 200 },
  { id: 'evelyn_fan', name: '📖 Letters to Evelyn Fan', description: 'Clicked on a book promo!', rare: true, xp: 100 },
  { id: 'konami_master', name: '🎮 Konami Master', description: 'Entered the secret code!', legendary: true, xp: 500 },
];

// Hilarious level titles
const LAUGH_LEVELS = [
  { level: 1, title: 'Giggle Rookie', minXP: 0 },
  { level: 2, title: 'Chuckle Cadet', minXP: 100 },
  { level: 3, title: 'Snicker Specialist', minXP: 300 },
  { level: 4, title: 'Guffaw Graduate', minXP: 600 },
  { level: 5, title: 'Belly Laugh Boss', minXP: 1000 },
  { level: 6, title: 'ROFL Royalty', minXP: 1500 },
  { level: 7, title: 'LOL Legend', minXP: 2500 },
  { level: 8, title: 'LMAO Lord', minXP: 4000 },
  { level: 9, title: 'Comedy Conqueror', minXP: 6000 },
  { level: 10, title: '🏆 Supreme Humor Overlord', minXP: 10000 },
];

// Random celebration messages
const CELEBRATION_MESSAGES = [
  "🎉 YOU DID IT! Your humor game is LEGENDARY!",
  "⭐ ACHIEVEMENT UNLOCKED! You're basically a comedy genius now!",
  "🚀 LEVEL UP! Your laugh stats are off the charts!",
  "🏆 NEW BADGE! Frame this moment - you're AMAZING!",
  "💎 RARE FIND! Not everyone sees this - you're special!",
  "🌟 INCREDIBLE! Your sense of humor is unmatched!",
  "🎯 BULLSEYE! You found the hidden gem!",
  "🔥 ON FIRE! Your comedy detector is ELITE!",
];

export const LaughProvider = ({ children }) => {
  const { user, token } = useAuth();
  const [laughStats, setLaughStats] = useState({
    totalLaughs: 0,
    todayLaughs: 0,
    easterEggsFound: 0,
    badges: [],
    xp: 0,
    level: 1,
    title: 'Giggle Rookie',
    lastLaugh: null,
  });
  const [showCelebration, setShowCelebration] = useState(null);
  const [recentBadge, setRecentBadge] = useState(null);

  // Load stats from localStorage/server
  useEffect(() => {
    const loadStats = async () => {
      // Try localStorage first for quick load
      const cached = localStorage.getItem('laughStats');
      if (cached) {
        setLaughStats(JSON.parse(cached));
      }
      
      // Then sync with server if logged in
      if (token) {
        try {
          const res = await fetch(`${API}/gamification/laugh-stats`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setLaughStats(prev => ({ ...prev, ...data }));
            localStorage.setItem('laughStats', JSON.stringify(data));
          }
        } catch (e) {
          console.log('Could not sync laugh stats');
        }
      }
    };
    loadStats();
  }, [token]);

  // Calculate level from XP
  const calculateLevel = (xp) => {
    for (let i = LAUGH_LEVELS.length - 1; i >= 0; i--) {
      if (xp >= LAUGH_LEVELS[i].minXP) {
        return LAUGH_LEVELS[i];
      }
    }
    return LAUGH_LEVELS[0];
  };

  // Record a laugh (funny message seen)
  const recordLaugh = async (source = 'general', messageId = null) => {
    const newTotal = laughStats.totalLaughs + 1;
    const newToday = laughStats.todayLaughs + 1;
    let newXP = laughStats.xp + 1; // 1 XP per laugh
    let newBadges = [...laughStats.badges];
    
    // Check for new laugh count badges
    for (const badge of LAUGH_BADGES) {
      if (newTotal >= badge.threshold && !newBadges.includes(badge.id)) {
        newBadges.push(badge.id);
        newXP += badge.xp;
        setRecentBadge(badge);
        setShowCelebration(CELEBRATION_MESSAGES[Math.floor(Math.random() * CELEBRATION_MESSAGES.length)]);
        setTimeout(() => setShowCelebration(null), 4000);
      }
    }
    
    // Check for time-based Easter eggs
    const hour = new Date().getHours();
    if (hour >= 0 && hour < 5 && !newBadges.includes('night_owl_laugh')) {
      newBadges.push('night_owl_laugh');
      newXP += 75;
      setRecentBadge(EASTER_EGG_BADGES.find(b => b.id === 'night_owl_laugh'));
    }
    if (hour >= 5 && hour < 6 && !newBadges.includes('early_bird_smile')) {
      newBadges.push('early_bird_smile');
      newXP += 75;
      setRecentBadge(EASTER_EGG_BADGES.find(b => b.id === 'early_bird_smile'));
    }
    
    const levelInfo = calculateLevel(newXP);
    
    const newStats = {
      ...laughStats,
      totalLaughs: newTotal,
      todayLaughs: newToday,
      badges: newBadges,
      xp: newXP,
      level: levelInfo.level,
      title: levelInfo.title,
      lastLaugh: new Date().toISOString(),
    };
    
    setLaughStats(newStats);
    localStorage.setItem('laughStats', JSON.stringify(newStats));
    
    // Sync to server
    if (token) {
      try {
        await fetch(`${API}/gamification/record-laugh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ source, messageId })
        });
      } catch (e) {
        // Silent fail - local storage has the data
      }
    }
  };

  // Record Easter egg discovery
  const recordEasterEgg = async (eggId) => {
    if (laughStats.badges.includes(eggId)) return; // Already found
    
    const egg = EASTER_EGG_BADGES.find(e => e.id === eggId);
    if (!egg) return;
    
    const newBadges = [...laughStats.badges, eggId];
    const newXP = laughStats.xp + egg.xp;
    const newEggs = laughStats.easterEggsFound + 1;
    const levelInfo = calculateLevel(newXP);
    
    // First Easter egg badge
    if (!laughStats.badges.includes('egg_hunter')) {
      newBadges.push('egg_hunter');
    }
    
    const newStats = {
      ...laughStats,
      easterEggsFound: newEggs,
      badges: newBadges,
      xp: newXP,
      level: levelInfo.level,
      title: levelInfo.title,
    };
    
    setLaughStats(newStats);
    localStorage.setItem('laughStats', JSON.stringify(newStats));
    setRecentBadge(egg);
    setShowCelebration(`🥚 EASTER EGG FOUND! ${egg.name} - ${egg.description}`);
    setTimeout(() => setShowCelebration(null), 5000);
    
    // Sync to server
    if (token) {
      try {
        await fetch(`${API}/gamification/record-easter-egg`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ eggId })
        });
      } catch (e) {
        // Silent fail
      }
    }
  };

  // Check for Konami code
  useEffect(() => {
    const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let konamiIndex = 0;
    
    const handleKeydown = (e) => {
      if (e.key === konamiCode[konamiIndex]) {
        konamiIndex++;
        if (konamiIndex === konamiCode.length) {
          recordEasterEgg('konami_master');
          konamiIndex = 0;
        }
      } else {
        konamiIndex = 0;
      }
    };
    
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, [laughStats.badges]);

  return (
    <LaughContext.Provider value={{
      laughStats,
      recordLaugh,
      recordEasterEgg,
      showCelebration,
      recentBadge,
      setRecentBadge,
      LAUGH_BADGES,
      EASTER_EGG_BADGES,
      LAUGH_LEVELS,
    }}>
      {children}
      
      {/* Celebration Toast */}
      {showCelebration && (
        <div style={{
          position: 'fixed',
          bottom: 100,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
          color: '#fff',
          padding: '15px 30px',
          borderRadius: 20,
          boxShadow: '0 10px 40px rgba(124, 58, 237, 0.5)',
          zIndex: 10000,
          animation: 'bounceIn 0.5s ease-out',
          fontWeight: 700,
          fontSize: '1.1rem',
          textAlign: 'center',
          maxWidth: '90vw',
        }}>
          {showCelebration}
        </div>
      )}
      
      <style>{`
        @keyframes bounceIn {
          0% { transform: translateX(-50%) scale(0.5); opacity: 0; }
          50% { transform: translateX(-50%) scale(1.1); }
          100% { transform: translateX(-50%) scale(1); opacity: 1; }
        }
      `}</style>
    </LaughContext.Provider>
  );
};

// Hook to use laugh context
export const useLaugh = () => {
  const context = useContext(LaughContext);
  if (!context) {
    throw new Error('useLaugh must be used within a LaughProvider');
  }
  return context;
};

// Laugh-O-Meter Display Component
export const LaughOMeterWidget = ({ compact = false }) => {
  const { laughStats, LAUGH_LEVELS } = useLaugh();
  
  const currentLevel = LAUGH_LEVELS.find(l => l.level === laughStats.level) || LAUGH_LEVELS[0];
  const nextLevel = LAUGH_LEVELS.find(l => l.level === laughStats.level + 1);
  const progress = nextLevel 
    ? ((laughStats.xp - currentLevel.minXP) / (nextLevel.minXP - currentLevel.minXP)) * 100
    : 100;

  if (compact) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(236, 72, 153, 0.2))',
        borderRadius: 12,
        padding: '10px 15px',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        border: '1px solid rgba(124, 58, 237, 0.3)'
      }}>
        <span style={{ fontSize: '1.5rem' }}>😂</span>
        <div>
          <div style={{ color: '#f472b6', fontWeight: 700, fontSize: '0.9rem' }}>
            Lvl {laughStats.level} {currentLevel.title}
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>
            {laughStats.totalLaughs} laughs • {laughStats.xp} XP
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(236, 72, 153, 0.15))',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(124, 58, 237, 0.3)'
    }} data-testid="laugh-o-meter">
      <h3 style={{ color: '#f472b6', marginTop: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
        😂 Laugh-O-Meter
        <span style={{
          background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
          color: '#fff',
          padding: '4px 12px',
          borderRadius: 20,
          fontSize: '0.75rem',
          fontWeight: 700
        }}>
          Level {laughStats.level}
        </span>
      </h3>
      
      <div style={{ marginBottom: 15 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
          <span style={{ color: '#a78bfa', fontWeight: 600 }}>{currentLevel.title}</span>
          <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>{laughStats.xp} XP</span>
        </div>
        <div style={{
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 10,
          height: 10,
          overflow: 'hidden'
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
            height: '100%',
            width: `${Math.min(progress, 100)}%`,
            borderRadius: 10,
            transition: 'width 0.5s ease'
          }} />
        </div>
        {nextLevel && (
          <p style={{ color: '#71717a', fontSize: '0.75rem', margin: '5px 0 0 0' }}>
            {nextLevel.minXP - laughStats.xp} XP to {nextLevel.title}
          </p>
        )}
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 15 }}>
        <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.2)', padding: 10, borderRadius: 10 }}>
          <div style={{ fontSize: '1.5rem', color: '#10b981' }}>{laughStats.totalLaughs}</div>
          <div style={{ color: '#71717a', fontSize: '0.75rem' }}>Total Laughs</div>
        </div>
        <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.2)', padding: 10, borderRadius: 10 }}>
          <div style={{ fontSize: '1.5rem', color: '#f59e0b' }}>{laughStats.todayLaughs}</div>
          <div style={{ color: '#71717a', fontSize: '0.75rem' }}>Today</div>
        </div>
        <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.2)', padding: 10, borderRadius: 10 }}>
          <div style={{ fontSize: '1.5rem', color: '#ec4899' }}>{laughStats.easterEggsFound}</div>
          <div style={{ color: '#71717a', fontSize: '0.75rem' }}>Easter Eggs</div>
        </div>
      </div>
      
      <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
        🏆 Badges: {laughStats.badges.length} / {LAUGH_BADGES.length + EASTER_EGG_BADGES.length}
      </div>
    </div>
  );
};

// Badge showcase component
export const BadgeShowcase = () => {
  const { laughStats, LAUGH_BADGES, EASTER_EGG_BADGES } = useLaugh();
  
  const allBadges = [...LAUGH_BADGES, ...EASTER_EGG_BADGES];
  
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
      gap: 15
    }}>
      {allBadges.map(badge => {
        const unlocked = laughStats.badges.includes(badge.id);
        return (
          <div
            key={badge.id}
            style={{
              background: unlocked 
                ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2))'
                : 'rgba(0, 0, 0, 0.3)',
              borderRadius: 12,
              padding: 15,
              textAlign: 'center',
              border: unlocked ? '2px solid rgba(16, 185, 129, 0.5)' : '2px solid transparent',
              opacity: unlocked ? 1 : 0.5,
              transition: 'all 0.3s'
            }}
          >
            <div style={{ fontSize: '2rem', marginBottom: 8 }}>
              {unlocked ? badge.name.split(' ')[0] : '🔒'}
            </div>
            <div style={{ 
              color: unlocked ? '#10b981' : '#71717a', 
              fontWeight: 600, 
              fontSize: '0.85rem',
              marginBottom: 5
            }}>
              {badge.name.split(' ').slice(1).join(' ')}
            </div>
            <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>
              {unlocked ? badge.description : '???'}
            </div>
            {badge.rare && (
              <span style={{
                background: 'linear-gradient(135deg, #f59e0b, #f97316)',
                color: '#fff',
                padding: '2px 8px',
                borderRadius: 10,
                fontSize: '0.65rem',
                fontWeight: 700,
                marginTop: 8,
                display: 'inline-block'
              }}>
                RARE
              </span>
            )}
            {badge.legendary && (
              <span style={{
                background: 'linear-gradient(135deg, #ec4899, #7c3aed)',
                color: '#fff',
                padding: '2px 8px',
                borderRadius: 10,
                fontSize: '0.65rem',
                fontWeight: 700,
                marginTop: 8,
                display: 'inline-block'
              }}>
                LEGENDARY
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default { LaughProvider, useLaugh, LaughOMeterWidget, BadgeShowcase };
