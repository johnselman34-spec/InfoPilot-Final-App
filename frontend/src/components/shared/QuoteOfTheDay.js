import React, { useState, useEffect, useRef } from 'react';

// Hilarious quotes from "Letters to Evelyn" manuscript (excluding "Drink water" per user request)
const MANUSCRIPT_QUOTES = [
  { quote: "I said fly to the sun, not IN it!", context: "Pilot instruction mishap", chapter: 9 },
  { quote: "These eggs are so good! Are they cage free?", context: "Unknowingly eating poisoned eggs", chapter: 3 },
  { quote: "Fack off!", context: "John's Monty Python response to being called Jesus", chapter: 5 },
  { quote: "I'm not even afraid of saving my pet gerbil.", context: "Random hallucination moment", chapter: 7 },
  { quote: "La-la-la-la!", context: "Captain plugging ears like Lloyd Christmas from Dumb & Dumber", chapter: 5 },
  { quote: "You're Jesus. - No I'm not! - You're Jesus. - STOP IT!", context: "Repeated 9-12 times per encounter", chapter: 5 },
  { quote: "I bent a penny barehanded... everyone came to lift me up and I went crowd surfing!", context: "Post-hallucination feat", chapter: 10 },
  { quote: "Only life, no more hurt.", context: "Aliens' farewell message", chapter: 15 },
  { quote: "The sky! This guy!", context: "Durham's universal broadcast to insult John", chapter: 25 },
  { quote: "I'm not the best extraterrestrial dinosaur vagina pilot! You're the woman! Take the controls!", context: "Peak absurdity", chapter: 25 },
  { quote: "I'm not Jesus! Why do you keep saying that I'm Jesus?", context: "John's frustration with the Captain", chapter: 5 },
  { quote: "We're either infinite Love or we're not. Can I say that one last time?", context: "John's philosophical repetition", chapter: 22 },
  { quote: "My life for the last few years has been occupied by you in my heart.", context: "To Evelyn", chapter: 1 },
  { quote: "The universe is inside each and every one of us.", context: "Profound moment", chapter: 22 },
  { quote: "Have a sense of humor, even when no one is looking.", context: "Life advice", chapter: 1 },
];

// Get quote based on day of year for consistency
const getQuoteOfTheDay = () => {
  const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0)) / 86400000);
  return MANUSCRIPT_QUOTES[dayOfYear % MANUSCRIPT_QUOTES.length];
};

// Generate shareable image using canvas
const generateShareImage = async (quote) => {
  const canvas = document.createElement('canvas');
  canvas.width = 1200;
  canvas.height = 630;
  const ctx = canvas.getContext('2d');
  
  // Background gradient
  const gradient = ctx.createLinearGradient(0, 0, 1200, 630);
  gradient.addColorStop(0, '#1a1a2e');
  gradient.addColorStop(0.5, '#302b63');
  gradient.addColorStop(1, '#24243e');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 1200, 630);
  
  // Purple accent bar
  ctx.fillStyle = '#7c3aed';
  ctx.fillRect(0, 0, 8, 630);
  
  // Quote marks decoration
  ctx.font = 'bold 200px Georgia';
  ctx.fillStyle = 'rgba(124, 58, 237, 0.15)';
  ctx.fillText('"', 30, 180);
  
  // Quote text
  ctx.font = 'italic 36px Georgia';
  ctx.fillStyle = '#fce7f3';
  
  // Word wrap the quote
  const words = quote.quote.split(' ');
  let line = '';
  let y = 200;
  const maxWidth = 1050;
  
  for (let word of words) {
    const testLine = line + word + ' ';
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && line !== '') {
      ctx.fillText('"' + line.trim() + (y === 200 ? '' : ''), 80, y);
      line = word + ' ';
      y += 50;
    } else {
      line = testLine;
    }
  }
  ctx.fillText((y === 200 ? '"' : '') + line.trim() + '"', 80, y);
  
  // Attribution
  ctx.font = 'bold 24px Arial';
  ctx.fillStyle = '#a78bfa';
  ctx.fillText(`— John Selman, "Letters to Evelyn" (Ch. ${quote.chapter})`, 80, y + 80);
  
  // Context
  ctx.font = '18px Arial';
  ctx.fillStyle = '#71717a';
  ctx.fillText(`Context: ${quote.context}`, 80, y + 115);
  
  // Book promo
  ctx.fillStyle = 'rgba(236, 72, 153, 0.3)';
  ctx.fillRect(80, 520, 400, 80);
  ctx.fillStyle = '#f472b6';
  ctx.font = 'bold 20px Arial';
  ctx.fillText('📚 Get the Book - Only $2.99!', 100, 565);
  ctx.font = '14px Arial';
  ctx.fillStyle = '#a78bfa';
  ctx.fillText('amazon.com/dp/B0CQZ8R191', 100, 588);
  
  // InfoPilot branding
  ctx.fillStyle = '#ec4899';
  ctx.font = 'bold 16px Arial';
  ctx.fillText('Shared from InfoPilot', 1000, 600);
  
  return canvas.toDataURL('image/png');
};

