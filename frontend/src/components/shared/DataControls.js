/**
 * DataControls - Reusable data control components
 * Features:
 * - Data source toggle (Personal/Worldwide)
 * - Select All/Deselect All for checkbox groups
 * - Document type filter with select all
 * - Compact design with funny messages
 */
import React from 'react';

// Funny loading/status messages
const FUNNY_MESSAGES = [
  "🚀 Data faster than a rocket-powered banana!",
  "📊 Numbers so fresh, they're still wearing dew!",
  "🎯 Accuracy level: Laser-guided wisdom!",
  "💡 Insights brighter than a supernova!",
  "🌟 Stats so good, even calculators are jealous!",
  "🎪 Welcome to the greatest data show on Earth!",
  "🦸 Your data superhero has arrived!",
  "🎭 Drama-free statistics, comedy included!",
];

/**
 * DataSourceToggle - Toggle between Personal and Worldwide data
 */
export const DataSourceToggle = ({ 
  dataSource, 
  setDataSource, 
  personalCount = 0, 
  worldwideCount = 0,
  compact = false 
}) => {
  const funnyMessage = FUNNY_MESSAGES[Math.floor(Math.random() * FUNNY_MESSAGES.length)];
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(236, 72, 153, 0.1))',
      borderRadius: compact ? 10 : 15,
      padding: compact ? '8px 12px' : '12px 20px',
      border: '1px solid rgba(139, 92, 246, 0.3)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: 10
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: compact ? '0.9rem' : '1rem' }}>🌐</span>
        <span style={{ 
          color: '#f472b6', 
          fontWeight: 600, 
          fontSize: compact ? '0.8rem' : '0.9rem' 
        }}>
          Data Source:
        </span>
        {!compact && (
          <span style={{ color: '#a1a1aa', fontSize: '0.7rem', fontStyle: 'italic' }}>
            {funnyMessage}
          </span>
        )}
      </div>
      
      <div style={{ 
        display: 'flex', 
        background: 'rgba(0,0,0,0.3)', 
        borderRadius: 20, 
        padding: 3 
      }}>
        <button
          onClick={() => setDataSource('personal')}
          style={{
            padding: compact ? '5px 12px' : '8px 16px',
            borderRadius: 18,
            border: 'none',
            background: dataSource === 'personal' 
              ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)' 
              : 'transparent',
            color: dataSource === 'personal' ? '#fff' : '#a1a1aa',
            cursor: 'pointer',
            fontSize: compact ? '0.75rem' : '0.85rem',
            fontWeight: 600,
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: 5
          }}
        >
          👤 My Data {personalCount > 0 && `(${personalCount})`}
        </button>
        <button
          onClick={() => setDataSource('worldwide')}
          style={{
            padding: compact ? '5px 12px' : '8px 16px',
            borderRadius: 18,
            border: 'none',
            background: dataSource === 'worldwide' 
              ? 'linear-gradient(135deg, #10b981, #059669)' 
              : 'transparent',
            color: dataSource === 'worldwide' ? '#fff' : '#a1a1aa',
            cursor: 'pointer',
            fontSize: compact ? '0.75rem' : '0.85rem',
            fontWeight: 600,
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: 5
          }}
        >
          🌍 Worldwide {worldwideCount > 0 && `(${worldwideCount})`}
        </button>
      </div>
    </div>
  );
};

/**
 * SelectAllControls - Select All / Deselect All buttons for checkbox groups
 */
export const SelectAllControls = ({ 
  onSelectAll, 
  onDeselectAll, 
  selectedCount = 0, 
  totalCount = 0,
  label = "Items",
  compact = false 
}) => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    gap: compact ? 6 : 10,
    flexWrap: 'wrap'
  }}>
    <span style={{ 
      color: '#a1a1aa', 
      fontSize: compact ? '0.7rem' : '0.8rem' 
    }}>
      {selectedCount} of {totalCount} {label} selected
    </span>
    <div style={{ display: 'flex', gap: 4 }}>
      <button
        onClick={onSelectAll}
        style={{
          padding: compact ? '4px 8px' : '6px 12px',
          borderRadius: 15,
          border: '1px solid rgba(16, 185, 129, 0.5)',
          background: selectedCount === totalCount 
            ? 'rgba(16, 185, 129, 0.3)' 
            : 'rgba(16, 185, 129, 0.1)',
          color: '#10b981',
          cursor: 'pointer',
          fontSize: compact ? '0.65rem' : '0.75rem',
          fontWeight: 600,
          transition: 'all 0.2s'
        }}
      >
        ✓ All
      </button>
      <button
        onClick={onDeselectAll}
        style={{
          padding: compact ? '4px 8px' : '6px 12px',
          borderRadius: 15,
          border: '1px solid rgba(239, 68, 68, 0.5)',
          background: selectedCount === 0 
            ? 'rgba(239, 68, 68, 0.3)' 
            : 'rgba(239, 68, 68, 0.1)',
          color: '#ef4444',
          cursor: 'pointer',
          fontSize: compact ? '0.65rem' : '0.75rem',
          fontWeight: 600,
          transition: 'all 0.2s'
        }}
      >
        ✗ None
      </button>
    </div>
  </div>
);

/**
 * DocumentTypeFilter - Filter by document/article type with select all
 */
