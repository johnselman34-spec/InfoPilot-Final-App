import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API, triggerMapRefresh } from '../utils/api';
import { Icons, ProtocolDebugger, ProtocolTemplates, CopyButton, AISuggestions } from '../components/shared';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Import refactored components
import {
  SearchControls,
  SearchResultsList,
  BatchManager,
  CreateCategoryModal,
  EditCategoryModal
} from '../components/UltimateSearch';

// Fix for leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom colored markers for categories
const createCategoryIcon = (color) => L.divIcon({
  className: 'custom-marker',
  html: `<div style="
    background: ${color};
    width: 24px;
    height: 24px;
    border-radius: 50% 50% 50% 0;
    transform: rotate(-45deg);
    border: 2px solid white;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
  "></div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 24],
  popupAnchor: [0, -24],
});

const UltimateSearchPage = ({ showToast }) => {
  const { token, user } = useAuth();
  
  // Core state
  const [categories, setCategories] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregation, setAggregation] = useState('and_or');
  const [loading, setLoading] = useState(false);
  const [collateLoading, setCollateLoading] = useState(false);
  
  // Modal state
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [newCategory, setNewCategory] = useState({ name: '', protocol: '', parent_id: null, is_public: false });
  const [editingCategory, setEditingCategory] = useState(null);
  const [editProtocol, setEditProtocol] = useState('');
  const [editCategoryName, setEditCategoryName] = useState('');
  const [editIsPublic, setEditIsPublic] = useState(false);
  const [editPrice, setEditPrice] = useState('');
  
  // UI toggles
  const [batches, setBatches] = useState([]);
  const [showBatchManager, setShowBatchManager] = useState(false);
  const [lastBatchId, setLastBatchId] = useState(null);
  const [showDebugger, setShowDebugger] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showMap, setShowMap] = useState(true);
  
  // Map state
  const [mapCenter, setMapCenter] = useState([39.8283, -98.5795]);
  const [mapZoom] = useState(4);
  const [filterInfo, setFilterInfo] = useState({ filter_applied: false, aggregation_mode: 'and_or' });
  
  // Document Type Filtering state
  const [selectedDocTypes, setSelectedDocTypes] = useState([]);
  const [showFilteredResults, setShowFilteredResults] = useState(false);
  
  // Available document types
  const documentTypes = useMemo(() => [
    { id: 'PhD Informative', name: 'PhD Informative', color: '#8b5cf6' },
    { id: 'Personal Report (Organic)', name: 'Personal Report (Organic)', color: '#10b981' },
    { id: 'Personal Report (Collected)', name: 'Personal Report (Collected)', color: '#14b8a6' },
    { id: 'News Article', name: 'News Article', color: '#3b82f6' },
    { id: 'Academic Paper', name: 'Academic Paper', color: '#6366f1' },
    { id: 'Government', name: 'Government', color: '#ef4444' },
    { id: 'Wiki', name: 'Wiki', color: '#f59e0b' },
    { id: 'Blog Post', name: 'Blog Post', color: '#ec4899' },
    { id: 'Forum', name: 'Forum', color: '#06b6d4' },
    { id: 'Video', name: 'Video', color: '#f472b6' },
    { id: 'PDF Document', name: 'PDF Document', color: '#dc2626' },
    { id: 'MS Word Document', name: 'MS Word Document', color: '#2563eb' },
    { id: 'Webpage', name: 'Webpage', color: '#6b7280' }
  ], []);

  // Category colors for map markers
  const categoryColors = useMemo(() => [
    '#f472b6', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', 
    '#ef4444', '#06b6d4', '#ec4899', '#84cc16', '#a855f7'
  ], []);

  // Get color for a category
  const getCategoryColor = useCallback((categoryId) => {
    const index = categories.findIndex(c => c.id === categoryId);
    return categoryColors[index % categoryColors.length];
  }, [categories, categoryColors]);

  // Results with location data for map
  const mapResults = useMemo(() => {
    return searchResults.filter(r => r.latitude && r.longitude);
  }, [searchResults]);
  
  // Filtered results based on category and document type selections
  const filteredResults = useMemo(() => {
    let results = searchResults;
    
    // Filter by selected categories
    if (selectedCategories.length > 0) {
      const selectedCatNames = categories
        .filter(c => selectedCategories.includes(c.id))
        .map(c => c.name);
      
      if (aggregation === 'and') {
        // AND: Must have ALL selected categories
        results = results.filter(r => 
          selectedCatNames.every(catName => r.categories?.includes(catName))
        );
      } else {
        // OR / AND_OR: Must have ANY selected category
        results = results.filter(r => 
          selectedCatNames.some(catName => r.categories?.includes(catName))
        );
      }
    }
    
    // Filter by selected document types
    if (selectedDocTypes.length > 0) {
      results = results.filter(r => selectedDocTypes.includes(r.article_type));
    }
    
    return results;
  }, [searchResults, selectedCategories, selectedDocTypes, categories, aggregation]);
  
  // Toggle document type selection
  const toggleDocType = (docType) => {
    setSelectedDocTypes(prev => 
      prev.includes(docType)
        ? prev.filter(d => d !== docType)
        : [...prev, docType]
    );
    // Show filtered results when filters are active
    setShowFilteredResults(true);
  };

  // Handle applying a template
  const handleApplyTemplate = (protocol, templateName) => {
    setNewCategory({ ...newCategory, protocol: protocol, name: templateName });
    setShowCategoryModal(true);
  };

  // === API CALLS ===
  
  const fetchBatches = useCallback(async () => {
    try {
      const res = await fetch(`${API}/ultimate-search/batches`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setBatches(data.batches || []);
      }
    } catch (e) {
      console.error('Failed to fetch batches:', e);
    }
  }, [token]);

  const deleteBatch = async (batchId) => {
    if (!window.confirm('Delete all results from this search session? This cannot be undone.')) return;
    try {
      const res = await fetch(`${API}/ultimate-search/batch/${batchId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`Deleted ${data.deleted_count} results`, 'success');
        fetchBatches();
        fetchSearchResults();
        // Trigger map refresh after data changes
        triggerMapRefresh();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to delete batch', 'error');
      }
    } catch (e) {
      showToast('Failed to delete batch', 'error');
    }
  };

  const deleteResult = async (resultId) => {
    try {
      const res = await fetch(`${API}/ultimate-search/result/${resultId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Result deleted', 'success');
        fetchSearchResults();
        // Trigger map refresh after data changes
        triggerMapRefresh();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to delete', 'error');
      }
    } catch (e) {
      showToast('Failed to delete result', 'error');
    }
  };

  const fetchCategories = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/categories`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data);
      }
    } catch (e) {
      console.error('Failed to fetch categories:', e);
    }
  }, [token]);

  const fetchSearchResults = useCallback(async () => {
    try {
      const params = new URLSearchParams({ aggregation, limit: 200 });
      if (selectedCategories.length > 0) {
        params.append('category_ids', selectedCategories.join(','));
      }
      
      const res = await fetch(`${API}/ultimate-search?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
        setFilterInfo({
          filter_applied: data.filter_applied || false,
          aggregation_mode: data.aggregation_mode || 'and_or',
          count: data.count || 0
        });
        
        // Update map center if there are results with locations
        const withLocation = (data.results || []).filter(r => r.latitude && r.longitude);
        if (withLocation.length > 0) {
          const avgLat = withLocation.reduce((sum, r) => sum + r.latitude, 0) / withLocation.length;
          const avgLng = withLocation.reduce((sum, r) => sum + r.longitude, 0) / withLocation.length;
          setMapCenter([avgLat, avgLng]);
        }
      }
    } catch (e) {
      console.error('Failed to fetch results:', e);
    }
  }, [token, selectedCategories, aggregation]);

  useEffect(() => {
    fetchCategories();
    fetchSearchResults();
    fetchBatches();
  }, [fetchCategories, fetchSearchResults, fetchBatches]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    const startTime = Date.now();
    try {
      const searchRes = await fetch(`${API}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query: searchQuery })
      });
      
      if (searchRes.ok) {
        const searchData = await searchRes.json();
        const collateRes = await fetch(`${API}/collate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ search_results: searchData.results })
        });
        
        if (collateRes.ok) {
          const collateData = await collateRes.json();
          const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
          setLastBatchId(collateData.batch_id);
          showToast(`Collated ${collateData.collated_count} of ${searchData.total} results in ${totalTime}s!`, 'success');
          fetchSearchResults();
          fetchBatches();
          // Trigger map refresh after data changes
          triggerMapRefresh();
        }
      }
    } catch (e) {
      showToast('Search failed', 'error');
    }
    setLoading(false);
  };

  // AUTO-CATEGORIZE: One-click search that matches against ALL categories
  const [autoCatLoading, setAutoCatLoading] = useState(false);
  const autoCategorizeSearc = async () => {
    if (!searchQuery.trim()) {
      showToast('Please enter a search query', 'error');
      return;
    }
    
    setAutoCatLoading(true);
    const startTime = Date.now();
    
    try {
      const res = await fetch(`${API}/auto-categorize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ query: searchQuery })
      });
      
      if (res.ok) {
        const data = await res.json();
        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
        setLastBatchId(data.batch_id);
        
        // Auto-select categories that matched
        if (data.category_summary && data.category_summary.length > 0) {
          const matchedCategoryIds = data.category_summary.map(c => c.id);
          setSelectedCategories(matchedCategoryIds);
        }
        
        showToast(`🎯 ${data.message} (${totalTime}s)`, 'success');
        fetchSearchResults();
        fetchBatches();
        triggerMapRefresh();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Auto-categorization failed', 'error');
      }
    } catch (e) {
      showToast('Auto-categorization failed', 'error');
    }
    
    setAutoCatLoading(false);
  };

  // AI INTELLIGENT SEARCH
  const [aiSearchLoading, setAiSearchLoading] = useState(false);
  const [aiSearchMode, setAiSearchMode] = useState('comprehensive');
  
  const aiIntelligentSearch = async () => {
    if (!searchQuery.trim()) {
      showToast('Please enter a search query', 'error');
      return;
    }
    
    setAiSearchLoading(true);
    const startTime = Date.now();
    
    try {
      const res = await fetch(`${API}/ai-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ 
          query: searchQuery,
          mode: aiSearchMode,
          auto_categorize: true
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
        setLastBatchId(data.batch_id);
        
        // Show AI suggestions if available
        if (data.ai_suggestions && data.ai_suggestions.length > 0) {
          console.log('AI Expanded Queries:', data.expanded_queries);
        }
        
        showToast(`🤖 ${data.message} (${totalTime}s)`, 'success');
        fetchSearchResults();
        fetchBatches();
        triggerMapRefresh();
      } else {
        const error = await res.json();
        showToast(error.detail || 'AI Search failed', 'error');
      }
    } catch (e) {
      showToast('AI Search failed', 'error');
    }
    
    setAiSearchLoading(false);
  };

  // DATABASE TEXT SEARCH - Search within already collated results
  const [dbSearchLoading, setDbSearchLoading] = useState(false);
  const [dbSearchMode, setDbSearchMode] = useState('smart');
  
  const databaseTextSearch = async () => {
    if (!searchQuery.trim()) {
      showToast('Please enter a search query', 'error');
      return;
    }
    
    setDbSearchLoading(true);
    const startTime = Date.now();
    
    try {
      const res = await fetch(`${API}/database-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ 
          query: searchQuery,
          mode: dbSearchMode,
          category_ids: selectedCategories,
          limit: 100
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
        
        // Display results directly from database search
        if (data.results && data.results.length > 0) {
          setSearchResults(data.results);
          showToast(`📚 ${data.message} (${totalTime}s) - Found in ${data.total_in_database} total records`, 'success');
        } else {
          showToast(`📚 No matches found in database. Try running a search first to collate results!`, 'info');
        }
      } else {
        const error = await res.json();
        showToast(error.detail || 'Database search failed', 'error');
      }
    } catch (e) {
      showToast('Database search failed', 'error');
    }
    
    setDbSearchLoading(false);
  };

  const collateWithCategories = async () => {
    if (selectedCategories.length === 0) {
      showToast('Please select at least one category to collate', 'error');
      return;
    }
    
    setCollateLoading(true);
    const startTime = Date.now();
    let totalCollated = 0;
    
    try {
      for (const categoryId of selectedCategories) {
        const res = await fetch(`${API}/collate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ category_id: categoryId, aggregation: aggregation })
        });
        
        if (res.ok) {
          const data = await res.json();
          totalCollated += data.total || 0;
          setLastBatchId(data.batch_id);
        }
      }
      
      const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
      showToast(`✅ Collated ${totalCollated} results across ${selectedCategories.length} categories in ${totalTime}s!`, 'success');
      fetchSearchResults();
      fetchBatches();
      // Trigger map refresh after data changes
      triggerMapRefresh();
    } catch (e) {
      showToast('Failed to collate results', 'error');
    }
    
    setCollateLoading(false);
  };

  const createCategory = async () => {
    if (!newCategory.name || !newCategory.protocol) {
      showToast('Name and protocol are required', 'error');
      return;
    }
    
    try {
      const res = await fetch(`${API}/categories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          name: newCategory.name,
          protocol: newCategory.protocol,
          parent_id: newCategory.parent_id || null,
          is_public: newCategory.is_public || false
        })
      });
      
      if (res.ok) {
        showToast(`Category "${newCategory.name}" created successfully!`, 'success');
        setShowCategoryModal(false);
        setNewCategory({ name: '', protocol: '', parent_id: null, is_public: false });
        fetchCategories();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to create category', 'error');
      }
    } catch (e) {
      showToast('Failed to create category', 'error');
    }
  };

  const saveProtocol = async () => {
    if (!editingCategory) return;
    try {
      const res = await fetch(`${API}/categories/${editingCategory.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ 
          name: editCategoryName,
          protocol: editProtocol,
          is_public: editIsPublic,
          price: editPrice ? parseFloat(editPrice) : null
        })
      });
      
      if (res.ok) {
        showToast('Category updated successfully!', 'success');
        fetchCategories();
        setEditingCategory(null);
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to update', 'error');
      }
    } catch (e) {
      showToast('Failed to update category', 'error');
    }
  };

  const deleteCategory = async (categoryId) => {
    try {
      const res = await fetch(`${API}/categories/${categoryId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast('Category deleted successfully!', 'success');
        setEditingCategory(null);
        setSelectedCategories(prev => prev.filter(id => id !== categoryId));
        fetchCategories();
        fetchSearchResults();
        triggerMapRefresh();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to delete category', 'error');
      }
    } catch (e) {
      showToast('Failed to delete category', 'error');
    }
  };

  const toggleCategorySelection = (catId) => {
    setSelectedCategories(prev => 
      prev.includes(catId) ? prev.filter(id => id !== catId) : [...prev, catId]
    );
  };

  const addReaction = async (resultId, reactionType) => {
    try {
      await fetch(`${API}/reactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ search_result_id: resultId, reaction_type: reactionType })
      });
      fetchSearchResults();
    } catch (e) {
      console.error('Failed to add reaction:', e);
    }
  };

  const handleEditCategory = (cat, e) => {
    e.stopPropagation();
    setEditingCategory(cat);
    setEditCategoryName(cat.name || '');
    setEditProtocol(cat.protocol || '');
    setEditIsPublic(cat.is_public || false);
    setEditPrice(cat.price ? cat.price.toString() : '');
  };

  // Build category tree for sidebar
  const buildCategoryTree = (cats, parentId = null, level = 0) => {
    return cats
      .filter(c => c.parent_id === parentId)
      .map(cat => (
        <div key={cat.id}>
          <div 
            className={`category-item category-item-level-${level} ${selectedCategories.includes(cat.id) ? 'selected' : ''}`}
            style={{ 
              flexDirection: 'column', 
              alignItems: 'stretch',
              borderLeft: selectedCategories.includes(cat.id) ? `3px solid ${getCategoryColor(cat.id)}` : '3px solid transparent',
              transition: 'all 0.2s'
            }}
          >
            <div 
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
              onClick={() => toggleCategorySelection(cat.id)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="checkbox"
                  checked={selectedCategories.includes(cat.id)}
                  onChange={() => {}}
                  style={{ accentColor: getCategoryColor(cat.id), width: 16, height: 16, cursor: 'pointer' }}
                  data-testid={`category-checkbox-${cat.id}`}
                />
                <span style={{ 
                  color: selectedCategories.includes(cat.id) ? '#f472b6' : '#e2e8f0',
                  fontWeight: selectedCategories.includes(cat.id) ? 600 : 400
                }}>
                  {cat.name}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
                <CopyButton text={cat.name} label="" successLabel="✓" size="sm" variant="icon" showToast={showToast} style={{ fontSize: '0.7rem' }} />
                {cat.protocol && (
                  <CopyButton text={cat.protocol} label="" successLabel="✓" size="sm" variant="icon" showToast={showToast} style={{ fontSize: '0.7rem', color: '#a78bfa' }} />
                )}
                {cat.is_public && <span style={{ fontSize: '0.65rem', color: '#10b981', padding: '2px 6px', background: 'rgba(16,185,129,0.2)', borderRadius: 4 }}>Public</span>}
                <button 
                  onClick={(e) => handleEditCategory(cat, e)}
                  style={{ background: 'transparent', border: 'none', color: '#a1a1aa', cursor: 'pointer', padding: '2px 6px', fontSize: '0.75rem' }}
                  title="Edit Protocol"
                  data-testid={`edit-category-${cat.id}`}
                >
                  ✏️
                </button>
              </div>
            </div>
            {cat.protocol && (
              <div style={{ fontSize: '0.7rem', color: '#71717a', marginTop: 4, padding: '4px 8px', background: 'rgba(124, 58, 237, 0.1)', borderRadius: 4, fontFamily: 'monospace', wordBreak: 'break-all' }}>
                {cat.protocol.length > 60 ? cat.protocol.substring(0, 60) + '...' : cat.protocol}
              </div>
            )}
          </div>
          {buildCategoryTree(cats, cat.id, level + 1)}
        </div>
      ));
  };

  return (
    <div>
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <h2>{user?.username}&apos;s Ultimate Search Page</h2>
          <button className="btn btn-primary" onClick={() => setShowCategoryModal(true)}>
            <Icons.Plus /> New Category
          </button>
        </div>

        {/* Search Controls Component */}
        <SearchControls
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onSearch={handleSearch}
          onCollate={collateWithCategories}
          onAutoCategorize={autoCategorizeSearc}
          onAISearch={aiIntelligentSearch}
          onDatabaseSearch={databaseTextSearch}
          loading={loading}
          collateLoading={collateLoading}
          autoCatLoading={autoCatLoading}
          aiSearchLoading={aiSearchLoading}
          dbSearchLoading={dbSearchLoading}
          selectedCategoriesCount={selectedCategories.length}
          aggregation={aggregation}
          setAggregation={setAggregation}
          aiSearchMode={aiSearchMode}
          setAiSearchMode={setAiSearchMode}
          dbSearchMode={dbSearchMode}
          setDbSearchMode={setDbSearchMode}
          showMap={showMap}
          setShowMap={setShowMap}
          mapResultsCount={mapResults.length}
          showDebugger={showDebugger}
          setShowDebugger={setShowDebugger}
          showTemplates={showTemplates}
          setShowTemplates={setShowTemplates}
          filterInfo={filterInfo}
        />

        {/* Protocol Debugger */}
        {showDebugger && <ProtocolDebugger showToast={showToast} />}
        
        {/* Protocol Templates */}
        {showTemplates && <ProtocolTemplates showToast={showToast} onApplyTemplate={handleApplyTemplate} />}
      </div>

      {/* AI-Powered Protocol Suggestions */}
      <AISuggestions 
        showToast={showToast} 
        onViewProtocol={(protocolId) => {
          window.location.hash = `#marketplace?protocol=${protocolId}`;
          showToast('Opening protocol in marketplace...', 'success');
        }}
      />

      {/* Interactive Map */}
      {showMap && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
            <h3 style={{ color: '#f472b6', margin: 0 }}>
              🗺️ Results Map 
              <span style={{ fontSize: '0.85rem', color: '#a1a1aa', fontWeight: 'normal', marginLeft: 10 }}>
                {mapResults.length} location{mapResults.length !== 1 ? 's' : ''} plotted
                {filterInfo.filter_applied && ` (${filterInfo.aggregation_mode.toUpperCase().replace('_', '/')} filter active)`}
              </span>
            </h3>
            {selectedCategories.length > 0 && (
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {selectedCategories.slice(0, 5).map((catId) => {
                  const cat = categories.find(c => c.id === catId);
                  return cat ? (
                    <span key={catId} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.75rem', color: '#a1a1aa' }}>
                      <span style={{ width: 10, height: 10, borderRadius: '50%', background: getCategoryColor(catId) }}></span>
                      {cat.name}
                    </span>
                  ) : null;
                })}
                {selectedCategories.length > 5 && <span style={{ fontSize: '0.75rem', color: '#71717a' }}>+{selectedCategories.length - 5} more</span>}
              </div>
            )}
          </div>
          
          <div style={{ height: 400, borderRadius: 12, overflow: 'hidden', border: '1px solid rgba(124, 58, 237, 0.3)' }}>
            <MapContainer center={mapCenter} zoom={mapZoom} style={{ height: '100%', width: '100%' }} key={`map-${mapCenter[0]}-${mapCenter[1]}`}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; OpenStreetMap' />
              {mapResults.map((result, idx) => (
                <Marker 
                  key={result.id || idx}
                  position={[result.latitude, result.longitude]}
                  icon={createCategoryIcon(
                    result.categories?.length > 0 
                      ? getCategoryColor(categories.find(c => result.categories.includes(c.name))?.id || '')
                      : '#7c3aed'
                  )}
                >
                  <Popup>
                    <div style={{ maxWidth: 250 }}>
                      <strong style={{ color: '#1e1b4b' }}>{result.title}</strong>
                      <p style={{ fontSize: '0.8rem', margin: '5px 0', color: '#4b5563' }}>{result.snippet?.substring(0, 100)}...</p>
                      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '0.7rem', padding: '2px 6px', background: '#e0e7ff', borderRadius: 4, color: '#3730a3' }}>{result.article_type}</span>
                        {result.categories?.map((cat, i) => (
                          <span key={i} style={{ fontSize: '0.7rem', padding: '2px 6px', background: '#fce7f3', borderRadius: 4, color: '#be185d' }}>{cat}</span>
                        ))}
                      </div>
                      <a href={result.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.75rem', color: '#7c3aed', display: 'block', marginTop: 8 }}>Open Link →</a>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
          
          {mapResults.length === 0 && searchResults.length > 0 && (
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem', marginTop: 10, textAlign: 'center' }}>
              💡 No results have location data. Results will appear on the map when they have latitude/longitude coordinates.
            </p>
          )}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20 }}>
        {/* Categories Sidebar */}
        <div className="card">
          <h3 style={{ marginBottom: 15, color: '#f472b6' }}>Categories</h3>
          <div className="categories-tree">
            {categories.length === 0 ? (
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>No categories yet. Create one to start organizing your searches!</p>
            ) : (
              buildCategoryTree(categories)
            )}
          </div>
          {selectedCategories.length > 0 && (
            <button className="btn btn-secondary" style={{ marginTop: 15, width: '100%' }} onClick={() => setSelectedCategories([])}>
              Clear Selection ({selectedCategories.length})
            </button>
          )}
        </div>

        {/* Batch Manager */}
        <BatchManager
          batches={batches}
          showBatchManager={showBatchManager}
          setShowBatchManager={setShowBatchManager}
          onFetchBatches={fetchBatches}
          onDeleteBatch={deleteBatch}
          lastBatchId={lastBatchId}
        />

        {/* Search Results List Component */}
        <SearchResultsList
          searchResults={searchResults}
          onDeleteResult={deleteResult}
          onAddReaction={addReaction}
        />
      </div>

      {/* Create Category Modal */}
      <CreateCategoryModal
        show={showCategoryModal}
        onClose={() => setShowCategoryModal(false)}
        newCategory={newCategory}
        setNewCategory={setNewCategory}
        categories={categories}
        onCreate={createCategory}
      />

      {/* Edit Category Modal */}
      <EditCategoryModal
        editingCategory={editingCategory}
        onClose={() => setEditingCategory(null)}
        editCategoryName={editCategoryName}
        setEditCategoryName={setEditCategoryName}
        editProtocol={editProtocol}
        setEditProtocol={setEditProtocol}
        editIsPublic={editIsPublic}
        setEditIsPublic={setEditIsPublic}
        editPrice={editPrice}
        setEditPrice={setEditPrice}
        user={user}
        onSave={saveProtocol}
        onDelete={deleteCategory}
      />
    </div>
  );
};

export default UltimateSearchPage;
