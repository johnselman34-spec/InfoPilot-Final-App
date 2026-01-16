import React, { useState, useEffect } from 'react';
import { Icons } from '../shared';
import { API } from '../../utils/api';

/**
 * SearchControls - Search input box with collate button, auto-categorize, AI search, and aggregation options
 * Now includes Brave and Yandex search engines!
 */
const SearchControls = ({
  searchQuery,
  setSearchQuery,
  onSearch,
  onCollate,
  onAutoCategorize,
  onAISearch,
  loading,
  collateLoading,
  autoCatLoading,
  aiSearchLoading,
  selectedCategoriesCount,
  aggregation,
  setAggregation,
  aiSearchMode,
  setAiSearchMode,
  showMap,
  setShowMap,
  mapResultsCount,
  showDebugger,
  setShowDebugger,
  showTemplates,
  setShowTemplates,
  filterInfo
}) => {
  const [searchEngines, setSearchEngines] = useState(null);
  
  // Fetch available search engines on mount
  useEffect(() => {
    const fetchEngines = async () => {
      try {
        const res = await fetch(`${API}/api/search-engines`);
        if (res.ok) {
          const data = await res.json();
          setSearchEngines(data);
        }
      } catch (e) {
        console.error('Failed to fetch search engines:', e);
      }
    };
    fetchEngines();
  }, []);

  return (
    <>
      {/* Search Engines Status */}
      {searchEngines && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 10,
          flexWrap: 'wrap',
          padding: '8px 12px',
          background: 'rgba(16, 185, 129, 0.1)',
          borderRadius: 8,
          border: '1px solid rgba(16, 185, 129, 0.2)'
        }}>
          <span style={{ color: '#10b981', fontSize: '0.8rem', fontWeight: 600 }}>
            🔍 Search Engines ({searchEngines.total_available} active):
          </span>
          {Object.entries(searchEngines.engines).map(([key, engine]) => (
            <span
              key={key}
              style={{
                fontSize: '0.7rem',
                padding: '3px 8px',
                borderRadius: 4,
                background: engine.available ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                color: engine.available ? '#10b981' : '#ef4444',
                border: `1px solid ${engine.available ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
              }}
              title={engine.description}
            >
              {engine.available ? '✓' : '✗'} {engine.name}
            </span>
          ))}
        </div>
      )}

      {/* Search Box */}
      <div className="search-box">
        <input
          className="input-field"
          placeholder="Enter search query (searches Google, DuckDuckGo, Brave, Yandex)..."
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
          {collateLoading ? '⏳ Collating...' : `🔍 Collate (${selectedCategoriesCount})`}
        </button>
      </div>
      
      {/* NEW: Auto-Categorize and AI Search Buttons */}
      <div style={{ 
        display: 'flex', 
        gap: 10, 
        marginBottom: 15, 
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        <button
          className="btn"
          onClick={onAutoCategorize}
          disabled={autoCatLoading || !searchQuery.trim()}
          style={{
            background: 'linear-gradient(135deg, #f59e0b, #d97706)',
            color: '#fff',
            padding: '10px 20px',
            fontWeight: 600,
            opacity: (!searchQuery.trim() || autoCatLoading) ? 0.5 : 1
          }}
          data-testid="auto-categorize-btn"
          title="One-click: Search and automatically match results against ALL your categories"
        >
          {autoCatLoading ? '⏳ Auto-Categorizing...' : '🎯 Auto-Categorize All'}
        </button>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <button
            className="btn"
            onClick={onAISearch}
            disabled={aiSearchLoading || !searchQuery.trim()}
            style={{
              background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
              color: '#fff',
              padding: '10px 20px',
              fontWeight: 600,
              opacity: (!searchQuery.trim() || aiSearchLoading) ? 0.5 : 1
            }}
            data-testid="ai-search-btn"
            title="AI-powered search across Google, DuckDuckGo, Bing with intelligent keyword expansion"
          >
            {aiSearchLoading ? '🤖 AI Searching...' : '🤖 AI Intelligent Search'}
          </button>
          
          {/* AI Search Mode Selector */}
          <select
            value={aiSearchMode || 'comprehensive'}
            onChange={(e) => setAiSearchMode && setAiSearchMode(e.target.value)}
            style={{
              background: 'rgba(124, 58, 237, 0.2)',
              border: '1px solid rgba(124, 58, 237, 0.4)',
              color: '#a78bfa',
              padding: '8px 12px',
              borderRadius: 8,
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
            data-testid="ai-search-mode"
          >
            <option value="comprehensive">📊 Comprehensive</option>
            <option value="news">📰 News Focus</option>
            <option value="research">🔬 Research Focus</option>
          </select>
        </div>
        
        <span style={{ 
          color: '#a1a1aa', 
          fontSize: '0.75rem', 
          marginLeft: 10,
          maxWidth: 250
        }}>
          💡 Auto-Categorize matches ALL categories at once. AI Search uses GPT to expand keywords.
        </span>
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