export const DocumentTypeFilter = ({ 
  selectedTypes, 
  setSelectedTypes,
  availableTypes = null,
  compact = false 
}) => {
  const defaultTypes = [
    { id: 'news', label: '📰 News Article', color: '#3b82f6' },
    { id: 'webpage', label: '🌐 Webpage', color: '#8b5cf6' },
    { id: 'blog', label: '✍️ Blog Post', color: '#f472b6' },
    { id: 'research', label: '🔬 Research Paper', color: '#10b981' },
    { id: 'video', label: '🎬 Video', color: '#ef4444' },
    { id: 'pdf', label: '📄 PDF Document', color: '#f59e0b' },
    { id: 'social', label: '💬 Social Media', color: '#06b6d4' },
  ];
  
  const types = availableTypes || defaultTypes;
  
  const toggleType = (typeId) => {
    if (selectedTypes.includes(typeId)) {
      setSelectedTypes(selectedTypes.filter(t => t !== typeId));
    } else {
      setSelectedTypes([...selectedTypes, typeId]);
    }
  };
  
  const selectAll = () => setSelectedTypes(types.map(t => t.id));
  const deselectAll = () => setSelectedTypes([]);
  
  return (
    <div style={{
      background: 'rgba(0,0,0,0.2)',
      borderRadius: compact ? 10 : 12,
      padding: compact ? '10px 12px' : '15px',
      border: '1px solid rgba(139, 92, 246, 0.2)'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: compact ? 8 : 12 
      }}>
        <h4 style={{ 
          color: '#f472b6', 
          margin: 0, 
          fontSize: compact ? '0.8rem' : '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: 6
        }}>
          📋 Document Types
        </h4>
        <SelectAllControls
          onSelectAll={selectAll}
          onDeselectAll={deselectAll}
          selectedCount={selectedTypes.length}
          totalCount={types.length}
          label="types"
          compact={compact}
        />
      </div>
      
      <div style={{ 
        display: 'flex', 
        flexWrap: 'wrap', 
        gap: compact ? 4 : 6 
      }}>
        {types.map(type => (
          <button
            key={type.id}
            onClick={() => toggleType(type.id)}
            style={{
              padding: compact ? '4px 10px' : '6px 14px',
              borderRadius: 20,
              border: `1px solid ${selectedTypes.includes(type.id) ? type.color : 'rgba(255,255,255,0.2)'}`,
              background: selectedTypes.includes(type.id) 
                ? `${type.color}30` 
                : 'transparent',
              color: selectedTypes.includes(type.id) ? type.color : '#71717a',
              cursor: 'pointer',
              fontSize: compact ? '0.65rem' : '0.75rem',
              fontWeight: 500,
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: 4
            }}
          >
            {type.label}
          </button>
        ))}
      </div>
    </div>
  );
};

/**
 * QuickStats - Compact statistics summary
 */
export const QuickStats = ({ stats, compact = false }) => (
  <div style={{
    display: 'grid',
    gridTemplateColumns: `repeat(auto-fit, minmax(${compact ? '80px' : '100px'}, 1fr))`,
    gap: compact ? 6 : 10
  }}>
    {stats.map((stat, idx) => (
      <div key={idx} style={{
        background: `linear-gradient(135deg, ${stat.color}20, transparent)`,
        borderRadius: compact ? 8 : 10,
        padding: compact ? '8px 10px' : '12px 15px',
        border: `1px solid ${stat.color}40`,
        textAlign: 'center'
      }}>
        <div style={{ fontSize: compact ? '1rem' : '1.2rem' }}>{stat.icon}</div>
        <div style={{ 
          color: '#fff', 
          fontWeight: 700, 
          fontSize: compact ? '0.9rem' : '1.1rem' 
        }}>
          {stat.value}
        </div>
        <div style={{ 
          color: '#a1a1aa', 
          fontSize: compact ? '0.6rem' : '0.7rem' 
        }}>
          {stat.label}
        </div>
      </div>
    ))}
  </div>
);

/**
 * FunnyBanner - Smaller, funnier promotional banner
 */
export const FunnyBanner = ({ 
  message, 
  icon = "🎉", 
  color = "#8b5cf6",
  onDismiss = null 
}) => (
  <div style={{
    background: `linear-gradient(135deg, ${color}20, ${color}05)`,
    borderRadius: 10,
    padding: '8px 15px',
    border: `1px solid ${color}30`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ fontSize: '1.2rem' }}>{icon}</span>
      <span style={{ color: '#fff', fontSize: '0.85rem' }}>{message}</span>
    </div>
    {onDismiss && (
      <button
        onClick={onDismiss}
        style={{
          background: 'transparent',
          border: 'none',
          color: '#71717a',
          cursor: 'pointer',
          fontSize: '1rem',
          padding: 5
        }}
      >
        ×
      </button>
    )}
  </div>
);

/**
 * CompactAd - Smaller advertisement component
 */
export const CompactAd = ({ 
  title, 
  subtitle, 
  cta, 
  ctaLink, 
  color = "#8b5cf6",
  icon = "📚" 
}) => (
  <div style={{
    background: `linear-gradient(135deg, ${color}15, ${color}05)`,
    borderRadius: 10,
    padding: '10px 15px',
    border: `1px solid ${color}25`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
    marginBottom: 10
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
      <span style={{ fontSize: '1.5rem' }}>{icon}</span>
      <div>
        <div style={{ color: '#fff', fontSize: '0.85rem', fontWeight: 600 }}>{title}</div>
        {subtitle && (
          <div style={{ color: '#a1a1aa', fontSize: '0.7rem' }}>{subtitle}</div>
        )}
      </div>
    </div>
    {cta && ctaLink && (
      <a
        href={ctaLink}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          padding: '6px 14px',
          background: color,
          color: '#fff',
          borderRadius: 15,
          textDecoration: 'none',
          fontSize: '0.75rem',
          fontWeight: 600,
          whiteSpace: 'nowrap'
        }}
      >
        {cta}
      </a>
    )}
  </div>
);

export default {
  DataSourceToggle,
  SelectAllControls,
  DocumentTypeFilter,
  QuickStats,
  FunnyBanner,
  CompactAd
};
