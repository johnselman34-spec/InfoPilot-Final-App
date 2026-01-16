/**
 * Floating Easter Eggs - The ULTIMATE Easter Egg Experience!
 * 
 * A fun gamification feature where colorful Easter eggs randomly float
 * across the screen. Users can click/catch them to earn rewards like:
 * - Protocol ideas
 * - Funny jokes (inspired by "Letters to Evelyn" by John Selman)
 * - Protocol pricing ideas
 * - Laughter points & XP
 * 
 * Born from a story of resilience - turning life's challenges into laughter!
 * "I survived January 3rd, 2000, and became a Hollywood Star!" 🌟
 * 
 * Inspired by John Selman's incredible journey from Naval Aviation to bestselling author.
 * Check out "Letters to Evelyn" on Amazon and ReadersFavorite.com!
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useLaugh } from './LaughOMeter';
import { useAuth } from '../../contexts/AuthContext';

// Easter Egg reward types - with EXTREMELY FUNNY jokes inspired by John Selman's story!
const EGG_REWARDS = [
  // Protocol Ideas - Enhanced with aviation themes
  { type: 'protocol', emoji: '📋', title: 'Protocol Idea!', rewards: [
    '(breaking news or latest updates) & (politics or government) & (analysis or opinion)+',
    '(scientific study or research paper) & (peer reviewed or published) & (findings or results)',
    '(aviation or flight or pilot) & (training or career or military) & (success or achievement)+',
    '(memoir or autobiography) & (survival or resilience) & (inspiring or motivational)+',
    '(health tips or wellness) & (doctor recommended or expert) & (natural or organic)+',
    '(financial advice or investment) & (stocks or crypto) & (beginner or expert)+',
    '(book review or literary criticism) & (bestseller or award winning) & (fiction or non-fiction)+',
    '(travel guide or destination) & (hidden gems or local tips) & (budget or affordable)',
    '(supernatural or paranormal) & (true story or documentary) & (evidence or investigation)+',
    '(family drama or memoir) & (overcoming adversity or triumph) & (inspirational)+',
  ]},
  
  // EXTREMELY FUNNY Jokes - Inspired by "Letters to Evelyn" by John Selman (with irreverent humor!)
  { type: 'joke', emoji: '😂', title: 'LOL Moment!', rewards: [
    "John's stepmother tried to poison him. Plot twist: He wrote a bestseller about it! Her cooking finally DID achieve something remarkable! 🥚📚",
    "My stepmother locked me in an oven at 130 degrees. Years later, I produced a movie. Guess which one of us is 'well done' now? 🔥🎬",
    "John wanted to fly jets like his dad. His stepmother wanted to give him a different kind of 'trip'. He chose the one with ACTUAL wings! ✈️",
    "Why did John's commanding officer call him Jesus? Because he survived his stepmother's 'Last Supper' and came back! 😇🍳",
    "My stepmother used military-grade interrogation drugs in my eggs. 10 months of hallucinations later, I got a 5-star book review. Worth it? 📖⭐",
    "John: *survives poisoning* John: *writes bestseller* John: *produces movie* Stepmother: 'Wait, that wasn't the plan...' 😱🏆",
    "What's the difference between John's stepmother and a pilot? A pilot's 'trips' have RETURN tickets! ✈️🎫",
    "John's dad flew A-4 Skyhawks. John's stepmother tried to make him see things that fly too. Different vibe entirely! 👽",
    "My stepmother's eggs were so 'special' they came with a 10-month hallucination package. No frequent flyer miles though! 🥚✨",
    "Why read 'Letters to Evelyn'? It has: ✈️ Aviation drama, 💕 Love story, 🦹‍♀️ World's worst villain, 🏆 5-star reviews! (Amazon it!)",
    "John went from 'Superman' on the USS Enterprise to 'Trash-O' (Waste Processing Officer). Still better than his stepmother's cooking! 🦸‍♂️→🗑️",
    "My stepmother's jealousy of my dad's aviation career was so intense, she tried to give ME a 'grounding' I'd never forget! ✈️📖",
    "Plot twist: The breakfast that was supposed to end John's story BECAME his story. Now THAT's what I call character development! 🍳→📚",
    "John's stepmother thought she was writing his ending. Instead, she wrote his BEGINNING. Thanks for the book material! 😂📖",
    "Why did John become famous? His stepmother's 'special recipe' + 10 months of cosmic visions = Amazon bestseller! 🌟📚",
    "From Navy pilot dreams to bestselling author... via a 'breakfast detour'. Life's flight path is rarely straight! ✈️🥚📖",
  ]},
  
  // Protocol Pricing Ideas - Enhanced with author wisdom
  { type: 'pricing', emoji: '💰', title: 'Pricing Wisdom!', rewards: [
    '💡 Start with FREE protocols to build your reputation - John Selman started with just a story and became a bestseller!',
    '🎯 Bundle 5 related protocols for $4.99 - everyone loves a deal! Like getting the whole "survival story" package!',
    '⭐ Premium exclusives at $2.99 perform better than $0.99! Quality matters - ask any pilot!',
    '📈 A/B test your prices - sometimes higher = more perceived value! Like hardcover vs paperback!',
    '🤝 Offer a "Pay What You Want" option - trust builds loyalty! John trusted his readers and they trusted him back!',
    '🔥 Flash sales (50% off for 24hrs) create urgency! Limited time, like Johns limited patience with bad eggs!',
    '💎 Create a "Pro Bundle" at $9.99 with your best 10 protocols! The "Full Story" package!',
    '🎁 Holiday specials work wonders - Easter eggs, anyone? 🥚 (Disclaimer: no hallucinations included)',
    '✈️ Price like a pilot: start low to gain altitude, then cruise at premium! 🛫',
    '📚 Authors like John prove: quality content sells itself. Invest in your protocols!',
  ]},
  
  // Motivational Messages - Survival & Success themed
  { type: 'motivation', emoji: '💪', title: "Survivor's Wisdom!", rewards: [
    '🌟 Every search brings you closer to knowledge - keep exploring! John searched for answers and found fame!',
    "🚀 You're building something incredible, one protocol at a time! Like John built his book, one letter at a time!",
    '🏆 Winners are just losers who tried one more time! John tried one more flight after every setback!',
    "💫 Your curiosity today shapes tomorrow's breakthroughs! John's curiosity about Evelyn shaped a bestseller!",
    "🎯 Focus + Consistency = Unstoppable! Even military-grade obstacles couldn't stop John!",
    "⚡ The best time to start was yesterday. The second best time is NOW! John didn't wait to write his story!",
    '🌈 After every storm comes a rainbow! After every bad egg comes... well, a book deal apparently! 📚',
    "🔥 You survived 100% of your worst days. John survived worse - you've got this! 💪",
    "✈️ Like a pilot, keep your eyes on the horizon. The turbulence doesn't last forever! 🛫",
    "📖 Your story isn't over yet. John's best chapters came AFTER his worst days! 🌟",
  ]},
  
  // Fun Facts - Aviation & Literary themed
  { type: 'fact', emoji: '🧠', title: 'Did You Know?', rewards: [
    "✈️ Naval aviators like John Selman's father flew the legendary A-4 Skyhawk - one of the most agile jets ever made!",
    '📚 "Letters to Evelyn" received 5 stars from Readers Favorite - a prestigious book review platform!',
    "🛫 The T-34C Turbomentor (John's training aircraft in Roswell) has trained thousands of Navy pilots since 1977!",
    '🌍 Honey never spoils - archaeologists found 3000-year-old honey still edible! (Much safer than some eggs...)',
    "💜 The USS Enterprise (where John served) was the world's first nuclear-powered aircraft carrier!",
    "🐙 Octopuses have three hearts and blue blood - almost as mysterious as John's journey!",
    "⚡ A bolt of lightning is 5x hotter than the surface of the sun - almost as hot as this app's features!",
    '🦋 Butterflies taste with their feet - probably a safer way to test food than what John experienced!',
    "📱 The first mobile phone call was made in 1973 - the same decade John's father was flying!",
    '🎬 John Selman went from Navy pilot to movie producer - talk about a plot twist! 🎥',
  ]},
  
  // Secret Tips - Enhanced with insider knowledge
  { type: 'secret', emoji: '🤫', title: 'Insider Secret!', rewards: [
    '🔑 Pro tip: Use "and" between parentheses - it works just like "&" in protocols!',
    '🎮 Konami code (↑↑↓↓←→←→BA) unlocks a secret badge! Like finding a hidden chapter!',
    '🌙 Search at night? You might earn the Night Owl badge! John wrote many letters at night!',
    '📊 The Statistics page now shows your Easter Egg catching stats! Check it out!',
    "🗺️ The Map View reveals geographical trends - trace John's journey from Roswell to the Enterprise!",
    '🎯 Categories with + at the end boost priority in results! Like adding extra engine power!',
    '💎 FREE protocols often get more downloads than paid ones! Build your squadron first!',
    '📈 Check your Analytics daily - knowledge is power! John analyzed his experiences into a book!',
    '📚 Visit https://www.amazon.com - search "Letters to Evelyn by John Selman" for more of the story!',
    '⭐ Check out readersfavorite.com for the 5-star review of "Letters to Evelyn"! 🏆',
  ]},
];

// Egg colors and styles
const EGG_STYLES = [
  { bg: 'linear-gradient(135deg, #ff6b6b, #feca57)', spots: '#fff5e6' },
  { bg: 'linear-gradient(135deg, #5f27cd, #a29bfe)', spots: '#e4dffb' },
  { bg: 'linear-gradient(135deg, #00d2d3, #1dd1a1)', spots: '#e3fcf9' },
  { bg: 'linear-gradient(135deg, #ff9ff3, #f368e0)', spots: '#ffe8fb' },
  { bg: 'linear-gradient(135deg, #ffeaa7, #fdcb6e)', spots: '#fff9e6' },
  { bg: 'linear-gradient(135deg, #74b9ff, #0984e3)', spots: '#e6f2ff' },
  { bg: 'linear-gradient(135deg, #ff7675, #d63031)', spots: '#ffe6e6' },
  { bg: 'linear-gradient(135deg, #55efc4, #00b894)', spots: '#e6fff5' },
];

// XP rewards per egg type
const XP_REWARDS = {
  protocol: 25,
  joke: 15,
  pricing: 20,
  motivation: 10,
  fact: 15,
  secret: 30,
};

const FloatingEgg = ({ egg, onCatch }) => {
  const [position, setPosition] = useState(egg.startPosition);
  const [isVisible, setIsVisible] = useState(true);
  const [isCaught, setIsCaught] = useState(false);
  
  useEffect(() => {
    if (isCaught) return;
    
    const animate = () => {
      setPosition(prev => {
        const newX = prev.x + egg.velocityX;
        const newY = prev.y + egg.velocityY;
        
        // Remove if off screen
        if (newX > window.innerWidth + 100 || newX < -100 || 
            newY > window.innerHeight + 100 || newY < -100) {
          setIsVisible(false);
          return prev;
        }
        
        return { x: newX, y: newY };
      });
    };
    
    const interval = setInterval(animate, 50);
    return () => clearInterval(interval);
  }, [egg.velocityX, egg.velocityY, isCaught]);
  
  const handleClick = () => {
    if (isCaught) return;
    setIsCaught(true);
    onCatch(egg);
    setTimeout(() => setIsVisible(false), 500);
  };
  
  if (!isVisible) return null;
  
  return (
    <div
      onClick={handleClick}
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        width: egg.size,
        height: egg.size * 1.3,
        background: egg.style.bg,
        borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
        cursor: 'pointer',
        zIndex: 9999,
        transform: `rotate(${egg.rotation}deg) scale(${isCaught ? 1.5 : 1})`,
        opacity: isCaught ? 0 : 1,
        transition: isCaught ? 'all 0.5s ease-out' : 'none',
        boxShadow: '0 4px 15px rgba(0,0,0,0.3), inset 0 -5px 15px rgba(0,0,0,0.2)',
        animation: `wobble ${egg.wobbleSpeed}s ease-in-out infinite`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      title="🥚 Catch me for a reward!"
    >
      {/* Egg spots/patterns */}
      <div style={{
        position: 'absolute',
        width: '30%',
        height: '30%',
        background: egg.style.spots,
        borderRadius: '50%',
        top: '20%',
        left: '15%',
        opacity: 0.8,
      }} />
      <div style={{
        position: 'absolute',
        width: '20%',
        height: '20%',
        background: egg.style.spots,
        borderRadius: '50%',
        top: '40%',
        right: '20%',
        opacity: 0.6,
      }} />
      <div style={{
        position: 'absolute',
        width: '15%',
        height: '15%',
        background: egg.style.spots,
        borderRadius: '50%',
        bottom: '30%',
        left: '25%',
        opacity: 0.5,
      }} />
      
      {/* Shine effect */}
      <div style={{
        position: 'absolute',
        width: '25%',
        height: '35%',
        background: 'linear-gradient(135deg, rgba(255,255,255,0.6), transparent)',
        borderRadius: '50%',
        top: '15%',
        left: '15%',
      }} />
    </div>
  );
};

