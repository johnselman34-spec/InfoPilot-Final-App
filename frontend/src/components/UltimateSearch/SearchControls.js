import React from 'react';
import { Icons } from '../shared';

/**
 * SearchControls - Search input box with collate button and aggregation options
 */
const SearchControls = ({
  searchQuery,
  setSearchQuery,
  onSearch,
  onCollate,
  loading,
  collateLoading,
  selectedCategoriesCount,
  aggregation,
  setAggregation,
  showMap,
  setShowMap,
  mapResultsCount,
  showDebugger,
  setShowDebugger,
  showTemplates,
  setShowTemplates,
  filterInfo
}) => {
  return (
    <>
      {/* Search Box */}
      <div className="search-box">
        <input
          className="input-field"
          placeholder="Enter search query and click 'Search & Collate'"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && onSearch()}
          data-testid="search-input"
        />
        <button 
          className="btn btn-primary" 
          onClick={onSearch} 
          disabled={loading} 
          data-testid="search-btn"
        >
          {loading ? 'Searching...' : 'Quick Search'}
        </button>
        <button 
          className="btn btn-primary" 
          onClick={onCollate} 
          disabled={collateLoading || selectedCategoriesCount === 0}
          style={{ 
            background: selectedCategoriesCount > 0 
              ? 'linear-gradient(135deg, #10b981, #059669)' 
              : 'rgba(107, 114, 128, 0.5)'
          }}
          data-testid="collate-btn"
        >
          {collateLoading ? '⏳ Collating...' : `🔍 Collate (${selectedCategoriesCount} selected)`}
        </button>
      </div>

      {/* Aggregation Options */}
      <div style={{ display: 'flex', gap: 20, marginBottom: 20, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ color: '#a1a1aa' }}>Category Logic:</span>
        {[
          { value: 'and_or', label: 'AND/OR', desc: 'Match any category' },
          { value: 'and', label: 'AND', desc: 'Match ALL categories' },
          { value: 'or', label: 'OR', desc: 'Match any category' }
        ].map(agg => (
          <label 
            key={agg.value} 
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 5, 
              cursor: 'pointer',
              padding: '6px 12px',
              borderRadius: 8,
              background: aggregation === agg.value ? 'rgba(124, 58, 237, 0.3)' : 'transparent',
              border: aggregation === agg.value ? '1px solid rgba(124, 58, 237, 0.5)' : '1px solid transparent',
              transition: 'all 0.2s'
            }}
            title={agg.desc}
            data-testid={`aggregation-${agg.value}`}
          >
            <input
              type="radio"
              name="aggregation"
              checked={aggregation === agg.value}
              onChange={() => setAggregation(agg.value)}
              style={{ accentColor: '#7c3aed' }}
            />
            <span style={{ color: aggregation === agg.value ? '#a78bfa' : '#9ca3af' }}>{agg.label}</span>
          </label>
        ))}
        
        {/* Show active filter status */}
        {selectedCategoriesCount > 0 && (
          <span style={{ 
            padding: '4px 10px', 
            background: 'rgba(16, 185, 129, 0.2)', 
            color: '#10b981',
            borderRadius: 6,
            fontSize: '0.8rem'
          }}>
            🔍 Filtering by {selectedCategoriesCount} categor{selectedCategoriesCount > 1 ? 'ies' : 'y'} ({aggregation.toUpperCase().replace('_', '/')})
          </span>
        )}
        
        <button
          className={`btn ${showMap ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setShowMap(!showMap)}
          style={{ padding: '8px 16px', fontSize: '0.85rem' }}
          data-testid="toggle-map-btn"
        >
          🗺️ {showMap ? 'Hide' : 'Show'} Map ({mapResultsCount} locations)
        </button>
        <button
          className={`btn ${showDebugger ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setShowDebugger(!showDebugger)}
          style={{ padding: '8px 16px', fontSize: '0.85rem' }}
          data-testid="toggle-debugger-btn"
        >
          🔧 {showDebugger ? 'Hide' : 'Show'} Protocol Debugger
        </button>
        <button
          className={`btn ${showTemplates ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setShowTemplates(!showTemplates)}
          style={{ padding: '8px 16px', fontSize: '0.85rem' }}
          data-testid="toggle-templates-btn"
        >
          📁 {showTemplates ? 'Hide' : 'Show'} Templates
        </button>
      </div>
    </>
  );
};

export default SearchControls;
