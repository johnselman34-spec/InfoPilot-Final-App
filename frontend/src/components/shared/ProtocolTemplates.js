import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

const ProtocolTemplates = ({ showToast, onApplyTemplate }) => {
  const { token } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [popularTemplates, setPopularTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('my'); // my, public, popular
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    description: '',
    protocol: '',
    category: 'General',
    tags: '',
    is_public: false
  });

  const templateCategories = [
    'General', 'News & Media', 'Science & Research', 'Business & Finance',
    'Technology', 'Health & Medical', 'Education', 'Entertainment', 'Government', 'Sports'
  ];

  const fetchTemplates = useCallback(async () => {
    try {
      const res = await fetch(`${API}/protocol-templates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.templates || []);
      }
    } catch (e) {
      console.error('Failed to fetch templates');
    }
    setLoading(false);
  }, [token]);

  const fetchPopularTemplates = useCallback(async () => {
    try {
      const res = await fetch(`${API}/protocol-templates/popular?limit=10`);
      if (res.ok) {
        const data = await res.json();
        setPopularTemplates(data.templates || []);
      }
    } catch (e) {
      console.error('Failed to fetch popular templates');
    }
  }, []);

  const fetchCategories = useCallback(async () => {
    try {
      const res = await fetch(`${API}/protocol-templates/categories`);
      if (res.ok) {
        const data = await res.json();
        setCategories(data.categories || []);
      }
    } catch (e) {
      console.error('Failed to fetch categories');
    }
  }, []);

  useEffect(() => {
    // Initial data loading
    let mounted = true;
    const loadData = async () => {
      if (mounted) {
        await Promise.all([fetchTemplates(), fetchPopularTemplates(), fetchCategories()]);
      }
    };
    loadData();
    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createTemplate = async () => {
    if (!newTemplate.name || !newTemplate.protocol) {
      showToast('Name and protocol are required', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/protocol-templates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...newTemplate,
          tags: newTemplate.tags.split(',').map(t => t.trim()).filter(t => t)
        })
      });

      if (res.ok) {
        showToast('Template created successfully!', 'success');
        setShowCreateModal(false);
        setNewTemplate({
          name: '', description: '', protocol: '', category: 'General', tags: '', is_public: false
        });
        fetchTemplates();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to create template', 'error');
      }
    } catch (e) {
      showToast('Failed to create template', 'error');
    }
  };

  const updateTemplate = async () => {
    if (!editingTemplate) return;

    try {
      const res = await fetch(`${API}/protocol-templates/${editingTemplate.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: editingTemplate.name,
          description: editingTemplate.description,
          protocol: editingTemplate.protocol,
          category: editingTemplate.category,
          tags: typeof editingTemplate.tags === 'string' 
            ? editingTemplate.tags.split(',').map(t => t.trim()).filter(t => t)
            : editingTemplate.tags,
          is_public: editingTemplate.is_public
        })
      });

      if (res.ok) {
        showToast('Template updated!', 'success');
        setEditingTemplate(null);
        fetchTemplates();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to update template', 'error');
      }
    } catch (e) {
      showToast('Failed to update template', 'error');
    }
  };

  const deleteTemplate = async (templateId) => {
    if (!window.confirm('Delete this template? This cannot be undone.')) return;

    try {
      const res = await fetch(`${API}/protocol-templates/${templateId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        showToast('Template deleted', 'success');
        fetchTemplates();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to delete template', 'error');
      }
    } catch (e) {
      showToast('Failed to delete template', 'error');
    }
  };

  const applyTemplate = async (template) => {
    try {
      const res = await fetch(`${API}/protocol-templates/${template.id}/use`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        if (onApplyTemplate) {
          onApplyTemplate(data.protocol, template.name);
        }
        showToast(`Applied template: ${template.name}`, 'success');
      }
    } catch (e) {
      showToast('Failed to apply template', 'error');
    }
  };

  const myTemplates = templates.filter(t => t.is_owner);
  const publicTemplates = templates.filter(t => t.is_public && !t.is_owner);

  const displayedTemplates = activeTab === 'my' ? myTemplates :
                             activeTab === 'public' ? publicTemplates : popularTemplates;

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 30 }}>
        <div className="spinner" style={{ margin: '0 auto' }}></div>
      </div>
    );
  }

  return (
    <div 
      style={{
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 16,
        padding: 20,
        marginBottom: 20,
        border: '1px solid rgba(16, 185, 129, 0.3)'
      }}
      data-testid="protocol-templates"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
        <h3 style={{ color: '#10b981', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          📁 Protocol Templates
        </h3>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
          style={{ padding: '8px 16px', fontSize: '0.85rem' }}
          data-testid="create-template-btn"
        >
          + New Template
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 15 }}>
        {[
          { id: 'my', label: `My Templates (${myTemplates.length})` },
          { id: 'public', label: `Public (${publicTemplates.length})` },
          { id: 'popular', label: '🔥 Popular' }
        ].map(tab => (
          <button
            key={tab.id}
            className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab(tab.id)}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Templates List */}
      {displayedTemplates.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 30, color: '#a1a1aa' }}>
          {activeTab === 'my' && (
            <>
              <p>You haven't created any templates yet.</p>
              <p style={{ fontSize: '0.85rem' }}>Save your favorite protocols as templates for quick access!</p>
            </>
          )}
          {activeTab === 'public' && <p>No public templates available.</p>}
          {activeTab === 'popular' && <p>No popular templates yet.</p>}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 300, overflowY: 'auto' }}>
          {displayedTemplates.map(template => (
            <div
              key={template.id}
              style={{
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: 10,
                padding: 12,
                border: '1px solid rgba(16, 185, 129, 0.2)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                <div>
                  <h4 style={{ color: '#10b981', margin: 0, fontSize: '0.95rem' }}>{template.name}</h4>
                  {template.description && (
                    <p style={{ color: '#a1a1aa', fontSize: '0.8rem', margin: '4px 0' }}>{template.description}</p>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  {template.is_public && (
                    <span style={{ 
                      fontSize: '0.65rem', 
                      padding: '2px 6px', 
                      background: 'rgba(16, 185, 129, 0.2)', 
                      color: '#10b981', 
                      borderRadius: 4 
                    }}>
                      Public
                    </span>
                  )}
                  <span style={{ 
                    fontSize: '0.65rem', 
                    padding: '2px 6px', 
                    background: 'rgba(124, 58, 237, 0.2)', 
                    color: '#a78bfa', 
                    borderRadius: 4 
                  }}>
                    {template.category}
                  </span>
                </div>
              </div>
              
              <div style={{
                background: 'rgba(16, 185, 129, 0.1)',
                padding: 8,
                borderRadius: 6,
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                color: '#10b981',
                marginBottom: 10,
                wordBreak: 'break-all'
              }}>
                {template.protocol.length > 80 ? template.protocol.substring(0, 80) + '...' : template.protocol}
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>
                  by {template.creator_name} • {template.use_count} uses
                </span>
                <div style={{ display: 'flex', gap: 6 }}>
                  {template.is_owner && (
                    <>
                      <button
                        onClick={() => setEditingTemplate({
                          ...template,
                          tags: Array.isArray(template.tags) ? template.tags.join(', ') : template.tags
                        })}
                        style={{
                          background: 'rgba(59, 130, 246, 0.2)',
                          border: 'none',
                          borderRadius: 6,
                          padding: '4px 10px',
                          color: '#3b82f6',
                          fontSize: '0.75rem',
                          cursor: 'pointer'
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => deleteTemplate(template.id)}
                        style={{
                          background: 'rgba(239, 68, 68, 0.2)',
                          border: 'none',
                          borderRadius: 6,
                          padding: '4px 10px',
                          color: '#ef4444',
                          fontSize: '0.75rem',
                          cursor: 'pointer'
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => applyTemplate(template)}
                    className="btn btn-primary"
                    style={{ padding: '4px 12px', fontSize: '0.75rem' }}
                    data-testid={`apply-template-${template.id}`}
                  >
                    Apply
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Template Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <h3 style={{ color: '#10b981', marginBottom: 20 }}>📁 Create Protocol Template</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <input
                className="input"
                placeholder="Template Name *"
                value={newTemplate.name}
                onChange={e => setNewTemplate({ ...newTemplate, name: e.target.value })}
                data-testid="template-name-input"
              />
              <textarea
                className="input"
                placeholder="Description (optional)"
                rows={2}
                value={newTemplate.description}
                onChange={e => setNewTemplate({ ...newTemplate, description: e.target.value })}
              />
              <textarea
                className="input"
                placeholder="Protocol String * e.g. (word1 or word2) & (word3)+"
                rows={3}
                value={newTemplate.protocol}
                onChange={e => setNewTemplate({ ...newTemplate, protocol: e.target.value })}
                style={{ fontFamily: 'monospace' }}
                data-testid="template-protocol-input"
              />
              <select
                className="input"
                value={newTemplate.category}
                onChange={e => setNewTemplate({ ...newTemplate, category: e.target.value })}
              >
                {templateCategories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <input
                className="input"
                placeholder="Tags (comma separated)"
                value={newTemplate.tags}
                onChange={e => setNewTemplate({ ...newTemplate, tags: e.target.value })}
              />
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#a1a1aa' }}>
                <input
                  type="checkbox"
                  checked={newTemplate.is_public}
                  onChange={e => setNewTemplate({ ...newTemplate, is_public: e.target.checked })}
                />
                Make this template public (others can use it)
              </label>
              <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
                <button className="btn btn-secondary" onClick={() => setShowCreateModal(false)} style={{ flex: 1 }}>
                  Cancel
                </button>
                <button className="btn btn-primary" onClick={createTemplate} style={{ flex: 1 }} data-testid="save-template-btn">
                  Create Template
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Template Modal */}
      {editingTemplate && (
        <div className="modal-overlay" onClick={() => setEditingTemplate(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <h3 style={{ color: '#3b82f6', marginBottom: 20 }}>✏️ Edit Template</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <input
                className="input"
                placeholder="Template Name *"
                value={editingTemplate.name}
                onChange={e => setEditingTemplate({ ...editingTemplate, name: e.target.value })}
              />
              <textarea
                className="input"
                placeholder="Description (optional)"
                rows={2}
                value={editingTemplate.description}
                onChange={e => setEditingTemplate({ ...editingTemplate, description: e.target.value })}
              />
              <textarea
                className="input"
                placeholder="Protocol String *"
                rows={3}
                value={editingTemplate.protocol}
                onChange={e => setEditingTemplate({ ...editingTemplate, protocol: e.target.value })}
                style={{ fontFamily: 'monospace' }}
              />
              <select
                className="input"
                value={editingTemplate.category}
                onChange={e => setEditingTemplate({ ...editingTemplate, category: e.target.value })}
              >
                {templateCategories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <input
                className="input"
                placeholder="Tags (comma separated)"
                value={editingTemplate.tags}
                onChange={e => setEditingTemplate({ ...editingTemplate, tags: e.target.value })}
              />
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#a1a1aa' }}>
                <input
                  type="checkbox"
                  checked={editingTemplate.is_public}
                  onChange={e => setEditingTemplate({ ...editingTemplate, is_public: e.target.checked })}
                />
                Make this template public
              </label>
              <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
                <button className="btn btn-secondary" onClick={() => setEditingTemplate(null)} style={{ flex: 1 }}>
                  Cancel
                </button>
                <button className="btn btn-primary" onClick={updateTemplate} style={{ flex: 1 }}>
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProtocolTemplates;
