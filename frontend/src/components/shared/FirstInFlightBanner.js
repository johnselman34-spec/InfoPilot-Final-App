/**
 * First in Flight Banner
 * Highlights InfoPilot's pioneering search monetization platform
 */
import React, { useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';

const FirstInFlightBanner = ({ onLearnMore }) => {
  const { isDarkMode } = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div 
      style={{
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(59, 130, 246, 0.15), rgba(16, 185, 129, 0.15))',
        borderRadius: 20,
        padding: '25px 30px',
        margin: '20px 0',
        border: '2px solid rgba(124, 58, 237, 0.3)',
        position: 'relative',
        overflow: 'hidden'
      }}
      data-testid="first-in-flight-banner"
    >
      {/* Background Airplane Animation */}
      <div style={{
        position: 'absolute',
        top: 10,
        right: 20,
        fontSize: '4rem',
        opacity: 0.1,
        transform: 'rotate(-15deg)'
      }}>
        ✈️
      </div>
      
      {/* Main Content */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 15,
          marginBottom: 15,
          flexWrap: 'wrap'
        }}>
          <span style={{ fontSize: '2.5rem' }}>🚀</span>
          <div>
            <h2 style={{
              margin: 0,
              background: 'linear-gradient(135deg, #7c3aed, #3b82f6, #10b981)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              fontSize: '1.8rem',
              fontWeight: 800
            }}>
              FIRST IN FLIGHT
            </h2>
            <p style={{
              margin: 0,
              color: '#f472b6',
              fontWeight: 600,
              fontSize: '1rem',
              letterSpacing: '0.5px'
            }}>
              with Search Monetization
            </p>
          </div>
          <span style={{
            background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
            padding: '6px 14px',
            borderRadius: 20,
            color: '#fff',
            fontWeight: 700,
            fontSize: '0.75rem',
            animation: 'pulse 2s infinite'
          }}>
            PIONEERING
          </span>
        </div>
        
        {/* Value Proposition */}
        <div style={{
          background: isDarkMode ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.5)',
          borderRadius: 15,
          padding: 20,
          marginBottom: 15
        }}>
          <p style={{
            margin: 0,
            color: isDarkMode ? '#e2e8f0' : '#1e293b',
            fontSize: '1.1rem',
            lineHeight: 1.7,
            fontWeight: 500
          }}>
            <span style={{ fontSize: '1.5rem', marginRight: 8 }}>💡</span>
            So much time is spent searching for valuable information. 
            <strong style={{ color: '#7c3aed' }}> Why cant it be worth anything?</strong>
          </p>
          <p style={{
            margin: '12px 0 0 0',
            color: isDarkMode ? '#a1a1aa' : '#64748b',
            fontSize: '1rem',
            lineHeight: 1.6
          }}>
            If your search expertise is valuable to businesses, then 
            <strong style={{ color: '#10b981' }}> it should be valuable to YOU!</strong>
          </p>
        </div>
        
        {/* Features Grid */}
        {isExpanded && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 15,
            marginBottom: 15,
            animation: 'fadeIn 0.3s ease'
          }}>
            {[
              { emoji: '🔍', title: 'Create Protocols', desc: 'Build powerful search formulas with InfoJet 2.0' },
              { emoji: '💰', title: 'Monetize', desc: 'Sell your protocols in the marketplace' },
              { emoji: '🌐', title: 'Share Knowledge', desc: 'Help others find valuable information' },
              { emoji: '📈', title: 'Earn Passive Income', desc: 'Get paid every time someone uses your protocol' }
            ].map((feature, idx) => (
              <div 
                key={idx}
                style={{
                  background: isDarkMode ? 'rgba(124, 58, 237, 0.1)' : 'rgba(124, 58, 237, 0.05)',
                  borderRadius: 12,
                  padding: 15,
                  border: '1px solid rgba(124, 58, 237, 0.2)'
                }}
              >
                <span style={{ fontSize: '1.5rem' }}>{feature.emoji}</span>
                <h4 style={{ 
                  margin: '8px 0 5px 0', 
                  color: '#7c3aed',
                  fontSize: '0.95rem'
                }}>
                  {feature.title}
                </h4>
                <p style={{ 
                  margin: 0, 
                  color: isDarkMode ? '#a1a1aa' : '#64748b',
                  fontSize: '0.8rem'
                }}>
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        )}
        
        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              background: 'linear-gradient(135deg, #7c3aed, #3b82f6)',
              border: 'none',
              borderRadius: 25,
              padding: '12px 25px',
              color: '#fff',
              fontWeight: 700,
              cursor: 'pointer',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: '0 5px 20px rgba(124, 58, 237, 0.4)'
            }}
            data-testid="learn-more-btn"
          >
            {isExpanded ? '▲ Show Less' : '▼ Learn More'}
          </button>
          
          {onLearnMore && (
            <button
              onClick={onLearnMore}
              style={{
                background: 'linear-gradient(135deg, #10b981, #059669)',
                border: 'none',
                borderRadius: 25,
                padding: '12px 25px',
                color: '#fff',
                fontWeight: 700,
                cursor: 'pointer',
                fontSize: '0.9rem',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                boxShadow: '0 5px 20px rgba(16, 185, 129, 0.4)'
              }}
              data-testid="start-earning-btn"
            >
              💰 Start Earning Now
            </button>
          )}
        </div>
      </div>
      
      {/* CSS for animations */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default FirstInFlightBanner;
