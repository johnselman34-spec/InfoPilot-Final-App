import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { DataExport, PushNotifications } from '../components/shared';

const SettingsPage = ({ showToast, setCurrentPage }) => {
  const { token, user, refreshUser } = useAuth();
  const [settings, setSettings] = useState({
    ultimate_search_public: user?.ultimate_search_public || false,
    friends_visible: user?.friends_visible || false
  });
  
  // Password change state
  const [hasPassword, setHasPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [showPasswordSection, setShowPasswordSection] = useState(false);
  
  // Promotion message state
  const [promoSettings, setPromoSettings] = useState(null);
  
  // Legal documents state
  const [showLegal, setShowLegal] = useState(null);
  const [legalContent, setLegalContent] = useState('');
  
  // Category Management state
  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [showCategoryManager, setShowCategoryManager] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editCategoryName, setEditCategoryName] = useState('');
  const [editProtocol, setEditProtocol] = useState('');
  const [editIsPublic, setEditIsPublic] = useState(false);
  const [editPrice, setEditPrice] = useState('');

  // Check if user has password on mount
  useEffect(() => {
    const checkPassword = async () => {
      try {
        const res = await fetch(`${API}/users/has-password`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const data = await res.json();
        setHasPassword(data.has_password);
      } catch (e) {
        console.error('Failed to check password status');
      }
    };
    checkPassword();
  }, [token]);
  
  // Fetch categories
  const fetchCategories = async () => {
    setCategoriesLoading(true);
    try {
      const res = await fetch(`${API}/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data);
      }
    } catch (e) {
      console.error('Failed to fetch categories');
    }
    setCategoriesLoading(false);
  };
  
  // Fetch categories when showing manager
  useEffect(() => {
    if (showCategoryManager) {
      fetchCategories();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showCategoryManager]);
  
  // Fetch admin promo settings
  useEffect(() => {
    const fetchPromoSettings = async () => {
      try {
        const res = await fetch(`${API}/admin/settings`);
        if (res.ok) {
          const data = await res.json();
          const settingsObj = {};
          if (Array.isArray(data)) {
            data.forEach(s => { settingsObj[s.key] = s.value; });
          } else {
            Object.assign(settingsObj, data);
          }
          setPromoSettings(settingsObj);
        }
      } catch (e) {
        console.error('Failed to fetch promo settings');
      }
    };
    fetchPromoSettings();
  }, []);
  
  // Fetch legal documents
  const fetchLegalDocument = async (type) => {
    try {
      const endpoint = type === 'terms' ? 'user-agreement' : 'privacy-policy';
      const res = await fetch(`${API}/legal/${endpoint}`);
      if (res.ok) {
        const data = await res.json();
        setLegalContent(data.content);
        setShowLegal(type);
      }
    } catch (e) {
      showToast('Failed to load document', 'error');
    }
  };

  const updateSettings = async () => {
    try {
      const params = new URLSearchParams();
      params.append('ultimate_search_public', settings.ultimate_search_public);
      params.append('friends_visible', settings.friends_visible);
      
      await fetch(`${API}/users/settings?${params}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      });
      showToast('Settings saved!', 'success');
      refreshUser();
    } catch (e) {
      showToast('Failed to save settings', 'error');
    }
  };

  const handleChangePassword = async () => {
    // Validation
    if (newPassword.length < 6) {
      showToast('Password must be at least 6 characters', 'error');
      return;
    }
    if (newPassword !== confirmPassword) {
      showToast('Passwords do not match', 'error');
      return;
    }
    if (hasPassword && !currentPassword) {
      showToast('Current password is required', 'error');
      return;
    }

    setPasswordLoading(true);
    try {
      const res = await fetch(`${API}/users/change-password`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({
          current_password: hasPassword ? currentPassword : null,
          new_password: newPassword
        })
      });

      const data = await res.json();
      
      if (res.ok) {
        showToast('Password changed successfully!', 'success');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setShowPasswordSection(false);
        setHasPassword(true);
      } else {
        showToast(data.detail || 'Failed to change password', 'error');
      }
    } catch (e) {
      showToast('Failed to change password', 'error');
    }
    setPasswordLoading(false);
  };
  
  // Category Management Functions
  const handleEditCategory = (cat) => {
    setEditingCategory(cat);
    setEditCategoryName(cat.name);
    setEditProtocol(cat.protocol || '');
    setEditIsPublic(cat.is_public || false);
    setEditPrice(cat.price || '');
  };
  
  const saveCategory = async () => {
    if (!editingCategory) return;
    
    try {
      const res = await fetch(`${API}/categories/${editingCategory.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: editCategoryName,
          protocol: editProtocol,
          is_public: editIsPublic,
          price: editPrice ? parseFloat(editPrice) : 0
        })
      });
      
      if (res.ok) {
        showToast('Category updated successfully!', 'success');
        setEditingCategory(null);
        fetchCategories();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to update category', 'error');
      }
    } catch (e) {
      showToast('Failed to update category', 'error');
    }
  };
  
  const deleteCategory = async (categoryId) => {
    const cat = categories.find(c => c.id === categoryId);
    const childCount = categories.filter(c => c.parent_id === categoryId).length;
    
    const confirmMsg = childCount > 0 
      ? `Delete "${cat?.name}" and its ${childCount} sub-categor${childCount === 1 ? 'y' : 'ies'}? This cannot be undone!`
      : `Delete "${cat?.name}"? This cannot be undone!`;
    
    if (!window.confirm(confirmMsg)) return;
    
    try {
      const res = await fetch(`${API}/categories/${categoryId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast('Category deleted successfully!', 'success');
        setEditingCategory(null);
        fetchCategories();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to delete category', 'error');
      }
    } catch (e) {
      showToast('Failed to delete category', 'error');
    }
  };
  
  // Build category tree with indentation
  const buildCategoryTree = (cats, parentId = null, level = 0) => {
    return cats
      .filter(cat => cat.parent_id === parentId)
      .map(cat => {
        const childCount = cats.filter(c => c.parent_id === cat.id).length;
        return (
          <div key={cat.id}>
            <div
              style={{
                padding: '10px 12px',
                marginLeft: level * 20,
                marginBottom: 6,
                background: editingCategory?.id === cat.id 
                  ? 'rgba(124, 58, 237, 0.2)' 
                  : 'rgba(30, 20, 50, 0.4)',
                borderRadius: 8,
                border: editingCategory?.id === cat.id 
                  ? '1px solid rgba(124, 58, 237, 0.5)' 
                  : '1px solid rgba(255,255,255,0.05)',
                cursor: 'pointer'
              }}
              onClick={() => handleEditCategory(cat)}
              data-testid={`settings-category-${cat.id}`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ 
                    color: cat.is_public ? '#10b981' : '#e2e8f0',
                    fontWeight: 500
                  }}>
                    {cat.name}
                  </span>
                  {childCount > 0 && (
                    <span style={{ fontSize: '0.7rem', color: '#a78bfa', background: 'rgba(124, 58, 237, 0.2)', padding: '2px 6px', borderRadius: 4 }}>
                      {childCount} sub
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  {cat.is_public && (
                    <span style={{ fontSize: '0.65rem', color: '#10b981', padding: '2px 6px', background: 'rgba(16,185,129,0.2)', borderRadius: 4 }}>
                      Public
                    </span>
                  )}
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteCategory(cat.id); }}
                    style={{
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      color: '#ef4444',
                      padding: '4px 8px',
                      borderRadius: 4,
                      fontSize: '0.7rem',
                      cursor: 'pointer'
                    }}
                    data-testid={`delete-category-settings-${cat.id}`}
                  >
                    🗑️
                  </button>
                </div>
              </div>
              {cat.protocol && (
                <div style={{ 
                  fontSize: '0.7rem', 
                  color: '#71717a', 
                  marginTop: 4, 
                  fontFamily: 'monospace',
                  wordBreak: 'break-all'
                }}>
                  {cat.protocol.length > 50 ? cat.protocol.substring(0, 50) + '...' : cat.protocol}
                </div>
              )}
            </div>
            {buildCategoryTree(cats, cat.id, level + 1)}
          </div>
        );
      });
  };

  return (
    <div className="card" data-testid="settings-page">
      <div className="card-header">
        <h2>User Settings</h2>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div style={{ padding: 15, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.ultimate_search_public}
              onChange={(e) => setSettings({ ...settings, ultimate_search_public: e.target.checked })}
            />
            <div>
              <strong>Make Ultimate Search Page Public</strong>
              <p style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 4 }}>
                Allow other users to view your Ultimate Search page and public categories
              </p>
            </div>
          </label>
        </div>

        <div style={{ padding: 15, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.friends_visible}
              onChange={(e) => setSettings({ ...settings, friends_visible: e.target.checked })}
            />
            <div>
              <strong>Show Friends List to Others</strong>
              <p style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 4 }}>
                Allow other users to see your friends list
              </p>
            </div>
          </label>
        </div>

        <button className="btn btn-primary" onClick={updateSettings} data-testid="save-settings-btn">
          Save Settings
        </button>

        {/* Account Info */}
        <div style={{ marginTop: 20, padding: 20, background: 'rgba(124, 58, 237, 0.1)', borderRadius: 10 }}>
          <h3 style={{ marginBottom: 15, color: '#f472b6' }}>Account Information</h3>
          <p><strong>Username:</strong> {user?.username}</p>
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>Status:</strong> {user?.is_admin ? 'Admin' : (user?.is_paid ? 'Premium' : 'Free')}</p>
        </div>

        {/* Category Management Section */}
        <div style={{ padding: 20, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: showCategoryManager ? 15 : 0 }}>
            <h3 style={{ color: '#a78bfa', margin: 0 }}>
              📂 Category Management
            </h3>
            <button 
              className="btn btn-secondary"
              onClick={() => setShowCategoryManager(!showCategoryManager)}
              style={{ padding: '8px 16px', fontSize: '0.9rem' }}
              data-testid="toggle-category-manager-btn"
            >
              {showCategoryManager ? 'Hide' : 'Manage Categories'}
            </button>
          </div>
          
          {!showCategoryManager && (
            <p style={{ fontSize: '0.85rem', color: '#a1a1aa', marginTop: 10 }}>
              View, edit, and delete your categories and sub-categories here.
            </p>
          )}
          
          {showCategoryManager && (
            <div>
              {categoriesLoading ? (
                <div style={{ textAlign: 'center', padding: 20, color: '#a1a1aa' }}>
                  Loading categories...
                </div>
              ) : categories.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 20 }}>
                  <p style={{ color: '#a1a1aa' }}>No categories yet.</p>
                  <button 
                    className="btn btn-primary"
                    onClick={() => setCurrentPage('ultimate-search')}
                    style={{ marginTop: 10 }}
                  >
                    Go to Ultimate Search to create categories
                  </button>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: editingCategory ? '1fr 1fr' : '1fr', gap: 20 }}>
                  {/* Category Tree */}
                  <div style={{ 
                    maxHeight: 400, 
                    overflowY: 'auto',
                    padding: 10,
                    background: 'rgba(0,0,0,0.2)',
                    borderRadius: 8
                  }}>
                    <p style={{ fontSize: '0.75rem', color: '#a1a1aa', marginBottom: 10 }}>
                      Click a category to edit • {categories.length} total
                    </p>
                    {buildCategoryTree(categories)}
                  </div>
                  
                  {/* Edit Panel */}
                  {editingCategory && (
                    <div style={{
                      padding: 15,
                      background: 'rgba(124, 58, 237, 0.1)',
                      borderRadius: 10,
                      border: '1px solid rgba(124, 58, 237, 0.3)'
                    }}>
                      <h4 style={{ color: '#f472b6', margin: '0 0 15px 0' }}>
                        ✏️ Edit: {editingCategory.name}
                      </h4>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div>
                          <label style={{ color: '#a78bfa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
                            Category Name
                          </label>
                          <input
                            type="text"
                            value={editCategoryName}
                            onChange={(e) => setEditCategoryName(e.target.value)}
                            className="input"
                            placeholder="Category name"
                            data-testid="edit-category-name-settings"
                          />
                        </div>
                        
                        <div>
                          <label style={{ color: '#a78bfa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
                            Protocol
                          </label>
                          <textarea
                            value={editProtocol}
                            onChange={(e) => setEditProtocol(e.target.value)}
                            placeholder="(term1 or term2) & (term3 or term4)"
                            rows={3}
                            style={{
                              width: '100%',
                              padding: 10,
                              borderRadius: 8,
                              border: '1px solid rgba(124, 58, 237, 0.3)',
                              background: 'rgba(30, 20, 50, 0.5)',
                              color: '#fff',
                              fontFamily: 'monospace',
                              fontSize: '0.85rem',
                              resize: 'vertical'
                            }}
                            data-testid="edit-protocol-settings"
                          />
                          <p style={{ fontSize: '0.7rem', color: '#71717a', marginTop: 5 }}>
                            Tip: Use "and" or "&" between groups. Use "or" within groups.
                          </p>
                        </div>
                        
                        <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={editIsPublic}
                            onChange={(e) => setEditIsPublic(e.target.checked)}
                          />
                          <span style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
                            Make this category public
                          </span>
                        </label>
                        
                        {editIsPublic && (
                          <div>
                            <label style={{ color: '#a78bfa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
                              Price (USD) - Leave empty for free
                            </label>
                            <input
                              type="number"
                              value={editPrice}
                              onChange={(e) => setEditPrice(e.target.value)}
                              className="input"
                              placeholder="0.00"
                              min="0"
                              step="0.01"
                            />
                          </div>
                        )}
                        
                        <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
                          <button
                            className="btn btn-secondary"
                            onClick={() => setEditingCategory(null)}
                            style={{ flex: 1 }}
                          >
                            Cancel
                          </button>
                          <button
                            className="btn btn-primary"
                            onClick={saveCategory}
                            style={{ flex: 1 }}
                            data-testid="save-category-settings-btn"
                          >
                            Save Changes
                          </button>
                        </div>
                        
                        {/* Delete Section */}
                        <div style={{
                          marginTop: 15,
                          padding: 12,
                          background: 'rgba(239, 68, 68, 0.1)',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          borderRadius: 8
                        }}>
                          <p style={{ color: '#ef4444', fontSize: '0.8rem', margin: '0 0 10px 0' }}>
                            🗑️ Delete this category permanently
                          </p>
                          <button
                            onClick={() => deleteCategory(editingCategory.id)}
                            style={{
                              width: '100%',
                              padding: '8px 16px',
                              background: 'rgba(239, 68, 68, 0.2)',
                              border: '1px solid rgba(239, 68, 68, 0.5)',
                              borderRadius: 6,
                              color: '#ef4444',
                              cursor: 'pointer',
                              fontWeight: 600
                            }}
                            data-testid="delete-category-confirm-btn"
                          >
                            Delete Category
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Password Change Section */}
        <div style={{ padding: 20, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: showPasswordSection ? 15 : 0 }}>
            <h3 style={{ color: '#f472b6', margin: 0 }}>
              {hasPassword ? 'Change Password' : 'Set Password'}
            </h3>
            <button 
              className="btn btn-secondary"
              onClick={() => setShowPasswordSection(!showPasswordSection)}
              style={{ padding: '8px 16px', fontSize: '0.9rem' }}
              data-testid="toggle-password-section-btn"
            >
              {showPasswordSection ? 'Cancel' : hasPassword ? 'Change' : 'Set Password'}
            </button>
          </div>
          
          {!hasPassword && !showPasswordSection && (
            <p style={{ fontSize: '0.85rem', color: '#a1a1aa', marginTop: 10 }}>
              You signed in with Google. Set a password to also login with email.
            </p>
          )}
          
          {showPasswordSection && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {hasPassword && (
                <input
                  type="password"
                  placeholder="Current Password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="input"
                  data-testid="current-password-input"
                />
              )}
              <input
                type="password"
                placeholder="New Password (min 6 characters)"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input"
                data-testid="new-password-input"
              />
              <input
                type="password"
                placeholder="Confirm New Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input"
                data-testid="confirm-password-input"
              />
              <button 
                className="btn btn-primary"
                onClick={handleChangePassword}
                disabled={passwordLoading}
                data-testid="change-password-btn"
              >
                {passwordLoading ? 'Saving...' : (hasPassword ? 'Change Password' : 'Set Password')}
              </button>
            </div>
          )}
        </div>

        {/* Subscription */}
        {!user?.is_paid && !user?.is_admin && (
          <div style={{ padding: 20, background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(124, 58, 237, 0.2))', borderRadius: 10, border: '1px solid rgba(236, 72, 153, 0.3)' }}>
            <h3 style={{ marginBottom: 10, color: '#f472b6' }}>Upgrade to Premium</h3>
            <p style={{ fontSize: '0.9rem', color: '#a1a1aa', marginBottom: 15 }}>
              Get unlimited search results, access to the interactive map, and more!
            </p>
            <button className="btn btn-primary" onClick={() => setCurrentPage('subscribe')} data-testid="upgrade-premium-btn">Subscribe - Pay What You Want</button>
            
            {/* Admin-controlled promotion message */}
            {promoSettings?.show_upgrade_promo !== false && (
              <div style={{
                marginTop: 15,
                padding: 12,
                background: 'rgba(245, 158, 11, 0.15)',
                borderRadius: 8,
                border: '1px dashed rgba(245, 158, 11, 0.4)'
              }} data-testid="upgrade-promo-message">
                <p style={{ 
                  color: '#f59e0b', 
                  fontSize: '0.8rem', 
                  fontWeight: 600, 
                  margin: '0 0 5px 0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5
                }}>
                  {promoSettings?.upgrade_promo_title || '⚠️ Limited Time Offer!'}
                </p>
                <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: 0, lineHeight: 1.4 }}>
                  {promoSettings?.upgrade_promo_message || 'Pay As You Go pricing is available while supplies last! We are testing our business model to see if we can sustain this incredible platform. Google Maps API keys and AI Search subscriptions are expensive - your support helps keep InfoPilot running!'}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Legal Documents */}
        <div style={{ marginTop: 20, padding: 20, background: 'rgba(39, 39, 42, 0.5)', borderRadius: 10 }}>
          <h3 style={{ marginBottom: 15, color: '#a1a1aa', fontSize: '1rem' }}>📜 Legal Documents</h3>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button 
              className="btn btn-secondary" 
              onClick={() => fetchLegalDocument('terms')}
              style={{ fontSize: '0.85rem' }}
              data-testid="view-terms-btn"
            >
              📋 User Agreement
            </button>
            <button 
              className="btn btn-secondary" 
              onClick={() => fetchLegalDocument('privacy')}
              style={{ fontSize: '0.85rem' }}
              data-testid="view-privacy-btn"
            >
              🔒 Privacy Policy
            </button>
          </div>
          <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
            Top Pilot Enterprises, Inc. • Brunswick, Maine
          </p>
        </div>
        
        {/* Legal Document Modal */}
        {showLegal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.85)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 20
          }}>
            <div style={{
              background: '#1a1a2e',
              borderRadius: 16,
              padding: 25,
              maxWidth: 800,
              maxHeight: '80vh',
              overflow: 'auto',
              width: '100%',
              border: '1px solid rgba(124, 58, 237, 0.3)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <h2 style={{ color: '#f472b6', margin: 0 }}>
                  {showLegal === 'terms' ? '📋 User Agreement' : '🔒 Privacy Policy'}
                </h2>
                <button 
                  onClick={() => setShowLegal(null)}
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid #ef4444',
                    color: '#ef4444',
                    padding: '8px 15px',
                    borderRadius: 8,
                    cursor: 'pointer'
                  }}
                >
                  ✕ Close
                </button>
              </div>
              <div style={{ 
                color: '#e4e4e7', 
                lineHeight: 1.7, 
                fontSize: '0.9rem',
                whiteSpace: 'pre-wrap'
              }}>
                {legalContent.split('\n').map((line, i) => {
                  if (line.startsWith('# ')) return <h1 key={i} style={{ color: '#f472b6', marginTop: 20 }}>{line.replace('# ', '')}</h1>;
                  if (line.startsWith('## ')) return <h2 key={i} style={{ color: '#a78bfa', marginTop: 15, fontSize: '1.2rem' }}>{line.replace('## ', '')}</h2>;
                  if (line.startsWith('### ')) return <h3 key={i} style={{ color: '#60a5fa', marginTop: 12, fontSize: '1rem' }}>{line.replace('### ', '')}</h3>;
                  if (line.startsWith('**') && line.endsWith('**')) return <p key={i} style={{ fontWeight: 600 }}>{line.replace(/\*\*/g, '')}</p>;
                  if (line.startsWith('- ')) return <li key={i} style={{ marginLeft: 20 }}>{line.replace('- ', '')}</li>;
                  if (line === '---') return <hr key={i} style={{ border: 'none', borderTop: '1px solid rgba(124, 58, 237, 0.3)', margin: '20px 0' }} />;
                  return <p key={i}>{line}</p>;
                })}
              </div>
            </div>
          </div>
        )}

        {/* Push Notifications Section */}
        <div style={{ marginTop: 20 }}>
          <PushNotifications showToast={showToast} />
        </div>

        {/* Data Export Section */}
        <div style={{ marginTop: 20 }}>
          <DataExport showToast={showToast} />
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
