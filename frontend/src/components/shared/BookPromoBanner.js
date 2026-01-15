import React, { useState, useEffect } from 'react';

// Book promotional images
const BOOK_IMAGES = [
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/024v1r34_Letters%20to%20Evelyn%20advertisement%201.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/e90a1rlq_Letters%20to%20Evelyn%20advertisement%202.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/ccdegcr8_Letters%20to%20Evelyn%20advertisement%203.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/3gqu0i0v_Letters%20to%20Evelyn%20advertisement%204.jpg"
];

const FUNNY_TAGLINES = [
  { image: 0, text: "WROTE A BOOK. UNIVERSE FACT-CHECKED IT. IT PASSED.", subtext: "Now it's YOUR turn to verify!" },
  { image: 1, text: "THERAPIST: THIS IS A LOT TO UNPACK.", subtext: "Bring snacks. Possibly a helmet." },
  { image: 2, text: "I FLEW JETS. THEN REALITY BROKE.", subtext: "Navy pilot meets cosmic chaos." },
  { image: 3, text: "TERROR OF THE COSMIC GULPER", subtext: "A comedy of galactic proportions!" }
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
    background: 'linear-gradient(135deg, rgba(139, 69, 19, 0.3), rgba(101, 67, 33, 0.4))',
    padding: 20,
    borderRadius: 15,
    border: '2px solid rgba(210, 105, 30, 0.5)',
    marginTop: 15
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 15, flexWrap: 'wrap' }}>
      <div style={{
        fontSize: '3rem',
        background: 'linear-gradient(135deg, #d97706, #f59e0b)',
        borderRadius: '50%',
        width: 70,
        height: 70,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        🍲
      </div>
      <div style={{ flex: 1, minWidth: 200 }}>
        <h3 style={{
          fontSize: '1.4rem',
          fontWeight: 800,
          color: '#f59e0b',
          marginBottom: 5
        }}>
          MAESTRO BISTRO
        </h3>
        <div style={{ color: '#fcd34d', fontSize: '0.9rem', marginBottom: 8 }}>
          🏪 On the Mall • Brunswick, Maine
        </div>
        <div style={{ color: '#fff', fontSize: '0.85rem', lineHeight: 1.5 }}>
          <div style={{ marginBottom: 5 }}>
            🥩 <strong style={{ color: '#f59e0b' }}>deLectaBLe Beef Chowder</strong> - Evenly spiced perfection
          </div>
          <div style={{ marginBottom: 5 }}>
            🥬 <strong style={{ color: '#10b981' }}>Vegetable Chowder</strong> - With Bacon! (Yes, really!)
          </div>
          <div>
            🐟 <strong style={{ color: '#38bdf8' }}>Fresh Fish Chowder</strong> - Maine's finest catch
          </div>
        </div>
        <div style={{
          marginTop: 12,
          padding: '8px 15px',
          background: 'rgba(251, 191, 36, 0.2)',
          borderRadius: 10,
          color: '#fbbf24',
          fontSize: '0.8rem',
          fontStyle: 'italic',
          fontWeight: 600
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
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % BOOK_IMAGES.length);
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  const currentTagline = FUNNY_TAGLINES[currentImageIndex];

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
                background: 'linear-gradient(135deg, #ec4899, #f97316)',
                color: 'white',
                padding: '14px 28px',
                borderRadius: 30,
                fontWeight: 800,
                fontSize: '1rem',
                textDecoration: 'none',
                boxShadow: '0 8px 30px rgba(236, 72, 153, 0.5)',
                border: '2px solid rgba(255,255,255,0.2)',
                transition: 'transform 0.2s'
              }}
            >
              🛒 BUY NOW - $2.99
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
              ⭐ READ REVIEWS
            </a>
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
    </div>
  );
};

export default BookPromoBanner;
