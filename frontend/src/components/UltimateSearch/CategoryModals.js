import React from 'react';

/**
 * CreateCategoryModal - Modal for creating new categories
 */
const CreateCategoryModal = ({
  show,
  onClose,
  newCategory,
  setNewCategory,
  categories,
  onCreate
}) => {
  if (!show) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create Category</h2>
          <button className="modal-close" onClick={onClose}>×</button>
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
          <button className="btn btn-primary" onClick={onCreate} data-testid="create-category-btn">
            Create Category
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * EditCategoryModal - Modal for editing existing categories
 */
const EditCategoryModal = ({
  editingCategory,
  onClose,
  editCategoryName,
  setEditCategoryName,
  editProtocol,
  setEditProtocol,
  editIsPublic,
  setEditIsPublic,
  editPrice,
  setEditPrice,
  user,
  onSave
}) => {
  if (!editingCategory) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 550 }}>
        <div className="modal-header">
          <h2>Edit Category</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
          {/* Category Name Edit */}
          <label style={{ color: '#f472b6', fontWeight: 600 }}>Category Name:</label>
          <input
            className="input-field"
            placeholder="Category Name"
            value={editCategoryName}
            onChange={(e) => setEditCategoryName(e.target.value)}
            data-testid="edit-category-name-input"
          />
          
          <div style={{ 
            background: 'rgba(124, 58, 237, 0.1)', 
            padding: 15, 
            borderRadius: 10,
            borderLeft: '4px solid #7c3aed'
          }}>
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
            className="input-field"
            placeholder="Enter new protocol (e.g., (keyphrase1 or keyphrase2) & (keyphrase3)+)"
            rows={5}
            value={editProtocol}
            onChange={(e) => setEditProtocol(e.target.value)}
            style={{ resize: 'vertical', fontFamily: 'monospace' }}
            data-testid="edit-protocol-input"
          />
          
          {/* Protocol Syntax Help */}
          <div style={{
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 8,
            padding: 12,
            fontSize: '0.8rem'
          }}>
            <p style={{ color: '#10b981', fontWeight: 600, marginBottom: 8 }}>📝 Protocol Syntax Help:</p>
            <ul style={{ color: '#a1a1aa', margin: 0, paddingLeft: 20, lineHeight: 1.6 }}>
              <li><code style={{ color: '#f472b6' }}>or</code> - Separate alternatives within a group</li>
              <li><code style={{ color: '#f472b6' }}>&</code> <strong>or</strong> <code style={{ color: '#f472b6' }}>and</code> - Connect groups (both work!)</li>
              <li><code style={{ color: '#f472b6' }}>+</code> - Boost priority of a group</li>
              <li><code style={{ color: '#f472b6' }}>^</code> - Exclude matches containing these terms</li>
            </ul>
            <p style={{ color: '#22d3ee', marginTop: 10, marginBottom: 0 }}>
              ✨ <strong>Tip:</strong> "and" works the same as "&" between groups!<br/>
              <span style={{ color: '#a1a1aa' }}>Example: <code>(aviation or pilot) and (safety)</code></span>
            </p>
          </div>
          
          {/* Visibility Toggle */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            padding: '12px 15px',
            background: editIsPublic ? 'rgba(16, 185, 129, 0.15)' : 'rgba(107, 114, 128, 0.15)',
            borderRadius: 10,
            border: `1px solid ${editIsPublic ? 'rgba(16, 185, 129, 0.3)' : 'rgba(107, 114, 128, 0.3)'}`
          }}>
            <div>
              <label style={{ 
                color: editIsPublic ? '#10b981' : '#9ca3af', 
                fontWeight: 600,
                display: 'block',
                marginBottom: 4
              }}>
                {editIsPublic ? '🌍 Public Category' : '🔒 Private Category'}
              </label>
              <p style={{ fontSize: '0.75rem', color: '#a1a1aa', margin: 0 }}>
                {editIsPublic 
                  ? 'This category is visible to all users' 
                  : 'Only you can see this category'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setEditIsPublic(!editIsPublic)}
              style={{
                width: 50,
                height: 28,
                borderRadius: 14,
                background: editIsPublic 
                  ? 'linear-gradient(135deg, #10b981, #059669)' 
                  : '#4b5563',
                border: 'none',
                cursor: 'pointer',
                position: 'relative',
                transition: 'background 0.2s'
              }}
              data-testid="edit-visibility-toggle"
            >
              <span style={{
                position: 'absolute',
                top: 2,
                left: editIsPublic ? 24 : 2,
                width: 24,
                height: 24,
                borderRadius: '50%',
                background: 'white',
                transition: 'left 0.2s',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
              }} />
            </button>
          </div>
          
          {/* Price Setting */}
          <div style={{ 
            padding: '12px 15px',
            background: 'rgba(245, 158, 11, 0.1)',
            borderRadius: 10,
            border: '1px solid rgba(245, 158, 11, 0.3)'
          }}>
            <label style={{ 
              color: '#f59e0b', 
              fontWeight: 600,
              display: 'block',
              marginBottom: 8
            }}>
              💰 Protocol Price (Optional)
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ color: '#f59e0b', fontSize: '1.2rem' }}>$</span>
              <input
                type="number"
                min="0"
                max="99"
                step="0.01"
                placeholder="0.00 (FREE)"
                value={editPrice}
                onChange={(e) => setEditPrice(e.target.value)}
                className="input-field"
                style={{ flex: 1, maxWidth: 150 }}
                data-testid="edit-price-input"
              />
              <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                {editPrice && parseFloat(editPrice) > 0 
                  ? `Will sell for $${parseFloat(editPrice).toFixed(2)}` 
                  : 'FREE to copy'}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#a1a1aa', margin: '8px 0 0 0' }}>
              Set a price ($1-$99) to sell this protocol on the marketplace, or leave empty/0 for FREE.
            </p>
          </div>

          {/* PayPal Connect Notice */}
          {editPrice && parseFloat(editPrice) > 0 && !user?.paypal_connected && (
            <div style={{ 
              padding: '15px',
              background: 'linear-gradient(135deg, rgba(0, 112, 186, 0.15) 0%, rgba(0, 48, 135, 0.15) 100%)',
              borderRadius: 10,
              border: '1px solid rgba(0, 112, 186, 0.3)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <span style={{ fontSize: '1.5rem' }}>💳</span>
                <div>
                  <h4 style={{ color: '#0070ba', margin: 0 }}>Connect PayPal to Sell</h4>
                  <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: 0 }}>
                    Connect your PayPal to receive payments when users buy your protocol
                  </p>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: 10 }}>
                <a
                  href="https://www.paypal.com/connect?flowEntry=static&client_id=BAABmhMWqe1WrfJkqJ7RRzEZwoAfxSF2bclm8_HY2BuU9C-7pnakTdjFVCvSJyWh63-wUWmKN1cT1hdMIY&scope=openid email&redirect_uri=https://infopilotexplorer.biz/paypal-callback"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '12px 24px',
                    background: '#0070ba',
                    color: 'white',
                    borderRadius: 25,
                    textDecoration: 'none',
                    fontWeight: 600,
                    fontSize: '0.95rem'
                  }}
                  data-testid="paypal-connect-btn"
                >
                  Connect with PayPal
                </a>
              </div>
            </div>
          )}

          {user?.paypal_connected && editPrice && parseFloat(editPrice) > 0 && (
            <div style={{ 
              padding: '12px 15px',
              background: 'rgba(16, 185, 129, 0.1)',
              borderRadius: 10,
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: 10
            }}>
              <span style={{ fontSize: '1.5rem' }}>✅</span>
              <div>
                <p style={{ color: '#10b981', fontWeight: 600, margin: 0 }}>PayPal Connected</p>
                <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: 0 }}>
                  You'll receive payments to your connected PayPal account
                </p>
              </div>
            </div>
          )}
          
          {/* Protocol Syntax Guide */}
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
              onClick={onClose}
              style={{ flex: 1 }}
            >
              Cancel
            </button>
            <button 
              className="btn btn-primary" 
              onClick={onSave}
              style={{ flex: 1 }}
              data-testid="save-protocol-btn"
            >
              Save Protocol
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export { CreateCategoryModal, EditCategoryModal };
