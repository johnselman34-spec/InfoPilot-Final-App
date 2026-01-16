/**
 * Bundle of the Week - Featured Bundle Component
 * Displays the hottest bundle with extremely funny marketing copy
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

// Hilarious rotating taglines
const FUNNY_TAGLINES = [
  "🔥 This bundle is SO HOT, even the sun is jealous!",
  "⚡ WARNING: May cause spontaneous productivity bursts!",
  "🎯 Hit ALL the bullseyes with this legendary bundle!",
  "💎 Diamond-tier value at bronze-tier prices!",
  "🚀 Your search game is about to go INTERSTELLAR!",
  "🏆 The bundle that other bundles wish they could be!",
  "✨ Certified 100% awesome by the International Bureau of Awesomeness!",
  "🌟 So good, we almost kept it for ourselves (almost)!",
  "🎪 Step right up to the GREATEST BUNDLE ON EARTH!",
  "💰 Your wallet will send you a thank-you card!",
];

const BundleOfTheWeek = ({ showToast }) => {
  const { token } = useAuth();
  const [featured, setFeatured] = useState(null);
  const [loading, setLoading] = useState(true);
  // Initialize tagline with a random value (stable across re-renders)
  const [tagline] = useState(() => FUNNY_TAGLINES[Math.floor(Math.random() * FUNNY_TAGLINES.length)]);
  const [purchasing, setPurchasing] = useState(false);

  useEffect(() => {
    // Fetch featured bundle
    const fetchFeatured = async () => {
      try {
        const res = await fetch(`${API}/bundles/featured`);
        if (res.ok) {
          const data = await res.json();
          setFeatured(data.featured);
        }
      } catch (e) {
        console.error('Failed to fetch featured bundle:', e);
      }
      setLoading(false);
    };
    
    fetchFeatured();
  }, []);

  const handlePurchase = async () => {
    if (!token) {
      showToast('Login to grab this amazing deal! 🎯', 'info');
      return;
    }
    
    setPurchasing(true);
    try {
      const res = await fetch(`${API}/bundles/purchase`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ bundle_id: featured.id })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        if (data.payment_url) {
          window.open(data.payment_url, '_blank');
          showToast('Complete PayPal payment to unlock!', 'info');
        } else {
          showToast('🎉 Bundle acquired! You are UNSTOPPABLE!', 'success');
        }
      } else {
        showToast(data.detail || 'Oops! Try again?', 'error');
      }
    } catch (e) {
      showToast('Network hiccup! Give it another shot!', 'error');
    }
    setPurchasing(false);
  };

  if (loading) {
    return null;
  }

  if (!featured) {
    return null;
  }

  return (
    <div 
      data-testid="bundle-of-the-week"
      style={{
        background: 'linear-gradient(135deg, #7c3aed 0%, #ec4899 50%, #f59e0b 100%)',
        borderRadius: 20,
        padding: 3,
        marginBottom: 25,
        animation: 'pulse 2s ease-in-out infinite'
      }}
    >
      <div style={{
        background: 'linear-gradient(135deg, rgba(30, 20, 50, 0.95), rgba(40, 20, 60, 0.95))',
        borderRadius: 18,
        padding: 25,
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Sparkle decorations */}
        <div style={{ position: 'absolute', top: 10, left: 20, fontSize: '1.5rem', opacity: 0.6 }}>✨</div>
        <div style={{ position: 'absolute', top: 30, right: 30, fontSize: '1.2rem', opacity: 0.5 }}>⭐</div>
        <div style={{ position: 'absolute', bottom: 20, left: 40, fontSize: '1rem', opacity: 0.4 }}>🌟</div>
        
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 15, marginBottom: 15 }}>
          <div style={{
            background: 'linear-gradient(135deg, #f59e0b, #f97316)',
            padding: '8px 16px',
            borderRadius: 30,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            boxShadow: '0 4px 20px rgba(245, 158, 11, 0.4)'
          }}>
            <span style={{ fontSize: '1.3rem' }}>🏆</span>
            <span style={{ color: '#fff', fontWeight: 800, fontSize: '0.95rem', textTransform: 'uppercase', letterSpacing: 1 }}>
              Bundle of the Week
            </span>
          </div>
          <span style={{
            background: 'rgba(236, 72, 153, 0.3)',
            color: '#f472b6',
            padding: '6px 14px',
            borderRadius: 20,
            fontSize: '0.85rem',
            fontWeight: 600
          }}>
            {featured.discount_percent}% OFF
          </span>
        </div>
        
        {/* Bundle Name & Description */}
        <h2 style={{ 
          color: '#fff', 
          fontSize: '1.8rem', 
          margin: '10px 0',
          background: 'linear-gradient(135deg, #fff 0%, #f472b6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontWeight: 800
        }}>
          📦 {featured.name}
        </h2>
        
        <p style={{ color: '#c4b5fd', fontSize: '1rem', marginBottom: 20, lineHeight: 1.6 }}>
          {featured.description}
        </p>
        
        {/* Tagline */}
        <div style={{
          background: 'rgba(124, 58, 237, 0.2)',
          border: '1px solid rgba(124, 58, 237, 0.4)',
          borderRadius: 12,
          padding: 15,
          marginBottom: 20,
          textAlign: 'center'
        }}>
          <p style={{ color: '#a78bfa', margin: 0, fontWeight: 600, fontSize: '1.05rem' }}>
            {tagline}
          </p>
        </div>
        
        {/* Protocols included */}
        <div style={{ marginBottom: 20 }}>
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 10 }}>
            🎁 {featured.protocol_count} Premium Protocols Included:
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {featured.protocols?.slice(0, 4).map((p, i) => (
              <span 
                key={i}
                style={{
                  background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.3), rgba(236, 72, 153, 0.3))',
                  color: '#f472b6',
                  padding: '6px 14px',
                  borderRadius: 20,
                  fontSize: '0.85rem',
                  fontWeight: 500
                }}
              >
                {p.name}
              </span>
            ))}
            {featured.protocols?.length > 4 && (
              <span style={{
                background: 'rgba(16, 185, 129, 0.3)',
                color: '#10b981',
                padding: '6px 14px',
                borderRadius: 20,
                fontSize: '0.85rem',
                fontWeight: 600
              }}>
                +{featured.protocols.length - 4} MORE!
              </span>
            )}
          </div>
        </div>
        
        {/* Pricing */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 15,
          padding: 20,
          marginBottom: 20
        }}>
          <div>
            <p style={{ color: '#71717a', textDecoration: 'line-through', margin: 0, fontSize: '1.1rem' }}>
              Was ${featured.original_price?.toFixed(2)}
            </p>
            <p style={{ 
              color: '#10b981', 
              fontSize: '2.2rem', 
              fontWeight: 800, 
              margin: '5px 0 0 0',
              textShadow: '0 0 20px rgba(16, 185, 129, 0.5)'
            }}>
              ${featured.bundle_price?.toFixed(2)}
            </p>
          </div>
          <div style={{
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))',
            borderRadius: 12,
            padding: 15,
            textAlign: 'center'
          }}>
            <p style={{ color: '#10b981', fontWeight: 700, fontSize: '1.4rem', margin: 0 }}>
              SAVE ${featured.savings?.toFixed(2)}
            </p>
            <p style={{ color: '#71717a', fontSize: '0.8rem', margin: '5px 0 0 0' }}>
              That is basically FREE money! 💸
            </p>
          </div>
        </div>
        
        {/* CTA Button */}
        <button
          onClick={handlePurchase}
          disabled={purchasing}
          style={{
            width: '100%',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%)',
            border: 'none',
            borderRadius: 12,
            padding: '18px 30px',
            fontSize: '1.2rem',
            fontWeight: 700,
            color: '#fff',
            cursor: purchasing ? 'wait' : 'pointer',
            opacity: purchasing ? 0.7 : 1,
            boxShadow: '0 8px 30px rgba(16, 185, 129, 0.4)',
            transition: 'all 0.3s ease',
            textTransform: 'uppercase',
            letterSpacing: 1
          }}
          data-testid="buy-bundle-of-week"
        >
          {purchasing ? '⏳ Grabbing Your Bundle...' : '🚀 Grab This Deal NOW!'}
        </button>
        
        {/* Sales count */}
        <p style={{ textAlign: 'center', color: '#71717a', fontSize: '0.85rem', marginTop: 15, marginBottom: 0 }}>
          🔥 {featured.total_sales || 0} smart people already grabbed this bundle!
        </p>
      </div>
      
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.95; }
        }
      `}</style>
    </div>
  );
};

export default BundleOfTheWeek;
