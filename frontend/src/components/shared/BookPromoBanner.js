import React, { useState, useEffect, useCallback } from 'react';
import { useVariant } from '../ABTesting/ABTestProvider';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

// Admin emails that can hide Maestro Bistro ads
const ADMIN_EMAILS = [
  'jjspilot24@gmail.com',
  'johnselman34@gmail.com', 
  'john.1976.selman@gmail.com'
];

// Book promotional images - including new ebook cover
const BOOK_IMAGES = [
  "https://customer-assets.emergentagent.com/job_protocol-hub-5/artifacts/149zoktj_ebook.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/024v1r34_Letters%20to%20Evelyn%20advertisement%201.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/e90a1rlq_Letters%20to%20Evelyn%20advertisement%202.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/ccdegcr8_Letters%20to%20Evelyn%20advertisement%203.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/3gqu0i0v_Letters%20to%20Evelyn%20advertisement%204.jpg"
];

const FUNNY_TAGLINES = [
  { image: 0, text: "⚡ LIMITED TIME: $2.99 - Less Than Your Coffee! ☕", subtext: "19 Five-Star Reviews • Optioned for Film • Read It Before Hollywood Does!" },
  { image: 1, text: "WROTE A BOOK. UNIVERSE FACT-CHECKED IT. IT PASSED.", subtext: "World Record Holder • Navy Pilot • Now Bestselling Author!" },
  { image: 2, text: "THERAPIST: THIS IS A LOT TO UNPACK.", subtext: "Warning: May cause uncontrollable laughter and existential questioning!" },
  { image: 3, text: "I FLEW JETS. THEN REALITY BROKE.", subtext: "From cockpit to cosmic encounters - the story Hollywood couldn't ignore!" },
  { image: 4, text: "🚀 TERROR OF THE COSMIC GULPER 🚀", subtext: "A comedy that will haunt you (in the best way possible!)" }
];

// Urgency/Scarcity messaging for CTAs
const URGENCY_MESSAGES = [
  "🔥 Over 10,000 readers can't be wrong!",
  "⏰ Film production starting soon - read the original first!",
  "💫 The book that made Hollywood take notice!",
  "🎬 Before it hits theaters - experience the source!",
  "✨ Join thousands who already know the secret!",
];

// CTA Button Styles for A/B testing
const CTA_STYLES = {
  gradient_pink_orange: {
    background: 'linear-gradient(135deg, #ec4899, #f97316)',
    boxShadow: '0 8px 30px rgba(236, 72, 153, 0.5)'
  },
  gradient_green: {
    background: 'linear-gradient(135deg, #10b981, #059669)',
    boxShadow: '0 8px 30px rgba(16, 185, 129, 0.5)'
  },
  gradient_purple: {
    background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
    boxShadow: '0 8px 30px rgba(139, 92, 246, 0.5)'
  }
};

// Professional Reviews from Readers' Favorite
const PROFESSIONAL_REVIEWS = [
  { reviewer: "Divine Zape", quote: "...a profound and unforgettable literary piece.", stars: 5 },
  { reviewer: "Paul Zietsman", quote: "...exceedingly brilliant.", stars: 5 },
  { reviewer: "Ruffina Oserio", quote: "...spellbinding...", stars: 5 },
  { reviewer: "Lauren Jones", quote: "The author's imagination is off the charts.", stars: 5 }
];

// Top Pilot Enterprises - Parent Company Banner
const TopPilotBanner = () => (
  <div style={{
    background: 'linear-gradient(135deg, #1a0a30 0%, #2d1b4e 50%, #1a365d 100%)',
    padding: '12px 20px',
    textAlign: 'center',
    borderBottom: '2px solid rgba(251, 191, 36, 0.5)'
  }}>
    <div style={{
      color: '#fbbf24',
      fontSize: '0.85rem',
      fontWeight: 700,
      letterSpacing: '2px',
      textTransform: 'uppercase'
    }}>
      ✈️ A <span style={{ color: '#fff' }}>Top Pilot Enterprises, Inc.</span> Venture ✈️
    </div>
    <div style={{
      color: 'rgba(255,255,255,0.7)',
      fontSize: '0.7rem',
      marginTop: 4,
      fontStyle: 'italic'
    }}>
      "Three ventures. One mission. Zero turbulence." (Okay, maybe a little during lunch rush at the bistro.)
    </div>
  </div>
);

