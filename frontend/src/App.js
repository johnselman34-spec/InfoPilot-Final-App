import React, { useState, useEffect, createContext, useContext, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

// Import refactored modules
import { API } from './utils/api';
import { extractHashtags } from './utils/hashtags';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Toast, Icons, HashtagDisplay, Sidebar, QuoteOfTheDay, BookPromoBanner } from './components/shared';
import { LoginPage, RegisterPage, AuthCallback, AdminPanel, SettingsPage, SubscribePage, MessagesPage } from './pages';

// Fix Leaflet default marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// NOTE: The following components are still defined inline for stability
// Future refactoring will move them to separate files:
// - UltimateSearchPage -> /pages/UltimateSearchPage.js
// - SocialPage -> /pages/SocialPage.js
// - GroupsSection -> /components/social/GroupsSection.js
// - PagesSection -> /components/social/PagesSection.js
// - MapPage -> /pages/MapPage.js
// - MessagesPage -> /pages/MessagesPage.js
// - MarketplacePage -> /pages/MarketplacePage.js
// - AchievementsPage -> /pages/AchievementsPage.js
// - BookPromoBanner -> /components/shared/BookPromoBanner.js

// ==================== ULTIMATE SEARCH PAGE ====================
const UltimateSearchPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [categories, setCategories] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregation, setAggregation] = useState('and_or');
  const [loading, setLoading] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [newCategory, setNewCategory] = useState({ name: '', protocol: '', parent_id: null, is_public: false });
  const [batches, setBatches] = useState([]);
  const [showBatchManager, setShowBatchManager] = useState(false);
  const [lastBatchId, setLastBatchId] = useState(null);

  // Fetch search batches for deletion
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

  // Delete a search batch
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
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to delete batch', 'error');
      }
    } catch (e) {
      showToast('Failed to delete batch', 'error');
    }
  };

  // Delete a single result
  const deleteResult = async (resultId) => {
    try {
      const res = await fetch(`${API}/ultimate-search/result/${resultId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Result deleted', 'success');
        fetchSearchResults();
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
      console.warn('No token available for fetchCategories');
      return;
    }
    try {
      const res = await fetch(`${API}/categories`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data);
      } else if (res.status === 401) {
        console.error('Token expired or invalid');
      }
    } catch (e) {
      console.error('Failed to fetch categories:', e);
    }
  }, [token]);

  const fetchSearchResults = useCallback(async () => {
    try {
      const params = new URLSearchParams({
        aggregation,
        page: 1
      });
      if (selectedCategories.length > 0) {
        params.append('category_ids', selectedCategories.join(','));
      }
      
      const res = await fetch(`${API}/ultimate-search?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
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
      // First search - using optimized fast search
      const searchRes = await fetch(`${API}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ query: searchQuery })
      });
      
      if (searchRes.ok) {
        const searchData = await searchRes.json();
        const searchTime = ((Date.now() - startTime) / 1000).toFixed(1);
        
        // Then collate
        const collateRes = await fetch(`${API}/collate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ search_results: searchData.results })
        });
        
        if (collateRes.ok) {
          const collateData = await collateRes.json();
          const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
          setLastBatchId(collateData.batch_id);
          showToast(`Collated ${collateData.collated_count} of ${searchData.total} results in ${totalTime}s!`, 'success');
          fetchSearchResults();
          fetchBatches();
        }
      }
    } catch (e) {
      showToast('Search failed', 'error');
    }
    setLoading(false);
  };

  const createCategory = async () => {
    if (!newCategory.name || !newCategory.protocol) {
      showToast('Name and protocol are required', 'error');
      return;
    }
    
    // Check if token exists
    if (!token) {
      showToast('Session expired. Please log in again.', 'error');
      return;
    }
    
    // Show loading state
    showToast('Creating category...', 'success');
    
    try {
      const requestBody = {
        name: newCategory.name,
        protocol: newCategory.protocol,
        parent_id: newCategory.parent_id || null,
        is_public: newCategory.is_public || false
      };
      
      const res = await fetch(`${API}/categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });
      
      // Clone response before reading to avoid "body stream already read" error
      const resClone = res.clone();
      
      let data;
      try {
        data = await res.json();
      } catch (jsonError) {
        // If JSON parsing fails, try to get text from cloned response
        const text = await resClone.text();
        console.error('Response parsing error:', text);
        throw new Error(`Server returned invalid response: ${res.status}`);
      }
      
      if (res.ok) {
        showToast(`Category "${newCategory.name}" created successfully!`, 'success');
        setShowCategoryModal(false);
        setNewCategory({ name: '', protocol: '', parent_id: null, is_public: false });
        fetchCategories();
      } else {
        const errorMsg = data.detail || data.message || 'Failed to create category. Please try again.';
        showToast(errorMsg, 'error');
      }
    } catch (e) {
      console.error('Category creation error:', e);
      if (e.message.includes('Failed to fetch')) {
        showToast('Network error. Please check your connection.', 'error');
      } else {
        showToast(e.message || 'Failed to create category', 'error');
      }
    }
  };

  const toggleCategorySelection = (catId) => {
    setSelectedCategories(prev => 
      prev.includes(catId) 
        ? prev.filter(id => id !== catId)
        : [...prev, catId]
    );
  };

  const addReaction = async (resultId, reactionType) => {
    try {
      await fetch(`${API}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ search_result_id: resultId, reaction_type: reactionType })
      });
      fetchSearchResults();
    } catch (e) {
      console.error('Failed to add reaction:', e);
    }
  };

  const [editingCategory, setEditingCategory] = useState(null);
  const [editProtocol, setEditProtocol] = useState('');

  const handleEditCategory = (cat, e) => {
    e.stopPropagation();
    setEditingCategory(cat);
    setEditProtocol(cat.protocol || '');
  };

  const saveProtocol = async () => {
    if (!editingCategory) return;
    try {
      const res = await fetch(`${API}/categories/${editingCategory.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ protocol: editProtocol })
      });
      if (res.ok) {
        showToast('Protocol updated!', 'success');
        fetchCategories();
        setEditingCategory(null);
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to update', 'error');
      }
    } catch (e) {
      showToast('Failed to update protocol', 'error');
    }
  };

  const buildCategoryTree = (cats, parentId = null, level = 0) => {
    return cats
      .filter(c => c.parent_id === parentId)
      .map(cat => (
        <div key={cat.id}>
          <div 
            className={`category-item category-item-level-${level} ${selectedCategories.includes(cat.id) ? 'selected' : ''}`}
            style={{ flexDirection: 'column', alignItems: 'stretch' }}
          >
            <div 
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
              onClick={() => toggleCategorySelection(cat.id)}
            >
              <span>{cat.name}</span>
              <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
                {cat.is_public && <span style={{ fontSize: '0.65rem', color: '#10b981', padding: '2px 6px', background: 'rgba(16,185,129,0.2)', borderRadius: 4 }}>Public</span>}
                <button 
                  onClick={(e) => handleEditCategory(cat, e)}
                  style={{ 
                    background: 'transparent', 
                    border: 'none', 
                    color: '#a1a1aa', 
                    cursor: 'pointer',
                    padding: '2px 6px',
                    fontSize: '0.75rem'
                  }}
                  title="Edit Protocol"
                  data-testid={`edit-category-${cat.id}`}
                >
                  ✏️
                </button>
              </div>
            </div>
            {cat.protocol && (
              <div style={{ 
                fontSize: '0.7rem', 
                color: '#71717a', 
                marginTop: 4,
                padding: '4px 8px',
                background: 'rgba(124, 58, 237, 0.1)',
                borderRadius: 4,
                fontFamily: 'monospace',
                wordBreak: 'break-all'
              }}>
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
          <h2>{user?.username}'s Ultimate Search Page</h2>
          <button className="btn btn-primary" onClick={() => setShowCategoryModal(true)}>
            <Icons.Plus /> New Category
          </button>
        </div>

        {/* Search Box */}
        <div className="search-box">
          <input
            className="input-field"
            placeholder="Enter search query and click 'Search & Collate'"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
            {loading ? 'Searching...' : 'Search & Collate'}
          </button>
        </div>

        {/* Aggregation Options */}
        <div style={{ display: 'flex', gap: 20, marginBottom: 20, alignItems: 'center' }}>
          <span style={{ color: '#a1a1aa' }}>Search Aggregation:</span>
          {['and_or', 'and', 'or'].map(agg => (
            <label key={agg} style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer' }}>
              <input
                type="radio"
                name="aggregation"
                checked={aggregation === agg}
                onChange={() => setAggregation(agg)}
              />
              {agg.toUpperCase().replace('_', '/')}
            </label>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20 }}>
        {/* Categories Sidebar */}
        <div className="card">
          <h3 style={{ marginBottom: 15, color: '#f472b6' }}>Categories</h3>
          <div className="categories-tree">
            {categories.length === 0 ? (
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
                No categories yet. Create one to start organizing your searches!
              </p>
            ) : (
              buildCategoryTree(categories)
            )}
          </div>
          {selectedCategories.length > 0 && (
            <button 
              className="btn btn-secondary" 
              style={{ marginTop: 15, width: '100%' }}
              onClick={() => setSelectedCategories([])}
            >
              Clear Selection ({selectedCategories.length})
            </button>
          )}
        </div>

        {/* Batch Manager - Delete Search Sessions */}
        <div style={{ marginBottom: 20 }}>
          <button
            className="btn btn-secondary"
            onClick={() => { setShowBatchManager(!showBatchManager); if (!showBatchManager) fetchBatches(); }}
            style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            data-testid="batch-manager-toggle"
          >
            🗑️ Manage Search Sessions ({batches.length})
          </button>
          
          {showBatchManager && (
            <div style={{ 
              marginTop: 10, 
              padding: 15, 
              background: 'rgba(30, 20, 50, 0.5)', 
              borderRadius: 12,
              border: '1px solid rgba(239, 68, 68, 0.3)'
            }}>
              <h4 style={{ color: '#f87171', marginBottom: 10 }}>Search Sessions (Batches)</h4>
              <p style={{ color: '#a1a1aa', fontSize: '0.8rem', marginBottom: 15 }}>
                Delete all results from a specific Search & Collate session:
              </p>
              {batches.length === 0 ? (
                <p style={{ color: '#71717a', fontSize: '0.9rem' }}>No search sessions found.</p>
              ) : (
                <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                  {batches.map(batch => (
                    <div 
                      key={batch.batch_id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '10px 12px',
                        background: 'rgba(0,0,0,0.2)',
                        borderRadius: 8,
                        marginBottom: 8
                      }}
                    >
                      <div>
                        <span style={{ color: '#e2e8f0', fontSize: '0.9rem' }}>
                          {batch.result_count} results
                        </span>
                        <span style={{ color: '#71717a', fontSize: '0.8rem', marginLeft: 10 }}>
                          "{batch.sample_title}..."
                        </span>
                        {batch.collated_at && (
                          <span style={{ color: '#6b7280', fontSize: '0.75rem', marginLeft: 10 }}>
                            {new Date(batch.collated_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <button
                        className="btn"
                        onClick={() => deleteBatch(batch.batch_id)}
                        style={{ 
                          background: 'rgba(239, 68, 68, 0.2)', 
                          color: '#f87171', 
                          padding: '6px 12px',
                          fontSize: '0.8rem',
                          border: '1px solid rgba(239, 68, 68, 0.3)'
                        }}
                        data-testid={`delete-batch-${batch.batch_id}`}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  ))}
                </div>
              )}
              {lastBatchId && (
                <button
                  className="btn"
                  onClick={() => deleteBatch(lastBatchId)}
                  style={{ 
                    marginTop: 10,
                    background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(249, 115, 22, 0.3))',
                    color: '#fbbf24',
                    border: '1px solid rgba(239, 68, 68, 0.5)'
                  }}
                  data-testid="delete-last-batch"
                >
                  🗑️ Delete Last Search Session
                </button>
              )}
            </div>
          )}
        </div>

        {/* Search Results */}
        <div className="card">
          <h3 style={{ marginBottom: 15, color: '#f472b6' }}>
            Search Results ({searchResults.length})
          </h3>
          <div className="results-grid">
            {searchResults.length === 0 ? (
              <p style={{ color: '#a1a1aa' }}>
                No results yet. Use "Search & Collate" to find and categorize web content!
              </p>
            ) : (
              searchResults.map(result => (
                <div key={result.id} className="result-card" style={{ position: 'relative' }}>
                  {/* Delete button - visible for user's own results or admin */}
                  <button
                    onClick={() => deleteResult(result.id)}
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
                  <h3>
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
                  <div className="reactions-bar">
                    {['Like', 'Love', 'Funny', 'Sad', 'Best'].map(reaction => (
                      <button
                        key={reaction}
                        className="reaction-btn"
                        onClick={() => addReaction(result.id, reaction)}
                      >
                        {reaction === 'Like' && '👍'}
                        {reaction === 'Love' && '❤️'}
                        {reaction === 'Funny' && '😂'}
                        {reaction === 'Sad' && '😢'}
                        {reaction === 'Best' && '⭐'}
                        {reaction}
                      </button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Create Category Modal */}
      {showCategoryModal && (
        <div className="modal-overlay" onClick={() => setShowCategoryModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create Category</h2>
              <button className="modal-close" onClick={() => setShowCategoryModal(false)}>×</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              <input
                className="input-field"
                placeholder="Category Name"
                value={newCategory.name}
                onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
              />
              <textarea
                className="input-field"
                placeholder="Protocol (e.g., (word1 or word2) & (word3)+ )"
                rows={4}
                value={newCategory.protocol}
                onChange={(e) => setNewCategory({ ...newCategory, protocol: e.target.value })}
                style={{ resize: 'vertical' }}
              />
              <select
                className="input-field"
                value={newCategory.parent_id || ''}
                onChange={(e) => setNewCategory({ ...newCategory, parent_id: e.target.value || null })}
              >
                <option value="">No Parent (Top Level)</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <input
                  type="checkbox"
                  checked={newCategory.is_public}
                  onChange={(e) => setNewCategory({ ...newCategory, is_public: e.target.checked })}
                />
                Make this category public
              </label>
              <p style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>
                💡 Protocols are case-insensitive. Use (keyphrase1 or keyphrase2) for OR logic, 
                & for AND, + for INCLUDE ALL, ^ for EXCLUDE ALL
              </p>
              <button className="btn btn-primary" onClick={createCategory}>
                Create Category
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Category Protocol Modal */}
      {editingCategory && (
        <div className="modal-overlay" onClick={() => setEditingCategory(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 550 }}>
            <div className="modal-header">
              <h2>Edit Protocol: {editingCategory.name}</h2>
              <button className="modal-close" onClick={() => setEditingCategory(null)}>×</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              <div style={{ 
                background: 'rgba(124, 58, 237, 0.1)', 
                padding: 15, 
                borderRadius: 10,
                borderLeft: '4px solid #7c3aed'
              }}>
                <p style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 8 }}>
                  <strong>Category:</strong> {editingCategory.name}
                </p>
                <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                  <strong>Current Protocol:</strong>
                </p>
                <code style={{ 
                  display: 'block',
                  background: 'rgba(0,0,0,0.3)', 
                  padding: 10, 
                  borderRadius: 6,
                  color: '#10b981',
                  fontSize: '0.8rem',
                  wordBreak: 'break-all',
                  marginTop: 5
                }}>
                  {editingCategory.protocol || '(no protocol set)'}
                </code>
              </div>
              
              <label style={{ color: '#f472b6', fontWeight: 600 }}>New Protocol:</label>
              <textarea
                className="input"
                placeholder="Enter new protocol (e.g., (keyphrase1 or keyphrase2) & (keyphrase3)+)"
                rows={5}
                value={editProtocol}
                onChange={(e) => setEditProtocol(e.target.value)}
                style={{ resize: 'vertical', fontFamily: 'monospace' }}
                data-testid="edit-protocol-input"
              />
              
              <div style={{ 
                background: 'rgba(16, 185, 129, 0.1)', 
                padding: 12, 
                borderRadius: 8,
                fontSize: '0.8rem',
                color: '#a1a1aa'
              }}>
                <p style={{ marginBottom: 8 }}><strong>Protocol Syntax Guide:</strong></p>
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  <li><code>(word1 or word2)</code> - Match ANY word (OR logic)</li>
                  <li><code>(word1 or word2)+</code> - Match ALL words (INCLUDE ALL)</li>
                  <li><code>(word1 or word2)^</code> - Exclude ALL words (EXCLUDE ALL)</li>
                  <li><code>&</code> - Combine groups (AND between groups)</li>
                  <li><code>"multi word phrase"</code> - Match exact phrase</li>
                </ul>
              </div>
              
              <div style={{ display: 'flex', gap: 10 }}>
                <button 
                  className="btn btn-secondary" 
                  onClick={() => setEditingCategory(null)}
                  style={{ flex: 1 }}
                >
                  Cancel
                </button>
                <button 
                  className="btn btn-primary" 
                  onClick={saveProtocol}
                  style={{ flex: 1 }}
                  data-testid="save-protocol-btn"
                >
                  Save Protocol
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== SOCIAL PAGE ====================
const SocialPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [activeTab, setActiveTab] = useState('feed');
  const [friends, setFriends] = useState([]);
  const [feedPosts, setFeedPosts] = useState([]);
  const [newPost, setNewPost] = useState('');
  const [postingFeed, setPostingFeed] = useState(false);

  useEffect(() => {
    if (activeTab === 'friends') fetchFriends();
    if (activeTab === 'feed') fetchFeed();
  }, [activeTab]);

  const fetchFriends = async () => {
    try {
      const res = await fetch(`${API}/friends`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFriends(data.friends || []);
      }
    } catch (e) {
      console.error('Failed to fetch friends:', e);
    }
  };

  const fetchFeed = async () => {
    try {
      const res = await fetch(`${API}/feed`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFeedPosts(data.posts || []);
      }
    } catch (e) {
      console.error('Failed to fetch feed:', e);
    }
  };

  const createFeedPost = async () => {
    if (!newPost.trim()) return;
    setPostingFeed(true);
    try {
      const res = await fetch(`${API}/feed/post`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: newPost })
      });
      if (res.ok) {
        showToast('Post created! +5 XP', 'success');
        setNewPost('');
        fetchFeed();
      }
    } catch (e) {
      showToast('Failed to create post', 'error');
    }
    setPostingFeed(false);
  };

  return (
    <div className="card" data-testid="social-page">
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Users />
          Social Network
        </h2>
      </div>

      <div className="tabs" style={{ marginBottom: 20 }}>
        {['feed', 'friends', 'groups', 'pages'].map(tab => (
          <div
            key={tab}
            className={`tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
            data-testid={`social-tab-${tab}`}
          >
            {tab === 'feed' && '📰 '}
            {tab === 'friends' && '👥 '}
            {tab === 'groups' && '🏘️ '}
            {tab === 'pages' && '📄 '}
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </div>
        ))}
      </div>

      {activeTab === 'feed' && (
        <div>
          {/* Create Post */}
          <div style={{ 
            marginBottom: 25, 
            padding: 20,
            background: 'rgba(30, 20, 50, 0.5)',
            borderRadius: 12
          }}>
            <textarea
              className="input"
              placeholder="What's on your mind?"
              rows={3}
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
              data-testid="feed-post-input"
            />
            <button 
              className="btn btn-primary" 
              style={{ marginTop: 10 }}
              onClick={createFeedPost}
              disabled={postingFeed || !newPost.trim()}
              data-testid="feed-post-btn"
            >
              {postingFeed ? 'Posting...' : 'Post'}
            </button>
          </div>

          {/* Feed Posts */}
          {feedPosts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
              <div style={{ fontSize: '3rem', marginBottom: 15 }}>📰</div>
              <p>Your feed is empty. Join groups to see posts!</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              {feedPosts.map(post => (
                <div key={post.id} className="post-card" style={{
                  padding: 20,
                  background: 'rgba(30, 20, 50, 0.5)',
                  borderRadius: 12,
                  border: '1px solid rgba(124, 58, 237, 0.2)'
                }}>
                  <div className="post-header" style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                    <div className="post-avatar" style={{
                      width: 40, height: 40, borderRadius: '50%',
                      background: 'linear-gradient(135deg, #f472b6, #7c3aed)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontWeight: 700, color: '#fff'
                    }}>
                      {post.author_name?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <strong style={{ color: '#fff' }}>{post.author_name}</strong>
                      {post.group_name && (
                        <span style={{ color: '#a1a1aa' }}> in <span style={{ color: '#f472b6' }}>{post.group_name}</span></span>
                      )}
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 2 }}>
                        {new Date(post.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="post-content" style={{ color: '#e5e7eb', marginBottom: 15, lineHeight: 1.6 }}>
                    {post.content}
                  </div>
                  <div className="post-actions" style={{ display: 'flex', gap: 15 }}>
                    <button className="reaction-btn" style={{
                      background: post.is_liked ? 'rgba(236, 72, 153, 0.2)' : 'transparent',
                      border: 'none',
                      color: post.is_liked ? '#f472b6' : '#a1a1aa',
                      cursor: 'pointer',
                      padding: '6px 12px',
                      borderRadius: 20,
                      fontSize: '0.85rem'
                    }}>
                      👍 {post.likes || 0}
                    </button>
                    <button className="reaction-btn" style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#a1a1aa',
                      cursor: 'pointer',
                      padding: '6px 12px',
                      borderRadius: 20,
                      fontSize: '0.85rem'
                    }}>
                      💬 {post.comment_count || 0}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'friends' && (
        <div>
          <div style={{ marginBottom: 20 }}>
            <input className="input" placeholder="Search for users..." data-testid="friend-search-input" />
          </div>
          {friends.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <div style={{ fontSize: '3rem', marginBottom: 15 }}>👥</div>
              <p style={{ color: '#a1a1aa' }}>No friends yet. Start connecting with other users!</p>
            </div>
          ) : (
            friends.map(friend => (
              <div key={friend.id} className="conversation-item" style={{
                display: 'flex',
                alignItems: 'center',
                gap: 15,
                padding: 15,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 10,
                marginBottom: 10
              }}>
                <div className="post-avatar" style={{
                  width: 45, height: 45, borderRadius: '50%',
                  background: 'linear-gradient(135deg, #10b981, #3b82f6)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 700, color: '#fff'
                }}>
                  {friend.username?.[0]?.toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <strong style={{ color: '#fff' }}>{friend.username}</strong>
                </div>
                <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                  View Profile
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'groups' && (
        <GroupsSection showToast={showToast} token={token} user={user} />
      )}

      {activeTab === 'pages' && (
        <PagesSection showToast={showToast} token={token} user={user} />
      )}
    </div>
  );
};

// ==================== GROUPS SECTION ====================
const GroupsSection = ({ showToast, token, user }) => {
  const [groups, setGroups] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [newGroup, setNewGroup] = useState({ name: '', description: '', is_public: true });
  const [newPost, setNewPost] = useState('');
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API}/groups`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setGroups(data);
      }
    } catch (e) {
      console.error('Failed to fetch groups');
    }
    setLoading(false);
  };

  const fetchGroupDetails = async (groupId) => {
    try {
      const res = await fetch(`${API}/groups/${groupId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedGroup(data);
      }
    } catch (e) {
      showToast('Failed to load group', 'error');
    }
  };

  const createGroup = async () => {
    if (!newGroup.name) {
      showToast('Group name is required', 'error');
      return;
    }
    try {
      const res = await fetch(`${API}/groups`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newGroup)
      });
      if (res.ok) {
        showToast('Group created!', 'success');
        setShowCreateModal(false);
        setNewGroup({ name: '', description: '', is_public: true });
        fetchGroups();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to create group', 'error');
      }
    } catch (e) {
      showToast('Failed to create group', 'error');
    }
  };

  const joinGroup = async (groupId) => {
    try {
      const res = await fetch(`${API}/groups/${groupId}/join`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Joined group!', 'success');
        fetchGroups();
        if (selectedGroup?.id === groupId) {
          fetchGroupDetails(groupId);
        }
      }
    } catch (e) {
      showToast('Failed to join group', 'error');
    }
  };

  const leaveGroup = async (groupId) => {
    try {
      const res = await fetch(`${API}/groups/${groupId}/leave`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Left group', 'success');
        fetchGroups();
        if (selectedGroup?.id === groupId) {
          fetchGroupDetails(groupId);
        }
      }
    } catch (e) {
      showToast('Failed to leave group', 'error');
    }
  };

  const createPost = async () => {
    if (!newPost.trim() || !selectedGroup) return;
    setPosting(true);
    try {
      const res = await fetch(`${API}/groups/${selectedGroup.id}/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: newPost })
      });
      if (res.ok) {
        showToast('Post created! +5 XP', 'success');
        setNewPost('');
        fetchGroupDetails(selectedGroup.id);
      }
    } catch (e) {
      showToast('Failed to create post', 'error');
    }
    setPosting(false);
  };

  const likePost = async (postId) => {
    try {
      await fetch(`${API}/groups/${selectedGroup.id}/posts/${postId}/like`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchGroupDetails(selectedGroup.id);
    } catch (e) {
      console.error('Failed to like post');
    }
  };

  if (loading) {
    return <div className="loading-spinner"><div className="spinner"></div></div>;
  }

  // Group Detail View
  if (selectedGroup) {
    return (
      <div>
        <button 
          className="btn btn-secondary" 
          onClick={() => setSelectedGroup(null)}
          style={{ marginBottom: 20 }}
        >
          ← Back to Groups
        </button>

        <div style={{ 
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.3), rgba(236, 72, 153, 0.2))',
          borderRadius: 16, padding: 25, marginBottom: 25
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <h2 style={{ color: '#f472b6', margin: 0, marginBottom: 8 }}>{selectedGroup.name}</h2>
              <p style={{ color: '#a1a1aa', marginBottom: 10 }}>{selectedGroup.description || 'No description'}</p>
              <span style={{ color: '#6b7280', fontSize: '0.85rem' }}>
                👤 {selectedGroup.member_count} members • {selectedGroup.is_public ? '🌐 Public' : '🔒 Private'}
              </span>
            </div>
            {selectedGroup.is_member ? (
              !selectedGroup.is_creator && (
                <button className="btn btn-secondary" onClick={() => leaveGroup(selectedGroup.id)}>
                  Leave Group
                </button>
              )
            ) : (
              <button className="btn btn-primary" onClick={() => joinGroup(selectedGroup.id)}>
                Join Group
              </button>
            )}
          </div>
        </div>

        {/* Create Post (if member) */}
        {(selectedGroup.is_member || selectedGroup.is_public) && (
          <div style={{ marginBottom: 25, padding: 20, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
            <textarea
              className="input"
              placeholder="Share something with the group..."
              rows={3}
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
            />
            <button 
              className="btn btn-primary" 
              style={{ marginTop: 10 }}
              onClick={createPost}
              disabled={posting || !newPost.trim()}
            >
              {posting ? 'Posting...' : 'Post to Group'}
            </button>
          </div>
        )}

        {/* Group Posts */}
        <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Posts</h3>
        {selectedGroup.posts?.length === 0 ? (
          <p style={{ color: '#a1a1aa', textAlign: 'center', padding: 30 }}>
            No posts yet. Be the first to post!
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            {selectedGroup.posts?.map(post => (
              <div key={post.id} style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(124, 58, 237, 0.2)'
              }}>
                <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: '50%',
                    background: 'linear-gradient(135deg, #f472b6, #7c3aed)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, color: '#fff'
                  }}>
                    {post.author_name?.[0]?.toUpperCase() || '?'}
                  </div>
                  <div>
                    <strong style={{ color: '#fff' }}>{post.author_name}</strong>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 2 }}>
                      {new Date(post.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <p style={{ color: '#e5e7eb', marginBottom: 15, lineHeight: 1.6 }}>{post.content}</p>
                <div style={{ display: 'flex', gap: 15 }}>
                  <button 
                    onClick={() => likePost(post.id)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#a1a1aa',
                      cursor: 'pointer',
                      padding: '6px 12px',
                      borderRadius: 20,
                      fontSize: '0.85rem'
                    }}
                  >
                    👍 {post.likes?.length || 0}
                  </button>
                  <button style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#a1a1aa',
                    cursor: 'pointer',
                    padding: '6px 12px',
                    borderRadius: 20,
                    fontSize: '0.85rem'
                  }}>
                    💬 {post.comments?.length || 0}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Groups List View
  return (
    <div>
      <button 
        className="btn btn-primary" 
        style={{ marginBottom: 20 }}
        onClick={() => setShowCreateModal(true)}
        data-testid="create-group-btn"
      >
        <Icons.Plus /> Create Group
      </button>

      {groups.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: '3rem', marginBottom: 15 }}>🏘️</div>
          <p style={{ color: '#a1a1aa' }}>No groups yet. Create one to start collaborating!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {groups.map(group => (
            <div 
              key={group.id} 
              style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(124, 58, 237, 0.3)',
                cursor: 'pointer',
                transition: 'transform 0.2s, border-color 0.2s'
              }}
              onClick={() => fetchGroupDetails(group.id)}
              data-testid={`group-card-${group.id}`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 10 }}>
                <h3 style={{ color: '#f472b6', margin: 0 }}>{group.name}</h3>
                <span style={{ 
                  fontSize: '0.7rem', 
                  padding: '3px 8px', 
                  borderRadius: 10,
                  background: group.is_public ? 'rgba(16, 185, 129, 0.2)' : 'rgba(124, 58, 237, 0.2)',
                  color: group.is_public ? '#10b981' : '#a78bfa'
                }}>
                  {group.is_public ? '🌐 Public' : '🔒 Private'}
                </span>
              </div>
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 15 }}>
                {group.description || 'No description'}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>
                  👤 {group.member_count || 1} members
                </span>
                <span style={{ color: '#7c3aed', fontSize: '0.8rem' }}>View →</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Group Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>Create New Group</h3>
            <input
              type="text"
              placeholder="Group Name"
              className="input"
              value={newGroup.name}
              onChange={e => setNewGroup({...newGroup, name: e.target.value})}
              style={{ marginBottom: 15 }}
              data-testid="group-name-input"
            />
            <textarea
              placeholder="Description (optional)"
              className="input"
              value={newGroup.description}
              onChange={e => setNewGroup({...newGroup, description: e.target.value})}
              rows={3}
              style={{ marginBottom: 15 }}
              data-testid="group-description-input"
            />
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, color: '#a1a1aa' }}>
              <input
                type="checkbox"
                checked={newGroup.is_public}
                onChange={e => setNewGroup({...newGroup, is_public: e.target.checked})}
              />
              Public group (anyone can join)
            </label>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={createGroup} data-testid="submit-group-btn">Create Group</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== PAGES SECTION ====================
const PagesSection = ({ showToast, token, user }) => {
  const [pages, setPages] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPage, setSelectedPage] = useState(null);
  const [newPage, setNewPage] = useState({ name: '', description: '', category: 'General' });
  const [newPost, setNewPost] = useState('');
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      const res = await fetch(`${API}/pages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPages(data);
      }
    } catch (e) {
      console.error('Failed to fetch pages');
    }
    setLoading(false);
  };

  const fetchPageDetails = async (pageId) => {
    try {
      const res = await fetch(`${API}/pages/${pageId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedPage(data);
      }
    } catch (e) {
      showToast('Failed to load page', 'error');
    }
  };

  const createPage = async () => {
    if (!newPage.name) {
      showToast('Page name is required', 'error');
      return;
    }
    try {
      const res = await fetch(`${API}/pages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newPage)
      });
      if (res.ok) {
        showToast('Page created!', 'success');
        setShowCreateModal(false);
        setNewPage({ name: '', description: '', category: 'General' });
        fetchPages();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to create page', 'error');
      }
    } catch (e) {
      showToast('Failed to create page', 'error');
    }
  };

  const likePage = async (pageId) => {
    try {
      await fetch(`${API}/pages/${pageId}/like`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchPages();
      if (selectedPage?.id === pageId) {
        fetchPageDetails(pageId);
      }
    } catch (e) {
      console.error('Failed to like page');
    }
  };

  const followPage = async (pageId) => {
    try {
      await fetch(`${API}/pages/${pageId}/follow`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (selectedPage?.id === pageId) {
        fetchPageDetails(pageId);
      }
    } catch (e) {
      console.error('Failed to follow page');
    }
  };

  const createPost = async () => {
    if (!newPost.trim() || !selectedPage) return;
    setPosting(true);
    try {
      const res = await fetch(`${API}/pages/${selectedPage.id}/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: newPost })
      });
      if (res.ok) {
        showToast('Post created!', 'success');
        setNewPost('');
        fetchPageDetails(selectedPage.id);
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to create post', 'error');
      }
    } catch (e) {
      showToast('Failed to create post', 'error');
    }
    setPosting(false);
  };

  if (loading) {
    return <div className="loading-spinner"><div className="spinner"></div></div>;
  }

  const categories = ['General', 'Technology', 'Science', 'History', 'Entertainment', 'Sports', 'News', 'Other'];

  // Page Detail View
  if (selectedPage) {
    return (
      <div>
        <button 
          className="btn btn-secondary" 
          onClick={() => setSelectedPage(null)}
          style={{ marginBottom: 20 }}
        >
          ← Back to Pages
        </button>

        <div style={{ 
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(59, 130, 246, 0.2))',
          borderRadius: 16, padding: 25, marginBottom: 25
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <h2 style={{ color: '#ec4899', margin: 0, marginBottom: 8 }}>{selectedPage.name}</h2>
              <p style={{ color: '#a1a1aa', marginBottom: 10 }}>{selectedPage.description || 'No description'}</p>
              <span style={{ 
                fontSize: '0.7rem', 
                padding: '3px 8px', 
                borderRadius: 10,
                background: 'rgba(59, 130, 246, 0.2)',
                color: '#3b82f6',
                marginRight: 10
              }}>
                {selectedPage.category}
              </span>
              <span style={{ color: '#6b7280', fontSize: '0.85rem' }}>
                ❤️ {selectedPage.likes} likes • 👥 {selectedPage.followers} followers
              </span>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button 
                className={`btn ${selectedPage.is_liked ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => likePage(selectedPage.id)}
              >
                {selectedPage.is_liked ? '❤️ Liked' : '🤍 Like'}
              </button>
              <button 
                className={`btn ${selectedPage.is_following ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => followPage(selectedPage.id)}
              >
                {selectedPage.is_following ? '✓ Following' : '+ Follow'}
              </button>
            </div>
          </div>
        </div>

        {/* Create Post (if page owner) */}
        {selectedPage.is_creator && (
          <div style={{ marginBottom: 25, padding: 20, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
            <textarea
              className="input"
              placeholder="Share an update with your followers..."
              rows={3}
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
            />
            <button 
              className="btn btn-primary" 
              style={{ marginTop: 10 }}
              onClick={createPost}
              disabled={posting || !newPost.trim()}
            >
              {posting ? 'Posting...' : 'Post Update'}
            </button>
          </div>
        )}

        {/* Page Posts */}
        <h3 style={{ color: '#ec4899', marginBottom: 15 }}>Updates</h3>
        {selectedPage.posts?.length === 0 ? (
          <p style={{ color: '#a1a1aa', textAlign: 'center', padding: 30 }}>
            No updates yet.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            {selectedPage.posts?.map(post => (
              <div key={post.id} style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(236, 72, 153, 0.2)'
              }}>
                <p style={{ color: '#e5e7eb', marginBottom: 15, lineHeight: 1.6 }}>{post.content}</p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                    {new Date(post.created_at).toLocaleString()}
                  </span>
                  <button style={{
                    background: post.is_liked ? 'rgba(236, 72, 153, 0.2)' : 'transparent',
                    border: 'none',
                    color: post.is_liked ? '#ec4899' : '#a1a1aa',
                    cursor: 'pointer',
                    padding: '6px 12px',
                    borderRadius: 20,
                    fontSize: '0.85rem'
                  }}>
                    ❤️ {post.likes || 0}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Pages List View
  return (
    <div>
      <button 
        className="btn btn-primary" 
        style={{ marginBottom: 20 }}
        onClick={() => setShowCreateModal(true)}
        data-testid="create-page-btn"
      >
        <Icons.Plus /> Create Page
      </button>

      {pages.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: '3rem', marginBottom: 15 }}>📄</div>
          <p style={{ color: '#a1a1aa' }}>No pages yet. Create one to share your content!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {pages.map(page => (
            <div 
              key={page.id} 
              style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(236, 72, 153, 0.3)',
                cursor: 'pointer'
              }}
              onClick={() => fetchPageDetails(page.id)}
              data-testid={`page-card-${page.id}`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 10 }}>
                <h3 style={{ color: '#ec4899', margin: 0 }}>{page.name}</h3>
                <span style={{ 
                  fontSize: '0.7rem', 
                  padding: '3px 8px', 
                  borderRadius: 10,
                  background: 'rgba(59, 130, 246, 0.2)',
                  color: '#3b82f6'
                }}>
                  {page.category}
                </span>
              </div>
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 15 }}>
                {page.description || 'No description'}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>
                  ❤️ {page.likes || 0} likes
                </span>
                <span style={{ color: '#ec4899', fontSize: '0.8rem' }}>View →</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Page Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: 20, color: '#ec4899' }}>Create New Page</h3>
            <input
              type="text"
              placeholder="Page Name"
              className="input"
              value={newPage.name}
              onChange={e => setNewPage({...newPage, name: e.target.value})}
              style={{ marginBottom: 15 }}
              data-testid="page-name-input"
            />
            <textarea
              placeholder="Description (optional)"
              className="input"
              value={newPage.description}
              onChange={e => setNewPage({...newPage, description: e.target.value})}
              rows={3}
              style={{ marginBottom: 15 }}
              data-testid="page-description-input"
            />
            <select
              className="input"
              value={newPage.category}
              onChange={e => setNewPage({...newPage, category: e.target.value})}
              style={{ marginBottom: 20 }}
              data-testid="page-category-input"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={createPage} data-testid="submit-page-btn">Create Page</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== MAP PAGE ====================
const MapPage = ({ showToast, setCurrentPage }) => {
  const { user, token } = useAuth();
  const [mapResults, setMapResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hoveredResult, setHoveredResult] = useState(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  const mapContainerRef = useRef(null);

  // Known locations for context-based geocoding
  const KNOWN_LOCATIONS = {
    'texas': { lat: 31.9686, lng: -99.9018 },
    'california': { lat: 36.7783, lng: -119.4179 },
    'new york': { lat: 40.7128, lng: -74.0060 },
    'florida': { lat: 27.6648, lng: -81.5158 },
    'washington': { lat: 47.7511, lng: -120.7401 },
    'washington dc': { lat: 38.9072, lng: -77.0369 },
    'virginia': { lat: 37.4316, lng: -78.6569 },
    'houston': { lat: 29.7604, lng: -95.3698 },
    'midland': { lat: 31.9973, lng: -102.0779 },
    'new haven': { lat: 41.3083, lng: -72.9279 },
    'yale': { lat: 41.3163, lng: -72.9223 },
    'gettysburg': { lat: 39.8309, lng: -77.2311 },
    'united states': { lat: 39.8283, lng: -98.5795 },
    'usa': { lat: 39.8283, lng: -98.5795 },
    'america': { lat: 39.8283, lng: -98.5795 },
    'england': { lat: 51.5074, lng: -0.1278 },
    'france': { lat: 46.2276, lng: 2.2137 },
    'germany': { lat: 51.1657, lng: 10.4515 },
    'air force': { lat: 38.8719, lng: -77.0563 },
    'pentagon': { lat: 38.8719, lng: -77.0563 },
    'white house': { lat: 38.8977, lng: -77.0365 },
  };

  const extractLocation = (text, title) => {
    if (!text && !title) return null;
    const combined = `${title || ''} ${text || ''}`.toLowerCase();
    for (const [place, coords] of Object.entries(KNOWN_LOCATIONS)) {
      if (combined.includes(place)) {
        return {
          lat: coords.lat + (Math.random() - 0.5) * 1.5,
          lng: coords.lng + (Math.random() - 0.5) * 1.5,
          place: place
        };
      }
    }
    return null;
  };

  useEffect(() => {
    fetchMapResults();
  }, []);

  const fetchMapResults = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/ultimate-search?limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const resultsWithLocation = data.results
          .map((r, idx) => {
            if (r.latitude && r.longitude && 
                r.latitude >= -90 && r.latitude <= 90 &&
                r.longitude >= -180 && r.longitude <= 180) {
              return { ...r, hasRealLocation: true, hashtags: extractHashtags(r.title, r.snippet, r.article_type) };
            }
            const extracted = extractLocation(r.content || r.snippet, r.title);
            if (extracted) {
              return { 
                ...r, 
                latitude: extracted.lat, 
                longitude: extracted.lng, 
                extractedPlace: extracted.place,
                hashtags: extractHashtags(r.title, r.snippet, r.article_type)
              };
            }
            return null;
          })
          .filter(r => r !== null);
        setMapResults(resultsWithLocation);
      }
    } catch (e) {
      console.error('Failed to fetch map results:', e);
    }
    setLoading(false);
  };

  const getMarkerColor = (articleType) => {
    const colors = {
      'News Article': '#ef4444',
      'Blog Post': '#f97316',
      'Academic Paper': '#3b82f6',
      'Wiki': '#10b981',
      'Forum': '#8b5cf6',
      'Government': '#06b6d4',
      'Video': '#ec4899',
      'Unknown': '#6b7280'
    };
    return colors[articleType] || colors['Unknown'];
  };

  // Create custom colored marker icon
  const createCustomIcon = (color) => {
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        width: 24px;
        height: 24px;
        background: ${color};
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 0 10px ${color}, 0 2px 6px rgba(0,0,0,0.4);
        cursor: pointer;
      "></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
      popupAnchor: [0, -12]
    });
  };

  // Handle marker click - open URL in new tab
  const handleMarkerClick = (result) => {
    if (result.url) {
      window.open(result.url, '_blank', 'noopener,noreferrer');
    }
  };

  // Handle marker hover
  const handleMarkerHover = (result, event) => {
    if (mapContainerRef.current) {
      const rect = mapContainerRef.current.getBoundingClientRect();
      const x = event.originalEvent.clientX - rect.left;
      const y = event.originalEvent.clientY - rect.top;
      setHoverPosition({ x, y });
    }
    setHoveredResult(result);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>🗺️ Interactive World Map</h2>
        <span style={{ color: '#10b981', fontSize: '0.9rem' }}>
          {mapResults.length} results mapped • Click markers to open articles
        </span>
      </div>

      {/* Legend */}
      <div style={{ 
        display: 'flex', gap: 15, flexWrap: 'wrap', marginBottom: 15,
        padding: 10, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10
      }}>
        {[
          { type: 'News Article', color: '#ef4444' },
          { type: 'Blog Post', color: '#f97316' },
          { type: 'Academic Paper', color: '#3b82f6' },
          { type: 'Wiki', color: '#10b981' },
          { type: 'Forum', color: '#8b5cf6' },
          { type: 'Government', color: '#06b6d4' }
        ].map(({ type, color }) => (
          <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: color, boxShadow: `0 0 5px ${color}` }} />
            <span style={{ fontSize: '0.75rem', color: '#a1a1aa' }}>{type}</span>
          </div>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <div className="loading-spinner"><div className="spinner"></div></div>
          <p style={{ color: '#a1a1aa', marginTop: 15 }}>Loading map data...</p>
        </div>
      ) : mapResults.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <p style={{ color: '#a1a1aa', fontSize: '1.1rem' }}>
            No mapped results yet. Search and collate content to see results on the map!
          </p>
          <button className="btn btn-primary" style={{ marginTop: 15 }} onClick={() => setCurrentPage('search')}>
            Go to Ultimate Search
          </button>
        </div>
      ) : (
        <>
          {/* React-Leaflet Map with hover popups */}
          <div 
            ref={mapContainerRef}
            style={{ 
              height: 450, borderRadius: 12, overflow: 'hidden',
              border: '2px solid rgba(124, 58, 237, 0.3)',
              position: 'relative'
            }}
          >
            <MapContainer
              center={[39.8283, -98.5795]}
              zoom={4}
              style={{ height: '100%', width: '100%' }}
              scrollWheelZoom={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mapResults.slice(0, 50).map((result, idx) => (
                <Marker
                  key={result.id || `marker-${idx}`}
                  position={[result.latitude, result.longitude]}
                  icon={createCustomIcon(getMarkerColor(result.article_type))}
                  eventHandlers={{
                    click: () => handleMarkerClick(result),
                    mouseover: (e) => handleMarkerHover(result, e),
                    mouseout: () => setHoveredResult(null)
                  }}
                />
              ))}
            </MapContainer>

            {/* Hover Popup Window */}
            {hoveredResult && (
              <div 
                style={{
                  position: 'absolute',
                  left: Math.min(hoverPosition.x + 15, mapContainerRef.current?.clientWidth - 320 || 0),
                  top: Math.max(hoverPosition.y - 150, 10),
                  width: 300,
                  background: 'rgba(15, 10, 35, 0.98)',
                  borderRadius: 12,
                  border: `2px solid ${getMarkerColor(hoveredResult.article_type)}`,
                  boxShadow: `0 8px 32px rgba(0,0,0,0.6), 0 0 20px ${getMarkerColor(hoveredResult.article_type)}40`,
                  zIndex: 1000,
                  pointerEvents: 'auto',
                  overflow: 'hidden'
                }}
              >
                {/* Header */}
                <div style={{
                  padding: '10px 12px',
                  background: `linear-gradient(135deg, ${getMarkerColor(hoveredResult.article_type)}30, transparent)`,
                  borderBottom: '1px solid rgba(255,255,255,0.1)'
                }}>
                  <span style={{
                    background: getMarkerColor(hoveredResult.article_type),
                    padding: '3px 8px', borderRadius: 10,
                    fontSize: '0.65rem', fontWeight: 600, color: '#fff'
                  }}>
                    {hoveredResult.article_type}
                  </span>
                  {hoveredResult.extractedPlace && (
                    <span style={{ color: '#10b981', fontSize: '0.7rem', marginLeft: 8 }}>
                      📍 {hoveredResult.extractedPlace.charAt(0).toUpperCase() + hoveredResult.extractedPlace.slice(1)}
                    </span>
                  )}
                </div>
                
                {/* Content */}
                <div style={{ padding: 12 }}>
                  <h4 style={{ color: '#fff', margin: '0 0 8px 0', fontSize: '0.85rem', lineHeight: 1.3 }}>
                    {hoveredResult.title?.substring(0, 70) || 'Untitled'}...
                  </h4>
                  <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: '0 0 8px 0', lineHeight: 1.4 }}>
                    {hoveredResult.snippet?.substring(0, 120) || 'No description'}...
                  </p>
                  
                  {/* Hashtags */}
                  {hoveredResult.hashtags && (
                    <HashtagDisplay hashtags={hoveredResult.hashtags} small={true} />
                  )}
                  
                  {/* Click instruction */}
                  <div style={{ 
                    marginTop: 10, padding: '6px 10px', 
                    background: `${getMarkerColor(hoveredResult.article_type)}30`,
                    borderRadius: 6, textAlign: 'center'
                  }}>
                    <span style={{ color: '#fff', fontSize: '0.7rem', fontWeight: 600 }}>
                      🖱️ Click marker to open article
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results list with hashtags */}
          <div style={{ marginTop: 20 }}>
            <h3 style={{ color: '#f472b6', marginBottom: 15 }}>📍 Mapped Results ({mapResults.length})</h3>
            <div style={{ 
              display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: 12, maxHeight: 400, overflowY: 'auto'
            }}>
              {mapResults.slice(0, 20).map((result, idx) => (
                <div 
                  key={result.id || `result-${idx}`}
                  data-testid={`map-result-${idx}`}
                  style={{
                    padding: 12,
                    background: 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 10,
                    border: '1px solid rgba(124, 58, 237, 0.2)',
                    cursor: 'pointer', transition: 'all 0.2s'
                  }}
                  onClick={() => window.open(result.url, '_blank', 'noopener,noreferrer')}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = getMarkerColor(result.article_type)}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = 'rgba(124, 58, 237, 0.2)'}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <div style={{
                      width: 10, height: 10, borderRadius: '50%',
                      background: getMarkerColor(result.article_type),
                      boxShadow: `0 0 6px ${getMarkerColor(result.article_type)}`
                    }} />
                    <span style={{ color: getMarkerColor(result.article_type), fontSize: '0.7rem', fontWeight: 600 }}>
                      {result.article_type}
                    </span>
                    {result.extractedPlace && (
                      <span style={{ color: '#10b981', fontSize: '0.65rem', marginLeft: 'auto' }}>
                        📍 {result.extractedPlace.charAt(0).toUpperCase() + result.extractedPlace.slice(1)}
                      </span>
                    )}
                  </div>
                  <div style={{ color: '#fff', fontWeight: 600, fontSize: '0.85rem', marginBottom: 5, lineHeight: 1.3 }}>
                    {result.title?.substring(0, 60) || 'Untitled'}...
                  </div>
                  <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: '0 0 8px 0', lineHeight: 1.4 }}>
                    {result.snippet?.substring(0, 80) || ''}...
                  </p>
                  {/* Hashtags */}
                  {result.hashtags && <HashtagDisplay hashtags={result.hashtags} small={true} />}
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      <p style={{ marginTop: 20, color: '#a1a1aa', fontSize: '0.85rem', textAlign: 'center' }}>
        💡 Hover over markers to preview details. Click any marker to open the article in a new tab!
      </p>
    </div>
  );
};


// ==================== PROTOCOL MARKETPLACE PAGE ====================
const MarketplacePage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [protocols, setProtocols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('browse'); // browse, sell, purchases, dashboard
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [sortBy, setSortBy] = useState('popular');
  
  // Sell form state
  const [newProtocol, setNewProtocol] = useState({
    name: '', description: '', protocol: '', price: 0.99, category: 'General', tags: ''
  });
  
  // Purchase state
  const [purchaseModal, setPurchaseModal] = useState(null);
  const [purchases, setPurchases] = useState([]);
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    fetchProtocols();
    fetchCategories();
    if (token) {
      fetchPurchases();
      fetchDashboard();
    }
  }, [token, selectedCategory, sortBy]);

  const fetchProtocols = async () => {
    try {
      let url = `${API}/marketplace/protocols?sort=${sortBy}`;
      if (selectedCategory) url += `&category=${selectedCategory}`;
      
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await res.json();
      setProtocols(data.protocols || []);
    } catch (e) {
      console.error('Failed to fetch protocols:', e);
    }
    setLoading(false);
  };

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API}/marketplace/categories`);
      const data = await res.json();
      setCategories(data.categories || []);
    } catch (e) {
      console.error('Failed to fetch categories:', e);
    }
  };

  const fetchPurchases = async () => {
    try {
      const res = await fetch(`${API}/marketplace/purchases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setPurchases(data.purchases || []);
    } catch (e) {
      console.error('Failed to fetch purchases:', e);
    }
  };

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API}/marketplace/seller/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setDashboard(data);
    } catch (e) {
      console.error('Failed to fetch dashboard:', e);
    }
  };

  const handleListProtocol = async () => {
    if (!newProtocol.name || !newProtocol.protocol || !newProtocol.description) {
      showToast('Please fill in all required fields', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/marketplace/protocols`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...newProtocol,
          tags: newProtocol.tags.split(',').map(t => t.trim()).filter(t => t)
        })
      });

      const data = await res.json();
      
      if (res.ok) {
        showToast('Protocol listed successfully!', 'success');
        setNewProtocol({ name: '', description: '', protocol: '', price: 0.99, category: 'General', tags: '' });
        fetchProtocols();
        fetchDashboard();
        setActiveTab('dashboard');
      } else {
        showToast(data.detail || 'Failed to list protocol', 'error');
      }
    } catch (e) {
      showToast('Failed to list protocol', 'error');
    }
  };

  const handlePurchase = async (protocol) => {
    try {
      // Initiate purchase on backend
      const res = await fetch(`${API}/marketplace/initiate-purchase`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ protocol_id: protocol.id })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        // Open PayPal payment in new window
        window.open(data.payment_url, '_blank', 'width=600,height=700');
        
        // Show confirmation modal with pending info
        setPurchaseModal({
          protocol,
          pending_id: data.pending_id,
          payment_url: data.payment_url,
          step: 'confirm'
        });
      } else {
        showToast(data.detail || 'Failed to initiate purchase', 'error');
      }
    } catch (e) {
      showToast('Failed to initiate purchase', 'error');
    }
  };

  const confirmPurchase = async () => {
    if (!purchaseModal) return;
    
    // Prompt for transaction ID
    const transactionId = prompt('Please enter your PayPal Transaction ID (found in your PayPal receipt):');
    if (!transactionId) {
      showToast('Transaction ID is required', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/marketplace/confirm-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          protocol_id: purchaseModal.protocol.id,
          transaction_id: transactionId,
          amount: purchaseModal.protocol.price
        })
      });

      const data = await res.json();
      
      if (res.ok) {
        showToast('🎉 Protocol purchased successfully! +10 XP', 'success');
        setPurchaseModal(null);
        fetchProtocols();
        fetchPurchases();
      } else {
        showToast(data.detail || 'Purchase confirmation failed', 'error');
      }
    } catch (e) {
      showToast('Purchase confirmation failed', 'error');
    }
  };

  const renderStars = (rating) => {
    return '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
  };

  return (
    <div className="card" data-testid="marketplace-page">
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Shop />
          Protocol Marketplace
        </h2>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Buy and sell search protocols • 90% to creators
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {['browse', 'sell', 'purchases', 'dashboard'].map(tab => (
          <button
            key={tab}
            className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab(tab)}
            data-testid={`marketplace-tab-${tab}`}
          >
            {tab === 'browse' && '🔍 Browse'}
            {tab === 'sell' && '💰 Sell Protocol'}
            {tab === 'purchases' && '📦 My Purchases'}
            {tab === 'dashboard' && '📊 Seller Dashboard'}
          </button>
        ))}
      </div>

      {/* Browse Tab */}
      {activeTab === 'browse' && (
        <div>
          {/* Filters */}
          <div style={{ display: 'flex', gap: 15, marginBottom: 20, flexWrap: 'wrap' }}>
            <select
              className="input"
              style={{ flex: 1, minWidth: 150 }}
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              data-testid="marketplace-category-filter"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat.name} value={cat.name}>{cat.name} ({cat.count})</option>
              ))}
            </select>
            <select
              className="input"
              style={{ flex: 1, minWidth: 150 }}
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              data-testid="marketplace-sort"
            >
              <option value="popular">Most Popular</option>
              <option value="newest">Newest</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
              <option value="rating">Highest Rated</option>
            </select>
          </div>

          {/* Protocol Grid */}
          {loading ? (
            <p style={{ textAlign: 'center', color: '#a1a1aa' }}>Loading protocols...</p>
          ) : protocols.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>No protocols listed yet. Be the first to sell!</p>
              <button className="btn btn-primary" onClick={() => setActiveTab('sell')}>
                List Your Protocol
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
              {protocols.map(protocol => (
                <div 
                  key={protocol.id}
                  style={{
                    background: 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 12,
                    padding: 20,
                    border: protocol.is_featured ? '2px solid #f472b6' : '1px solid rgba(124, 58, 237, 0.3)',
                    position: 'relative'
                  }}
                  data-testid={`protocol-card-${protocol.id}`}
                >
                  {protocol.is_featured && (
                    <span style={{
                      position: 'absolute', top: -10, right: 10,
                      background: '#f472b6', color: '#fff', padding: '4px 10px',
                      borderRadius: 20, fontSize: '0.7rem', fontWeight: 700
                    }}>
                      FEATURED
                    </span>
                  )}
                  
                  <h3 style={{ color: '#f472b6', marginBottom: 8 }}>{protocol.name}</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 10 }}>
                    {protocol.description.substring(0, 100)}...
                  </p>
                  
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
                    <span style={{ background: 'rgba(124, 58, 237, 0.2)', color: '#a78bfa', padding: '3px 8px', borderRadius: 10, fontSize: '0.75rem' }}>
                      {protocol.category}
                    </span>
                    {protocol.tags?.slice(0, 2).map(tag => (
                      <span key={tag} style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', padding: '3px 8px', borderRadius: 10, fontSize: '0.75rem' }}>
                        {tag}
                      </span>
                    ))}
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
                    <div>
                      <span style={{ color: '#fbbf24' }}>{renderStars(protocol.rating)}</span>
                      <span style={{ color: '#a1a1aa', fontSize: '0.8rem', marginLeft: 5 }}>({protocol.review_count})</span>
                    </div>
                    <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{protocol.total_sales} sales</span>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#10b981', fontSize: '1.3rem', fontWeight: 700 }}>${protocol.price.toFixed(2)}</span>
                    {protocol.is_owned ? (
                      <span style={{ color: '#10b981', fontSize: '0.9rem' }}>✓ Owned</span>
                    ) : (
                      <button 
                        className="btn btn-primary"
                        onClick={() => handlePurchase(protocol)}
                        data-testid={`buy-protocol-${protocol.id}`}
                      >
                        Buy Now
                      </button>
                    )}
                  </div>
                  
                  <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
                    by {protocol.creator_name}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sell Tab */}
      {activeTab === 'sell' && (
        <div style={{ maxWidth: 600 }}>
          <div style={{ 
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))',
            padding: 20, borderRadius: 12, marginBottom: 20
          }}>
            <h3 style={{ color: '#10b981', marginBottom: 10 }}>💰 Earn Money from Your Protocols!</h3>
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
              List your search protocols and earn <strong>90%</strong> of every sale. 
              Set your own price between $0.99 - $99.99.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            <input
              className="input"
              placeholder="Protocol Name *"
              value={newProtocol.name}
              onChange={(e) => setNewProtocol({ ...newProtocol, name: e.target.value })}
              data-testid="protocol-name-input"
            />
            <textarea
              className="input"
              placeholder="Description - Explain what your protocol searches for *"
              rows={3}
              value={newProtocol.description}
              onChange={(e) => setNewProtocol({ ...newProtocol, description: e.target.value })}
              data-testid="protocol-description-input"
            />
            <textarea
              className="input"
              placeholder="Protocol String - e.g. (climate or weather) & (data or statistics)+ *"
              rows={2}
              value={newProtocol.protocol}
              onChange={(e) => setNewProtocol({ ...newProtocol, protocol: e.target.value })}
              data-testid="protocol-string-input"
            />
            <div style={{ display: 'flex', gap: 15 }}>
              <div style={{ flex: 1 }}>
                <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Price (USD)</label>
                <input
                  className="input"
                  type="number"
                  min="0.99"
                  max="99.99"
                  step="0.01"
                  value={newProtocol.price}
                  onChange={(e) => setNewProtocol({ ...newProtocol, price: parseFloat(e.target.value) || 0.99 })}
                  data-testid="protocol-price-input"
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Category</label>
                <select
                  className="input"
                  value={newProtocol.category}
                  onChange={(e) => setNewProtocol({ ...newProtocol, category: e.target.value })}
                  data-testid="protocol-category-input"
                >
                  <option>General</option>
                  <option>News & Media</option>
                  <option>Science & Research</option>
                  <option>Business & Finance</option>
                  <option>Technology</option>
                  <option>Health & Medical</option>
                  <option>Education</option>
                  <option>Entertainment</option>
                </select>
              </div>
            </div>
            <input
              className="input"
              placeholder="Tags (comma separated)"
              value={newProtocol.tags}
              onChange={(e) => setNewProtocol({ ...newProtocol, tags: e.target.value })}
              data-testid="protocol-tags-input"
            />
            <button className="btn btn-primary" onClick={handleListProtocol} data-testid="list-protocol-btn">
              List Protocol for Sale
            </button>
          </div>
        </div>
      )}

      {/* Purchases Tab */}
      {activeTab === 'purchases' && (
        <div>
          {purchases.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>You haven't purchased any protocols yet.</p>
              <button className="btn btn-primary" onClick={() => setActiveTab('browse')}>
                Browse Marketplace
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              {purchases.map(purchase => (
                <div 
                  key={purchase.id}
                  style={{
                    background: 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 12,
                    padding: 20,
                    border: '1px solid rgba(16, 185, 129, 0.3)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div>
                      <h3 style={{ color: '#f472b6', marginBottom: 5 }}>{purchase.name}</h3>
                      <span style={{ color: '#71717a', fontSize: '0.8rem' }}>{purchase.category}</span>
                    </div>
                    <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                      Purchased: {new Date(purchase.purchased_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div style={{ 
                    marginTop: 15, padding: 15, 
                    background: 'rgba(16, 185, 129, 0.1)', 
                    borderRadius: 8,
                    fontFamily: 'monospace',
                    color: '#10b981'
                  }}>
                    {purchase.protocol}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <div>
          {dashboard && (
            <>
              {/* Stats Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 15, marginBottom: 25 }}>
                <div style={{ background: 'rgba(124, 58, 237, 0.2)', padding: 20, borderRadius: 12, textAlign: 'center' }}>
                  <div style={{ color: '#a78bfa', fontSize: '2rem', fontWeight: 700 }}>{dashboard.total_listings}</div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Listings</div>
                </div>
                <div style={{ background: 'rgba(236, 72, 153, 0.2)', padding: 20, borderRadius: 12, textAlign: 'center' }}>
                  <div style={{ color: '#f472b6', fontSize: '2rem', fontWeight: 700 }}>{dashboard.total_sales}</div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Total Sales</div>
                </div>
                <div style={{ background: 'rgba(16, 185, 129, 0.2)', padding: 20, borderRadius: 12, textAlign: 'center' }}>
                  <div style={{ color: '#10b981', fontSize: '2rem', fontWeight: 700 }}>${dashboard.total_earnings?.toFixed(2) || '0.00'}</div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Your Earnings (90%)</div>
                </div>
              </div>

              {/* Listings */}
              <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Your Listings</h3>
              {dashboard.listings?.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 30, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
                  <p style={{ color: '#a1a1aa', marginBottom: 15 }}>You haven't listed any protocols yet.</p>
                  <button className="btn btn-primary" onClick={() => setActiveTab('sell')}>
                    Create Your First Listing
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {dashboard.listings?.map(listing => (
                    <div 
                      key={listing.id}
                      style={{
                        background: 'rgba(30, 20, 50, 0.5)',
                        borderRadius: 10,
                        padding: 15,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <h4 style={{ color: '#fff', marginBottom: 5 }}>{listing.name}</h4>
                        <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                          ${listing.price.toFixed(2)} • {listing.sales} sales • ${listing.earnings?.toFixed(2) || '0.00'} earned
                        </span>
                      </div>
                      <span style={{ 
                        color: listing.status === 'active' ? '#10b981' : '#f59e0b',
                        fontSize: '0.8rem',
                        textTransform: 'uppercase'
                      }}>
                        {listing.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Purchase Confirmation Modal */}
      {purchaseModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
            borderRadius: 20, padding: 30, maxWidth: 450, width: '90%',
            border: '2px solid rgba(124, 58, 237, 0.5)'
          }}>
            <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Confirm Purchase</h3>
            <p style={{ color: '#fff', marginBottom: 10 }}>
              <strong>{purchaseModal.protocol.name}</strong>
            </p>
            <p style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700, marginBottom: 20 }}>
              ${purchaseModal.protocol.price.toFixed(2)}
            </p>
            
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 20 }}>
              Please complete your PayPal payment, then click "Confirm Purchase" below.
            </p>
            
            <div style={{ display: 'flex', gap: 10 }}>
              <button 
                className="btn btn-secondary" 
                onClick={() => setPurchaseModal(null)}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                onClick={confirmPurchase}
                style={{ flex: 1 }}
                data-testid="confirm-purchase-btn"
              >
                Confirm Purchase
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== ACHIEVEMENTS PAGE ====================
const AchievementsPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [allBadges, setAllBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile'); // profile, badges, leaderboard

  useEffect(() => {
    fetchData();
    trackLogin();
  }, [token]);

  const fetchData = async () => {
    try {
      const [profileRes, leaderboardRes, badgesRes] = await Promise.all([
        fetch(`${API}/gamification/profile`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/gamification/leaderboard`),
        fetch(`${API}/gamification/badges`)
      ]);

      const profileData = await profileRes.json();
      const leaderboardData = await leaderboardRes.json();
      const badgesData = await badgesRes.json();

      setProfile(profileData);
      setLeaderboard(leaderboardData.leaderboard || []);
      setAllBadges(badgesData.badges || []);

      // Show new badges notification
      if (profileData.new_badges?.length > 0) {
        profileData.new_badges.forEach(badge => {
          showToast(`🎉 New Badge Earned: ${badge.icon} ${badge.name}!`, 'success');
        });
      }
    } catch (e) {
      console.error('Failed to fetch gamification data:', e);
    }
    setLoading(false);
  };

  const trackLogin = async () => {
    try {
      await fetch(`${API}/gamification/track-login`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (e) {
      console.error('Failed to track login');
    }
  };

  const getRarityColor = (rarity) => {
    switch (rarity) {
      case 'legendary': return 'linear-gradient(135deg, #fbbf24, #f59e0b)';
      case 'rare': return 'linear-gradient(135deg, #a78bfa, #7c3aed)';
      case 'uncommon': return 'linear-gradient(135deg, #34d399, #10b981)';
      default: return 'linear-gradient(135deg, #94a3b8, #64748b)';
    }
  };

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 60 }}>
        <div className="spinner" style={{ margin: '0 auto' }}></div>
        <p style={{ color: '#a1a1aa', marginTop: 20 }}>Loading achievements...</p>
      </div>
    );
  }

  return (
    <div className="card" data-testid="achievements-page">
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Trophy />
          Achievements & Rewards
        </h2>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Earn badges, gain XP, and climb the leaderboard!
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 25 }}>
        {['profile', 'badges', 'leaderboard'].map(tab => (
          <button
            key={tab}
            className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab(tab)}
            data-testid={`achievements-tab-${tab}`}
          >
            {tab === 'profile' && '👤 My Progress'}
            {tab === 'badges' && '🏅 All Badges'}
            {tab === 'leaderboard' && '🏆 Leaderboard'}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && profile && (
        <div>
          {/* Level & XP Card */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.3), rgba(236, 72, 153, 0.3))',
            borderRadius: 16,
            padding: 25,
            marginBottom: 25,
            border: '1px solid rgba(124, 58, 237, 0.5)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
              <div>
                <h3 style={{ color: '#fff', fontSize: '1.8rem', marginBottom: 5 }}>
                  Level {profile.level?.level || 1}
                </h3>
                <p style={{ color: '#a1a1aa' }}>{profile.username}</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: '#fbbf24', fontSize: '1.5rem', fontWeight: 700 }}>
                  {profile.level?.total_xp || 0} XP
                </div>
                <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                  Rank #{profile.rank?.position || '?'} (Top {profile.rank?.percentile || 0}%)
                </p>
              </div>
            </div>

            {/* XP Progress Bar */}
            <div style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#a1a1aa', marginBottom: 5 }}>
                <span>Progress to Level {(profile.level?.level || 1) + 1}</span>
                <span>{profile.level?.current_xp || 0} / {profile.level?.xp_for_next_level || 100} XP</span>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 10, height: 12, overflow: 'hidden' }}>
                <div style={{
                  background: 'linear-gradient(90deg, #f472b6, #a78bfa)',
                  height: '100%',
                  width: `${profile.level?.progress_percent || 0}%`,
                  borderRadius: 10,
                  transition: 'width 0.5s ease'
                }} />
              </div>
            </div>

            {/* Login Streak */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 15 }}>
              <span style={{ fontSize: '1.2rem' }}>🔥</span>
              <span style={{ color: '#ef4444', fontWeight: 600 }}>{profile.stats?.login_streak || 0} day streak</span>
            </div>
          </div>

          {/* Stats Grid */}
          <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Your Stats</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 25 }}>
            {[
              { label: 'Searches', value: profile.stats?.searches || 0, icon: '🔍' },
              { label: 'Protocols Created', value: profile.stats?.protocols_created || 0, icon: '📝' },
              { label: 'Protocols Sold', value: profile.stats?.protocols_sold || 0, icon: '💰' },
              { label: 'Protocols Bought', value: profile.stats?.protocols_purchased || 0, icon: '🛒' },
              { label: 'Friends', value: profile.stats?.friends || 0, icon: '👥' },
              { label: 'Reviews', value: profile.stats?.reviews || 0, icon: '⭐' }
            ].map(stat => (
              <div key={stat.label} style={{
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                padding: 15,
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '1.5rem', marginBottom: 5 }}>{stat.icon}</div>
                <div style={{ color: '#fff', fontSize: '1.3rem', fontWeight: 700 }}>{stat.value}</div>
                <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>{stat.label}</div>
              </div>
            ))}
          </div>

          {/* My Badges */}
          <h3 style={{ color: '#f472b6', marginBottom: 15 }}>My Badges ({profile.badges?.length || 0})</h3>
          {profile.badges?.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 30, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa' }}>No badges yet. Start exploring to earn your first badge!</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
              {profile.badges?.map(badge => (
                <div
                  key={badge.id}
                  style={{
                    background: getRarityColor(badge.rarity),
                    borderRadius: 12,
                    padding: '12px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    minWidth: 180
                  }}
                  title={badge.description}
                >
                  <span style={{ fontSize: '1.5rem' }}>{badge.icon}</span>
                  <div>
                    <div style={{ color: '#fff', fontWeight: 600, fontSize: '0.9rem' }}>{badge.name}</div>
                    <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.7rem', textTransform: 'uppercase' }}>{badge.rarity}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* All Badges Tab */}
      {activeTab === 'badges' && (
        <div>
          <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
            Collect all badges by completing various activities on InfoPilot!
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 15 }}>
            {allBadges.map(badge => {
              const isEarned = profile?.badges?.some(b => b.id === badge.id);
              return (
                <div
                  key={badge.id}
                  style={{
                    background: isEarned ? getRarityColor(badge.rarity) : 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 12,
                    padding: 20,
                    opacity: isEarned ? 1 : 0.6,
                    border: isEarned ? 'none' : '1px dashed rgba(124, 58, 237, 0.3)',
                    position: 'relative'
                  }}
                >
                  {isEarned && (
                    <span style={{
                      position: 'absolute',
                      top: -8,
                      right: -8,
                      background: '#10b981',
                      color: '#fff',
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.8rem'
                    }}>✓</span>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: '2rem', filter: isEarned ? 'none' : 'grayscale(1)' }}>{badge.icon}</span>
                    <div>
                      <div style={{ color: '#fff', fontWeight: 600 }}>{badge.name}</div>
                      <div style={{ color: isEarned ? 'rgba(255,255,255,0.8)' : '#71717a', fontSize: '0.8rem', marginTop: 3 }}>
                        {badge.description}
                      </div>
                      <div style={{ 
                        color: isEarned ? 'rgba(255,255,255,0.6)' : '#52525b', 
                        fontSize: '0.7rem', 
                        textTransform: 'uppercase',
                        marginTop: 5
                      }}>
                        {badge.rarity}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div>
          <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
            Top InfoPilot users ranked by XP
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {leaderboard.map((entry, index) => {
              const isCurrentUser = entry.user_id === profile?.user_id;
              return (
                <div
                  key={entry.user_id}
                  style={{
                    background: isCurrentUser 
                      ? 'linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(124, 58, 237, 0.3))'
                      : 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 12,
                    padding: '15px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 15,
                    border: isCurrentUser ? '2px solid #f472b6' : '1px solid rgba(124, 58, 237, 0.2)'
                  }}
                >
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '1.1rem',
                    background: index === 0 ? '#fbbf24' : index === 1 ? '#94a3b8' : index === 2 ? '#cd7f32' : 'rgba(124, 58, 237, 0.3)',
                    color: index < 3 ? '#000' : '#fff'
                  }}>
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : entry.rank}
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#fff', fontWeight: 600 }}>
                      {entry.username}
                      {isCurrentUser && <span style={{ color: '#f472b6', marginLeft: 8, fontSize: '0.8rem' }}>(You)</span>}
                    </div>
                    <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                      Level {entry.level} • {entry.badge_count} badges
                    </div>
                  </div>
                  
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: '#fbbf24', fontWeight: 700 }}>{entry.xp.toLocaleString()} XP</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== BOOK PROMOTION BANNER (Enhanced with Funny Images) ====================
const BOOK_IMAGES = [
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/024v1r34_Letters%20to%20Evelyn%20advertisement%201.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/e90a1rlq_Letters%20to%20Evelyn%20advertisement%202.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/ccdegcr8_Letters%20to%20Evelyn%20advertisement%203.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/3gqu0i0v_Letters%20to%20Evelyn%20advertisement%204.jpg"
];

const FUNNY_TAGLINES = [
  { image: 0, text: "WROTE A BOOK. UNIVERSE FACT-CHECKED IT. IT PASSED.", subtext: "Now it's YOUR turn to verify!" },
  { image: 1, text: "THERAPIST: THIS IS A LOT TO UNPACK.", subtext: "Bring snacks. Possibly a helmet." },
  { image: 2, text: "I FLEW JETS. THEN REALITY BROKE.", subtext: "Navy pilot meets cosmic chaos." },
  { image: 3, text: "TERROR OF THE COSMIC GULPER", subtext: "A comedy of galactic proportions!" }
];

const BookPromoBanner = () => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % BOOK_IMAGES.length);
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  const currentTagline = FUNNY_TAGLINES[currentImageIndex];

  return (
    <div data-testid="book-promo-banner" style={{
      background: 'linear-gradient(135deg, rgba(20, 10, 40, 0.98), rgba(80, 20, 100, 0.95))',
      borderRadius: 20,
      padding: 0,
      marginBottom: 25,
      border: '3px solid rgba(236, 72, 153, 0.7)',
      overflow: 'hidden',
      boxShadow: '0 25px 80px rgba(124, 58, 237, 0.5)'
    }}>
      {/* Animated Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #7c3aed, #ec4899, #f97316)',
        padding: '18px 25px',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Shimmer effect */}
        <div style={{
          position: 'absolute',
          top: 0, left: '-100%', right: 0, bottom: 0,
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
          animation: 'shimmer 3s infinite'
        }} />
        
        <div style={{
          position: 'absolute',
          top: 8,
          right: 15,
          background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
          color: '#000',
          padding: '6px 18px',
          borderRadius: 20,
          fontWeight: 800,
          fontSize: '0.8rem',
          boxShadow: '0 4px 20px rgba(251, 191, 36, 0.6)',
          animation: 'pulse 2s infinite'
        }}>
          🎬 OPTIONED FOR FILM!
        </div>
        
        <div style={{
          fontSize: '1.6rem',
          fontWeight: 900,
          color: '#fff',
          textShadow: '2px 2px 8px rgba(0,0,0,0.4)',
          letterSpacing: '1px',
          transition: 'all 0.5s'
        }}>
          {currentTagline.text}
        </div>
        <div style={{
          fontSize: '1rem',
          color: 'rgba(255,255,255,0.95)',
          marginTop: 5,
          fontWeight: 600,
          fontStyle: 'italic'
        }}>
          {currentTagline.subtext}
        </div>
      </div>

      {/* Main Content */}
      <div style={{
        display: 'flex',
        gap: 30,
        padding: 25,
        flexWrap: 'wrap',
        alignItems: 'flex-start'
      }}>
        {/* Book Image with Gallery */}
        <div style={{ flex: '0 0 auto', position: 'relative' }}>
          <div style={{
            width: 250,
            height: 320,
            borderRadius: 15,
            overflow: 'hidden',
            boxShadow: '0 20px 60px rgba(236, 72, 153, 0.6)',
            border: '4px solid rgba(255, 255, 255, 0.25)',
            transition: 'transform 0.3s',
            cursor: 'pointer'
          }}>
            <img 
              src={BOOK_IMAGES[currentImageIndex]} 
              alt="Letters to Evelyn - Funny Promo"
              style={{ width: '100%', height: '100%', objectFit: 'cover', transition: 'all 0.5s' }}
            />
          </div>
          {/* Thumbnail Gallery */}
          <div style={{ 
            display: 'flex', 
            gap: 10, 
            marginTop: 15,
            justifyContent: 'center'
          }}>
            {BOOK_IMAGES.map((img, idx) => (
              <div 
                key={idx}
                onClick={() => setCurrentImageIndex(idx)}
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 10,
                  overflow: 'hidden',
                  cursor: 'pointer',
                  border: idx === currentImageIndex ? '3px solid #ec4899' : '2px solid rgba(255,255,255,0.3)',
                  opacity: idx === currentImageIndex ? 1 : 0.7,
                  transition: 'all 0.3s',
                  boxShadow: idx === currentImageIndex ? '0 0 15px rgba(236, 72, 153, 0.5)' : 'none'
                }}
              >
                <img src={img} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
            ))}
          </div>
        </div>

        {/* Book Details */}
        <div style={{ flex: 1, minWidth: 300 }}>
          <h2 style={{
            fontSize: '2.2rem',
            fontWeight: 900,
            background: 'linear-gradient(135deg, #f472b6, #ec4899, #fbbf24)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: 10,
            letterSpacing: '1px'
          }}>
            LETTERS TO EVELYN
          </h2>
          
          <div style={{ 
            color: '#a78bfa', 
            fontSize: '1.1rem', 
            marginBottom: 8,
            fontWeight: 600
          }}>
            A Supernatural Thriller Comedy Memoir
          </div>
          
          <div style={{ 
            color: '#fbbf24', 
            fontSize: '1rem', 
            marginBottom: 12,
            fontWeight: 700
          }}>
            By World Record Aviation Holder <span style={{ color: '#fff' }}>John Selman</span>
          </div>

          {/* Star Rating */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 15 }}>
            <span style={{ color: '#fbbf24', fontSize: '1.4rem' }}>★★★★★</span>
            <span style={{ color: '#fbbf24', fontWeight: 800, fontSize: '1rem' }}>19 Five-Star Reviews</span>
            <span style={{ 
              background: 'rgba(16, 185, 129, 0.2)', 
              color: '#10b981', 
              padding: '4px 12px', 
              borderRadius: 15,
              fontSize: '0.8rem',
              fontWeight: 700
            }}>
              Readers' Favorite
            </span>
          </div>

          {/* Key Selling Points */}
          <div style={{ marginBottom: 18 }}>
            <div style={{ color: '#f472b6', fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              ✈️ <span>Written by a Navy pilot who flew 10 aircraft types</span>
            </div>
            <div style={{ color: '#a78bfa', fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              👽 <span>Extraterrestrial encounters & cosmic visions</span>
            </div>
            <div style={{ color: '#fbbf24', fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              😂 <span>"Comedy that creeps into your mind and causes abrupt laughter"</span>
            </div>
          </div>

          {/* Review Quote */}
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            padding: 15,
            borderRadius: 12,
            marginBottom: 20,
            borderLeft: '4px solid #10b981'
          }}>
            <div style={{ color: '#10b981', fontStyle: 'italic', fontSize: '0.95rem', lineHeight: 1.5 }}>
              "The comical side is exceedingly brilliant... imagination off the charts. A true story that defies belief!"
            </div>
            <div style={{ 
              color: '#34d399', 
              fontSize: '0.85rem', 
              marginTop: 8, 
              fontWeight: 600
            }}>
              — Professional Review, Readers' Favorite ★★★★★
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 15 }}>
            <a 
              href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191"
              target="_blank"
              rel="noopener noreferrer"
              data-testid="book-buy-amazon"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'linear-gradient(135deg, #ec4899, #f97316)',
                color: 'white',
                padding: '14px 28px',
                borderRadius: 30,
                fontWeight: 800,
                fontSize: '1rem',
                textDecoration: 'none',
                boxShadow: '0 8px 30px rgba(236, 72, 153, 0.5)',
                border: '2px solid rgba(255,255,255,0.2)',
                transition: 'transform 0.2s'
              }}
            >
              🛒 BUY NOW - $2.99
            </a>
            <a 
              href="https://letters-to-evelyn.sintra.site"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(124, 58, 237, 0.3)',
                color: '#a78bfa',
                padding: '14px 24px',
                borderRadius: 30,
                fontWeight: 700,
                fontSize: '1rem',
                textDecoration: 'none',
                border: '2px solid rgba(124, 58, 237, 0.5)'
              }}
            >
              🌐 OFFICIAL SITE
            </a>
            <a 
              href="https://readersfavorite.com/book-review/letters-to-evelyn"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(16, 185, 129, 0.2)',
                color: '#10b981',
                padding: '14px 24px',
                borderRadius: 30,
                fontWeight: 700,
                fontSize: '1rem',
                textDecoration: 'none',
                border: '2px solid rgba(16, 185, 129, 0.5)'
              }}
            >
              ⭐ READ REVIEWS
            </a>
          </div>

          {/* Film Badge */}
          <div style={{
            display: 'inline-block',
            background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.3))',
            padding: '12px 20px',
            borderRadius: 25,
            border: '2px solid rgba(251, 191, 36, 0.6)'
          }}>
            <span style={{ color: '#fbbf24', fontWeight: 800, fontSize: '0.9rem' }}>
              🎬 Hollywood couldn't resist - OPTIONED FOR FILM!
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==================== MAIN APP ====================
const MainApp = () => {
  const { user } = useAuth();
  const [currentPage, setCurrentPage] = useState('search');
  const [toast, setToast] = useState(null);

  const showToast = (message, type) => {
    setToast({ message, type });
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'admin':
        return user?.is_admin ? <AdminPanel showToast={showToast} /> : <UltimateSearchPage showToast={showToast} />;
      case 'search':
        return <UltimateSearchPage showToast={showToast} />;
      case 'marketplace':
        return <MarketplacePage showToast={showToast} />;
      case 'achievements':
        return <AchievementsPage showToast={showToast} />;
      case 'social':
        return <SocialPage showToast={showToast} />;
      case 'map':
        return <MapPage showToast={showToast} setCurrentPage={setCurrentPage} />;
      case 'messages':
        return <MessagesPage showToast={showToast} />;
      case 'settings':
        return <SettingsPage showToast={showToast} setCurrentPage={setCurrentPage} />;
      case 'subscribe':
        return <SubscribePage showToast={showToast} onBack={() => setCurrentPage('settings')} />;
      default:
        return <UltimateSearchPage showToast={showToast} />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <main className="main-content">
        {/* Book Promotion Banner - Always visible */}
        <BookPromoBanner />
        {/* Quote of the Day - Rotating manuscript quotes */}
        <QuoteOfTheDay />
        {renderPage()}
      </main>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

// ==================== APP ROOT ====================
function App() {
  const [authMode, setAuthMode] = useState('login');

  return (
    <AuthProvider>
      <AppContent authMode={authMode} setAuthMode={setAuthMode} />
    </AuthProvider>
  );
}

const AppContent = ({ authMode, setAuthMode }) => {
  const { user, loading } = useAuth();

  // Check for session_id in URL hash (Google OAuth callback)
  // REMINDER: This check must happen synchronously during render, NOT in useEffect
  if (window.location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  if (loading) {
    return (
      <div className="auth-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return authMode === 'login' 
      ? <LoginPage onSwitch={() => setAuthMode('register')} />
      : <RegisterPage onSwitch={() => setAuthMode('login')} />;
  }

  return <MainApp />;
};

export default App;
