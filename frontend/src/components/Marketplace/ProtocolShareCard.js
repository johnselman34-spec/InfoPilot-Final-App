/**
 * Protocol Share Card Component
 * Generates beautiful shareable cards for protocols on social media
 * Creates Open Graph-compatible previews for Twitter/Facebook sharing
 */
import React, { useState } from 'react';
import { API } from '../../utils/api';

// Share templates for different platforms
const SHARE_TEMPLATES = {
  twitter: (protocol) => {
    const priceText = protocol.price > 0 ? `$${protocol.price.toFixed(2)}` : '🆓 FREE';
    const hashtags = 'InfoPilot,SearchProtocol,InfoJet';
    return `🚀 Check out "${protocol.name}" on InfoPilot!\n\n${protocol.protocol?.substring(0, 100)}...\n\n💰 ${priceText}\n📊 ${protocol.copy_count || 0} copies\n\n#${hashtags}`;
  },
  facebook: (protocol) => {
    const priceText = protocol.price > 0 ? `$${protocol.price.toFixed(2)}` : 'FREE';
    return `🔍 Found an amazing search protocol!\n\n"${protocol.name}"\n${protocol.protocol?.substring(0, 150)}...\n\nPrice: ${priceText} | Copies: ${protocol.copy_count || 0}`;
  },
  linkedin: (protocol) => {
    const priceText = protocol.price > 0 ? `$${protocol.price.toFixed(2)}` : 'FREE';
    return `I'm using "${protocol.name}" on InfoPilot Explorer to supercharge my searches!\n\n${protocol.protocol?.substring(0, 200)}...\n\nPrice: ${priceText}\n\n#DataResearch #SearchOptimization #InfoPilot`;
  },
  email: (protocol) => {
    const priceText = protocol.price > 0 ? `$${protocol.price.toFixed(2)}` : 'FREE';
    return {
      subject: `Check out this search protocol: ${protocol.name}`,
      body: `Hey!\n\nI found this amazing search protocol on InfoPilot Explorer:\n\n"${protocol.name}"\n\nProtocol: ${protocol.protocol}\n\nPrice: ${priceText}\nCopies: ${protocol.copy_count || 0}\n\nCheck it out at: https://infopilotexplorer.biz\n\nHappy searching!`
    };
  }
};

// Fun share messages inspired by Letters to Evelyn
const SHARE_MESSAGES = [
  "This protocol is BETTER than my stepmother's cooking! 🍳📚",
  "I searched 10 months of hallucinations to find this gem! ✨",
  "From Navy pilot to search master - this protocol FLIES! ✈️",
  "Not even military-grade drugs could stop me from sharing this! 💪",
  "My stepmother tried to ground me, but THIS protocol helps me soar! 🚀",
  "5-star protocol! Even Readers' Favorite would approve! ⭐⭐⭐⭐⭐",
  "This search protocol turned my chaos into a bestseller! 📖",
  "Voyage Media should option THIS protocol for film! 🎬",
];

