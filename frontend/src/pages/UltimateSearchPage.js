import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API, triggerMapRefresh } from '../utils/api';
import { Icons, ProtocolDebugger, ProtocolTemplates, CopyButton, AISuggestions } from '../components/shared';
import SmartSearchSuggestions from '../components/shared/SmartSearchSuggestions';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Import refactored components
import {
  SearchControls,
  SearchResultsList,
  BatchManager,
  CreateCategoryModal,
  EditCategoryModal,
  CollapsibleCategoryTree
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
  
  // Quality Score Filtering state
  const [minQualityScore, setMinQualityScore] = useState(0); // 0 = show all, 50 = Good+, 65 = High Quality+, 80 = Premium only
  
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

  // Results with location data for map - ONLY show logged-in user's results
  const mapResults = useMemo(() => {
    const userId = user?.id || user?._id;
    return searchResults.filter(r => 
      r.latitude && r.longitude && 
      r.user_id === userId // Only show current user's results on USP map
    );
  }, [searchResults, user]);
  
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
    
    // Filter by minimum quality score
    if (minQualityScore > 0) {
      results = results.filter(r => (r.content_quality_score || 50) >= minQualityScore);
    }
    
    return results;
  }, [searchResults, selectedCategories, selectedDocTypes, categories, aggregation, minQualityScore]);
  
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
    if (!token) {
      console.log('[fetchCategories] No token available, skipping');
      return;
    }
    console.log('[fetchCategories] Starting fetch...');
    try {
      const url = `${API}/categories`;
      console.log('[fetchCategories] URL:', url);
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      console.log('[fetchCategories] Response received, status:', res.status);
      if (res.ok) {
        const data = await res.json();
        console.log('[fetchCategories] Categories parsed, count:', data.length);
        setCategories(data);
        console.log('[fetchCategories] State updated with', data.length, 'categories');
      } else {
        const errorText = await res.text();
        console.error('[fetchCategories] Response not ok:', res.status, errorText);
      }
    } catch (e) {
      console.error('[fetchCategories] Exception:', e.message, e);
    }
    console.log('[fetchCategories] Done');
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
    // Only load data if token is available
    if (!token) {
      console.log('[loadData] No token, skipping data load');
      return;
    }
    console.log('[loadData] Token available, loading data...');
    
    // Load categories first, then others
    fetchCategories()
      .then(() => {
        console.log('[loadData] Categories loaded, now loading search results and batches');
        return Promise.all([fetchSearchResults(), fetchBatches()]);
      })
      .then(() => {
        console.log('[loadData] All data loaded');
      })
      .catch((e) => {
        console.error('[loadData] Error during data load:', e);
      });
  }, [token, fetchCategories, fetchSearchResults, fetchBatches]);

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

  // Clean category (remove all results associated with the category)
  const cleanCategory = async (categoryId, mode = 'delete_all') => {
    try {
      const res = await fetch(`${API}/categories/${categoryId}/clean?mode=${mode}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(data.message || 'Category cleaned successfully!', 'success');
        setEditingCategory(null);
        fetchSearchResults();
        triggerMapRefresh();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to clean category', 'error');
      }
    } catch (e) {
      console.error('Clean category error:', e);
      showToast('Failed to clean category', 'error');
    }
  };

  const toggleCategorySelection = (catId) => {
    setSelectedCategories(prev => {
      const newSelection = prev.includes(catId) ? prev.filter(id => id !== catId) : [...prev, catId];
      // Automatically show filtered results when categories are selected
      if (newSelection.length > 0) {
        setShowFilteredResults(true);
      }
      return newSelection;
    });
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
  // Calculate result counts per category
  const getCategoryResultCount = (categoryId) => {
    return searchResults.filter(r => 
      r.category_ids?.includes(categoryId) || 
      r.categories?.some(c => categories.find(cat => cat.name === c)?.id === categoryId)
    ).length;
  };

  const buildCategoryTree = (cats, parentId = null, level = 0) => {
    return cats
      .filter(c => c.parent_id === parentId)
      .map(cat => {
        const resultCount = getCategoryResultCount(cat.id);
        return (
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
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', flexWrap: 'nowrap', gap: 8 }}
              onClick={() => toggleCategorySelection(cat.id)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: '1 1 auto', minWidth: 0, overflow: 'hidden' }}>
                <input
                  type="checkbox"
                  checked={selectedCategories.includes(cat.id)}
                  onChange={() => {}}
                  style={{ accentColor: getCategoryColor(cat.id), width: 16, height: 16, cursor: 'pointer', flexShrink: 0 }}
                  data-testid={`category-checkbox-${cat.id}`}
                />
                <span style={{ 
                  color: selectedCategories.includes(cat.id) ? '#f472b6' : '#e2e8f0',
                  fontWeight: selectedCategories.includes(cat.id) ? 600 : 400,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {cat.name}
                  {/* Result count in parentheses */}
                  <span style={{ 
                    color: resultCount > 0 ? '#10b981' : '#71717a',
                    fontSize: '0.75rem',
                    marginLeft: 6,
                    fontWeight: 400
                  }}>
                    ({resultCount})
                  </span>
                </span>
              </div>
              <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexShrink: 0 }}>
                <CopyButton text={cat.name} label="" successLabel="✓" size="sm" variant="icon" showToast={showToast} style={{ fontSize: '0.7rem' }} />
                {cat.protocol && (
                  <CopyButton text={cat.protocol} label="" successLabel="✓" size="sm" variant="icon" showToast={showToast} style={{ fontSize: '0.7rem', color: '#a78bfa' }} />
                )}
                {cat.is_public && <span style={{ fontSize: '0.6rem', color: '#10b981', padding: '1px 4px', background: 'rgba(16,185,129,0.2)', borderRadius: 4, flexShrink: 0 }}>Pub</span>}
                <button 
                  onClick={(e) => handleEditCategory(cat, e)}
                  style={{ background: 'transparent', border: 'none', color: '#a1a1aa', cursor: 'pointer', padding: '2px 4px', fontSize: '0.7rem', flexShrink: 0 }}
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
      )});
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

        {/* Smart Search Suggestions - AI-powered */}
        <SmartSearchSuggestions 
          query={searchQuery}
          onSuggestionClick={(suggestion) => setSearchQuery(suggestion)}
          showToast={showToast}
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
          
          {/* Document Type Filters - Beneath the Map */}
          <div style={{
            marginTop: 15,
            padding: 15,
            background: 'rgba(30, 20, 50, 0.4)',
            borderRadius: 10,
            border: '1px solid rgba(124, 58, 237, 0.2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <h4 style={{ color: '#a78bfa', margin: 0, fontSize: '0.95rem' }}>
                📄 Filter by Document Type
              </h4>
              {selectedDocTypes.length > 0 && (
                <button
                  onClick={() => { setSelectedDocTypes([]); setShowFilteredResults(false); }}
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#f87171',
                    padding: '4px 12px',
                    borderRadius: 6,
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                >
                  Clear ({selectedDocTypes.length})
                </button>
              )}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {documentTypes.map(docType => (
                <label
                  key={docType.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 12px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    background: selectedDocTypes.includes(docType.id) 
                      ? `${docType.color}30`
                      : 'rgba(255,255,255,0.05)',
                    border: selectedDocTypes.includes(docType.id)
                      ? `2px solid ${docType.color}`
                      : '1px solid rgba(255,255,255,0.1)',
                    transition: 'all 0.2s'
                  }}
                  data-testid={`doctype-${docType.id.replace(/[^a-z0-9]/gi, '-').toLowerCase()}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedDocTypes.includes(docType.id)}
                    onChange={() => toggleDocType(docType.id)}
                    style={{ 
                      accentColor: docType.color,
                      width: 14,
                      height: 14
                    }}
                  />
                  <span style={{ 
                    color: selectedDocTypes.includes(docType.id) ? docType.color : '#a1a1aa',
                    fontSize: '0.8rem',
                    fontWeight: selectedDocTypes.includes(docType.id) ? 600 : 400
                  }}>
                    {docType.name}
                  </span>
                </label>
              ))}
            </div>
            <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
              💡 Check document types to filter results. Selected categories and document types combine to show matching results below.
            </p>
          </div>
          
          {/* Quality Score Filter */}
          <div style={{
            marginTop: 15,
            padding: 15,
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1))',
            borderRadius: 10,
            border: '1px solid rgba(16, 185, 129, 0.2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h4 style={{ color: '#10b981', margin: 0, fontSize: '0.95rem' }}>
                📊 Filter by Content Quality
              </h4>
              {minQualityScore > 0 && (
                <button
                  onClick={() => setMinQualityScore(0)}
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#f87171',
                    padding: '4px 12px',
                    borderRadius: 6,
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                  data-testid="clear-quality-filter"
                >
                  Clear Filter
                </button>
              )}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {[
                { value: 0, label: '📋 Show All', color: '#a1a1aa', desc: 'No filter' },
                { value: 50, label: '📄 Good+', color: '#f59e0b', desc: 'Score 50+' },
                { value: 65, label: '✨ High Quality+', color: '#3b82f6', desc: 'Score 65+' },
                { value: 80, label: '📚 Premium Only', color: '#10b981', desc: 'Score 80+' }
              ].map(option => (
                <button
                  key={option.value}
                  onClick={() => {
                    setMinQualityScore(option.value);
                    if (option.value > 0) setShowFilteredResults(true);
                  }}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    padding: '10px 16px',
                    background: minQualityScore === option.value 
                      ? `${option.color}20` 
                      : 'rgba(30, 20, 50, 0.5)',
                    border: minQualityScore === option.value 
                      ? `2px solid ${option.color}` 
                      : '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 10,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    minWidth: 100
                  }}
                  data-testid={`quality-filter-${option.value}`}
                >
                  <span style={{ 
                    color: minQualityScore === option.value ? option.color : '#e2e8f0',
                    fontWeight: minQualityScore === option.value ? 700 : 500,
                    fontSize: '0.85rem'
                  }}>
                    {option.label}
                  </span>
                  <span style={{ 
                    color: '#71717a', 
                    fontSize: '0.7rem',
                    marginTop: 3
                  }}>
                    {option.desc}
                  </span>
                </button>
              ))}
            </div>
            <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
              🎯 Filter to show only high-quality, extensively informative content. Premium content has detailed, well-researched information.
            </p>
          </div>
        </div>
      )}
      
      {/* Filtered Results Section - Bottom Center */}
      {(selectedCategories.length > 0 || selectedDocTypes.length > 0 || minQualityScore > 0) && showFilteredResults && (
        <div className="card" style={{ 
          marginBottom: 20,
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(236, 72, 153, 0.1))',
          border: '2px solid rgba(124, 58, 237, 0.3)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
            <h3 style={{ color: '#f472b6', margin: 0 }}>
              🎯 Filtered Results 
              <span style={{ fontSize: '0.85rem', color: '#a1a1aa', fontWeight: 'normal', marginLeft: 10 }}>
                {filteredResults.length} of {searchResults.length} results match your filters
                {minQualityScore > 0 && (
                  <span style={{ marginLeft: 8, color: '#10b981' }}>
                    (Quality: {minQualityScore}+)
                  </span>
                )}
              </span>
            </h3>
            <button
              onClick={() => setShowFilteredResults(false)}
              style={{
                background: 'rgba(107, 114, 128, 0.2)',
                border: '1px solid rgba(107, 114, 128, 0.3)',
                color: '#9ca3af',
                padding: '6px 14px',
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              ✕ Hide
            </button>
          </div>
          
          {/* Active Filters Display */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 15 }}>
            {selectedCategories.map(catId => {
              const cat = categories.find(c => c.id === catId);
              return cat ? (
                <span 
                  key={catId}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 5,
                    padding: '4px 10px',
                    background: 'rgba(236, 72, 153, 0.2)',
                    border: '1px solid rgba(236, 72, 153, 0.3)',
                    borderRadius: 6,
                    color: '#f472b6',
                    fontSize: '0.75rem'
                  }}
                >
                  📁 {cat.name}
                  <button
                    onClick={() => setSelectedCategories(prev => prev.filter(id => id !== catId))}
                    style={{ 
                      background: 'none', 
                      border: 'none', 
                      color: '#f472b6', 
                      cursor: 'pointer',
                      padding: 0,
                      fontSize: '0.8rem'
                    }}
                  >
                    ✕
                  </button>
                </span>
              ) : null;
            })}
            {selectedDocTypes.map(docType => {
              const dt = documentTypes.find(d => d.id === docType);
              return (
                <span 
                  key={docType}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 5,
                    padding: '4px 10px',
                    background: `${dt?.color || '#6b7280'}20`,
                    border: `1px solid ${dt?.color || '#6b7280'}50`,
                    borderRadius: 6,
                    color: dt?.color || '#6b7280',
                    fontSize: '0.75rem'
                  }}
                >
                  📄 {docType}
                  <button
                    onClick={() => setSelectedDocTypes(prev => prev.filter(d => d !== docType))}
                    style={{ 
                      background: 'none', 
                      border: 'none', 
                      color: dt?.color || '#6b7280', 
                      cursor: 'pointer',
                      padding: 0,
                      fontSize: '0.8rem'
                    }}
                  >
                    ✕
                  </button>
                </span>
              );
            })}
          </div>
          
          {/* Filtered Results Grid */}
          <div className="results-grid">
            {filteredResults.length === 0 ? (
              <p style={{ color: '#a1a1aa', textAlign: 'center', padding: 20 }}>
                No results match your current filter criteria. Try adjusting your category or document type selections.
              </p>
            ) : (
              filteredResults.slice(0, 50).map(result => (
                <div 
                  key={result.id} 
                  className="result-card"
                  style={{ background: 'rgba(30, 20, 50, 0.5)' }}
                >
                  <h3>
                    <a href={result.url} target="_blank" rel="noopener noreferrer">
                      {result.title}
                    </a>
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: '#a1a1aa' }}>{result.snippet?.substring(0, 150)}...</p>
                  <div className="result-card-meta">
                    <span 
                      className="result-tag" 
                      style={{ 
                        background: `${documentTypes.find(d => d.id === result.article_type)?.color || '#6b7280'}30`,
                        color: documentTypes.find(d => d.id === result.article_type)?.color || '#6b7280'
                      }}
                    >
                      {result.article_type}
                    </span>
                    <span className="result-tag">{result.root_domain}</span>
                    {result.categories?.slice(0, 3).map((cat, i) => (
                      <span key={i} className="result-tag" style={{ background: 'rgba(236, 72, 153, 0.2)', color: '#f472b6' }}>
                        {cat}
                      </span>
                    ))}
                    {result.categories?.length > 3 && (
                      <span className="result-tag" style={{ background: 'rgba(107, 114, 128, 0.2)', color: '#9ca3af' }}>
                        +{result.categories.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
          
          {filteredResults.length > 50 && (
            <p style={{ color: '#a1a1aa', textAlign: 'center', marginTop: 15, fontSize: '0.85rem' }}>
              Showing first 50 of {filteredResults.length} filtered results.
            </p>
          )}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20 }}>
        {/* Categories Sidebar - Collapsible Tree View */}
        <div className="card">
          <h3 style={{ marginBottom: 15, color: '#f472b6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>📂 My Categories</span>
            <span style={{ fontSize: '0.75rem', color: '#a1a1aa', fontWeight: 'normal' }}>
              {categories.length} categories
            </span>
          </h3>
          
          {/* Collapsible Category Tree */}
          <CollapsibleCategoryTree
            categories={categories}
            selectedCategories={selectedCategories}
            onToggleSelect={toggleCategorySelection}
            onSelectAll={() => setSelectedCategories(categories.map(c => c.id))}
            onDeselectAll={() => setSelectedCategories([])}
            onEdit={(cat) => {
              setEditingCategory(cat);
              setEditCategoryName(cat.name || '');
              setEditProtocol(cat.protocol || '');
              setEditIsPublic(cat.is_public || false);
              setEditPrice(cat.price ? cat.price.toString() : '');
            }}
            onDelete={(catId) => deleteCategory(catId)}
            isOwner={true}
            compact={false}
          />
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
          showToast={showToast}
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
        onCleanCategory={cleanCategory}
      />
    </div>
  );
};

export default UltimateSearchPage;
