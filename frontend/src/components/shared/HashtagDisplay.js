import React from 'react';

// Hashtag component for displaying clickable hashtags
const HashtagDisplay = ({ hashtags, small = false }) => (
  <div style={{ 
    display: 'flex', 
    flexWrap: 'wrap', 
    gap: small ? 4 : 6, 
    marginTop: small ? 6 : 10 
  }}>
    {hashtags.map((tag, idx) => (
      <span
        key={idx}
        style={{
          background: 'rgba(124, 58, 237, 0.2)',
          color: '#a78bfa',
          padding: small ? '2px 6px' : '3px 8px',
          borderRadius: 12,
          fontSize: small ? '0.65rem' : '0.7rem',
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'all 0.2s',
          border: '1px solid rgba(124, 58, 237, 0.3)'
        }}
        onMouseEnter={(e) => {
          e.target.style.background = 'rgba(124, 58, 237, 0.4)';
          e.target.style.color = '#c4b5fd';
        }}
        onMouseLeave={(e) => {
          e.target.style.background = 'rgba(124, 58, 237, 0.2)';
          e.target.style.color = '#a78bfa';
        }}
      >
        {tag}
      </span>
    ))}
  </div>
);

export default HashtagDisplay;