const ProtocolShareCard = ({ protocol, showToast }) => {
  const [showShareModal, setShowShareModal] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  
  if (!protocol) return null;
  
  const shareUrl = `https://infopilotexplorer.biz/marketplace?protocol=${protocol.id}`;
  const funnyMessage = SHARE_MESSAGES[Math.floor(Math.random() * SHARE_MESSAGES.length)];
  
  const handleShare = (platform) => {
    let url = '';
    
    switch (platform) {
      case 'twitter':
        const twitterText = encodeURIComponent(SHARE_TEMPLATES.twitter(protocol));
        url = `https://twitter.com/intent/tweet?text=${twitterText}&url=${encodeURIComponent(shareUrl)}`;
        break;
      case 'facebook':
        url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}&quote=${encodeURIComponent(SHARE_TEMPLATES.facebook(protocol))}`;
        break;
      case 'linkedin':
        url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
        break;
      case 'email':
        const emailData = SHARE_TEMPLATES.email(protocol);
        url = `mailto:?subject=${encodeURIComponent(emailData.subject)}&body=${encodeURIComponent(emailData.body)}`;
        break;
      default:
        break;
    }
    
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer,width=600,height=400');
    }
    
    showToast?.(`📤 Sharing to ${platform}!`, 'success');
  };
  
  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopiedLink(true);
      showToast?.('🔗 Link copied to clipboard!', 'success');
      setTimeout(() => setCopiedLink(false), 3000);
    } catch (e) {
      showToast?.('Failed to copy link', 'error');
    }
  };
  
  return (
    <>
      {/* Share Button */}
      <button
        onClick={() => setShowShareModal(true)}
        style={{
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(16, 185, 129, 0.2))',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: 8,
          padding: '6px 12px',
          color: '#60a5fa',
          fontSize: '0.8rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 5,
          transition: 'all 0.2s'
        }}
        data-testid={`share-protocol-${protocol.id}`}
        title="Share this protocol"
      >
        📤 Share
      </button>
      
      {/* Share Modal */}
      {showShareModal && (
        <div 
          className="modal-overlay" 
          onClick={() => setShowShareModal(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000
          }}
        >
          <div 
            className="modal"
            onClick={e => e.stopPropagation()}
            style={{
              background: 'linear-gradient(135deg, rgba(20, 10, 40, 0.98), rgba(30, 20, 60, 0.98))',
              borderRadius: 20,
              padding: 25,
              maxWidth: 500,
              width: '90%',
              border: '2px solid rgba(124, 58, 237, 0.5)',
              boxShadow: '0 25px 50px rgba(124, 58, 237, 0.3)'
            }}
            data-testid="share-modal"
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h2 style={{ color: '#f472b6', margin: 0 }}>📤 Share Protocol</h2>
              <button
                onClick={() => setShowShareModal(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#a1a1aa',
                  fontSize: '1.5rem',
                  cursor: 'pointer'
                }}
              >
                ×
              </button>
            </div>
            
            {/* Protocol Preview Card */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(236, 72, 153, 0.15))',
              borderRadius: 16,
              padding: 20,
              marginBottom: 20,
              border: '1px solid rgba(124, 58, 237, 0.3)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <h3 style={{ color: '#fff', margin: 0, fontSize: '1.1rem' }}>{protocol.name}</h3>
                <span style={{
                  background: protocol.price > 0 ? 'linear-gradient(135deg, #f59e0b, #d97706)' : 'linear-gradient(135deg, #10b981, #059669)',
                  color: '#fff',
                  padding: '4px 10px',
                  borderRadius: 20,
                  fontSize: '0.8rem',
                  fontWeight: 700
                }}>
                  {protocol.price > 0 ? `$${protocol.price.toFixed(2)}` : '🆓 FREE'}
                </span>
              </div>
              
              <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '10px 0', lineHeight: 1.5 }}>
                <code style={{ 
                  background: 'rgba(0,0,0,0.3)', 
                  padding: '2px 6px', 
                  borderRadius: 4,
                  color: '#10b981'
                }}>
                  {protocol.protocol?.substring(0, 100)}...
                </code>
              </p>
              
              <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap' }}>
                <span style={{ color: '#60a5fa', fontSize: '0.8rem' }}>
                  📊 {protocol.copy_count || 0} copies
                </span>
                <span style={{ color: '#a78bfa', fontSize: '0.8rem' }}>
                  🏷️ {protocol.category || 'Uncategorized'}
                </span>
                <span style={{ color: '#f472b6', fontSize: '0.8rem' }}>
                  👤 {protocol.author_name || 'Anonymous'}
                </span>
              </div>
            </div>
            
            {/* Funny Message */}
            <div style={{
              background: 'rgba(245, 158, 11, 0.1)',
              borderRadius: 10,
              padding: 12,
              marginBottom: 20,
              borderLeft: '4px solid #f59e0b'
            }}>
              <p style={{ color: '#fbbf24', margin: 0, fontSize: '0.85rem', fontStyle: 'italic' }}>
                💡 {funnyMessage}
              </p>
            </div>
            
            {/* Share Buttons */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, marginBottom: 20 }}>
              <button
                onClick={() => handleShare('twitter')}
                style={{
                  background: 'linear-gradient(135deg, #1da1f2, #0d8bd9)',
                  border: 'none',
                  borderRadius: 10,
                  padding: '12px 20px',
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8
                }}
                data-testid="share-twitter"
              >
                🐦 Twitter
              </button>
              
              <button
                onClick={() => handleShare('facebook')}
                style={{
                  background: 'linear-gradient(135deg, #4267b2, #365899)',
                  border: 'none',
                  borderRadius: 10,
                  padding: '12px 20px',
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8
                }}
                data-testid="share-facebook"
              >
                📘 Facebook
              </button>
              
              <button
                onClick={() => handleShare('linkedin')}
                style={{
                  background: 'linear-gradient(135deg, #0077b5, #005582)',
                  border: 'none',
                  borderRadius: 10,
                  padding: '12px 20px',
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8
                }}
                data-testid="share-linkedin"
              >
                💼 LinkedIn
              </button>
              
              <button
                onClick={() => handleShare('email')}
                style={{
                  background: 'linear-gradient(135deg, #7c3aed, #6d28d9)',
                  border: 'none',
                  borderRadius: 10,
                  padding: '12px 20px',
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8
                }}
                data-testid="share-email"
              >
                📧 Email
              </button>
            </div>
            
            {/* Copy Link */}
            <div style={{
              display: 'flex',
              gap: 10,
              background: 'rgba(0,0,0,0.3)',
              borderRadius: 10,
              padding: 10
            }}>
              <input
                type="text"
                value={shareUrl}
                readOnly
                style={{
                  flex: 1,
                  background: 'transparent',
                  border: 'none',
                  color: '#a1a1aa',
                  fontSize: '0.85rem'
                }}
              />
              <button
                onClick={copyLink}
                style={{
                  background: copiedLink ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #6b7280, #4b5563)',
                  border: 'none',
                  borderRadius: 8,
                  padding: '8px 15px',
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: '0.85rem'
                }}
                data-testid="copy-share-link"
              >
                {copiedLink ? '✓ Copied!' : '📋 Copy'}
              </button>
            </div>
            
            {/* Letters to Evelyn Promo */}
            <div style={{
              marginTop: 20,
              padding: 15,
              background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.1), rgba(124, 58, 237, 0.1))',
              borderRadius: 12,
              border: '1px dashed rgba(236, 72, 153, 0.3)',
              textAlign: 'center'
            }}>
              <p style={{ color: '#f472b6', margin: 0, fontSize: '0.8rem' }}>
                📚 While sharing, check out Letters to Evelyn by John Selman!
                <br />
                <a 
                  href="https://www.amazon.com/Letters-Evelyn-John-Selman/dp/B0F3XFG14J/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ color: '#60a5fa', textDecoration: 'underline' }}
                >
                  ⭐ 19 Five-Star Reviews on Amazon!
                </a>
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ProtocolShareCard;
