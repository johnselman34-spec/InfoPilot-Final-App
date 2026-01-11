import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';

const QuoteGalleryPage = ({ showToast }) => {
  const { token } = useAuth();
  const [quotes, setQuotes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [shareModal, setShareModal] = useState(null);

  const fetchQuotes = useCallback(async () => {
    try {
      const res = await fetch(`${API}/quotes/gallery`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setQuotes(data.quotes || []);
        setCategories(data.categories || []);
      }
    } catch (e) {
      console.error('Failed to fetch quotes:', e);
    }
    setLoading(false);
  }, [token]);

  useEffect(() => {
    fetchQuotes();
  }, [fetchQuotes]);

  const filteredQuotes = selectedCategory === 'all' 
    ? quotes 
    : quotes.filter(q => q.category === selectedCategory);

  const handleShare = (quote) => {
    setShareModal(quote);
  };

  const shareToTwitter = (quote) => {
    const text = encodeURIComponent(`"${quote.quote}" - from Letters to Evelyn by John Selman\n\n📖 Get the book: https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191`);
    window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
    showToast('Opening Twitter...', 'success');
    setShareModal(null);
  };

  const shareToFacebook = (quote) => {
    const url = encodeURIComponent('https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191');
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}&quote=${encodeURIComponent(quote.quote)}`, '_blank');
    showToast('Opening Facebook...', 'success');
    setShareModal(null);
  };

  const copyToClipboard = async (quote) => {
    const text = `"${quote.quote}"\n\n- from Letters to Evelyn by John Selman\n📖 Get the book: https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191`;
    try {
      await navigator.clipboard.writeText(text);
      showToast('Quote copied to clipboard!', 'success');
      setShareModal(null);
    } catch (e) {
      showToast('Failed to copy', 'error');
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'hilarious': '#f472b6',
      'profound': '#a78bfa',
      'dad_joke': '#fbbf24',
      'chapter_teaser': '#10b981',
      'wild_element': '#ef4444',
      'marketing': '#3b82f6'
    };
    return colors[category] || '#6b7280';
  };

  const getCategoryIcon = (category) => {
    const icons = {
      'hilarious': '😂',
      'profound': '💭',
      'dad_joke': '🤣',
      'chapter_teaser': '📖',
      'wild_element': '🔥',
      'marketing': '📢'
    };
    return icons[category] || '💬';
  };

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 60 }}>
        <div className="spinner" style={{ margin: '0 auto' }}></div>
        <p style={{ color: '#a1a1aa', marginTop: 20 }}>Loading Quote Gallery...</p>
      </div>
    );
  }

  return (
    <div className="card" data-testid="quote-gallery-page">
      <div className="card-header">
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            📜 Quote Gallery
          </h2>
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginTop: 5 }}>
            Hilarious & Profound quotes from "Letters to Evelyn" by John Selman
          </p>
        </div>
        <a 
          href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-primary"
        >
          📖 Get the Book - $2.99
        </a>
      </div>

      {/* Category Filter */}
      <div style={{ 
        display: 'flex', 
        gap: 10, 
        flexWrap: 'wrap', 
        marginBottom: 25,
        padding: 15,
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 12
      }}>
        <button
          className={`btn ${selectedCategory === 'all' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setSelectedCategory('all')}
          style={{ padding: '8px 16px', fontSize: '0.85rem' }}
        >
          🎯 All ({quotes.length})
        </button>
        {categories.map(cat => (
          <button
            key={cat.id}
            className={`btn ${selectedCategory === cat.id ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedCategory(cat.id)}
            style={{ 
              padding: '8px 16px', 
              fontSize: '0.85rem',
              borderColor: selectedCategory === cat.id ? getCategoryColor(cat.id) : undefined
            }}
          >
            {getCategoryIcon(cat.id)} {cat.name} ({cat.count})
          </button>
        ))}
      </div>

      {/* Quote Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', 
        gap: 20 
      }}>
        {filteredQuotes.map((quote, idx) => (
          <div
            key={idx}
            style={{
              background: 'rgba(30, 20, 50, 0.6)',
              borderRadius: 16,
              padding: 20,
              border: `2px solid ${getCategoryColor(quote.category)}40`,
              position: 'relative',
              transition: 'transform 0.2s, border-color 0.2s',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.borderColor = getCategoryColor(quote.category);
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.borderColor = `${getCategoryColor(quote.category)}40`;
            }}
            data-testid={`quote-card-${idx}`}
          >
            {/* Category Badge */}
            <div style={{
              position: 'absolute',
              top: -10,
              right: 15,
              background: getCategoryColor(quote.category),
              color: '#fff',
              padding: '4px 12px',
              borderRadius: 20,
              fontSize: '0.7rem',
              fontWeight: 600,
              textTransform: 'uppercase'
            }}>
              {getCategoryIcon(quote.category)} {quote.category.replace('_', ' ')}
            </div>

            {/* Quote Text */}
            <div style={{ marginTop: 10, marginBottom: 15 }}>
              <span style={{ 
                fontSize: '2rem', 
                color: getCategoryColor(quote.category),
                lineHeight: 1,
                opacity: 0.5
              }}>"</span>
              <p style={{ 
                color: '#fff', 
                fontSize: '1.05rem', 
                lineHeight: 1.6,
                fontStyle: 'italic',
                margin: '0 0 10px 10px'
              }}>
                {quote.quote}
              </p>
              <span style={{ 
                fontSize: '2rem', 
                color: getCategoryColor(quote.category),
                lineHeight: 1,
                opacity: 0.5,
                float: 'right'
              }}>"</span>
            </div>

            {/* Context */}
            {quote.context && (
              <p style={{ 
                color: '#a1a1aa', 
                fontSize: '0.85rem',
                marginBottom: 15,
                paddingLeft: 10,
                borderLeft: `3px solid ${getCategoryColor(quote.category)}50`
              }}>
                {quote.context}
              </p>
            )}

            {/* Share Button */}
            <button
              onClick={() => handleShare(quote)}
              style={{
                background: `${getCategoryColor(quote.category)}20`,
                border: `1px solid ${getCategoryColor(quote.category)}50`,
                color: getCategoryColor(quote.category),
                padding: '8px 16px',
                borderRadius: 20,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                width: '100%',
                justifyContent: 'center',
                transition: 'background 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = `${getCategoryColor(quote.category)}30`}
              onMouseLeave={(e) => e.currentTarget.style.background = `${getCategoryColor(quote.category)}20`}
              data-testid={`share-quote-${idx}`}
            >
              📤 Share Quote
            </button>
          </div>
        ))}
      </div>

      {filteredQuotes.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <p style={{ color: '#a1a1aa', fontSize: '1.1rem' }}>
            No quotes found in this category.
          </p>
        </div>
      )}

      {/* Book Promo Footer */}
      <div style={{
        marginTop: 30,
        padding: 25,
        background: 'linear-gradient(135deg, rgba(244, 114, 182, 0.2), rgba(124, 58, 237, 0.2))',
        borderRadius: 16,
        textAlign: 'center',
        border: '1px solid rgba(244, 114, 182, 0.3)'
      }}>
        <h3 style={{ color: '#f472b6', marginBottom: 10 }}>📖 Want More?</h3>
        <p style={{ color: '#e5e7eb', marginBottom: 15 }}>
          These quotes are just the beginning! "Letters to Evelyn" is a wild ride of humor, 
          cosmic adventures, and genuine heart.
        </p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
          <a 
            href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary"
          >
            🛒 Buy on Amazon - $2.99
          </a>
          <a 
            href="https://readersfavorite.com/book-review/letters-to-evelyn"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
          >
            ⭐ Read 19 Five-Star Reviews
          </a>
        </div>
      </div>

      {/* Share Modal */}
      {shareModal && (
        <div 
          className="modal-overlay"
          onClick={() => setShareModal(null)}
          style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
        >
          <div 
            className="modal"
            onClick={e => e.stopPropagation()}
            style={{
              background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
              borderRadius: 20,
              padding: 30,
              maxWidth: 450,
              width: '90%',
              border: '2px solid rgba(244, 114, 182, 0.5)'
            }}
          >
            <h3 style={{ color: '#f472b6', marginBottom: 15 }}>📤 Share This Quote</h3>
            
            <div style={{
              background: 'rgba(30, 20, 50, 0.5)',
              padding: 15,
              borderRadius: 12,
              marginBottom: 20
            }}>
              <p style={{ color: '#fff', fontStyle: 'italic', marginBottom: 10 }}>
                "{shareModal.quote}"
              </p>
              <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                - Letters to Evelyn by John Selman
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                className="btn"
                onClick={() => shareToTwitter(shareModal)}
                style={{ 
                  background: '#1DA1F2', 
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8
                }}
              >
                🐦 Share on Twitter
              </button>
              <button
                className="btn"
                onClick={() => shareToFacebook(shareModal)}
                style={{ 
                  background: '#4267B2', 
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8
                }}
              >
                📘 Share on Facebook
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => copyToClipboard(shareModal)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8
                }}
              >
                📋 Copy to Clipboard
              </button>
              <button
                className="btn"
                onClick={() => setShareModal(null)}
                style={{ 
                  background: 'transparent',
                  border: '1px solid rgba(255,255,255,0.2)',
                  color: '#a1a1aa'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuoteGalleryPage;
