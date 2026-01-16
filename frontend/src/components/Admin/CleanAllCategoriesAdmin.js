/**
 * Clean All Categories Admin Dashboard
 * Allows admins to view all categories with result counts and perform bulk cleanup
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

const CleanAllCategoriesAdmin = ({ showToast }) => {
  const { token } = useAuth();
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategories, setSelectedCategories] = useState(new Set());
  const [processing, setProcessing] = useState(false);
  const [sortBy, setSortBy] = useState('results_desc');
  const [filter, setFilter] = useState('all');
  const [totalStats, setTotalStats] = useState({ categories: 0, results: 0, exclusive: 0 });
  
  // Fetch all categories with result counts
  const fetchCategories = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const cats = await res.json();
        
        // Fetch result counts for each category
        const catsWithCounts = await Promise.all(cats.map(async (cat) => {
          try {
            const countRes = await fetch(`${API}/api/categories/${cat.id}/results-count`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            if (countRes.ok) {
              const countData = await countRes.json();
              return { ...cat, ...countData };
            }
          } catch (e) {
            // Ignore count errors
          }
          return { ...cat, total_results: cat.result_count || 0, exclusive_results: 0, shared_results: 0 };
        }));
        
        setCategories(catsWithCounts);
        
        // Calculate totals
        const totals = catsWithCounts.reduce((acc, cat) => ({
          categories: acc.categories + 1,
          results: acc.results + (cat.total_results || 0),
          exclusive: acc.exclusive + (cat.exclusive_results || 0)
        }), { categories: 0, results: 0, exclusive: 0 });
        
        setTotalStats(totals);
      }
    } catch (e) {
      showToast('Failed to fetch categories', 'error');
    }
    setLoading(false);
  }, [token, showToast]);
  
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);
  
  // Sort categories
  const sortedCategories = [...categories].sort((a, b) => {
    switch (sortBy) {
      case 'results_desc':
        return (b.total_results || 0) - (a.total_results || 0);
      case 'results_asc':
        return (a.total_results || 0) - (b.total_results || 0);
      case 'name_asc':
        return a.name.localeCompare(b.name);
      case 'name_desc':
        return b.name.localeCompare(a.name);
      case 'exclusive_desc':
        return (b.exclusive_results || 0) - (a.exclusive_results || 0);
      default:
        return 0;
    }
  }).filter(cat => {
    switch (filter) {
      case 'empty':
        return (cat.total_results || 0) === 0;
      case 'has_results':
        return (cat.total_results || 0) > 0;
      case 'has_exclusive':
        return (cat.exclusive_results || 0) > 0;
      default:
        return true;
    }
  });
  
  // Toggle category selection
  const toggleCategory = (catId) => {
    const newSelected = new Set(selectedCategories);
    if (newSelected.has(catId)) {
      newSelected.delete(catId);
    } else {
      newSelected.add(catId);
    }
    setSelectedCategories(newSelected);
  };
  
  // Select/Deselect all
  const toggleSelectAll = () => {
    if (selectedCategories.size === sortedCategories.length) {
      setSelectedCategories(new Set());
    } else {
      setSelectedCategories(new Set(sortedCategories.map(c => c.id)));
    }
  };
  
  // Bulk clean selected categories
  const bulkCleanCategories = async (mode) => {
    if (selectedCategories.size === 0) {
      showToast('No categories selected', 'error');
      return;
    }
    
    const modeDescriptions = {
      remove: 'remove category tags from',
      delete: 'delete exclusive results from',
      delete_all: 'DELETE ALL results from'
    };
    
    const totalAffected = Array.from(selectedCategories).reduce((sum, catId) => {
      const cat = categories.find(c => c.id === catId);
      return sum + (cat?.total_results || 0);
    }, 0);
    
    if (!window.confirm(
      `Are you sure you want to ${modeDescriptions[mode]} ${selectedCategories.size} categories?\n\n` +
      `This will affect approximately ${totalAffected} search results.\n\n` +
      (mode === 'delete_all' ? '⚠️ THIS CANNOT BE UNDONE!' : '')
    )) return;
    
    setProcessing(true);
    let successCount = 0;
    let errorCount = 0;
    
    for (const catId of selectedCategories) {
      try {
        const res = await fetch(`${API}/api/categories/${catId}/clean?mode=${mode}`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (res.ok) {
          successCount++;
        } else {
          errorCount++;
        }
      } catch (e) {
        errorCount++;
      }
    }
    
    setProcessing(false);
    showToast(
      `Cleaned ${successCount} categories` + (errorCount > 0 ? `, ${errorCount} failed` : ''),
      errorCount > 0 ? 'warning' : 'success'
    );
    
    setSelectedCategories(new Set());
    fetchCategories();
  };
  
  // Clean empty categories (delete categories with 0 results)
  const cleanEmptyCategories = async () => {
    const emptyCategories = categories.filter(c => (c.total_results || 0) === 0);
    
    if (emptyCategories.length === 0) {
      showToast('No empty categories found', 'info');
      return;
    }
    
    if (!window.confirm(
      `Delete ${emptyCategories.length} empty categories (0 results)?\n\n` +
      'This will remove the category definitions themselves, not just results.'
    )) return;
    
    setProcessing(true);
    let successCount = 0;
    
    for (const cat of emptyCategories) {
      try {
        const res = await fetch(`${API}/api/categories/${cat.id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) successCount++;
      } catch (e) {
        // Continue
      }
    }
    
    setProcessing(false);
    showToast(`Deleted ${successCount} empty categories`, 'success');
    fetchCategories();
  };

  return (
    <div className="card" data-testid="clean-all-categories-admin">
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #ef4444, #dc2626)',
        padding: '20px 25px',
        borderRadius: '12px 12px 0 0'
      }}>
        <h2 style={{ color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          🧹 Clean All Categories Dashboard
        </h2>
        <p style={{ color: '#fca5a5', margin: '5px 0 0 0', fontSize: '0.9rem' }}>
          Bulk manage and clean search results across all categories
        </p>
      </div>
      
      {/* Stats Summary */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: 15,
        padding: 20,
        background: 'rgba(239, 68, 68, 0.1)',
        borderBottom: '1px solid rgba(239, 68, 68, 0.3)'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#ef4444', fontSize: '2rem', fontWeight: 700 }}>{totalStats.categories}</div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Total Categories</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#f59e0b', fontSize: '2rem', fontWeight: 700 }}>{totalStats.results.toLocaleString()}</div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Total Results</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#10b981', fontSize: '2rem', fontWeight: 700 }}>{totalStats.exclusive.toLocaleString()}</div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Exclusive Results</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ color: '#3b82f6', fontSize: '2rem', fontWeight: 700 }}>{selectedCategories.size}</div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Selected</div>
        </div>
      </div>
      
      {/* Controls */}
      <div style={{ padding: 20, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 15 }}>
          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="input-field"
            style={{ width: 'auto', padding: '8px 12px', fontSize: '0.85rem' }}
          >
            <option value="results_desc">Most Results</option>
            <option value="results_asc">Least Results</option>
            <option value="exclusive_desc">Most Exclusive</option>
            <option value="name_asc">Name A-Z</option>
            <option value="name_desc">Name Z-A</option>
          </select>
          
          {/* Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="input-field"
            style={{ width: 'auto', padding: '8px 12px', fontSize: '0.85rem' }}
          >
            <option value="all">All Categories</option>
            <option value="empty">Empty (0 results)</option>
            <option value="has_results">Has Results</option>
            <option value="has_exclusive">Has Exclusive</option>
          </select>
          
          <button
            onClick={toggleSelectAll}
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem' }}
          >
            {selectedCategories.size === sortedCategories.length ? '✗ Deselect All' : '✓ Select All'}
          </button>
          
          <button
            onClick={() => fetchCategories()}
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem' }}
            disabled={loading}
          >
            🔄 Refresh
          </button>
        </div>
        
        {/* Bulk Actions */}
        {selectedCategories.size > 0 && (
          <div style={{ 
            display: 'flex', 
            gap: 10, 
            flexWrap: 'wrap',
            padding: 15,
            background: 'rgba(239, 68, 68, 0.1)',
            borderRadius: 10,
            border: '1px solid rgba(239, 68, 68, 0.3)'
          }}>
            <span style={{ color: '#fca5a5', fontSize: '0.85rem', alignSelf: 'center' }}>
              Bulk Actions ({selectedCategories.size} selected):
            </span>
            <button
              onClick={() => bulkCleanCategories('remove')}
              disabled={processing}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', background: 'rgba(59, 130, 246, 0.2)', borderColor: '#3b82f6', color: '#3b82f6' }}
            >
              🔗 Unlink All
            </button>
            <button
              onClick={() => bulkCleanCategories('delete')}
              disabled={processing}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', background: 'rgba(245, 158, 11, 0.2)', borderColor: '#f59e0b', color: '#f59e0b' }}
            >
              🗑️ Delete Exclusive
            </button>
            <button
              onClick={() => bulkCleanCategories('delete_all')}
              disabled={processing}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', background: 'rgba(239, 68, 68, 0.2)', borderColor: '#ef4444', color: '#ef4444' }}
            >
              💥 Delete ALL Results
            </button>
          </div>
        )}
        
        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: 10, marginTop: 15 }}>
          <button
            onClick={cleanEmptyCategories}
            disabled={processing}
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem' }}
          >
            🗑️ Delete Empty Categories ({categories.filter(c => (c.total_results || 0) === 0).length})
          </button>
        </div>
      </div>
      
      {/* Category List */}
      <div style={{ padding: 20, maxHeight: 500, overflowY: 'auto' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
            ⏳ Loading categories...
          </div>
        ) : sortedCategories.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
            No categories match the current filter.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {sortedCategories.map(cat => (
              <div
                key={cat.id}
                onClick={() => toggleCategory(cat.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 15,
                  padding: 12,
                  background: selectedCategories.has(cat.id) 
                    ? 'rgba(239, 68, 68, 0.2)' 
                    : 'rgba(30, 20, 50, 0.5)',
                  border: selectedCategories.has(cat.id)
                    ? '2px solid #ef4444'
                    : '1px solid rgba(124, 58, 237, 0.3)',
                  borderRadius: 10,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                data-testid={`category-row-${cat.id}`}
              >
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedCategories.has(cat.id)}
                  onChange={() => {}}
                  style={{ width: 20, height: 20, accentColor: '#ef4444' }}
                />
                
                {/* Category Info */}
                <div style={{ flex: 1 }}>
                  <div style={{ color: '#e5e7eb', fontWeight: 600 }}>{cat.name}</div>
                  {cat.protocol && (
                    <div style={{ color: '#71717a', fontSize: '0.75rem', fontFamily: 'monospace' }}>
                      {cat.protocol.substring(0, 50)}...
                    </div>
                  )}
                </div>
                
                {/* Stats */}
                <div style={{ display: 'flex', gap: 15, fontSize: '0.8rem' }}>
                  <span style={{ color: '#f59e0b' }}>
                    📊 {cat.total_results || 0} total
                  </span>
                  <span style={{ color: '#10b981' }}>
                    🎯 {cat.exclusive_results || 0} exclusive
                  </span>
                  <span style={{ color: '#3b82f6' }}>
                    🔗 {cat.shared_results || 0} shared
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Processing Indicator */}
      {processing && (
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: 12
        }}>
          <div style={{ color: '#fff', fontSize: '1.2rem' }}>
            ⏳ Processing... Please wait
          </div>
        </div>
      )}
    </div>
  );
};

export default CleanAllCategoriesAdmin;
