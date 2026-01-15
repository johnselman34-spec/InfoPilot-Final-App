import React from 'react';

/**
 * ProtocolCard - Individual protocol display in marketplace
 */
export const ProtocolCard = ({ 
  protocol, 
  onCopy, 
  onBuy, 
  onView, 
  isOwned, 
  isFree,
  currentUserId 
}) => {
  const isCreator = protocol.creator_id === currentUserId;
  const price = protocol.price || 0;
  
  return (
    <div style={{
      background: 'rgba(30, 20, 50, 0.7)',
      borderRadius: 15,
      padding: 20,
      border: isFree ? '2px solid rgba(16, 185, 129, 0.5)' : '1px solid rgba(124, 58, 237, 0.3)',
      position: 'relative',
      transition: 'transform 0.2s, box-shadow 0.2s',
      cursor: 'pointer'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-5px)';
      e.currentTarget.style.boxShadow = '0 10px 30px rgba(124, 58, 237, 0.3)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = 'none';
    }}
    onClick={() => onView?.(protocol)}
    >
      {/* Price Badge */}
      <div style={{
        position: 'absolute',
        top: -10,
        right: 15,
        padding: '6px 15px',
        borderRadius: 20,
        background: isFree 
          ? 'linear-gradient(135deg, #10b981, #059669)' 
          : 'linear-gradient(135deg, #f59e0b, #d97706)',
        color: 'white',
        fontWeight: 'bold',
        fontSize: '0.9rem',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
      }}>
        {isFree ? '🎁 FREE' : `$${price.toFixed(2)}`}
      </div>

      {/* Protocol Name */}
      <h3 style={{ 
        color: '#e2e8f0', 
        margin: '15px 0 10px 0',
        fontSize: '1.1rem'
      }}>
        {protocol.name}
      </h3>

      {/* Category */}
      <div style={{
        display: 'inline-block',
        padding: '3px 10px',
        background: 'rgba(124, 58, 237, 0.2)',
        borderRadius: 15,
        fontSize: '0.75rem',
        color: '#a78bfa',
        marginBottom: 10
      }}>
        {protocol.category || 'General'}
      </div>

      {/* Protocol Preview */}
      {protocol.protocol && (
        <div style={{
          padding: 10,
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 8,
          fontFamily: 'monospace',
          fontSize: '0.75rem',
          color: '#10b981',
          marginBottom: 15,
          maxHeight: 60,
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>
          {protocol.protocol.substring(0, 100)}{protocol.protocol.length > 100 ? '...' : ''}
        </div>
      )}

      {/* Stats */}
      <div style={{ 
        display: 'flex', 
        gap: 15, 
        marginBottom: 15,
        fontSize: '0.8rem',
        color: '#a1a1aa'
      }}>
        <span>📋 {protocol.copies || 0} copies</span>
        <span>👁️ {protocol.views || 0} views</span>
        {protocol.rating && <span>⭐ {protocol.rating.toFixed(1)}</span>}
      </div>

      {/* Creator */}
      <div style={{ 
        fontSize: '0.8rem', 
        color: '#71717a',
        marginBottom: 15
      }}>
        by {protocol.creator?.username || 'Anonymous'}
        {isCreator && <span style={{ color: '#10b981', marginLeft: 10 }}>👤 You</span>}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 10 }} onClick={(e) => e.stopPropagation()}>
        {isOwned || isCreator ? (
          <button 
            className="btn btn-primary" 
            onClick={() => onCopy?.(protocol)}
            style={{ flex: 1 }}
          >
            📋 Copy Protocol
          </button>
        ) : isFree ? (
          <button 
            className="btn btn-primary" 
            onClick={() => onCopy?.(protocol)}
            style={{ flex: 1, background: 'linear-gradient(135deg, #10b981, #059669)' }}
          >
            🎁 Get FREE
          </button>
        ) : (
          <button 
            className="btn btn-primary" 
            onClick={() => onBuy?.(protocol)}
            style={{ flex: 1, background: 'linear-gradient(135deg, #f59e0b, #d97706)' }}
          >
            💳 Buy ${price.toFixed(2)}
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * CategoryFilter - Category selection for filtering
 */
export const CategoryFilter = ({ 
  categories, 
  selectedCategories, 
  onToggle, 
  onSelectAll, 
  onDeselectAll 
}) => {
  const categoryColors = {
    'General': '#7c3aed',
    'News & Media': '#f59e0b',
    'Technology': '#3b82f6',
    'Science & Research': '#10b981',
    'Business & Finance': '#ef4444',
    'Entertainment': '#f472b6',
    'Sports': '#06b6d4',
    'Health & Medicine': '#84cc16'
  };

  return (
    <div style={{
      background: 'rgba(30, 20, 50, 0.5)',
      borderRadius: 12,
      padding: 15,
      marginBottom: 20
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 15
      }}>
        <h4 style={{ margin: 0, color: '#f472b6' }}>🏷️ Filter by Category</h4>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={onSelectAll} style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
            Select All
          </button>
          <button className="btn btn-secondary" onClick={onDeselectAll} style={{ padding: '4px 10px', fontSize: '0.75rem' }}>
            Clear
          </button>
        </div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {categories.map(cat => {
          const isSelected = selectedCategories.includes(cat);
          const color = categoryColors[cat] || '#7c3aed';
          
          return (
            <button
              key={cat}
              onClick={() => onToggle(cat)}
              style={{
                padding: '6px 12px',
                borderRadius: 20,
                background: isSelected ? `${color}30` : 'rgba(30, 20, 50, 0.8)',
                border: isSelected ? `2px solid ${color}` : '1px solid rgba(124, 58, 237, 0.3)',
                color: isSelected ? color : '#a1a1aa',
                cursor: 'pointer',
                fontSize: '0.8rem',
                transition: 'all 0.2s'
              }}
            >
              {cat}
            </button>
          );
        })}
      </div>
    </div>
  );
};

/**
 * ProtocolStats - Stats display for protocol analytics
 */
export const ProtocolStats = ({ stats }) => {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
      gap: 15,
      marginBottom: 20
    }}>
      {[
        { label: 'Total Protocols', value: stats?.total || 0, icon: '📋', color: '#8b5cf6' },
        { label: 'Free Protocols', value: stats?.free || 0, icon: '🎁', color: '#10b981' },
        { label: 'Paid Protocols', value: stats?.paid || 0, icon: '💰', color: '#f59e0b' },
        { label: 'Total Copies', value: stats?.copies || 0, icon: '📥', color: '#3b82f6' },
        { label: 'Total Revenue', value: `$${(stats?.revenue || 0).toFixed(2)}`, icon: '💎', color: '#ec4899' }
      ].map((stat, idx) => (
        <div key={idx} style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          padding: 15,
          textAlign: 'center',
          border: `1px solid ${stat.color}30`
        }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 5 }}>{stat.icon}</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: stat.color }}>
            {stat.value}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#a1a1aa' }}>{stat.label}</div>
        </div>
      ))}
    </div>
  );
};

