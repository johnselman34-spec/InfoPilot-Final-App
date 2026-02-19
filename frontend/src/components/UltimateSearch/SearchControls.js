import React, { useState, useEffect } from 'react';
import { Icons } from '../shared';
import { API } from '../../utils/api';

/**
 * SearchControls - Search input box with categorize button, AI search, database search, and aggregation options
 * Includes Google (SerpAPI), Bing, Brave, DuckDuckGo, and Basic search engines!
 * New: Certification filter checkboxes for PearsonVUE, Government, Advanced Degree
 */
const SearchControls = ({
  searchQuery,
  setSearchQuery,
  onSearch,
  onCollate,
  onAutoCategorize,
  onAISearch,
  onDatabaseSearch,
  loading,
  collateLoading,
  autoCatLoading,
  aiSearchLoading,
  dbSearchLoading,
  selectedCategoriesCount,
  aggregation,
  setAggregation,
  aiSearchMode,
  setAiSearchMode,
  dbSearchMode,
  setDbSearchMode,
  showMap,
  setShowMap,
  mapResultsCount,
  showDebugger,
  setShowDebugger,
  showTemplates,
  setShowTemplates,
  filterInfo,
  certificationFilters,
  setCertificationFilters
}) => {
  const [searchEngines, setSearchEngines] = useState(null);
  
  // Local state for certification filters if not provided via props
  const [localCertFilters, setLocalCertFilters] = useState({
    pearsonvue: true,
    government: true,
    advancedDegree: true
  });
  
  const certFilters = certificationFilters || localCertFilters;
  const setCertFilters = setCertificationFilters || setLocalCertFilters;
  
  const toggleCertFilter = (filterKey) => {
    setCertFilters(prev => ({
      ...prev,
      [filterKey]: !prev[filterKey]
    }));
  };
  
  // Fetch available search engines on mount
  useEffect(() => {
    const fetchEngines = async () => {
      try {
        const res = await fetch(`${API}/search-engines`);
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
          placeholder="Enter search query (searches Google, Bing, DuckDuckGo, Brave)..."
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
      
      {/* Search Action Buttons Row 1: Search & Categorize and AI Intelligent Search */}
      <div style={{ 
        display: 'flex', 
        gap: 10, 
        marginBottom: 10, 
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
          {autoCatLoading ? '⏳ Categorizing...' : '🎯 Search & Categorize'}
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
            title="AI-powered search across Google, Bing, DuckDuckGo, Brave with intelligent keyword expansion"
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
      </div>
      
      {/* Search Action Buttons Row 2: Database Text Search */}
      <div style={{ 
        display: 'flex', 
        gap: 10, 
        marginBottom: 15, 
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <button
            className="btn"
            onClick={onDatabaseSearch}
            disabled={dbSearchLoading || !searchQuery.trim()}
            style={{
              background: 'linear-gradient(135deg, #06b6d4, #0891b2)',
              color: '#fff',
              padding: '10px 20px',
              fontWeight: 600,
              opacity: (!searchQuery.trim() || dbSearchLoading) ? 0.5 : 1
            }}
            data-testid="database-search-btn"
            title="Search within your already collated database results"
          >
            {dbSearchLoading ? '📚 Searching Database...' : '📚 Database Text Search'}
          </button>
          
          {/* Database Search Mode Selector */}
          <select
            value={dbSearchMode || 'smart'}
            onChange={(e) => setDbSearchMode && setDbSearchMode(e.target.value)}
            style={{
              background: 'rgba(6, 182, 212, 0.2)',
              border: '1px solid rgba(6, 182, 212, 0.4)',
              color: '#22d3ee',
              padding: '8px 12px',
              borderRadius: 8,
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
            data-testid="db-search-mode"
          >
            <option value="smart">🧠 Smart Match</option>
            <option value="exact">🎯 Exact Phrase</option>
            <option value="fuzzy">🔍 Fuzzy Match</option>
          </select>
        </div>
        
        <span style={{ 
          color: '#a1a1aa', 
          fontSize: '0.75rem', 
          maxWidth: 450
        }}>
          💡 <strong>AI Search:</strong> Searches Google, Bing, DuckDuckGo, Brave with GPT keyword expansion. 
          <strong> Database Search:</strong> Finds content in your already collated results.
        </span>
      </div>

      {/* Certification Filters - NEW */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 15,
        marginBottom: 15,
        padding: '12px 16px',
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(59, 130, 246, 0.15))',
        borderRadius: 12,
        border: '1px solid rgba(139, 92, 246, 0.3)',
        flexWrap: 'wrap'
      }}>
        <span style={{ color: '#a78bfa', fontWeight: 600, fontSize: '0.9rem' }}>
          🎓 Certification Filters:
        </span>
        
        {[
          { key: 'pearsonvue', label: 'PearsonVUE Certification', icon: '📜', color: '#8b5cf6' },
          { key: 'government', label: 'Government Certification', icon: '🏛️', color: '#ef4444' },
          { key: 'advancedDegree', label: 'Advanced Degree Information', icon: '🎓', color: '#3b82f6' }
        ].map(filter => (
          <label
            key={filter.key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 14px',
              borderRadius: 20,
              cursor: 'pointer',
              background: certFilters[filter.key] 
                ? `${filter.color}25`
                : 'rgba(30, 20, 50, 0.5)',
              border: certFilters[filter.key]
                ? `2px solid ${filter.color}`
                : '1px solid rgba(255,255,255,0.1)',
              transition: 'all 0.2s',
              userSelect: 'none'
            }}
            data-testid={`cert-filter-${filter.key}`}
          >
            <input
              type="checkbox"
              checked={certFilters[filter.key]}
              onChange={() => toggleCertFilter(filter.key)}
              style={{ 
                accentColor: filter.color,
                width: 16,
                height: 16,
                cursor: 'pointer'
              }}
            />
            <span style={{ fontSize: '1rem' }}>{filter.icon}</span>
            <span style={{ 
              color: certFilters[filter.key] ? '#fff' : '#a1a1aa',
              fontSize: '0.85rem',
              fontWeight: certFilters[filter.key] ? 600 : 400
            }}>
              {filter.label}
            </span>
          </label>
        ))}
        
        <button
          onClick={() => setCertFilters({ pearsonvue: true, government: true, advancedDegree: true })}
          style={{
            background: 'rgba(16, 185, 129, 0.2)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            color: '#10b981',
            padding: '6px 12px',
            borderRadius: 8,
            fontSize: '0.75rem',
            cursor: 'pointer',
            marginLeft: 'auto'
          }}
          data-testid="select-all-certs"
        >
          ✓ Select All
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
