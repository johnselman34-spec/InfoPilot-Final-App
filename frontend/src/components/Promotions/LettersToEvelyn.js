/**
 * Letters to Evelyn - Enhanced Book Promotion Component
 * Features hilarious and compelling promotional content
 * Designed for MAXIMUM SALES while being extremely funny and interesting!
 */
import React, { useState, useEffect } from 'react';
import { useLaugh } from '../Gamification/LaughOMeter';

// Rotating headlines for maximum impact
const HEADLINES = [
  "📚 Letters to Evelyn - The Book That'll Change Your Life!",
  "✈️ Navy Pilot Saves Universe with His Memoir!",
  "🛸 Aliens, Comedy & Romance - All in One Book!",
  "😂 19 Five-Star Reviews Can't Be Wrong!",
  "🎬 OPTIONED FOR FILM by Hollywood!",
  "🌟 The Memoir Everyone's Talking About!",
];

const TAGLINES = [
  "A hysterically heartwarming journey on a hilarious roller coaster ride!",
  "More than 50 finely-crafted jokes that induce HURRICANE FORCE WINDS of laughter!",
  "Comedy that creeps into your mind and causes abrupt laughter!",
  "So funny, it should be illegal! (But it's not, we checked!)",
  "Ready to levitate people off their rockers in stupefying hee-haw laughter!",
];

const REVIEWS = [
  { reviewer: "Olga Markova", text: "Grabbed me from the first page with fast-moving, easy-to-read, and action-packed storytelling!", stars: 5 },
  { reviewer: "P. Zeitsman", text: "The comical side of it is exceedingly brilliant... imagination off the charts!", stars: 5 },
  { reviewer: "R. Tanveer", text: "The narrative was smooth, fast-paced and exceptionally well-written!", stars: 5 },
  { reviewer: "L. Jones", text: "A story that you will never forget. The author's imagination is OFF THE CHARTS!", stars: 5 },
  { reviewer: "Divine Zape", text: "A haunting odyssey of love and redemption - profound and unforgettable!", stars: 5 },
];

const PURCHASE_LINKS = {
  amazonEbook: "https://a.co/d/gsRLapf",
  amazonPaperback: "https://www.amazon.com/dp/B0F3XCYVYP",
  amazonHardcover: "https://www.amazon.com/dp/B0F3XFG14J",
  barnesNoble: "https://www.barnesandnoble.com/w/letters-to-evelyn-john-selman/1119415091",
  freeExcerpt: "https://drive.google.com/file/d/14_QbMQClOH5_sUiq6A5nE7DL-BIBUlZX/view",
};

// Compact promo for sidebar/widgets
export const LettersToEvelynCompact = ({ onPromoClick }) => {
  const { recordEasterEgg } = useLaugh();
  const [headline] = useState(HEADLINES[Math.floor(Math.random() * HEADLINES.length)]);
  
  const handleClick = () => {
    recordEasterEgg?.('evelyn_fan');
    onPromoClick?.();
    window.open(PURCHASE_LINKS.amazonEbook, '_blank');
  };
  
  return (
    <div
      onClick={handleClick}
      data-testid="lte-promo-compact"
      style={{
        background: 'linear-gradient(135deg, rgba(255, 107, 107, 0.2), rgba(254, 202, 87, 0.2))',
        borderRadius: 12,
        padding: 15,
        cursor: 'pointer',
        border: '2px solid rgba(255, 107, 107, 0.4)',
        transition: 'all 0.3s'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: '2rem' }}>📚</span>
        <div>
          <p style={{ color: '#ff6b6b', fontWeight: 700, margin: '0 0 5px 0', fontSize: '0.95rem' }}>
            Letters to Evelyn
          </p>
          <p style={{ color: '#a1a1aa', margin: 0, fontSize: '0.8rem' }}>
            Only $2.99 • 19 Five-Star Reviews!
          </p>
        </div>
      </div>
      <div style={{ 
        background: 'rgba(255, 107, 107, 0.3)', 
        padding: '4px 10px', 
        borderRadius: 8,
        marginTop: 10,
        textAlign: 'center'
      }}>
        <span style={{ color: '#feca57', fontSize: '0.75rem', fontWeight: 600 }}>
          🎬 OPTIONED FOR FILM!
        </span>
      </div>
    </div>
  );
};