/**
 * SellProtocolForm - Form for listing a protocol for sale
 */
export const SellProtocolForm = ({ onSubmit, loading, categories }) => {
  const [formData, setFormData] = React.useState({
    name: '',
    protocol: '',
    category: 'General',
    price: '',
    description: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            Protocol Name *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="My Awesome Protocol"
            className="input-field"
            required
          />
        </div>
        
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            Protocol Content *
          </label>
          <textarea
            value={formData.protocol}
            onChange={(e) => setFormData({ ...formData, protocol: e.target.value })}
            placeholder="(keyword1 or keyword2) & (keyword3)+"
            className="input-field"
            style={{ minHeight: 100, fontFamily: 'monospace' }}
            required
          />
        </div>
        
        <div style={{ display: 'flex', gap: 15 }}>
          <div style={{ flex: 1 }}>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
              Category
            </label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="input-field"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          
          <div style={{ flex: 1 }}>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
              Price ($) - Leave empty for FREE
            </label>
            <input
              type="number"
              min="0"
              max="99"
              step="0.01"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              placeholder="0.00"
              className="input-field"
            />
          </div>
        </div>
        
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            Description (optional)
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="What does this protocol help users find?"
            className="input-field"
            style={{ minHeight: 60 }}
          />
        </div>
        
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={loading || !formData.name || !formData.protocol}
        >
          {loading ? '⏳ Listing...' : '🚀 List Protocol'}
        </button>
      </div>
    </form>
  );
};

export default ProtocolCard;
