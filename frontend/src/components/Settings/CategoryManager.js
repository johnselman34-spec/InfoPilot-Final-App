/**
 * CategoryManager Component
 * Allows users to manage categories from the Settings page
 * Supports: Create, Edit, Delete, Clean categories and sub-categories
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

const CategoryManager = ({ showToast }) => {
  const { token } = useAuth();
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', protocol: '', is_public: false });
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCategory, setNewCategory] = useState({ name: '', protocol: '', parent_id: null, is_public: false });
  
  // Fetch categories
  const fetchCategories = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data || []);
      }
    } catch (e) {
      console.error('Failed to fetch categories:', e);
    } finally {
      setLoading(false);
    }
  }, [token]);
  
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);
  
  // Toggle expand/collapse
  const toggleExpand = (catId) => {
    setExpanded(prev => ({ ...prev, [catId]: !prev[catId] }));
  };
  
  // Start editing a category
  const startEdit = (cat) => {
    setEditingId(cat.id);
    setEditForm({
      name: cat.name,
      protocol: cat.protocol || '',
      is_public: cat.is_public || false
    });
  };
  
  // Save edit
  const saveEdit = async (catId) => {
    try {
      const res = await fetch(`${API}/categories/${catId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(editForm)
      });
      if (res.ok) {
        showToast('Category updated!', 'success');
        setEditingId(null);
        fetchCategories();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to update', 'error');
      }
    } catch (e) {
      showToast('Failed to update category', 'error');
    }
  };
  
  // Delete category
  const deleteCategory = async (catId, catName) => {
    if (!window.confirm(`Delete "${catName}" and all its sub-categories? This cannot be undone!`)) return;
    
    try {
      const res = await fetch(`${API}/categories/${catId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Category deleted!', 'success');
        fetchCategories();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to delete', 'error');
      }
    } catch (e) {
      showToast('Failed to delete category', 'error');
    }
  };
  
  // Clean category (remove all results)
  const cleanCategory = async (catId, catName) => {
    if (!window.confirm(`Remove ALL search results from "${catName}"? This cannot be undone!`)) return;
    
    try {
      const res = await fetch(`${API}/categories/${catId}/clean`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        showToast(data.message || 'Category cleaned!', 'success');
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to clean', 'error');
      }
    } catch (e) {
      showToast('Failed to clean category', 'error');
    }
  };
  
  // Create new category
  const createCategory = async () => {
    if (!newCategory.name.trim()) {
      showToast('Category name is required', 'error');
      return;
    }
    
    try {
      const res = await fetch(`${API}/categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newCategory)
      });
      if (res.ok) {
        showToast('Category created!', 'success');
        setShowCreateForm(false);
        setNewCategory({ name: '', protocol: '', parent_id: null, is_public: false });
        fetchCategories();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to create', 'error');
      }
    } catch (e) {
      showToast('Failed to create category', 'error');
    }
  };
  
  // Build category tree
  const buildTree = (parentId = null, level = 0) => {
    return categories
      .filter(c => c.parent_id === parentId)
      .map(cat => {
        const hasChildren = categories.some(c => c.parent_id === cat.id);
        const isExpanded = expanded[cat.id];
        const isEditing = editingId === cat.id;
        
        return (
          <div key={cat.id} style={{ marginLeft: level * 20 }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 12px',
              background: level === 0 
                ? 'rgba(124, 58, 237, 0.1)' 
                : `rgba(124, 58, 237, ${0.05 * (level + 1)})`,
              borderRadius: 8,
              marginBottom: 5,
              border: isEditing ? '2px solid #7c3aed' : '1px solid rgba(124, 58, 237, 0.2)'
            }} data-testid={`settings-category-${cat.id}`}>
              {/* Expand/Collapse */}
              {hasChildren && (
                <button
                  onClick={() => toggleExpand(cat.id)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#a78bfa',
                    cursor: 'pointer',
                    padding: '2px 5px',
                    fontSize: '0.8rem'
                  }}
                >
                  {isExpanded ? '▼' : '▶'}
                </button>
              )}
              {!hasChildren && <span style={{ width: 20 }} />}
              
              {isEditing ? (
                // Edit form
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    placeholder="Category name"
                    style={{
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid rgba(124, 58, 237, 0.3)',
                      borderRadius: 6,
                      padding: '6px 10px',
                      color: '#fff',
                      fontSize: '0.85rem'
                    }}
                  />
                  <input
                    type="text"
                    value={editForm.protocol}
                    onChange={(e) => setEditForm({ ...editForm, protocol: e.target.value })}
                    placeholder="Protocol: (word1 or word2) and (word3)"
                    style={{
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid rgba(124, 58, 237, 0.3)',
                      borderRadius: 6,
                      padding: '6px 10px',
                      color: '#10b981',
                      fontSize: '0.75rem',
                      fontFamily: 'monospace'
                    }}
                  />
                  <p style={{ color: '#71717a', fontSize: '0.7rem', margin: 0 }}>
                    💡 Tip: Use "and" or "&amp;" between groups. Example: (aviation or pilot) and (training or career)
                  </p>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#a1a1aa', fontSize: '0.8rem' }}>
                    <input
                      type="checkbox"
                      checked={editForm.is_public}
                      onChange={(e) => setEditForm({ ...editForm, is_public: e.target.checked })}
                    />
                    Public (visible to other users)
                  </label>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      onClick={() => saveEdit(cat.id)}
                      style={{
                        background: 'linear-gradient(135deg, #10b981, #059669)',
                        border: 'none',
                        borderRadius: 6,
                        padding: '6px 12px',
                        color: '#fff',
                        fontSize: '0.8rem',
                        cursor: 'pointer'
                      }}
                    >
                      ✓ Save
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      style={{
                        background: 'rgba(107, 114, 128, 0.3)',
                        border: '1px solid rgba(107, 114, 128, 0.5)',
                        borderRadius: 6,
                        padding: '6px 12px',
                        color: '#9ca3af',
                        fontSize: '0.8rem',
                        cursor: 'pointer'
                      }}
                    >
                      ✕ Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // Display view
                <>
                  <span style={{ 
                    flex: 1, 
                    color: '#e2e8f0', 
                    fontSize: '0.9rem',
                    fontWeight: level === 0 ? 600 : 400
                  }}>
                    {cat.name}
                    {cat.is_public && (
                      <span style={{ marginLeft: 8, fontSize: '0.65rem', color: '#10b981', background: 'rgba(16,185,129,0.2)', padding: '2px 6px', borderRadius: 4 }}>
                        Public
                      </span>
                    )}
                  </span>
                  
                  {/* Action buttons */}
                  <div style={{ display: 'flex', gap: 5 }}>
                    <button
                      onClick={() => startEdit(cat)}
                      title="Edit"
                      style={{
                        background: 'rgba(124, 58, 237, 0.2)',
                        border: 'none',
                        borderRadius: 4,
                        padding: '4px 8px',
                        color: '#a78bfa',
                        cursor: 'pointer',
                        fontSize: '0.75rem'
                      }}
                      data-testid={`edit-category-settings-${cat.id}`}
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => cleanCategory(cat.id, cat.name)}
                      title="Clean (remove all results)"
                      style={{
                        background: 'rgba(245, 158, 11, 0.2)',
                        border: 'none',
                        borderRadius: 4,
                        padding: '4px 8px',
                        color: '#f59e0b',
                        cursor: 'pointer',
                        fontSize: '0.75rem'
                      }}
                      data-testid={`clean-category-settings-${cat.id}`}
                    >
                      🧹
                    </button>
                    <button
                      onClick={() => deleteCategory(cat.id, cat.name)}
                      title="Delete"
                      style={{
                        background: 'rgba(239, 68, 68, 0.2)',
                        border: 'none',
                        borderRadius: 4,
                        padding: '4px 8px',
                        color: '#ef4444',
                        cursor: 'pointer',
                        fontSize: '0.75rem'
                      }}
                      data-testid={`delete-category-settings-${cat.id}`}
                    >
                      🗑️
                    </button>
                  </div>
                </>
              )}
            </div>
            
            {/* Children */}
            {hasChildren && isExpanded && buildTree(cat.id, level + 1)}
          </div>
        );
      });
  };
  
  if (loading) {
    return <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Loading categories...</p>;
  }
  
  return (
    <div>
      {/* Create New Category Button */}
      <button
        onClick={() => setShowCreateForm(!showCreateForm)}
        style={{
          background: showCreateForm 
            ? 'rgba(239, 68, 68, 0.2)' 
            : 'linear-gradient(135deg, #7c3aed, #ec4899)',
          border: showCreateForm ? '1px solid rgba(239, 68, 68, 0.5)' : 'none',
          borderRadius: 8,
          padding: '8px 16px',
          color: '#fff',
          fontWeight: 600,
          cursor: 'pointer',
          marginBottom: 15,
          fontSize: '0.85rem'
        }}
        data-testid="create-category-settings-btn"
      >
        {showCreateForm ? '✕ Cancel' : '+ New Category'}
      </button>
      
      {/* Create Form */}
      {showCreateForm && (
        <div style={{
          background: 'rgba(124, 58, 237, 0.1)',
          borderRadius: 10,
          padding: 15,
          marginBottom: 15,
          border: '1px solid rgba(124, 58, 237, 0.3)'
        }}>
          <h4 style={{ color: '#f472b6', marginTop: 0, marginBottom: 12 }}>Create New Category</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <input
              type="text"
              value={newCategory.name}
              onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
              placeholder="Category name"
              style={{
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(124, 58, 237, 0.3)',
                borderRadius: 6,
                padding: '8px 12px',
                color: '#fff',
                fontSize: '0.9rem'
              }}
              data-testid="new-category-name-input"
            />
            <input
              type="text"
              value={newCategory.protocol}
              onChange={(e) => setNewCategory({ ...newCategory, protocol: e.target.value })}
              placeholder="Protocol: (word1 or word2) and (word3 or word4)"
              style={{
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(124, 58, 237, 0.3)',
                borderRadius: 6,
                padding: '8px 12px',
                color: '#10b981',
                fontSize: '0.85rem',
                fontFamily: 'monospace'
              }}
              data-testid="new-category-protocol-input"
            />
            <p style={{ color: '#71717a', fontSize: '0.75rem', margin: 0 }}>
              💡 Tip: Use "and" or "&" to combine groups. Example: (aviation or pilot) and (training or career)
            </p>
            <select
              value={newCategory.parent_id || ''}
              onChange={(e) => setNewCategory({ ...newCategory, parent_id: e.target.value || null })}
              style={{
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(124, 58, 237, 0.3)',
                borderRadius: 6,
                padding: '8px 12px',
                color: '#a1a1aa',
                fontSize: '0.85rem'
              }}
            >
              <option value="">No parent (top-level category)</option>
              {categories.filter(c => !c.parent_id).map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#a1a1aa', fontSize: '0.85rem' }}>
              <input
                type="checkbox"
                checked={newCategory.is_public}
                onChange={(e) => setNewCategory({ ...newCategory, is_public: e.target.checked })}
              />
              Public (visible to other users)
            </label>
            <button
              onClick={createCategory}
              style={{
                background: 'linear-gradient(135deg, #10b981, #059669)',
                border: 'none',
                borderRadius: 8,
                padding: '10px 20px',
                color: '#fff',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
              data-testid="save-new-category-btn"
            >
              ✓ Create Category
            </button>
          </div>
        </div>
      )}
      
      {/* Category Tree */}
      {categories.length === 0 ? (
        <p style={{ color: '#71717a', fontSize: '0.85rem' }}>
          No categories yet. Create your first category above!
        </p>
      ) : (
        <div style={{ maxHeight: 400, overflowY: 'auto' }}>
          {buildTree()}
        </div>
      )}
      
      <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 15 }}>
        {categories.length} categories • Manage categories from here or from the Ultimate Search page
      </p>
    </div>
  );
};

export default CategoryManager;
