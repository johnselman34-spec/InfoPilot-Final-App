/**
 * Marketplace Component Library
 * Refactored from MarketplacePage.js for better maintainability
 */
import React from 'react';

// Constants
export const FREE_MESSAGES = [
  "💸 100% FREE - Your wallet just did a happy dance!",
  "🎉 ABSOLUTELY FREE - Even your piggy bank is celebrating!",
  "🚀 FREE AS A BIRD - Fly high without spending a dime!",
  "💰 ZERO DOLLARS - Math doesn't get easier than this!",
  "🎁 FREE FOREVER - Like a gift that keeps on giving!",
  "🤑 SO FREE it should be illegal (but it's not, we checked)!",
  "🎪 FREE! FREE! FREE! - Now say it three times fast!",
  "💎 FREE - Worth its weight in gold (gold weighs a lot)!",
  "🌈 FREE at the end of every rainbow!",
  "🎯 FREE - Hitting your budget where it counts!",
];

export const CATEGORY_COLORS = {
  'General': '#7c3aed', 'News & Media': '#f59e0b', 'Technology': '#3b82f6',
  'Science & Research': '#10b981', 'Business & Finance': '#ef4444',
  'Entertainment': '#f472b6', 'Sports': '#06b6d4', 'Health & Medicine': '#84cc16'
};

export const LOCATIONS = [
  { lat: 40.7128, lng: -74.0060, city: 'New York' },
  { lat: 34.0522, lng: -118.2437, city: 'Los Angeles' },
  { lat: 51.5074, lng: -0.1278, city: 'London' },
  { lat: 48.8566, lng: 2.3522, city: 'Paris' },
  { lat: 35.6762, lng: 139.6503, city: 'Tokyo' },
  { lat: -33.8688, lng: 151.2093, city: 'Sydney' },
  { lat: 43.9108, lng: -69.9669, city: 'Brunswick, ME' },
  { lat: 55.7558, lng: 37.6173, city: 'Moscow' },
  { lat: 19.4326, lng: -99.1332, city: 'Mexico City' },
  { lat: -23.5505, lng: -46.6333, city: 'São Paulo' },
];

/**
 * FreeBanner - Displays the FREE promotional banner
 */
export const FreeBanner = ({ message }) => (
  <div style={{
    background: 'linear-gradient(135deg, #10b981, #059669, #047857)',
    padding: 20, textAlign: 'center', borderRadius: '12px 12px 0 0',
    position: 'relative', overflow: 'hidden'
  }}>
    <div style={{
      position: 'absolute', inset: 0,
      background: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.05) 10px, rgba(255,255,255,0.05) 20px)'
    }} />
    <h1 style={{ color: '#fff', fontSize: '2rem', fontWeight: 900, margin: 0, textShadow: '2px 2px 4px rgba(0,0,0,0.3)', position: 'relative' }}>
      🆓 COMPLETELY FREE TO USE! 🆓
    </h1>
    <p style={{ color: '#d1fae5', margin: '10px 0 0 0', fontSize: '1.1rem', position: 'relative' }}>{message}</p>
    <div style={{ marginTop: 15, display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap', position: 'relative' }}>
      {['Browse FREE', 'Search FREE', 'Create Categories FREE', 'Earn Money Selling!'].map((text, i) => (
        <span key={i} style={{ color: '#fff', fontSize: '0.9rem' }}>✓ {text}</span>
      ))}
    </div>
  </div>
);

/**
 * WorldWideMap - Visual map showing protocol distribution
 */
export const WorldWideMap = ({ protocols, categories, selectedCategories, onSelectAll, onDeselectAll }) => {
  const filteredProtocols = protocols.filter(p => selectedCategories.length === 0 || selectedCategories.includes(p.category));
  
  return (
    <div style={{ background: 'linear-gradient(135deg, rgba(20, 10, 40, 0.95), rgba(30, 20, 60, 0.95))', borderRadius: 15, padding: 20, marginBottom: 20, border: '2px solid rgba(124, 58, 237, 0.4)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15, flexWrap: 'wrap', gap: 10 }}>
        <h3 style={{ color: '#f472b6', display: 'flex', alignItems: 'center', gap: 10, margin: 0 }}>
          🗺️ World Wide Protocol Map
          <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 400 }}>LIVE • {filteredProtocols.length} protocols</span>
        </h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-primary" onClick={onSelectAll} style={{ padding: '6px 12px', fontSize: '0.75rem' }}>✓ Select All</button>
          <button className="btn btn-secondary" onClick={onDeselectAll} style={{ padding: '6px 12px', fontSize: '0.75rem' }}>✗ Deselect All</button>
        </div>
      </div>
      
      <div style={{ background: 'linear-gradient(135deg, #1a365d 0%, #2d3748 50%, #1a202c 100%)', borderRadius: 12, height: 280, position: 'relative', overflow: 'hidden', border: '1px solid rgba(124, 58, 237, 0.5)' }}>
        <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(124, 58, 237, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(124, 58, 237, 0.1) 1px, transparent 1px)', backgroundSize: '50px 50px' }} />
        
        {filteredProtocols.map((protocol, index) => {
          const loc = LOCATIONS[index % LOCATIONS.length];
          const x = ((loc.lng + 180) / 360) * 100;
          const y = ((90 - loc.lat) / 180) * 100;
          const color = CATEGORY_COLORS[protocol.category] || '#7c3aed';
          
          return (
            <div key={protocol.id} style={{ position: 'absolute', left: `${Math.min(92, Math.max(8, x))}%`, top: `${Math.min(88, Math.max(12, y))}%`, transform: 'translate(-50%, -50%)', cursor: 'pointer', zIndex: 10 }} title={`${protocol.name} (${protocol.category})`}>
              <div style={{ width: 16, height: 16, borderRadius: '50%', background: color, border: '2px solid white', boxShadow: `0 0 12px ${color}80`, animation: 'pulse 2s infinite' }} />
            </div>
          );
        })}
        
        <div style={{ position: 'absolute', bottom: 10, right: 10, background: 'rgba(0,0,0,0.8)', padding: '10px 15px', borderRadius: 10, maxWidth: 200, maxHeight: 150, overflowY: 'auto' }}>
          <div style={{ color: '#fff', fontSize: '0.7rem', fontWeight: 600, marginBottom: 8 }}>Categories:</div>
          {categories.slice(0, 6).map((cat, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: CATEGORY_COLORS[cat.name] || '#7c3aed' }} />
              <span style={{ color: '#a1a1aa', fontSize: '0.65rem' }}>{cat.name}</span>
            </div>
          ))}
        </div>
        
        <div style={{ position: 'absolute', top: 10, left: 10, background: 'linear-gradient(135deg, #10b981, #059669)', padding: '6px 12px', borderRadius: 20, color: '#fff', fontSize: '0.7rem', fontWeight: 700, boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)' }}>
          🆓 100% FREE TO BROWSE!
        </div>
      </div>
    </div>
  );
};