// Maestro Bistro Promo Section
const MaestroBistroSection = () => (
  <div style={{
    background: 'linear-gradient(135deg, rgba(45, 20, 5, 0.7), rgba(70, 35, 15, 0.6))',
    padding: 20,
    borderRadius: 15,
    border: '2px solid rgba(139, 69, 19, 0.6)',
    marginTop: 15
  }}>
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap' }}>
      {/* Beef Rouladen Dish - Detailed bowl with all components */}
      <div style={{
        width: 100,
        height: 100,
        borderRadius: 12,
        background: 'linear-gradient(180deg, #2d1a0f 0%, #1f120a 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: 'inset 0 -10px 25px rgba(0,0,0,0.6), 0 6px 15px rgba(0,0,0,0.5)',
        position: 'relative',
        overflow: 'hidden',
        border: '3px solid #5c3d2e'
      }}>
        {/* Dark reddish-brown gravy pool */}
        <div style={{
          position: 'absolute',
          bottom: 8,
          width: '85%',
          height: '60%',
          background: 'linear-gradient(180deg, #7a3d20 0%, #5c2d15 40%, #3d1f0c 100%)',
          borderRadius: '50% 50% 45% 45%',
          boxShadow: 'inset 0 3px 10px rgba(120, 60, 30, 0.5)'
        }}/>
        {/* Beef Rouladen roll #1 - dark brown with bacon visible */}
        <div style={{
          position: 'absolute',
          bottom: 22,
          left: '15%',
          width: 28,
          height: 16,
          background: 'linear-gradient(135deg, #4a2510 0%, #3a1c0c 50%, #2a1408 100%)',
          borderRadius: '45% 45% 40% 40%',
          boxShadow: '0 3px 6px rgba(0,0,0,0.6)',
          border: '1px solid #5c3018'
        }}>
          {/* Bacon stripe */}
          <div style={{ position: 'absolute', top: 4, left: 3, width: 22, height: 2, background: '#8b4513', borderRadius: 1, opacity: 0.7 }}/>
          {/* Dijon mustard hint */}
          <div style={{ position: 'absolute', top: 7, left: 8, width: 12, height: 2, background: '#c9a227', borderRadius: 1, opacity: 0.5 }}/>
        </div>
        {/* Beef Rouladen roll #2 */}
        <div style={{
          position: 'absolute',
          bottom: 20,
          left: '45%',
          width: 24,
          height: 14,
          background: 'linear-gradient(135deg, #4a2510 0%, #351a0a 100%)',
          borderRadius: '45%',
          boxShadow: '0 2px 4px rgba(0,0,0,0.5)',
          border: '1px solid #5c3018'
        }}/>
        {/* Egg noodles covered in gravy */}
        <div style={{
          position: 'absolute',
          bottom: 14,
          right: '12%',
          width: 28,
          height: 22,
          background: 'linear-gradient(135deg, #c9a54d 0%, #a68940 50%, #8b7535 100%)',
          borderRadius: '35%',
          boxShadow: 'inset 0 2px 4px rgba(90, 60, 20, 0.4)'
        }}>
          {/* Gravy drizzle on noodles */}
          <div style={{ position: 'absolute', top: 3, left: 5, width: 18, height: 3, background: '#5c2d15', borderRadius: 2, opacity: 0.6 }}/>
          <div style={{ position: 'absolute', top: 8, left: 8, width: 12, height: 2, background: '#4a2510', borderRadius: 1, opacity: 0.5 }}/>
        </div>
        {/* Peas scattered */}
        <div style={{ position: 'absolute', bottom: 28, left: '12%', width: 6, height: 6, background: 'linear-gradient(135deg, #4a8f4a, #3d7a3d)', borderRadius: '50%', boxShadow: 'inset 0 -1px 2px rgba(0,0,0,0.3)' }}/>
        <div style={{ position: 'absolute', bottom: 34, left: '18%', width: 5, height: 5, background: 'linear-gradient(135deg, #5a9f5a, #4a8f4a)', borderRadius: '50%' }}/>
        <div style={{ position: 'absolute', bottom: 26, left: '26%', width: 5, height: 5, background: '#3d7a3d', borderRadius: '50%' }}/>
        <div style={{ position: 'absolute', bottom: 32, right: '35%', width: 5, height: 5, background: '#4a8f4a', borderRadius: '50%' }}/>
        {/* Carrot slices */}
        <div style={{ position: 'absolute', bottom: 30, right: '15%', width: 9, height: 6, background: 'linear-gradient(135deg, #e07020, #d45a10)', borderRadius: '40%', boxShadow: 'inset 0 1px 2px rgba(255,150,50,0.3)' }}/>
        <div style={{ position: 'absolute', bottom: 24, right: '25%', width: 7, height: 5, background: 'linear-gradient(135deg, #d45a10, #c04a00)', borderRadius: '40%' }}/>
      </div>
      
      {/* Fish Chowder Bowl */}
      <div style={{
        width: 80,
        height: 80,
        borderRadius: '50%',
        background: 'linear-gradient(180deg, #d4c4a0 0%, #c9b896 50%, #b8a882 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: 'inset 0 -8px 20px rgba(0,0,0,0.2), 0 4px 12px rgba(0,0,0,0.3)',
        position: 'relative',
        overflow: 'hidden',
        border: '3px solid #a89870'
      }}>
        {/* Creamy chowder base */}
        <div style={{
          position: 'absolute',
          bottom: 8,
          width: '80%',
          height: '55%',
          background: 'linear-gradient(180deg, #f5f0e0 0%, #e8e0c8 50%, #d8d0b8 100%)',
          borderRadius: '50% 50% 45% 45%',
          boxShadow: 'inset 0 2px 6px rgba(200, 180, 140, 0.4)'
        }}/>
        {/* White fish chunks */}
        <div style={{ position: 'absolute', bottom: 18, left: '20%', width: 14, height: 10, background: 'linear-gradient(135deg, #f8f8f0, #e8e8e0)', borderRadius: '30%', boxShadow: '0 1px 2px rgba(0,0,0,0.1)' }}/>
        <div style={{ position: 'absolute', bottom: 22, right: '22%', width: 12, height: 8, background: 'linear-gradient(135deg, #f0f0e8, #e0e0d8)', borderRadius: '35%' }}/>
        {/* Potato chunks */}
        <div style={{ position: 'absolute', bottom: 16, left: '40%', width: 10, height: 8, background: 'linear-gradient(135deg, #f5e8c0, #e8d8a8)', borderRadius: '25%' }}/>
        <div style={{ position: 'absolute', bottom: 24, right: '35%', width: 8, height: 7, background: '#f0e0b0', borderRadius: '30%' }}/>
        {/* Bacon bits */}
        <div style={{ position: 'absolute', bottom: 28, left: '28%', width: 6, height: 3, background: '#8b4020', borderRadius: 1 }}/>
        <div style={{ position: 'absolute', bottom: 20, right: '30%', width: 5, height: 2, background: '#9a4828', borderRadius: 1 }}/>
        {/* Yellow onion pieces */}
        <div style={{ position: 'absolute', bottom: 14, left: '32%', width: 5, height: 4, background: '#e8d090', borderRadius: '40%', opacity: 0.8 }}/>
        <div style={{ position: 'absolute', bottom: 26, left: '50%', width: 4, height: 3, background: '#f0d898', borderRadius: '30%', opacity: 0.7 }}/>
      </div>
      
      <div style={{ flex: 1, minWidth: 220 }}>
        <h3 style={{
          fontSize: '1.4rem',
          fontWeight: 800,
          color: '#d97706',
          marginBottom: 5,
          textShadow: '0 1px 2px rgba(0,0,0,0.5)'
        }}>
          MAESTRO BISTRO
        </h3>
        <div style={{ color: '#fbbf24', fontSize: '0.9rem', marginBottom: 10 }}>
          🏪 On the Mall • Brunswick, Maine
        </div>
        <div style={{ color: '#fff', fontSize: '0.85rem', lineHeight: 1.7 }}>
          <div style={{ marginBottom: 8 }}>
            <strong style={{ color: '#d97706' }}>🥩 deLectaBLe Beef Rouladen</strong>
            <div style={{ color: '#d4c4a0', fontSize: '0.8rem', marginLeft: 22 }}>
              Dark brown beef rolls with bacon & dijon mustard inside, smothered in rich reddish-brown gravy, served with egg noodles, sweet peas & carrots
            </div>
          </div>
          <div style={{ marginBottom: 8 }}>
            <strong style={{ color: '#10b981' }}>🥬 Vegetable Rouladen</strong>
            <div style={{ color: '#d4c4a0', fontSize: '0.8rem', marginLeft: 22 }}>
              Fresh garden vegetables in savory brown gravy - It's German Cuisine!
            </div>
          </div>
          <div>
            <strong style={{ color: '#38bdf8' }}>🐟 Maine Fish Chowder</strong>
            <div style={{ color: '#d4c4a0', fontSize: '0.8rem', marginLeft: 22 }}>
              Creamy chowder with tender white fish, potatoes, crispy bacon bits & yellow onions
            </div>
          </div>
        </div>
        <div style={{
          marginTop: 12,
          padding: '8px 15px',
          background: 'rgba(139, 69, 19, 0.3)',
          borderRadius: 10,
          color: '#fbbf24',
          fontSize: '0.8rem',
          fontStyle: 'italic',
          fontWeight: 600,
          border: '1px solid rgba(210, 105, 30, 0.4)'
        }}>
          "Appropriate & conscientable prices for appropriately & conscientiously AMAZING food!" 🎻
        </div>
      </div>
    </div>
  </div>
);
            }}/>
            <span><strong style={{ color: '#38bdf8' }}>Fresh Fish Chowder</strong> - Maine's finest catch</span>
          </div>
        </div>
        <div style={{
          marginTop: 12,
          padding: '8px 15px',
          background: 'rgba(139, 69, 19, 0.3)',
          borderRadius: 10,
          color: '#fbbf24',
          fontSize: '0.8rem',
          fontStyle: 'italic',
          fontWeight: 600,
          border: '1px solid rgba(210, 105, 30, 0.4)'
        }}>
          "Appropriate & conscientable prices for appropriately & conscientiously AMAZING food!" 🎻
        </div>
      </div>
    </div>
  </div>
);