// Full promotional banner
export const LettersToEvelynBanner = ({ variant = 'default' }) => {
  const { recordEasterEgg } = useLaugh();
  const [currentReview, setCurrentReview] = useState(0);
  const [headline] = useState(HEADLINES[Math.floor(Math.random() * HEADLINES.length)]);
  const [tagline] = useState(TAGLINES[Math.floor(Math.random() * TAGLINES.length)]);
  
  // Rotate reviews
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentReview(prev => (prev + 1) % REVIEWS.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);
  
  const handleClick = () => {
    recordEasterEgg?.('evelyn_fan');
  };
  
  return (
    <div
      data-testid="lte-promo-banner"
      onClick={handleClick}
      style={{
        background: 'linear-gradient(135deg, #ff6b6b 0%, #feca57 50%, #ff9ff3 100%)',
        borderRadius: 20,
        padding: 3,
        marginBottom: 25,
        cursor: 'pointer'
      }}
    >
      <div style={{
        background: 'linear-gradient(135deg, rgba(30, 20, 50, 0.95), rgba(40, 20, 60, 0.95))',
        borderRadius: 18,
        padding: 25,
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Decorative elements */}
        <div style={{ position: 'absolute', top: 10, right: 20, fontSize: '1.5rem', opacity: 0.3 }}>✈️</div>
        <div style={{ position: 'absolute', bottom: 20, left: 20, fontSize: '1.2rem', opacity: 0.3 }}>🛸</div>
        <div style={{ position: 'absolute', top: 50, left: '80%', fontSize: '1rem', opacity: 0.2 }}>⭐</div>
        
        {/* Film badge */}
        <div style={{
          position: 'absolute',
          top: 15,
          right: 15,
          background: 'linear-gradient(135deg, #f59e0b, #f97316)',
          color: '#fff',
          padding: '6px 14px',
          borderRadius: 20,
          fontSize: '0.75rem',
          fontWeight: 800,
          boxShadow: '0 4px 15px rgba(245, 158, 11, 0.4)',
          textTransform: 'uppercase'
        }}>
          🎬 Film Option!
        </div>
        
        {/* Header */}
        <h2 style={{ 
          color: '#fff',
          fontSize: '1.5rem',
          margin: '0 0 10px 0',
          background: 'linear-gradient(135deg, #ff6b6b 0%, #feca57 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontWeight: 800,
          paddingRight: 100
        }}>
          {headline}
        </h2>
        
        {/* Author */}
        <p style={{ color: '#a1a1aa', margin: '0 0 15px 0', fontSize: '0.9rem' }}>
          by <span style={{ color: '#ff6b6b', fontWeight: 600 }}>John Selman</span> • Navy Pilot & World Record Holder
        </p>
        
        {/* Tagline */}
        <div style={{
          background: 'rgba(255, 107, 107, 0.15)',
          borderLeft: '4px solid #ff6b6b',
          padding: '12px 15px',
          borderRadius: '0 10px 10px 0',
          marginBottom: 20
        }}>
          <p style={{ color: '#feca57', margin: 0, fontStyle: 'italic', fontWeight: 500 }}>
            "{tagline}"
          </p>
        </div>
        
        {/* Genre tags */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
          {['Rom-Com', 'Sci-Fi', 'Memoir', 'Aviation', 'Supernatural'].map(genre => (
            <span 
              key={genre}
              style={{
                background: 'rgba(255, 107, 107, 0.2)',
                color: '#ff6b6b',
                padding: '4px 12px',
                borderRadius: 15,
                fontSize: '0.75rem',
                fontWeight: 600
              }}
            >
              {genre}
            </span>
          ))}
        </div>
        
        {/* Rotating review */}
        <div style={{
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 12,
          padding: 15,
          marginBottom: 20,
          minHeight: 80
        }}>
          <div style={{ display: 'flex', marginBottom: 8 }}>
            {[...Array(5)].map((_, i) => (
              <span key={i} style={{ color: '#fbbf24', fontSize: '0.9rem' }}>⭐</span>
            ))}
            <span style={{ color: '#fbbf24', marginLeft: 8, fontSize: '0.75rem', fontWeight: 600 }}>
              Readers' Favorite
            </span>
          </div>
          <p style={{ color: '#e2e8f0', margin: '0 0 8px 0', fontStyle: 'italic', fontSize: '0.9rem' }}>
            "{REVIEWS[currentReview].text}"
          </p>
          <p style={{ color: '#71717a', margin: 0, fontSize: '0.8rem' }}>
            — {REVIEWS[currentReview].reviewer}
          </p>
        </div>
        
        {/* CTAs */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <a
            href={PURCHASE_LINKS.amazonEbook}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              flex: '1 1 auto',
              background: 'linear-gradient(135deg, #ff6b6b, #ff9ff3)',
              color: '#fff',
              textDecoration: 'none',
              padding: '14px 25px',
              borderRadius: 12,
              fontWeight: 700,
              textAlign: 'center',
              boxShadow: '0 6px 20px rgba(255, 107, 107, 0.4)',
              transition: 'all 0.3s'
            }}
          >
            📖 Get it for $2.99!
          </a>
          <a
            href={PURCHASE_LINKS.freeExcerpt}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              padding: '14px 20px',
              borderRadius: 12,
              background: 'rgba(255, 255, 255, 0.1)',
              color: '#fff',
              textDecoration: 'none',
              fontWeight: 600,
              textAlign: 'center',
              border: '2px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s'
            }}
          >
            👀 Read Free Excerpt
          </a>
        </div>
        
        {/* Stats footer */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-around', 
          marginTop: 20,
          paddingTop: 15,
          borderTop: '1px solid rgba(255, 107, 107, 0.2)'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#feca57', fontSize: '1.2rem', fontWeight: 700 }}>19</div>
            <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Five-Star Reviews</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#ff6b6b', fontSize: '1.2rem', fontWeight: 700 }}>50+</div>
            <div style={{ color: '#71717a', fontSize: '0.7rem' }}>Hilarious Jokes</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#ff9ff3', fontSize: '1.2rem', fontWeight: 700 }}>1</div>
            <div style={{ color: '#71717a', fontSize: '0.7rem' }}>World Record</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Newsletter signup CTA
export const LettersToEvelynNewsletter = () => {
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(255, 107, 107, 0.15))',
      borderRadius: 12,
      padding: 20,
      textAlign: 'center',
      border: '1px dashed rgba(255, 107, 107, 0.4)'
    }}>
      <h4 style={{ color: '#ff6b6b', margin: '0 0 10px 0' }}>
        📬 Get More Laughs Delivered!
      </h4>
      <p style={{ color: '#a1a1aa', margin: '0 0 15px 0', fontSize: '0.9rem' }}>
        Sign up for the tri-weekly newsletter featuring hilarious content from InfoPilot and Letters to Evelyn!
      </p>
      <a
        href="https://www.LetterstoEvelynbyJohnSelmanII.com"
        target="_blank"
        rel="noopener noreferrer"
        className="btn btn-primary"
        style={{
          background: 'linear-gradient(135deg, #ff6b6b, #feca57)',
          padding: '10px 25px',
          textDecoration: 'none'
        }}
      >
        Sign Up at LetterstoEvelyn.com
      </a>
    </div>
  );
};

export default { LettersToEvelynCompact, LettersToEvelynBanner, LettersToEvelynNewsletter };