// Reward popup component
const RewardPopup = ({ reward, onClose }) => {
  if (!reward) return null;
  
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 10001,
      animation: 'fadeIn 0.3s ease-out',
    }} onClick={onClose}>
      <div 
        style={{
          background: 'linear-gradient(135deg, #2d1f4e, #1a1035)',
          borderRadius: 20,
          padding: 30,
          maxWidth: 450,
          width: '90%',
          border: '3px solid #7c3aed',
          boxShadow: '0 20px 60px rgba(124, 58, 237, 0.5)',
          animation: 'bounceIn 0.5s ease-out',
          textAlign: 'center',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Celebration header */}
        <div style={{ fontSize: '4rem', marginBottom: 15 }}>
          {reward.emoji} 🥚 {reward.emoji}
        </div>
        
        <h2 style={{ 
          color: '#f472b6', 
          fontSize: '1.5rem', 
          margin: '0 0 10px 0',
          textShadow: '0 2px 10px rgba(244, 114, 182, 0.5)'
        }}>
          {reward.title}
        </h2>
        
        <div style={{
          background: 'rgba(124, 58, 237, 0.2)',
          borderRadius: 12,
          padding: 20,
          marginBottom: 20,
          border: '1px solid rgba(124, 58, 237, 0.3)',
        }}>
          <p style={{ 
            color: '#e5e7eb', 
            fontSize: '1rem', 
            margin: 0,
            lineHeight: 1.6,
            fontFamily: reward.type === 'protocol' ? 'monospace' : 'inherit',
          }}>
            {reward.content}
          </p>
        </div>
        
        {/* XP earned */}
        <div style={{
          background: 'linear-gradient(135deg, #10b981, #059669)',
          borderRadius: 20,
          padding: '8px 20px',
          display: 'inline-block',
          marginBottom: 15,
        }}>
          <span style={{ color: '#fff', fontWeight: 700, fontSize: '1.1rem' }}>
            +{reward.xp} XP Earned! 🎉
          </span>
        </div>
        
        {/* Copy button for protocols */}
        {reward.type === 'protocol' && (
          <button
            onClick={() => {
              navigator.clipboard.writeText(reward.content);
              // Show mini toast
            }}
            style={{
              display: 'block',
              width: '100%',
              padding: '12px',
              background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '1rem',
              marginBottom: 15,
            }}
          >
            📋 Copy Protocol to Clipboard
          </button>
        )}
        
        <button
          onClick={onClose}
          style={{
            padding: '10px 30px',
            background: 'rgba(255,255,255,0.1)',
            color: '#a1a1aa',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 8,
            cursor: 'pointer',
            fontSize: '0.9rem',
          }}
        >
          Awesome! Close
        </button>
      </div>
    </div>
  );
};