// InfoPilot Promo Section
const InfoPilotSection = () => (
  <div style={{
    background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(59, 130, 246, 0.2))',
    padding: 20,
    borderRadius: 15,
    border: '2px solid rgba(124, 58, 237, 0.5)',
    marginTop: 15
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 15, flexWrap: 'wrap' }}>
      <div style={{
        fontSize: '2.5rem',
        background: 'linear-gradient(135deg, #7c3aed, #3b82f6)',
        borderRadius: 15,
        width: 70,
        height: 70,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 900,
        color: '#fff'
      }}>
        🔍
      </div>
      <div style={{ flex: 1, minWidth: 200 }}>
        <h3 style={{
          fontSize: '1.4rem',
          fontWeight: 800,
          background: 'linear-gradient(135deg, #7c3aed, #3b82f6)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: 5
        }}>
          INFOPILOT EXPLORER
        </h3>
        <div style={{ color: '#a78bfa', fontSize: '0.9rem', marginBottom: 8 }}>
          🌐 World Wide Information Exchange
        </div>
        <div style={{ color: '#fff', fontSize: '0.85rem', lineHeight: 1.6 }}>
          <div style={{ marginBottom: 5 }}>
            ⚡ <strong style={{ color: '#7c3aed' }}>InfoJet 2.0™</strong> - Proprietary search & categorization language
          </div>
          <div style={{ marginBottom: 5 }}>
            🗺️ <strong style={{ color: '#3b82f6' }}>Interactive Maps</strong> - Geolocated results worldwide
          </div>
          <div>
            🏪 <strong style={{ color: '#10b981' }}>Protocol Marketplace</strong> - Buy & sell search protocols
          </div>
        </div>
        <div style={{
          marginTop: 12,
          display: 'flex',
          gap: 10,
          flexWrap: 'wrap'
        }}>
          <span style={{
            padding: '6px 12px',
            background: 'rgba(16, 185, 129, 0.2)',
            color: '#10b981',
            borderRadius: 20,
            fontSize: '0.75rem',
            fontWeight: 700
          }}>
            ✓ 100% FREE
          </span>
          <span style={{
            padding: '6px 12px',
            background: 'rgba(124, 58, 237, 0.2)',
            color: '#a78bfa',
            borderRadius: 20,
            fontSize: '0.75rem',
            fontWeight: 700
          }}>
            ✓ Google Sign-In
          </span>
          <span style={{
            padding: '6px 12px',
            background: 'rgba(251, 191, 36, 0.2)',
            color: '#fbbf24',
            borderRadius: 20,
            fontSize: '0.75rem',
            fontWeight: 700
          }}>
            ✓ Copyright Protected
          </span>
        </div>
      </div>
    </div>
  </div>
);

