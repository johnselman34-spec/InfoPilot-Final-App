import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { extractHashtags } from '../utils/hashtags';
import { Icons, HashtagDisplay, ProtocolDebugger } from '../components/shared';

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
  const [editingCategory, setEditingCategory] = useState(null);
  const [editProtocol, setEditProtocol] = useState('');
  const [showDebugger, setShowDebugger] = useState(false);

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
    
    if (!token) {
      showToast('Session expired. Please log in again.', 'error');
      return;
    }
    
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
      
      const resClone = res.clone();
      
      let data;
      try {
        data = await res.json();
      } catch (jsonError) {
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
            data-testid="search-input"
          />
          <button className="btn btn-primary" onClick={handleSearch} disabled={loading} data-testid="search-btn">
            {loading ? 'Searching...' : 'Search & Collate'}
          </button>
        </div>

        {/* Aggregation Options */}
        <div style={{ display: 'flex', gap: 20, marginBottom: 20, alignItems: 'center', flexWrap: 'wrap' }}>
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
          <button
            className={`btn ${showDebugger ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setShowDebugger(!showDebugger)}
            style={{ marginLeft: 'auto', padding: '8px 16px', fontSize: '0.85rem' }}
            data-testid="toggle-debugger-btn"
          >
            🔧 {showDebugger ? 'Hide' : 'Show'} Protocol Debugger
          </button>
        </div>

        {/* Protocol Debugger */}
        {showDebugger && <ProtocolDebugger showToast={showToast} />}
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
                  {/* Delete button */}
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
                data-testid="category-name-input"
              />
              <textarea
                className="input-field"
                placeholder="Protocol (e.g., (word1 or word2) & (word3)+ )"
                rows={4}
                value={newCategory.protocol}
                onChange={(e) => setNewCategory({ ...newCategory, protocol: e.target.value })}
                style={{ resize: 'vertical' }}
                data-testid="category-protocol-input"
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
              <button className="btn btn-primary" onClick={createCategory} data-testid="create-category-btn">
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

export default UltimateSearchPage;