const QuoteOfTheDay = ({ compact = false }) => {
  const [quote, setQuote] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const [showShareOptions, setShowShareOptions] = useState(false);

  useEffect(() => {
    setQuote(getQuoteOfTheDay());
  }, []);

  const handleShare = async (platform) => {
    if (!quote) return;
    setIsSharing(true);
    
    const shareText = `"${quote.quote}" — John Selman, "Letters to Evelyn" (Ch. ${quote.chapter})\n\nContext: ${quote.context}\n\n📚 Get the book: https://amazon.com/dp/B0CQZ8R191`;
    const shareUrl = 'https://amazon.com/dp/B0CQZ8R191';
    
    try {
      switch (platform) {
        case 'twitter':
          window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}`, '_blank');
          break;
        case 'facebook':
          window.open(`https://www.facebook.com/sharer/sharer.php?quote=${encodeURIComponent(shareText)}&u=${encodeURIComponent(shareUrl)}`, '_blank');
          break;
        case 'linkedin':
          window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`, '_blank');
          break;
        case 'copy':
          await navigator.clipboard.writeText(shareText);
          alert('Quote copied to clipboard!');
          break;
        case 'image':
          const imageData = await generateShareImage(quote);
          const link = document.createElement('a');
          link.download = 'letters-to-evelyn-quote.png';
          link.href = imageData;
          link.click();
          break;
        default:
          if (navigator.share) {
            await navigator.share({
              title: 'Quote from "Letters to Evelyn"',
              text: shareText,
              url: shareUrl
            });
          }
      }
    } catch (err) {
      console.error('Share failed:', err);
    }
    
    setIsSharing(false);
    setShowShareOptions(false);
  };

  if (!quote) return null;

  if (compact) {
    return (
      <div 
        style={{
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(236, 72, 153, 0.15))',
          borderRadius: 12,
          padding: '12px 16px',
          marginBottom: 15,
          border: '1px solid rgba(124, 58, 237, 0.3)',
          cursor: 'pointer'
        }}
        onClick={() => setIsExpanded(!isExpanded)}
        data-testid="quote-of-day-compact"
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: '1.1rem' }}>💬</span>
          <span style={{ fontSize: '0.7rem', color: '#a78bfa', fontWeight: 600, textTransform: 'uppercase' }}>
            Quote of the Day
          </span>
        </div>
        <p style={{ 
          color: '#f472b6', 
          fontStyle: 'italic', 
          fontSize: '0.85rem', 
          margin: 0,
          lineHeight: 1.4
        }}>
          "{quote.quote}"
        </p>
        {isExpanded && (
          <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(124, 58, 237, 0.2)' }}>
            <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: 0 }}>
              — From "Letters to Evelyn" (Ch. {quote.chapter})
            </p>
            <p style={{ color: '#71717a', fontSize: '0.7rem', margin: '4px 0 0 0' }}>
              Context: {quote.context}
            </p>
          </div>
        )}
      </div>
    );
  }

  // Full-size version
  return (
    <div 
      style={{
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(236, 72, 153, 0.2))',
        borderRadius: 16,
        padding: 20,
        marginBottom: 20,
        border: '2px solid rgba(124, 58, 237, 0.4)',
        position: 'relative',
        overflow: 'hidden'
      }}
      data-testid="quote-of-day-full"
    >
      {/* Decorative quote marks */}
      <div style={{
        position: 'absolute',
        top: -10,
        left: 10,
        fontSize: '5rem',
        color: 'rgba(124, 58, 237, 0.15)',
        fontFamily: 'Georgia, serif',
        lineHeight: 1
      }}>"</div>
      
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '1.5rem' }}>💬</span>
          <span style={{ 
            fontSize: '0.85rem', 
            color: '#a78bfa', 
            fontWeight: 700, 
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Quote of the Day
          </span>
          <span style={{ 
            background: 'rgba(236, 72, 153, 0.2)', 
            color: '#f472b6', 
            padding: '2px 8px', 
            borderRadius: 10, 
            fontSize: '0.7rem' 
          }}>
            From "Letters to Evelyn"
          </span>
        </div>
        
        {/* Share Button */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowShareOptions(!showShareOptions)}
            style={{
              background: 'rgba(124, 58, 237, 0.3)',
              border: '1px solid rgba(124, 58, 237, 0.5)',
              borderRadius: 20,
              padding: '6px 14px',
              color: '#a78bfa',
              fontSize: '0.8rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
            data-testid="share-quote-btn"
          >
            📤 Share
          </button>
          
          {/* Share dropdown */}
          {showShareOptions && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: 8,
              background: '#1a1a2e',
              border: '1px solid rgba(124, 58, 237, 0.5)',
              borderRadius: 12,
              padding: 8,
              zIndex: 100,
              minWidth: 180,
              boxShadow: '0 10px 30px rgba(0,0,0,0.5)'
            }}>
              {[
                { id: 'twitter', icon: '🐦', label: 'Twitter/X' },
                { id: 'facebook', icon: '📘', label: 'Facebook' },
                { id: 'linkedin', icon: '💼', label: 'LinkedIn' },
                { id: 'copy', icon: '📋', label: 'Copy Text' },
                { id: 'image', icon: '🖼️', label: 'Download Image' },
              ].map(option => (
                <button
                  key={option.id}
                  onClick={() => handleShare(option.id)}
                  disabled={isSharing}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    width: '100%',
                    padding: '10px 12px',
                    background: 'transparent',
                    border: 'none',
                    borderRadius: 8,
                    color: '#e2e8f0',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                  onMouseEnter={(e) => e.target.style.background = 'rgba(124, 58, 237, 0.2)'}
                  onMouseLeave={(e) => e.target.style.background = 'transparent'}
                  data-testid={`share-${option.id}`}
                >
                  <span>{option.icon}</span>
                  <span>{option.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      
      <blockquote style={{ 
        color: '#fce7f3', 
        fontStyle: 'italic', 
        fontSize: '1.1rem', 
        margin: '0 0 15px 0',
        lineHeight: 1.5,
        position: 'relative',
        zIndex: 1
      }}>
        "{quote.quote}"
      </blockquote>
      
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 10
      }}>
        <div>
          <p style={{ color: '#a78bfa', fontSize: '0.85rem', margin: 0, fontWeight: 600 }}>
            — John Selman, Chapter {quote.chapter}
          </p>
          <p style={{ color: '#71717a', fontSize: '0.75rem', margin: '4px 0 0 0' }}>
            Context: {quote.context}
          </p>
        </div>
        
        <a 
          href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: 'linear-gradient(135deg, #ec4899, #f97316)',
            color: 'white',
            padding: '8px 16px',
            borderRadius: 20,
            fontSize: '0.8rem',
            fontWeight: 700,
            textDecoration: 'none',
            boxShadow: '0 4px 15px rgba(236, 72, 153, 0.3)'
          }}
          data-testid="quote-buy-book-link"
        >
          📚 Read the Book - $2.99
        </a>
      </div>
    </div>
  );
};

export default QuoteOfTheDay;