const BookPromoBanner = () => {
  const { user, token } = useAuth();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [hideMaestroBistro, setHideMaestroBistro] = useState(false);
  
  // Check if user is an admin who can hide ads
  const canHideAds = user?.email && ADMIN_EMAILS.map(e => e.toLowerCase()).includes(user.email.toLowerCase());
  
  // Load hide preference from localStorage or user settings
  useEffect(() => {
    if (canHideAds) {
      const savedPref = localStorage.getItem('hideMaestroBistro');
      if (savedPref !== null) {
        setHideMaestroBistro(savedPref === 'true');
      }
    }
  }, [canHideAds, user?.email]);
  
  // Toggle Maestro Bistro visibility
  const toggleMaestroBistro = () => {
    const newValue = !hideMaestroBistro;
    setHideMaestroBistro(newValue);
    localStorage.setItem('hideMaestroBistro', String(newValue));
  };
  
  // A/B Testing hooks for headline and CTA
  const { variant: headlineVariant, trackEvent: trackHeadlineEvent } = useVariant('book_promo_headline');
  const { variant: ctaVariant, trackEvent: trackCtaEvent } = useVariant('book_promo_cta_button');
  
  // Track impression on mount
  useEffect(() => {
    if (headlineVariant) {
      trackHeadlineEvent('impression');
    }
    if (ctaVariant) {
      trackCtaEvent('impression');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [headlineVariant?.variant_id, ctaVariant?.variant_id]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % BOOK_IMAGES.length);
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  // Use A/B variant content or fallback to defaults
  const currentTagline = headlineVariant?.content 
    ? { text: headlineVariant.content.headline, subtext: headlineVariant.content.subtext }
    : FUNNY_TAGLINES[currentImageIndex];
  
  const ctaContent = ctaVariant?.content || { text: '🛒 GET IT NOW - Only $2.99!', style: 'gradient_pink_orange' };
  const ctaStyle = CTA_STYLES[ctaContent.style] || CTA_STYLES.gradient_pink_orange;
  
  // Handle CTA click with A/B tracking
  const handleCtaClick = () => {
    if (ctaVariant) {
      trackCtaEvent('click');
    }
    // Conversion is tracked when user actually purchases (external)
  };

  return (
    <div data-testid="book-promo-banner" style={{
      background: 'linear-gradient(135deg, rgba(20, 10, 40, 0.98), rgba(80, 20, 100, 0.95))',
      borderRadius: 20,
      padding: 0,
      marginBottom: 25,
      border: '3px solid rgba(236, 72, 153, 0.7)',
      overflow: 'hidden',
      boxShadow: '0 25px 80px rgba(124, 58, 237, 0.5)'
    }}>
      {/* Top Pilot Enterprises Banner */}
      <TopPilotBanner />
      
      {/* Animated Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #7c3aed, #ec4899, #f97316)',
        padding: '18px 25px',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Shimmer effect */}
        <div style={{
          position: 'absolute',
          top: 0, left: '-100%', right: 0, bottom: 0,
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
          animation: 'shimmer 3s infinite'
        }} />
        
        {/* A/B Test Indicator (only in dev) */}
        {process.env.NODE_ENV === 'development' && headlineVariant && (
          <div style={{
            position: 'absolute',
            top: 2,
            left: 5,
            background: 'rgba(0,0,0,0.5)',
            padding: '2px 6px',
            borderRadius: 4,
            fontSize: '0.6rem',
            color: '#10b981'
          }}>
            A/B: {headlineVariant.variant_id}
          </div>
        )}
        
        <div style={{
          position: 'absolute',
          top: 8,
          right: 15,
          background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
          color: '#000',
          padding: '6px 18px',
          borderRadius: 20,
          fontWeight: 800,
          fontSize: '0.8rem',
          boxShadow: '0 4px 20px rgba(251, 191, 36, 0.6)',
          animation: 'pulse 2s infinite'
        }}>
          🎬 OPTIONED FOR FILM!
        </div>
        
        <div style={{
          fontSize: '1.6rem',
          fontWeight: 900,
          color: '#fff',
          textShadow: '2px 2px 8px rgba(0,0,0,0.4)',
          letterSpacing: '1px',
          transition: 'all 0.5s'
        }}>
          {currentTagline.text}
        </div>
        <div style={{
          fontSize: '1rem',
          color: 'rgba(255,255,255,0.95)',
          marginTop: 5,
          fontWeight: 600,
          fontStyle: 'italic'
        }}>
          {currentTagline.subtext}
        </div>
      </div>

      {/* Main Content */}
      <div style={{
        display: 'flex',
        gap: 30,
        padding: 25,
        flexWrap: 'wrap',
        alignItems: 'flex-start'
      }}>
        {/* Book Image with Gallery */}
        <div style={{ flex: '0 0 auto', position: 'relative' }}>
          <div style={{
            width: 250,
            height: 320,
            borderRadius: 15,
            overflow: 'hidden',
            boxShadow: '0 20px 60px rgba(236, 72, 153, 0.6)',
            border: '4px solid rgba(255, 255, 255, 0.25)',
            transition: 'transform 0.3s',
            cursor: 'pointer'
          }}>
            <img 
              src={BOOK_IMAGES[currentImageIndex]} 
              alt="Letters to Evelyn - Funny Promo"
              style={{ width: '100%', height: '100%', objectFit: 'cover', transition: 'all 0.5s' }}
            />
          </div>
          {/* Thumbnail Gallery */}
          <div style={{ 
            display: 'flex', 
            gap: 10, 
            marginTop: 15,
            justifyContent: 'center'
          }}>
            {BOOK_IMAGES.map((img, idx) => (
              <div 
                key={idx}
                onClick={() => setCurrentImageIndex(idx)}
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 10,
                  overflow: 'hidden',
                  cursor: 'pointer',
                  border: idx === currentImageIndex ? '3px solid #ec4899' : '2px solid rgba(255,255,255,0.3)',
                  opacity: idx === currentImageIndex ? 1 : 0.7,
                  transition: 'all 0.3s',
                  boxShadow: idx === currentImageIndex ? '0 0 15px rgba(236, 72, 153, 0.5)' : 'none'
                }}
              >
                <img src={img} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
            ))}
          </div>
        </div>

        {/* Book Details */}
        <div style={{ flex: 1, minWidth: 300 }}>
          <h2 style={{
            fontSize: '2.2rem',
            fontWeight: 900,
            background: 'linear-gradient(135deg, #f472b6, #ec4899, #fbbf24)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: 10,
            letterSpacing: '1px'
          }}>
            LETTERS TO EVELYN
          </h2>
          
          <div style={{ 
            color: '#a78bfa', 
            fontSize: '1.1rem', 
            marginBottom: 8,
            fontWeight: 600
          }}>
            A Supernatural Thriller Comedy Memoir
          </div>
          
          <div style={{ 
            color: '#fbbf24', 
            fontSize: '1rem', 
            marginBottom: 12,
            fontWeight: 700
          }}>
            By World Record Aviation Holder <span style={{ color: '#fff' }}>John Selman</span>
          </div>

          {/* Star Rating */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 15 }}>
            <span style={{ color: '#fbbf24', fontSize: '1.4rem' }}>★★★★★</span>
            <span style={{ color: '#fbbf24', fontWeight: 800, fontSize: '1rem' }}>19 Five-Star Reviews</span>
            <span style={{ 
              background: 'rgba(16, 185, 129, 0.2)', 
              color: '#10b981', 
              padding: '4px 12px', 
              borderRadius: 15,
              fontSize: '0.8rem',
              fontWeight: 700
            }}>
              Readers' Favorite
            </span>
          </div>

          {/* Key Selling Points */}
          <div style={{ marginBottom: 18 }}>
            <div style={{ color: '#f472b6', fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              ✈️ <span>Written by a Navy pilot who flew 10 aircraft types</span>
            </div>
            <div style={{ color: '#a78bfa', fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              👽 <span>Extraterrestrial encounters & cosmic visions</span>
            </div>
            <div style={{ color: '#fbbf24', fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              😂 <span>"Comedy that creeps into your mind and causes abrupt laughter"</span>
            </div>
          </div>

          {/* Review Quote */}
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            padding: 15,
            borderRadius: 12,
            marginBottom: 20,
            borderLeft: '4px solid #10b981'
          }}>
            <div style={{ color: '#10b981', fontStyle: 'italic', fontSize: '0.95rem', lineHeight: 1.5 }}>
              "The comical side is exceedingly brilliant... imagination off the charts. A true story that defies belief!"
            </div>
            <div style={{ 
              color: '#34d399', 
              fontSize: '0.85rem', 
              marginTop: 8, 
              fontWeight: 600
            }}>
              — Professional Review, Readers' Favorite ★★★★★
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 15 }}>
            <a 
              href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191"
              target="_blank"
              rel="noopener noreferrer"
              data-testid="book-buy-amazon"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                ...ctaStyle,
                color: 'white',
                padding: '14px 28px',
                borderRadius: 30,
                fontWeight: 800,
                fontSize: '1rem',
                textDecoration: 'none',
                border: '2px solid rgba(255,255,255,0.2)',
                transition: 'transform 0.2s',
                animation: 'pulse 2s infinite'
              }}
              onClick={handleCtaClick}
            >
              {ctaContent.text}
            </a>
            <a 
              href="https://letters-to-evelyn.sintra.site"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(124, 58, 237, 0.3)',
                color: '#a78bfa',
                padding: '14px 24px',
                borderRadius: 30,
                fontWeight: 700,
                fontSize: '1rem',
                textDecoration: 'none',
                border: '2px solid rgba(124, 58, 237, 0.5)'
              }}
            >
              🌐 OFFICIAL SITE
            </a>
            <a 
              href="https://readersfavorite.com/book-review/letters-to-evelyn"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(16, 185, 129, 0.2)',
                color: '#10b981',
                padding: '14px 24px',
                borderRadius: 30,
                fontWeight: 700,
                fontSize: '1rem',
                textDecoration: 'none',
                border: '2px solid rgba(16, 185, 129, 0.5)'
              }}
            >
              ⭐ SEE 19 Five-Star Reviews
            </a>
          </div>

          {/* Urgency Message - Rotating */}
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 12,
            padding: '10px 16px',
            marginBottom: 15,
            display: 'flex',
            alignItems: 'center',
            gap: 10
          }}>
            <span style={{ fontSize: '1.2rem', animation: 'pulse 1.5s infinite' }}>🔥</span>
            <span style={{ color: '#f87171', fontSize: '0.9rem', fontWeight: 600 }}>
              {URGENCY_MESSAGES[Math.floor(Date.now() / 10000) % URGENCY_MESSAGES.length]}
            </span>
          </div>

          {/* Film Badge */}
          <div style={{
            display: 'inline-block',
            background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.3))',
            padding: '12px 20px',
            borderRadius: 25,
            border: '2px solid rgba(251, 191, 36, 0.6)'
          }}>
            <span style={{ color: '#fbbf24', fontWeight: 800, fontSize: '0.9rem' }}>
              🎬 Hollywood couldn't resist - OPTIONED FOR FILM!
            </span>
          </div>
        </div>
      </div>

      {/* Other Top Pilot Enterprises Ventures */}
      <div style={{ padding: '0 25px 25px 25px' }}>
        <div style={{
          textAlign: 'center',
          color: '#a1a1aa',
          fontSize: '0.8rem',
          marginBottom: 15,
          fontWeight: 600,
          letterSpacing: '1px',
          textTransform: 'uppercase'
        }}>
          — More from Top Pilot Enterprises, Inc. —
        </div>
        
        {/* InfoPilot Promo */}
        <InfoPilotSection />
        
        {/* Admin Control for Maestro Bistro */}
        {canHideAds && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            marginBottom: 15
          }}>
            <button
              onClick={toggleMaestroBistro}
              style={{
                padding: '8px 16px',
                background: hideMaestroBistro ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                border: `1px solid ${hideMaestroBistro ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'}`,
                borderRadius: 20,
                color: hideMaestroBistro ? '#10b981' : '#f87171',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600
              }}
              data-testid="toggle-maestro-bistro"
            >
              {hideMaestroBistro ? '👁️ Show Maestro Bistro Ads' : '🙈 Hide Maestro Bistro Ads'}
            </button>
          </div>
        )}
        
        {/* Maestro Bistro Promo - Hidden if admin toggled off */}
        {!hideMaestroBistro && <MaestroBistroSection />}
        
        {/* Footer */}
        <div style={{
          textAlign: 'center',
          marginTop: 20,
          padding: 15,
          background: 'rgba(0,0,0,0.3)',
          borderRadius: 12
        }}>
          <div style={{ color: '#fbbf24', fontSize: '0.85rem', fontWeight: 700, marginBottom: 5 }}>
            ✈️ Top Pilot Enterprises, Inc.
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.7rem', fontStyle: 'italic' }}>
            "Where every venture reaches cruising altitude" • Cleared for takeoff since Day One
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookPromoBanner;
