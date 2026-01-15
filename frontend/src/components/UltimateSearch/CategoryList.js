import React from 'react';

/**
 * Category List Component
 * Displays and manages search categories/protocols
 */
const CategoryList = ({
  categories,
  selectedCategories,
  onToggle,
  onSelectAll,
  onDeselectAll,
  onEdit,
  onDelete,
  onViewDetails,
  isOwner = false
}) => {
  if (!categories || categories.length === 0) {
    return (
      <div style={{
        background: 'rgba(139, 92, 246, 0.1)',
        borderRadius: 12,
        padding: 30,
        textAlign: 'center',
        border: '1px dashed rgba(139, 92, 246, 0.3)'
      }}>
        <div style={{ fontSize: '2rem', marginBottom: 10, opacity: 0.6 }}>📂</div>
        <p style={{ color: '#a1a1aa', margin: 0 }}>No categories yet</p>
        <p style={{ color: '#71717a', margin: '5px 0 0 0', fontSize: '0.85rem' }}>
          Create your first search category to get started
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Selection Controls */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 15
      }}>
        <span style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          {selectedCategories.length} of {categories.length} selected
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={onSelectAll}
            style={{
              background: 'rgba(16, 185, 129, 0.2)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#10b981',
              padding: '6px 12px',
              borderRadius: 6,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            Select All
          </button>
          <button
            onClick={onDeselectAll}
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              padding: '6px 12px',
              borderRadius: 6,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            Deselect All
          </button>
        </div>
      </div>

      {/* Categories Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 12
      }}>
        {categories.map((category) => (
          <CategoryCard
            key={category.id || category._id}
            category={category}
            isSelected={selectedCategories.includes(category.id || category._id)}
            onToggle={() => onToggle(category.id || category._id)}
            onEdit={() => onEdit && onEdit(category)}
            onDelete={() => onDelete && onDelete(category.id || category._id)}
            onViewDetails={() => onViewDetails && onViewDetails(category)}
            isOwner={isOwner}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Individual Category Card with Result Count
 */
const CategoryCard = ({
  category,
  isSelected,
  onToggle,
  onEdit,
  onDelete,
  onViewDetails,
  isOwner
}) => {
  const protocolPreview = (category.protocol || '').slice(0, 100);
  const resultCount = category.result_count || 0;
  const subcategoryCount = category.subcategory_count || 0;

  return (
    <div
      onClick={onToggle}
      data-testid={`category-card-${category.id || category._id}`}
      style={{
        background: isSelected 
          ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(59, 130, 246, 0.2))'
          : 'rgba(0,0,0,0.2)',
        borderRadius: 12,
        padding: 15,
        cursor: 'pointer',
        border: isSelected 
          ? '2px solid rgba(139, 92, 246, 0.5)'
          : '2px solid transparent',
        transition: 'all 0.2s',
        position: 'relative'
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.background = 'rgba(139, 92, 246, 0.1)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.background = 'rgba(0,0,0,0.2)';
        }
      }}
    >
      {/* Selection Indicator */}
      <div style={{
        position: 'absolute',
        top: 10,
        right: 10,
        width: 24,
        height: 24,
        borderRadius: '50%',
        background: isSelected ? '#8b5cf6' : 'rgba(255,255,255,0.1)',
        border: '2px solid rgba(255,255,255,0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {isSelected && <span style={{ color: '#fff', fontSize: '0.8rem' }}>✓</span>}
      </div>
      
      {/* Result Count Badge */}
      {resultCount > 0 && (
        <div style={{
          position: 'absolute',
          top: 10,
          left: 10,
          background: 'linear-gradient(135deg, #10b981, #059669)',
          color: '#fff',
          padding: '3px 8px',
          borderRadius: 12,
          fontSize: '0.75rem',
          fontWeight: 700,
          boxShadow: '0 2px 8px rgba(16, 185, 129, 0.4)'
        }}>
          {resultCount} result{resultCount !== 1 ? 's' : ''}
        </div>
      )}

      {/* Category Name */}
      <h4 style={{ 
        color: '#fff', 
        margin: '0 0 8px 0',
        paddingRight: 30,
        fontSize: '1rem'
      }}>
        {category.name}
      </h4>

      {/* Protocol Preview */}
      <p style={{ 
        color: '#a1a1aa', 
        margin: '0 0 12px 0',
        fontSize: '0.8rem',
        lineHeight: 1.4,
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden'
      }}>
        {protocolPreview || 'No protocol defined'}
        {(category.protocol || '').length > 100 && '...'}
      </p>

      {/* Price Badge (if marketplace) */}
      {category.price !== undefined && category.price > 0 && (
        <span style={{
          background: 'linear-gradient(135deg, #10b981, #059669)',
          padding: '4px 10px',
          borderRadius: 12,
          fontSize: '0.75rem',
          fontWeight: 600,
          color: '#fff',
          marginRight: 8
        }}>
          ${category.price.toFixed(2)}
        </span>
      )}

      {/* Action Buttons */}
      {isOwner && (
        <div 
          style={{ 
            display: 'flex', 
            gap: 8, 
            marginTop: 10,
            borderTop: '1px solid rgba(255,255,255,0.1)',
            paddingTop: 10
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={onViewDetails}
            style={{
              background: 'rgba(59, 130, 246, 0.2)',
              border: 'none',
              color: '#3b82f6',
              padding: '5px 10px',
              borderRadius: 6,
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            View
          </button>
          <button
            onClick={onEdit}
            style={{
              background: 'rgba(251, 191, 36, 0.2)',
              border: 'none',
              color: '#fbbf24',
              padding: '5px 10px',
              borderRadius: 6,
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              border: 'none',
              color: '#f87171',
              padding: '5px 10px',
              borderRadius: 6,
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
};

export default CategoryList;
export { CategoryCard };
