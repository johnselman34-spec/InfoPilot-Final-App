/**
 * Cross-Sell Recommendations Component
 * Shows related protocols and bundles during checkout
 * Designed for MAXIMUM REVENUE with hilarious upsell messages! 💰
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

// Hilarious upsell messages
const UPSELL_MESSAGES = [
  "🎯 People with exquisite taste also bought these!",
  "💎 Complete your collection! Your future self is cheering!",
  "🚀 Level up your search game to LEGENDARY status!",
  "🏆 Champions bundle these together - become one of them!",
  "✨ These protocols are practically BEGGING to join your library!",
  "🔥 Hot picks that'll make your searches 10x more awesome!",
  "💡 Your brain will thank you for these additions!",
  "🎪 Don't let these gems slip away into the void!",
  "🌟 The universe is telling you to grab these too!",
  "🎁 Treat yourself! You've earned it!",
];

const DISCOUNT_MESSAGES = [
  "💰 Bundle & SAVE! Your wallet approves!",
  "🎉 Why buy one when you can have MANY for less?",
  "💸 Math says bundles = smart. Be smart!",
  "🏅 Elite users always go for the bundle deal!",
];

const CrossSellSection = ({ protocolId, showToast, onAddToCart }) => {
  const { token } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  // Initialize with stable random message
  const [funnyMessage, setFunnyMessage] = useState(() => UPSELL_MESSAGES[Math.floor(Math.random() * UPSELL_MESSAGES.length)]);
  // Stable random discount message
  const [discountMessage] = useState(() => DISCOUNT_MESSAGES[Math.floor(Math.random() * DISCOUNT_MESSAGES.length)]);

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!protocolId) return;
      
      try {
        const res = await fetch(`${API}/bundles/cross-sell/${protocolId}`);
        if (res.ok) {
          const data = await res.json();
          setRecommendations(data.recommendations || []);
          if (data.funny_message) {
            setFunnyMessage(data.funny_message);
          }
        }
      } catch (e) {
        console.error('Failed to fetch cross-sell:', e);
      }
      setLoading(false);
    };
    
    fetchRecommendations();
  }, [protocolId]);

  if (loading) {
    return (
      <div style={{ padding: 20, textAlign: 'center', color: '#a1a1aa' }}>
        <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>🔄</span>
        {' '}Finding perfect matches...
      </div>
    );
  }

  if (recommendations.length === 0) {
    return null;
  }

  const protocols = recommendations.filter(r => r.type === 'protocol');
  const bundles = recommendations.filter(r => r.type === 'bundle');

  return (
    <div 
      data-testid="cross-sell-section"
      style={{
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(236, 72, 153, 0.1))',
        borderRadius: 16,
        padding: 20,
        marginTop: 20,
        border: '2px dashed rgba(245, 158, 11, 0.4)'
      }}
    >
      {/* Header with sparkles */}
      <div style={{ textAlign: 'center', marginBottom: 20 }}>
        <div style={{ fontSize: '1.5rem', marginBottom: 10 }}>
          ✨ WAIT! Before you go... ✨
        </div>
        <h3 style={{ 
          color: '#f59e0b', 
          margin: 0,
          background: 'linear-gradient(135deg, #f59e0b, #ec4899)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontWeight: 800
        }}>
          {funnyMessage}
        </h3>
      </div>

      {/* Bundle Recommendations (Show first for higher value) */}
      {bundles.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <p style={{ color: '#ec4899', fontWeight: 600, marginBottom: 10 }}>
            📦 {DISCOUNT_MESSAGES[Math.floor(Math.random() * DISCOUNT_MESSAGES.length)]}
          </p>
          <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap' }}>
            {bundles.map(bundle => (
              <div
                key={bundle.id}
                style={{
                  background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(236, 72, 153, 0.2))',
                  borderRadius: 12,
                  padding: 15,
                  flex: '1 1 250px',
                  border: '2px solid rgba(124, 58, 237, 0.4)',
                  position: 'relative'
                }}
              >
                {/* Discount badge */}
                <div style={{
                  position: 'absolute',
                  top: -10,
                  right: 10,
                  background: 'linear-gradient(135deg, #f472b6, #ec4899)',
                  color: '#fff',
                  padding: '4px 12px',
                  borderRadius: 15,
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  boxShadow: '0 4px 15px rgba(236, 72, 153, 0.4)'
                }}>
                  {bundle.discount_percent}% OFF
                </div>
                
                <h4 style={{ color: '#f472b6', margin: '5px 0 10px 0' }}>
                  📦 {bundle.name}
                </h4>
                <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '0 0 10px 0' }}>
                  {bundle.protocol_count} protocols included!
                </p>
                <button
                  onClick={() => onAddToCart?.('bundle', bundle)}
                  className="btn btn-primary"
                  style={{
                    width: '100%',
                    background: 'linear-gradient(135deg, #10b981, #059669)',
                    border: 'none',
                    padding: '10px 15px',
                    fontSize: '0.9rem',
                    fontWeight: 600
                  }}
                >
                  🛒 Add Bundle
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Related Protocols */}
      {protocols.length > 0 && (
        <div>
          <p style={{ color: '#10b981', fontWeight: 600, marginBottom: 10 }}>
            🎯 Related Protocols You Might Love:
          </p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {protocols.map(protocol => (
              <div
                key={protocol.id}
                style={{
                  background: 'rgba(0, 0, 0, 0.3)',
                  borderRadius: 10,
                  padding: 12,
                  flex: '1 1 180px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <h5 style={{ color: '#e2e8f0', margin: '0 0 5px 0', fontSize: '0.9rem' }}>
                    {protocol.name}
                  </h5>
                  <span style={{ 
                    color: protocol.is_free ? '#10b981' : '#f59e0b',
                    fontWeight: 700,
                    fontSize: '0.85rem'
                  }}>
                    {protocol.is_free ? '🆓 FREE!' : `$${protocol.price?.toFixed(2)}`}
                  </span>
                </div>
                <button
                  onClick={() => onAddToCart?.('protocol', protocol)}
                  className="btn btn-secondary"
                  style={{
                    marginTop: 10,
                    padding: '8px 12px',
                    fontSize: '0.8rem',
                    fontWeight: 600
                  }}
                >
                  + Add
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fun footer */}
      <div style={{ 
        textAlign: 'center', 
        marginTop: 20, 
        paddingTop: 15, 
        borderTop: '1px dashed rgba(245, 158, 11, 0.3)' 
      }}>
        <p style={{ color: '#71717a', fontSize: '0.8rem', margin: 0, fontStyle: 'italic' }}>
          💡 Pro tip: Bundle buyers save an average of 23% and look 47% cooler!*
        </p>
        <p style={{ color: '#52525b', fontSize: '0.65rem', margin: '5px 0 0 0' }}>
          *Statistics may be entirely made up but the savings are REAL!
        </p>
      </div>
    </div>
  );
};

export default CrossSellSection;