/**
 * CategoryTree - Collapsible category filter
 */
export const CategoryTree = ({ categories, selectedCategories, onToggle, expanded, onExpandToggle }) => (
  <div style={{ background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12, padding: 15, marginBottom: 15 }}>
    <h4 style={{ color: '#f472b6', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
      📁 Categories <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 400 }}>(All checked by default!)</span>
    </h4>
    <div style={{ maxHeight: 250, overflowY: 'auto' }}>
      {categories.map((cat, i) => (
        <div key={i} style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', background: selectedCategories.includes(cat.name) ? 'rgba(124, 58, 237, 0.2)' : 'rgba(0,0,0,0.2)', borderRadius: 8, cursor: 'pointer' }}>
            <button onClick={() => onExpandToggle(cat.name)} style={{ width: 20, height: 20, borderRadius: 4, border: 'none', background: 'rgba(124, 58, 237, 0.3)', color: '#a78bfa', cursor: 'pointer', fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {expanded[cat.name] ? '−' : '+'}
            </button>
            <input type="checkbox" checked={selectedCategories.includes(cat.name)} onChange={() => onToggle(cat.name)} style={{ accentColor: '#7c3aed' }} />
            <span style={{ color: selectedCategories.includes(cat.name) ? '#fff' : '#a1a1aa', flex: 1 }}>{cat.name}</span>
            <span style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', padding: '2px 8px', borderRadius: 10, fontSize: '0.7rem' }}>{cat.count}</span>
          </div>
          {expanded[cat.name] && (
            <div style={{ marginLeft: 30, marginTop: 5 }}>
              {['Sub-category A', 'Sub-category B', 'Sub-category C'].map((sub, j) => (
                <div key={j} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 10px', color: '#71717a', fontSize: '0.85rem' }}>
                  <input type="checkbox" defaultChecked style={{ accentColor: '#7c3aed' }} />{sub}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  </div>
);

/**
 * RevenueInfo - Revenue distribution display
 */
export const RevenueInfo = ({ adminPercent = 10 }) => (
  <div style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))', borderRadius: 12, padding: 15, marginBottom: 15, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
    <h4 style={{ color: '#10b981', marginBottom: 10 }}>💸 Revenue Distribution</h4>
    <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap' }}>
      <div style={{ flex: 1, minWidth: 120 }}>
        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#10b981' }}>{100 - adminPercent}%</div>
        <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>To Protocol Creator</div>
      </div>
      <div style={{ flex: 1, minWidth: 120 }}>
        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f59e0b' }}>{adminPercent}%</div>
        <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Platform Fee</div>
      </div>
    </div>
    <div style={{ marginTop: 10, padding: 10, background: 'rgba(0,0,0,0.2)', borderRadius: 8, fontSize: '0.75rem', color: '#a1a1aa' }}>
      💡 <strong>PayPal Note:</strong> Earnings under $1.00 are accumulated until they reach the minimum payout threshold.
    </div>
  </div>
);

export default {
  FREE_MESSAGES,
  CATEGORY_COLORS,
  LOCATIONS,
  FreeBanner,
  WorldWideMap,
  CategoryTree,
  RevenueInfo
};
