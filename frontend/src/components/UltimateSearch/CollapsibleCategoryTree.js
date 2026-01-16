import React, { useState, useMemo } from 'react';

/**
 * Collapsible Category Tree Component
 * Displays categories in a hierarchical tree with +/- expansion buttons
 * Shows result counts in parentheses next to each category
 * Includes Quick Search filter to find categories by name
 */
const CollapsibleCategoryTree = ({
  categories,
  selectedCategories,
  onToggleSelect,
  onSelectAll,
  onDeselectAll,
  onEdit,
  onDelete,
  onViewDetails,
  isOwner = false,
  compact = false
}) => {
  // Track which categories are expanded
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  // Quick search filter
  const [searchFilter, setSearchFilter] = useState('');

  // Build hierarchy from flat category list
  const categoryTree = useMemo(() => {
    if (!categories || categories.length === 0) return [];
    
    const categoryMap = new Map();
    const roots = [];
    
    // First pass: Create map of all categories
    categories.forEach(cat => {
      const id = cat.id || cat._id;
      categoryMap.set(id, { ...cat, children: [] });
    });
    
    // Second pass: Build tree structure
    categories.forEach(cat => {
      const id = cat.id || cat._id;
      const node = categoryMap.get(id);
      
      if (cat.parent_id && categoryMap.has(cat.parent_id)) {
        categoryMap.get(cat.parent_id).children.push(node);
      } else {
        roots.push(node);
      }
    });
    
    // Sort by name
    const sortByName = (a, b) => (a.name || '').localeCompare(b.name || '');
    roots.sort(sortByName);
    categoryMap.forEach(node => node.children.sort(sortByName));
    
    return roots;
  }, [categories]);

  // Filter categories by search term (include parents of matching children)
  const filteredTree = useMemo(() => {
    if (!searchFilter.trim()) return categoryTree;
    
    const searchLower = searchFilter.toLowerCase();
    
    const filterNode = (node) => {
      const nameMatches = (node.name || '').toLowerCase().includes(searchLower);
      
      // Recursively filter children
      const filteredChildren = (node.children || [])
        .map(child => filterNode(child))
        .filter(child => child !== null);
      
      // Include node if name matches OR any children match
      if (nameMatches || filteredChildren.length > 0) {
        return { ...node, children: filteredChildren };
      }
      
      return null;
    };
    
    return categoryTree.map(root => filterNode(root)).filter(node => node !== null);
  }, [categoryTree, searchFilter]);

  // Calculate total result count for a category including all descendants
  const getTotalResultCount = (category) => {
    let count = category.result_count || 0;
    if (category.children) {
      category.children.forEach(child => {
        count += getTotalResultCount(child);
      });
    }
    return count;
  };

  // Toggle expand/collapse
  const toggleExpand = (categoryId, e) => {
    e.stopPropagation();
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  // Expand all categories
  const expandAll = () => {
    const allIds = new Set();
    const addIds = (cats) => {
      cats.forEach(cat => {
        if (cat.children && cat.children.length > 0) {
          allIds.add(cat.id || cat._id);
          addIds(cat.children);
        }
      });
    };
    addIds(filteredTree);
    setExpandedCategories(allIds);
  };

  // Collapse all categories
  const collapseAll = () => {
    setExpandedCategories(new Set());
  };

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
    <div data-testid="collapsible-category-tree">
      {/* Quick Search Filter */}
      <div style={{ marginBottom: 12 }}>
        <input
          type="text"
          placeholder="🔍 Search categories..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          data-testid="category-search-filter"
          style={{
            width: '100%',
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid rgba(139, 92, 246, 0.3)',
            background: 'rgba(0,0,0,0.3)',
            color: '#fff',
            fontSize: '0.85rem',
            outline: 'none'
          }}
        />
        {searchFilter && (
          <div style={{ 
            marginTop: 6, 
            fontSize: '0.75rem', 
            color: '#a78bfa',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span>Found {filteredTree.length} matching categories</span>
            <button
              onClick={() => setSearchFilter('')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#f87171',
                cursor: 'pointer',
                fontSize: '0.75rem'
              }}
            >
              ✕ Clear
            </button>
          </div>
        )}
      </div>

      {/* Control Bar */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 12,
        flexWrap: 'wrap',
        gap: 8
      }}>
        <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
          {selectedCategories.length} of {categories.length} selected
        </span>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <button
            onClick={expandAll}
            data-testid="expand-all-btn"
            style={{
              background: 'rgba(139, 92, 246, 0.2)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              color: '#a78bfa',
              padding: '4px 10px',
              borderRadius: 6,
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            + Expand All
          </button>
          <button
            onClick={collapseAll}
            data-testid="collapse-all-btn"
            style={{
              background: 'rgba(139, 92, 246, 0.2)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              color: '#a78bfa',
              padding: '4px 10px',
              borderRadius: 6,
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            - Collapse All
          </button>
          <button
            onClick={onSelectAll}
            data-testid="select-all-btn"
            style={{
              background: 'rgba(16, 185, 129, 0.2)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#10b981',
              padding: '4px 10px',
              borderRadius: 6,
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            Select All
          </button>
          <button
            onClick={onDeselectAll}
            data-testid="deselect-all-btn"
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              padding: '4px 10px',
              borderRadius: 6,
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            Deselect All
          </button>
        </div>
      </div>

      {/* Tree View */}
      <div style={{
        background: 'rgba(0,0,0,0.2)',
        borderRadius: 12,
        padding: compact ? 10 : 15,
        maxHeight: '500px',
        overflowY: 'auto'
      }}>
        {filteredTree.length === 0 && searchFilter ? (
          <div style={{ textAlign: 'center', padding: 20, color: '#a1a1aa' }}>
            <p style={{ margin: 0 }}>No categories match "{searchFilter}"</p>
          </div>
        ) : (
          filteredTree.map(category => (
            <CategoryTreeNode
              key={category.id || category._id}
              category={category}
              level={0}
              expanded={expandedCategories}
              onToggleExpand={toggleExpand}
              selectedCategories={selectedCategories}
              onToggleSelect={onToggleSelect}
              onEdit={onEdit}
              onDelete={onDelete}
              onViewDetails={onViewDetails}
              isOwner={isOwner}
              compact={compact}
              getTotalResultCount={getTotalResultCount}
            />
          ))
        )}
      </div>
    </div>
  );
};

/**
 * Individual Category Tree Node (recursive)
 */
const CategoryTreeNode = ({
  category,
  level,
  expanded,
  onToggleExpand,
  selectedCategories,
  onToggleSelect,
  onEdit,
  onDelete,
  onViewDetails,
  isOwner,
  compact,
  getTotalResultCount
}) => {
  const categoryId = category.id || category._id;
  const hasChildren = category.children && category.children.length > 0;
  const isExpanded = expanded.has(categoryId);
  const isSelected = selectedCategories.includes(categoryId);
  const resultCount = category.result_count || 0;
  const totalCount = getTotalResultCount(category);
  const indent = level * (compact ? 16 : 20);

  return (
    <div data-testid={`category-node-${categoryId}`}>
      {/* Category Row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: compact ? '6px 8px' : '8px 12px',
          marginLeft: indent,
          marginBottom: 2,
          borderRadius: 8,
          background: isSelected 
            ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(59, 130, 246, 0.2))'
            : 'rgba(255,255,255,0.03)',
          border: isSelected 
            ? '1px solid rgba(139, 92, 246, 0.5)'
            : '1px solid transparent',
          cursor: 'pointer',
          transition: 'all 0.15s'
        }}
        onClick={() => onToggleSelect(categoryId)}
        onMouseEnter={(e) => {
          if (!isSelected) {
            e.currentTarget.style.background = 'rgba(139, 92, 246, 0.1)';
          }
        }}
        onMouseLeave={(e) => {
          if (!isSelected) {
            e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
          }
        }}
      >
        {/* Expand/Collapse Button */}
        <div
          onClick={(e) => hasChildren && onToggleExpand(categoryId, e)}
          style={{
            width: 22,
            height: 22,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: 8,
            borderRadius: 4,
            background: hasChildren ? 'rgba(139, 92, 246, 0.3)' : 'transparent',
            color: hasChildren ? '#a78bfa' : '#52525b',
            fontSize: '0.9rem',
            fontWeight: 'bold',
            cursor: hasChildren ? 'pointer' : 'default',
            flexShrink: 0
          }}
        >
          {hasChildren ? (isExpanded ? '−' : '+') : '•'}
        </div>

        {/* Checkbox */}
        <div
          style={{
            width: 18,
            height: 18,
            borderRadius: 4,
            background: isSelected ? '#8b5cf6' : 'rgba(255,255,255,0.1)',
            border: '2px solid rgba(255,255,255,0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: 10,
            flexShrink: 0
          }}
        >
          {isSelected && <span style={{ color: '#fff', fontSize: '0.7rem' }}>✓</span>}
        </div>

        {/* Category Name with Count */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <span style={{ 
            color: '#fff', 
            fontSize: compact ? '0.85rem' : '0.9rem',
            fontWeight: 500
          }}>
            {category.name}
          </span>
          
          {/* Result Count in Parentheses */}
          {totalCount > 0 && (
            <span style={{ 
              color: '#10b981', 
              fontSize: compact ? '0.75rem' : '0.8rem',
              marginLeft: 6,
              fontWeight: 600
            }}>
              ({totalCount})
            </span>
          )}
          
          {/* Child count indicator */}
          {hasChildren && (
            <span style={{ 
              color: '#a78bfa', 
              fontSize: '0.7rem',
              marginLeft: 6
            }}>
              [{category.children.length} sub]
            </span>
          )}
        </div>

        {/* Price Badge */}
        {category.price > 0 && (
          <span style={{
            background: 'linear-gradient(135deg, #10b981, #059669)',
            padding: '2px 8px',
            borderRadius: 10,
            fontSize: '0.7rem',
            fontWeight: 600,
            color: '#fff',
            marginLeft: 8,
            flexShrink: 0
          }}>
            ${category.price.toFixed(2)}
          </span>
        )}

        {/* Public Badge */}
        {category.is_public && (
          <span style={{
            background: 'rgba(59, 130, 246, 0.3)',
            padding: '2px 6px',
            borderRadius: 10,
            fontSize: '0.65rem',
            color: '#60a5fa',
            marginLeft: 6,
            flexShrink: 0
          }}>
            PUBLIC
          </span>
        )}

        {/* Action Buttons (for owners) */}
        {isOwner && !compact && (
          <div 
            style={{ display: 'flex', gap: 4, marginLeft: 8 }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => onEdit && onEdit(category)}
              title="Edit"
              style={{
                background: 'rgba(251, 191, 36, 0.2)',
                border: 'none',
                color: '#fbbf24',
                padding: '3px 6px',
                borderRadius: 4,
                fontSize: '0.7rem',
                cursor: 'pointer'
              }}
            >
              ✏️
            </button>
            <button
              onClick={() => onDelete && onDelete(categoryId)}
              title="Delete"
              style={{
                background: 'rgba(239, 68, 68, 0.2)',
                border: 'none',
                color: '#f87171',
                padding: '3px 6px',
                borderRadius: 4,
                fontSize: '0.7rem',
                cursor: 'pointer'
              }}
            >
              🗑️
            </button>
          </div>
        )}
      </div>

      {/* Children (if expanded) */}
      {hasChildren && isExpanded && (
        <div>
          {category.children.map(child => (
            <CategoryTreeNode
              key={child.id || child._id}
              category={child}
              level={level + 1}
              expanded={expanded}
              onToggleExpand={onToggleExpand}
              selectedCategories={selectedCategories}
              onToggleSelect={onToggleSelect}
              onEdit={onEdit}
              onDelete={onDelete}
              onViewDetails={onViewDetails}
              isOwner={isOwner}
              compact={compact}
              getTotalResultCount={getTotalResultCount}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default CollapsibleCategoryTree;
export { CategoryTreeNode };