// Main floating eggs controller
export const FloatingEasterEggsController = ({ enabled = true, frequency = 30000 }) => {
  const [eggs, setEggs] = useState([]);
  const [currentReward, setCurrentReward] = useState(null);
  const [stats, setStats] = useState({ caught: 0, total: 0 });
  const { recordLaugh, recordEasterEgg } = useLaugh();
  const { token } = useAuth();
  const eggIdCounter = useRef(0);
  
  // Spawn new eggs periodically
  useEffect(() => {
    if (!enabled) return;
    
    const spawnEgg = () => {
      const edge = Math.floor(Math.random() * 4); // 0=top, 1=right, 2=bottom, 3=left
      let startX, startY, velX, velY;
      
      switch (edge) {
        case 0: // From top
          startX = Math.random() * window.innerWidth;
          startY = -60;
          velX = (Math.random() - 0.5) * 3;
          velY = Math.random() * 2 + 1;
          break;
        case 1: // From right
          startX = window.innerWidth + 60;
          startY = Math.random() * window.innerHeight;
          velX = -(Math.random() * 2 + 1);
          velY = (Math.random() - 0.5) * 3;
          break;
        case 2: // From bottom
          startX = Math.random() * window.innerWidth;
          startY = window.innerHeight + 60;
          velX = (Math.random() - 0.5) * 3;
          velY = -(Math.random() * 2 + 1);
          break;
        default: // From left
          startX = -60;
          startY = Math.random() * window.innerHeight;
          velX = Math.random() * 2 + 1;
          velY = (Math.random() - 0.5) * 3;
      }
      
      const rewardCategory = EGG_REWARDS[Math.floor(Math.random() * EGG_REWARDS.length)];
      const rewardContent = rewardCategory.rewards[Math.floor(Math.random() * rewardCategory.rewards.length)];
      
      const newEgg = {
        id: ++eggIdCounter.current,
        startPosition: { x: startX, y: startY },
        velocityX: velX,
        velocityY: velY,
        size: 40 + Math.random() * 20,
        rotation: Math.random() * 30 - 15,
        wobbleSpeed: 1 + Math.random() * 0.5,
        style: EGG_STYLES[Math.floor(Math.random() * EGG_STYLES.length)],
        reward: {
          type: rewardCategory.type,
          emoji: rewardCategory.emoji,
          title: rewardCategory.title,
          content: rewardContent,
          xp: XP_REWARDS[rewardCategory.type],
        },
      };
      
      setEggs(prev => [...prev, newEgg]);
      setStats(prev => ({ ...prev, total: prev.total + 1 }));
    };
    
    // Spawn initial egg after short delay
    const initialTimeout = setTimeout(spawnEgg, 5000);
    
    // Spawn eggs periodically
    const interval = setInterval(spawnEgg, frequency);
    
    return () => {
      clearTimeout(initialTimeout);
      clearInterval(interval);
    };
  }, [enabled, frequency]);
  
  // Clean up old eggs
  useEffect(() => {
    const cleanup = setInterval(() => {
      setEggs(prev => prev.filter(egg => 
        egg.id > eggIdCounter.current - 20 // Keep only recent eggs
      ));
    }, 10000);
    
    return () => clearInterval(cleanup);
  }, []);
  
  const handleCatch = useCallback((egg) => {
    setCurrentReward(egg.reward);
    setStats(prev => ({ ...prev, caught: prev.caught + 1 }));
    
    // Record the catch
    recordLaugh('easter_egg', `egg_${egg.id}`);
    
    // First catch earns special badge
    if (stats.caught === 0) {
      recordEasterEgg('egg_hunter');
    }
    
    // Remove caught egg
    setEggs(prev => prev.filter(e => e.id !== egg.id));
  }, [recordLaugh, recordEasterEgg, stats.caught]);
  
  if (!enabled) return null;
  
  return (
    <>
      {/* Floating eggs */}
      {eggs.map(egg => (
        <FloatingEgg key={egg.id} egg={egg} onCatch={handleCatch} />
      ))}
      
      {/* Reward popup */}
      <RewardPopup 
        reward={currentReward} 
        onClose={() => setCurrentReward(null)} 
      />
      
      {/* Egg counter (optional mini display) */}
      {stats.caught > 0 && (
        <div style={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
          color: '#fff',
          padding: '8px 15px',
          borderRadius: 20,
          fontSize: '0.85rem',
          fontWeight: 700,
          zIndex: 9998,
          boxShadow: '0 4px 15px rgba(124, 58, 237, 0.4)',
        }}>
          🥚 {stats.caught} eggs caught!
        </div>
      )}
      
      {/* CSS animations */}
      <style>{`
        @keyframes wobble {
          0%, 100% { transform: rotate(-15deg); }
          50% { transform: rotate(15deg); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes bounceIn {
          0% { transform: scale(0.5); opacity: 0; }
          60% { transform: scale(1.1); }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </>
  );
};

// Export stats component for settings/profile pages
export const EasterEggStats = () => {
  const [stats, setStats] = useState(() => {
    const cached = localStorage.getItem('easterEggStats');
    return cached ? JSON.parse(cached) : { caught: 0, total: 0, rewards: [] };
  });
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(236, 72, 153, 0.15))',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(124, 58, 237, 0.3)',
    }}>
      <h3 style={{ color: '#f472b6', marginTop: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
        🥚 Easter Egg Collection
      </h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 15 }}>
        <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.2)', padding: 15, borderRadius: 10 }}>
          <div style={{ fontSize: '2rem', color: '#10b981' }}>{stats.caught}</div>
          <div style={{ color: '#71717a', fontSize: '0.8rem' }}>Eggs Caught</div>
        </div>
        <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.2)', padding: 15, borderRadius: 10 }}>
          <div style={{ fontSize: '2rem', color: '#f59e0b' }}>{stats.caught * 15}</div>
          <div style={{ color: '#71717a', fontSize: '0.8rem' }}>XP Earned</div>
        </div>
        <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.2)', padding: 15, borderRadius: 10 }}>
          <div style={{ fontSize: '2rem', color: '#ec4899' }}>{Math.round((stats.caught / (stats.total || 1)) * 100)}%</div>
          <div style={{ color: '#71717a', fontSize: '0.8rem' }}>Catch Rate</div>
        </div>
      </div>
      
      <p style={{ color: '#a1a1aa', fontSize: '0.85rem', marginTop: 15, marginBottom: 0, textAlign: 'center' }}>
        Keep your eyes peeled for floating Easter eggs! 👀
      </p>
    </div>
  );
};

// Reward History Component - Shows all collected rewards with share functionality
export const EasterEggRewardHistory = () => {
  const [rewards, setRewards] = useState(() => {
    const cached = localStorage.getItem('easterEggRewards');
    return cached ? JSON.parse(cached) : [];
  });
  const [filter, setFilter] = useState('all');
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareReward, setShareReward] = useState(null);
  
  // Save reward to history
  const saveReward = (reward) => {
    const newRewards = [...rewards, { ...reward, timestamp: new Date().toISOString(), id: Date.now() }];
    setRewards(newRewards);
    localStorage.setItem('easterEggRewards', JSON.stringify(newRewards.slice(-100))); // Keep last 100
  };
  
  // Filter rewards by type
  const filteredRewards = filter === 'all' 
    ? rewards 
    : rewards.filter(r => r.type === filter);
  
  // Share to social media
  const shareToSocial = (platform, reward) => {
    const text = encodeURIComponent(`🥚 I caught an Easter Egg on InfoPilot Explorer!\n\n"${reward.content.substring(0, 100)}..."\n\n#InfoPilot #EasterEgg`);
    const url = encodeURIComponent('https://infopilot.com');
    
    const urls = {
      twitter: `https://twitter.com/intent/tweet?text=${text}&url=${url}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}&quote=${text}`,
    };
    
    window.open(urls[platform], '_blank', 'width=600,height=400');
    setShowShareModal(false);
  };
  
  // Copy reward to clipboard
  const copyReward = (content) => {
    navigator.clipboard.writeText(content);
  };
  
  const typeEmojis = {
    protocol: '📋',
    joke: '😂',
    pricing: '💰',
    motivation: '💪',
    fact: '🧠',
    secret: '🤫'
  };
  
  const typeLabels = {
    protocol: 'Protocol Ideas',
    joke: 'Jokes',
    pricing: 'Pricing Tips',
    motivation: 'Motivation',
    fact: 'Fun Facts',
    secret: 'Secrets'
  };
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(236, 72, 153, 0.1))',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(124, 58, 237, 0.3)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 10 }}>
        <h3 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          🎁 Reward Collection ({rewards.length})
        </h3>
        
        {/* Filter buttons */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            onClick={() => setFilter('all')}
            style={{
              background: filter === 'all' ? 'rgba(124, 58, 237, 0.3)' : 'rgba(0,0,0,0.2)',
              color: filter === 'all' ? '#a78bfa' : '#71717a',
              border: 'none',
              padding: '5px 12px',
              borderRadius: 15,
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            All
          </button>
          {Object.entries(typeLabels).map(([type, label]) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              style={{
                background: filter === type ? 'rgba(124, 58, 237, 0.3)' : 'rgba(0,0,0,0.2)',
                color: filter === type ? '#a78bfa' : '#71717a',
                border: 'none',
                padding: '5px 12px',
                borderRadius: 15,
                fontSize: '0.75rem',
                cursor: 'pointer'
              }}
            >
              {typeEmojis[type]} {label}
            </button>
          ))}
        </div>
      </div>
      
      {filteredRewards.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 30, color: '#71717a' }}>
          <div style={{ fontSize: '3rem', marginBottom: 10 }}>🥚</div>
          <p>No rewards collected yet. Catch some eggs!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 12, maxHeight: 400, overflowY: 'auto' }}>
          {filteredRewards.slice().reverse().map((reward, idx) => (
            <div 
              key={reward.id || idx}
              style={{
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 10,
                padding: 15,
                border: '1px solid rgba(124, 58, 237, 0.2)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <span style={{ fontSize: '1.2rem' }}>{typeEmojis[reward.type]}</span>
                    <span style={{ color: '#f472b6', fontWeight: 600, fontSize: '0.9rem' }}>
                      {reward.title}
                    </span>
                    <span style={{
                      background: 'rgba(16, 185, 129, 0.2)',
                      color: '#10b981',
                      padding: '2px 8px',
                      borderRadius: 10,
                      fontSize: '0.7rem'
                    }}>
                      +{reward.xp} XP
                    </span>
                  </div>
                  <p style={{ 
                    color: '#d1d5db', 
                    fontSize: '0.85rem', 
                    margin: 0, 
                    lineHeight: 1.5,
                    fontFamily: reward.type === 'protocol' ? 'monospace' : 'inherit'
                  }}>
                    {reward.content}
                  </p>
                  {reward.timestamp && (
                    <div style={{ color: '#71717a', fontSize: '0.7rem', marginTop: 8 }}>
                      Caught: {new Date(reward.timestamp).toLocaleDateString()}
                    </div>
                  )}
                </div>
                
                {/* Action buttons */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  <button
                    onClick={() => copyReward(reward.content)}
                    style={{
                      background: 'rgba(124, 58, 237, 0.2)',
                      border: 'none',
                      color: '#a78bfa',
                      padding: '5px 10px',
                      borderRadius: 5,
                      fontSize: '0.7rem',
                      cursor: 'pointer'
                    }}
                    title="Copy to clipboard"
                  >
                    📋 Copy
                  </button>
                  <button
                    onClick={() => { setShareReward(reward); setShowShareModal(true); }}
                    style={{
                      background: 'rgba(236, 72, 153, 0.2)',
                      border: 'none',
                      color: '#f472b6',
                      padding: '5px 10px',
                      borderRadius: 5,
                      fontSize: '0.7rem',
                      cursor: 'pointer'
                    }}
                    title="Share to social media"
                  >
                    📤 Share
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Share Modal */}
      {showShareModal && shareReward && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10002
        }} onClick={() => setShowShareModal(false)}>
          <div style={{
            background: 'linear-gradient(135deg, #2d1f4e, #1a1035)',
            borderRadius: 16,
            padding: 25,
            maxWidth: 400,
            width: '90%',
            border: '2px solid rgba(124, 58, 237, 0.4)'
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ color: '#f472b6', marginTop: 0 }}>📤 Share Your Reward!</h3>
            
            <div style={{ 
              background: 'rgba(0,0,0,0.3)', 
              borderRadius: 10, 
              padding: 15, 
              marginBottom: 20 
            }}>
              <p style={{ color: '#d1d5db', fontSize: '0.85rem', margin: 0 }}>
                {shareReward.content.substring(0, 150)}...
              </p>
            </div>
            
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={() => shareToSocial('twitter', shareReward)}
                style={{
                  flex: 1,
                  background: '#1DA1F2',
                  color: '#fff',
                  border: 'none',
                  padding: '12px',
                  borderRadius: 8,
                  cursor: 'pointer',
                  fontWeight: 600
                }}
              >
                🐦 Twitter
              </button>
              <button
                onClick={() => shareToSocial('facebook', shareReward)}
                style={{
                  flex: 1,
                  background: '#4267B2',
                  color: '#fff',
                  border: 'none',
                  padding: '12px',
                  borderRadius: 8,
                  cursor: 'pointer',
                  fontWeight: 600
                }}
              >
                📘 Facebook
              </button>
            </div>
            
            <button
              onClick={() => setShowShareModal(false)}
              style={{
                width: '100%',
                marginTop: 15,
                background: 'transparent',
                border: '1px solid rgba(255,255,255,0.2)',
                color: '#a1a1aa',
                padding: '10px',
                borderRadius: 8,
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FloatingEasterEggsController;
