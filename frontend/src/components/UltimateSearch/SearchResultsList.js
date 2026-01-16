import React, { useState } from 'react';
import { HashtagDisplay } from '../shared';
import { extractHashtags } from '../../utils/hashtags';
import SearchResultComments from '../Comments/SearchResultComments';

/**
 * SearchResultsList - Display grid of search results with reactions
 */
const SearchResultsList = ({
  searchResults,
  onDeleteResult,
  onAddReaction,
  showToast
}) => {
  const [commentsResultId, setCommentsResultId] = useState(null);
  
  return (
    <div className="card">
      <h3 style={{ marginBottom: 15, color: '#f472b6' }}>
        Search Results ({searchResults.length})
      </h3>
      <div className="results-grid">
        {searchResults.length === 0 ? (
          <p style={{ color: '#a1a1aa' }}>
            No results yet. Use Search &amp; Collate to find and categorize web content!
          </p>
        ) : (
          searchResults.map(result => (
            <ResultCard
              key={result.id}
              result={result}
              onDelete={() => onDeleteResult(result.id)}
              onReaction={(type) => onAddReaction(result.id, type)}
              onOpenComments={() => setCommentsResultId(result.id)}
            />
          ))
        )}
      </div>
      
      {/* Comments Panel */}
      {commentsResultId && (
        <SearchResultComments
          resultId={commentsResultId}
          showToast={showToast}
          onClose={() => setCommentsResultId(null)}
        />
      )}
    </div>
  );
};

/**
 * ResultCard - Individual search result card
 */
const ResultCard = ({ result, onDelete, onReaction, onOpenComments }) => {
  // Determine content quality badge based on score
  const qualityScore = result.content_quality_score || 50;
  const getQualityBadge = () => {
    if (qualityScore >= 80) return { label: '📚 Premium Content', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' };
    if (qualityScore >= 65) return { label: '✨ High Quality', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)' };
    if (qualityScore >= 50) return { label: '📄 Good', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' };
    return null; // Don't show badge for lower quality
  };
  const badge = getQualityBadge();

  return (
    <div className="result-card" style={{ position: 'relative' }}>
      {/* Content Quality Badge */}
      {badge && (
        <div
          style={{
            position: 'absolute',
            top: 8,
            left: 8,
            background: badge.bg,
            border: `1px solid ${badge.color}40`,
            borderRadius: 12,
            padding: '3px 10px',
            fontSize: '0.7rem',
            fontWeight: 600,
            color: badge.color,
            zIndex: 1
          }}
          title={`Quality Score: ${qualityScore}/100`}
          data-testid={`quality-badge-${result.id}`}
        >
          {badge.label}
        </div>
      )}
      {/* Delete button */}
      <button
        onClick={onDelete}
        style={{
          position: 'absolute',
          top: 8,
          right: 8,
          background: 'rgba(239, 68, 68, 0.2)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 6,
          padding: '4px 8px',
          color: '#f87171',
          fontSize: '0.7rem',
          cursor: 'pointer',
          opacity: 0.7,
          transition: 'opacity 0.2s'
        }}
        onMouseEnter={(e) => e.target.style.opacity = 1}
        onMouseLeave={(e) => e.target.style.opacity = 0.7}
        title="Delete this result"
        data-testid={`delete-result-${result.id}`}
      >
        ✕
      </button>
      <h3 style={{ marginTop: badge ? 28 : 0 }}>
        <a href={result.url} target="_blank" rel="noopener noreferrer">
          {result.title}
        </a>
      </h3>
      <p>{result.snippet}</p>
      <div className="result-card-meta">
        <span className="result-tag">{result.article_type}</span>
        <span className="result-tag">{result.root_domain}</span>
        {result.categories?.map((cat, i) => (
          <span key={i} className="result-tag" style={{ background: 'rgba(236, 72, 153, 0.2)', color: '#f472b6' }}>
            {cat}
          </span>
        ))}
      </div>
      {/* Hashtags */}
      <HashtagDisplay hashtags={extractHashtags(result.title, result.snippet, result.article_type)} />
      <div className="reactions-bar" style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 5 }}>
        {['Like', 'Love', 'Funny', 'Sad', 'Best'].map(reaction => (
          <button
            key={reaction}
            className="reaction-btn"
            onClick={() => onReaction(reaction)}
          >
            {reaction === 'Like' && '👍'}
            {reaction === 'Love' && '❤️'}
            {reaction === 'Funny' && '😂'}
            {reaction === 'Sad' && '😢'}
            {reaction === 'Best' && '⭐'}
            {reaction}
          </button>
        ))}
        {/* Comments Button */}
        <button
          onClick={onOpenComments}
          className="reaction-btn"
          style={{
            background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(236, 72, 153, 0.2))',
            border: '1px solid rgba(124, 58, 237, 0.3)',
            color: '#a78bfa',
            marginLeft: 'auto'
          }}
          data-testid={`open-comments-${result.id}`}
          title="View and add comments"
        >
          💬 Comments
        </button>
      </div>
    </div>
  );
};

export { SearchResultsList, ResultCard };
export default SearchResultsList;
