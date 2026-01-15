import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons, ProtocolCopyButtons, AISuggestions } from '../components/shared';
import ProtocolAnalyticsDashboard from '../components/Admin/ProtocolAnalyticsDashboard';
import ProtocolBundlesSection from '../components/Marketplace/ProtocolBundlesSection';
import BundleOfTheWeek from '../components/Marketplace/BundleOfTheWeek';

// Constants - HILARIOUS FREE MESSAGES 🎉
const FREE_MESSAGES = [
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

const CATEGORY_COLORS = {
  'General': '#7c3aed', 'News & Media': '#f59e0b', 'Technology': '#3b82f6',
  'Science & Research': '#10b981', 'Business & Finance': '#ef4444',
  'Entertainment': '#f472b6', 'Sports': '#06b6d4', 'Health & Medicine': '#84cc16'
};

const LOCATIONS = [
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

// Sub-components
const FreeBanner = ({ message }) => (
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

const WorldWideMap = ({ protocols, categories, selectedCategories, onSelectAll, onDeselectAll }) => {
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

const CategoryTree = ({ categories, selectedCategories, onToggle, expanded, onExpandToggle }) => (
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

const RevenueInfo = ({ adminPercent = 10 }) => (
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

const ProtocolCard = ({ protocol, onCopyFree, onPurchase, showToast }) => (
  <div style={{ background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12, padding: 15, border: protocol.is_featured ? '2px solid #f472b6' : '1px solid rgba(124, 58, 237, 0.3)', position: 'relative' }} data-testid={`protocol-card-${protocol.id}`}>
    {protocol.is_featured && (
      <span style={{ position: 'absolute', top: -8, right: 10, background: '#f472b6', color: '#fff', padding: '3px 10px', borderRadius: 15, fontSize: '0.65rem', fontWeight: 700 }}>FEATURED</span>
    )}
    <h4 style={{ color: '#f472b6', marginBottom: 8 }}>{protocol.name}</h4>
    <p style={{ color: '#a1a1aa', fontSize: '0.8rem', marginBottom: 10 }}>{protocol.description?.substring(0, 80)}...</p>
    <ProtocolCopyButtons title={protocol.name} protocol={protocol.protocol_string} hasAccess={protocol.is_owned || protocol.price === 0 || protocol.is_free} showToast={showToast} style={{ marginBottom: 10 }} />
    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 10 }}>
      <span style={{ background: 'rgba(124, 58, 237, 0.2)', color: '#a78bfa', padding: '2px 8px', borderRadius: 10, fontSize: '0.7rem' }}>{protocol.category}</span>
    </div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
      <span style={{ color: '#fbbf24', fontSize: '0.8rem' }}>{'★'.repeat(Math.round(protocol.rating))}{'☆'.repeat(5 - Math.round(protocol.rating))} ({protocol.review_count})</span>
      <span style={{ color: '#71717a', fontSize: '0.75rem' }}>{protocol.total_sales} sales</span>
    </div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      {protocol.price === 0 || protocol.is_free ? (
        <span style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: '#fff', padding: '4px 12px', borderRadius: 20, fontSize: '0.85rem', fontWeight: 700 }}>🆓 FREE!</span>
      ) : (
        <span style={{ color: '#10b981', fontSize: '1.2rem', fontWeight: 700 }}>${protocol.price.toFixed(2)}</span>
      )}
      {protocol.is_owned ? (
        <span style={{ color: '#10b981', fontSize: '0.85rem' }}>✓ Owned</span>
      ) : protocol.price === 0 || protocol.is_free ? (
        <button className="btn btn-primary" onClick={() => onCopyFree(protocol)} style={{ padding: '6px 15px', fontSize: '0.85rem', background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}>📋 Copy FREE</button>
      ) : (
        <button className="btn btn-primary" onClick={() => onPurchase(protocol)} style={{ padding: '6px 15px', fontSize: '0.85rem' }}>Buy Now</button>
      )}
    </div>
  </div>
);

const SellForm = ({ newProtocol, setNewProtocol, onSubmit, adminPercent }) => (
  <div style={{ maxWidth: 600 }}>
    <div style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))', padding: 20, borderRadius: 12, marginBottom: 20 }}>
      <h3 style={{ color: '#10b981', marginBottom: 10 }}>💰 Earn HUNDREDS or THOUSANDS of Easy Dollars!</h3>
      <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
        List your search protocols and earn <strong style={{ color: '#10b981' }}>{100 - adminPercent}%</strong> of every sale!
        <br/><span style={{ color: '#71717a', fontSize: '0.8rem' }}>Platform fee: {adminPercent}% • Listing is FREE • No monthly fees • Ever!</span>
      </p>
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
      <input className="input" placeholder="Protocol Name * (Make it catchy!)" value={newProtocol.name} onChange={(e) => setNewProtocol({ ...newProtocol, name: e.target.value })} />
      <textarea className="input" placeholder="Description - Tell buyers why they need this! *" rows={3} value={newProtocol.description} onChange={(e) => setNewProtocol({ ...newProtocol, description: e.target.value })} />
      <textarea className="input" placeholder="Protocol String - Your secret sauce! *" rows={2} value={newProtocol.protocol} onChange={(e) => setNewProtocol({ ...newProtocol, protocol: e.target.value })} style={{ fontFamily: 'monospace' }} />
      <div style={{ display: 'flex', gap: 15 }}>
        <div style={{ flex: 1 }}>
          <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Price ($0.00 FREE or $0.01 - $99.99)</label>
          <input className="input" type="number" min="0" max="99.99" step="0.01" value={newProtocol.price} onChange={(e) => setNewProtocol({ ...newProtocol, price: parseFloat(e.target.value) || 0 })} />
          {newProtocol.price === 0 && (
            <div style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: '#fff', padding: '8px 12px', borderRadius: 8, marginTop: 8, fontSize: '0.85rem', textAlign: 'center' }}>
              🆓 Your protocol will be FREE TO COPY! Great for building reputation!
            </div>
          )}
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Category</label>
          <select className="input" value={newProtocol.category} onChange={(e) => setNewProtocol({ ...newProtocol, category: e.target.value })}>
            {['General', 'News & Media', 'Science & Research', 'Business & Finance', 'Technology', 'Entertainment', 'History & Politics', 'Aviation & Military', 'Education', 'Health & Medical'].map(cat => (
              <option key={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </div>
      <input className="input" placeholder="Tags (comma-separated)" value={newProtocol.tags} onChange={(e) => setNewProtocol({ ...newProtocol, tags: e.target.value })} />
      <div style={{ background: 'rgba(251, 191, 36, 0.1)', padding: 15, borderRadius: 10, border: '1px solid rgba(251, 191, 36, 0.3)' }}>
        <p style={{ color: '#fbbf24', fontSize: '0.9rem', margin: 0 }}>💵 You'll earn: <strong>${((newProtocol.price || 0.99) * (100 - adminPercent) / 100).toFixed(2)}</strong> per sale</p>
      </div>
      <button className="btn btn-primary" onClick={onSubmit} style={{ marginTop: 10, fontSize: '1.1rem', padding: '15px' }}>🚀 List Protocol & Start Earning!</button>
    </div>
  </div>
);

const DashboardTab = ({ dashboard, adminPercent }) => {
  if (!dashboard) return <p style={{ color: '#a1a1aa' }}>Loading dashboard...</p>;
  
  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginBottom: 30 }}>
        <div style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))', borderRadius: 12, padding: 20, textAlign: 'center' }}>
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Your Earnings</p>
          <p style={{ color: '#10b981', fontSize: '2.5rem', fontWeight: 700 }}>${(dashboard.total_earnings || 0).toFixed(2)}</p>
          <p style={{ color: '#71717a', fontSize: '0.75rem' }}>{dashboard.total_earnings < 1 ? 'Accumulating... (PayPal min: $1.00)' : 'Ready for payout!'}</p>
        </div>
        <div style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(124, 58, 237, 0.1))', borderRadius: 12, padding: 20, textAlign: 'center' }}>
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Total Sales</p>
          <p style={{ color: '#a78bfa', fontSize: '2.5rem', fontWeight: 700 }}>{dashboard.total_sales || 0}</p>
        </div>
        <div style={{ background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(236, 72, 153, 0.1))', borderRadius: 12, padding: 20, textAlign: 'center' }}>
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Your Protocols</p>
          <p style={{ color: '#f472b6', fontSize: '2.5rem', fontWeight: 700 }}>{dashboard.protocol_count || 0}</p>
        </div>
        <div style={{ background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.1))', borderRadius: 12, padding: 20, textAlign: 'center' }}>
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Avg Rating</p>
          <p style={{ color: '#fbbf24', fontSize: '2.5rem', fontWeight: 700 }}>{'★'.repeat(Math.round(dashboard.avg_rating || 0))}</p>
        </div>
      </div>
      
      {dashboard.protocols?.length > 0 && (
        <div>
          <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Your Listed Protocols</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            {dashboard.protocols.map(p => (
              <div key={p.id} style={{ background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12, padding: 20, border: '1px solid rgba(124, 58, 237, 0.3)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h4 style={{ color: '#f472b6', marginBottom: 5 }}>{p.name}</h4>
                    <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>{p.total_sales} sales • {p.price === 0 ? 'FREE' : `$${p.price.toFixed(2)}`}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ color: '#10b981', fontSize: '1.2rem', fontWeight: 700 }}>${(p.earnings || 0).toFixed(2)}</p>
                    <p style={{ color: '#71717a', fontSize: '0.75rem' }}>earned</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Main Component
const MarketplacePage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [protocols, setProtocols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('browse');
  const [categories, setCategories] = useState([]);
  const [sortBy, setSortBy] = useState('popular');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [expandedCategories, setExpandedCategories] = useState({});
  const [aiSearchQuery, setAiSearchQuery] = useState('');
  const [searchLogic, setSearchLogic] = useState('AND/OR');
  const [adminPercent, setAdminPercent] = useState(10);
  const [newProtocol, setNewProtocol] = useState({ name: '', description: '', protocol: '', price: 0.99, category: 'General', tags: '' });
  const [purchaseModal, setPurchaseModal] = useState(null);
  const [purchases, setPurchases] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [freeMessage] = useState(() => FREE_MESSAGES[Math.floor(Math.random() * FREE_MESSAGES.length)]);

  // Fetch functions
  const fetchProtocols = useCallback(async () => {
    try {
      const res = await fetch(`${API}/marketplace/protocols?sort=${sortBy}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      const data = await res.json();
      setProtocols(data.protocols || []);
    } catch (e) { console.error('Failed to fetch protocols:', e); }
    setLoading(false);
  }, [token, sortBy]);

  const fetchCategories = useCallback(async () => {
    try {
      const res = await fetch(`${API}/marketplace/categories`);
      const data = await res.json();
      const cats = data.categories || [];
      setCategories(cats);
      setSelectedCategories(cats.map(c => c.name));
    } catch (e) { console.error('Failed to fetch categories:', e); }
  }, []);

  const fetchPurchases = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/marketplace/purchases`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setPurchases(data.purchases || []);
    } catch (e) { console.error('Failed to fetch purchases:', e); }
  }, [token]);

  const fetchDashboard = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/marketplace/seller/dashboard`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setDashboard(data);
    } catch (e) { console.error('Failed to fetch dashboard:', e); }
  }, [token]);

  useEffect(() => {
    fetchProtocols();
    fetchCategories();
    if (token) { fetchPurchases(); fetchDashboard(); }
  }, [fetchProtocols, fetchCategories, fetchPurchases, fetchDashboard, token]);

  useEffect(() => {
    if (user?.is_admin && token) {
      fetch(`${API}/marketplace/admin/revenue-settings`, { headers: { Authorization: `Bearer ${token}` } })
        .then(res => res.ok ? res.json() : null)
        .then(data => data && setAdminPercent(data.admin_percent || 10))
        .catch(() => {});
    }
  }, [user, token]);

  // Filter protocols
  const filteredProtocols = protocols.filter(protocol => {
    if (selectedCategories.length > 0 && !selectedCategories.includes(protocol.category)) return false;
    if (aiSearchQuery.trim()) {
      const query = aiSearchQuery.toLowerCase();
      const searchTerms = query.split(/\s+/);
      const text = `${protocol.name} ${protocol.description} ${protocol.category} ${(protocol.tags || []).join(' ')}`.toLowerCase();
      if (searchLogic === 'AND') { if (!searchTerms.every(term => text.includes(term))) return false; }
      else if (searchLogic === 'OR') { if (!searchTerms.some(term => text.includes(term))) return false; }
      else { const matches = searchTerms.filter(term => text.includes(term)); if (matches.length < Math.ceil(searchTerms.length / 2)) return false; }
    }
    return true;
  });

  // Handlers
  const handleListProtocol = async () => {
    if (!newProtocol.name || !newProtocol.protocol || !newProtocol.description) { showToast('Please fill in all required fields', 'error'); return; }
    try {
      const res = await fetch(`${API}/marketplace/protocols`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...newProtocol, tags: newProtocol.tags.split(',').map(t => t.trim()).filter(t => t) })
      });
      if (res.ok) {
        showToast('🎉 Protocol listed successfully!', 'success');
        setNewProtocol({ name: '', description: '', protocol: '', price: 0, category: 'General', tags: '' });
        fetchProtocols(); fetchDashboard(); setActiveTab('dashboard');
      } else { const data = await res.json(); showToast(data.detail || 'Failed to list protocol', 'error'); }
    } catch (e) { showToast('Failed to list protocol', 'error'); }
  };

  const handleCopyFreeProtocol = async (protocol) => {
    try {
      const res = await fetch(`${API}/marketplace/protocols/${protocol.id}/copy`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
      });
      const data = await res.json();
      if (res.ok) {
        navigator.clipboard.writeText(data.protocol).then(() => showToast('🎉 FREE Protocol copied to clipboard!', 'success')).catch(() => showToast(`Protocol: ${data.protocol}`, 'info'));
      } else { showToast(data.detail || 'Failed to copy protocol', 'error'); }
    } catch (e) { showToast('Failed to copy protocol', 'error'); }
  };

  const handlePurchase = async (protocol) => {
    try {
      const res = await fetch(`${API}/marketplace/initiate-purchase`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ protocol_id: protocol.id })
      });
      const data = await res.json();
      if (res.ok) {
        window.open(data.payment_url, '_blank', 'width=600,height=700');
        setPurchaseModal({ protocol, pending_id: data.pending_id, payment_url: data.payment_url, step: 'confirm' });
      } else { showToast(data.detail || 'Failed to initiate purchase', 'error'); }
    } catch (e) { showToast('Failed to initiate purchase', 'error'); }
  };

  const confirmPurchase = async () => {
    if (!purchaseModal) return;
    const transactionId = prompt('Enter your PayPal Transaction ID:');
    if (!transactionId) { showToast('Transaction ID is required', 'error'); return; }
    try {
      const res = await fetch(`${API}/marketplace/confirm-payment`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ protocol_id: purchaseModal.protocol.id, transaction_id: transactionId, amount: purchaseModal.protocol.price })
      });
      if (res.ok) { showToast('🎉 Protocol purchased!', 'success'); setPurchaseModal(null); fetchProtocols(); fetchPurchases(); }
      else { const data = await res.json(); showToast(data.detail || 'Purchase confirmation failed', 'error'); }
    } catch (e) { showToast('Purchase confirmation failed', 'error'); }
  };

  return (
    <div className="card" data-testid="marketplace-page">
      <FreeBanner message={freeMessage} />
      
      <div style={{ background: 'linear-gradient(135deg, #1a0a30, #2d1b4e)', padding: '10px 20px', textAlign: 'center', borderBottom: '2px solid rgba(251, 191, 36, 0.5)' }}>
        <span style={{ color: '#fbbf24', fontSize: '0.8rem', fontWeight: 700, letterSpacing: '1px' }}>✈️ WORLD WIDE MARKETPLACE • Powered by TOP PILOT ENTERPRISES, INC. ✈️</span>
      </div>

      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Shop /> Protocol Marketplace
          <span style={{ background: '#10b981', color: '#fff', padding: '4px 12px', borderRadius: 20, fontSize: '0.75rem', fontWeight: 700 }}>100% FREE</span>
        </h2>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>Make HUNDREDS or even THOUSANDS of easy dollars! 💰</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {['browse', 'bundles', 'sell', 'purchases', 'dashboard', 'analytics'].map(tab => (
          <button key={tab} className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab(tab)} data-testid={`marketplace-tab-${tab}`}>
            {tab === 'browse' && '🔍 Browse FREE'}{tab === 'bundles' && '📦 Bundles'}{tab === 'sell' && '💰 Sell & Earn'}{tab === 'purchases' && '📦 My Purchases'}{tab === 'dashboard' && '📊 My Earnings'}{tab === 'analytics' && '📈 Analytics'}
          </button>
        ))}
        {user?.is_admin && <button className={`btn ${activeTab === 'admin' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab('admin')} style={{ marginLeft: 'auto' }}>⚙️ Admin</button>}
      </div>

      {/* Browse Tab */}
      {activeTab === 'browse' && (
        <div>
          {/* Bundle of the Week - Featured Section */}
          <BundleOfTheWeek showToast={showToast} />
          
          <AISuggestions showToast={showToast} onViewProtocol={() => {}} />
          <WorldWideMap protocols={filteredProtocols} categories={categories} selectedCategories={selectedCategories} onSelectAll={() => setSelectedCategories(categories.map(c => c.name))} onDeselectAll={() => setSelectedCategories([])} />
          
          <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20 }}>
            <div>
              <CategoryTree categories={categories} selectedCategories={selectedCategories} onToggle={(cat) => setSelectedCategories(prev => prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat])} expanded={expandedCategories} onExpandToggle={(cat) => setExpandedCategories(prev => ({ ...prev, [cat]: !prev[cat] }))} />
              <RevenueInfo adminPercent={adminPercent} />
              <div style={{ background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.2))', borderRadius: 12, padding: 15, border: '1px solid rgba(251, 191, 36, 0.3)', textAlign: 'center' }}>
                <h4 style={{ color: '#fbbf24', margin: '0 0 10px 0' }}>💵 Want to Earn Money?</h4>
                <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '0 0 10px 0' }}>List your protocols and earn {100 - adminPercent}% of every sale!</p>
                <button className="btn btn-primary" onClick={() => setActiveTab('sell')} style={{ width: '100%' }}>Start Selling Now!</button>
              </div>
            </div>
            
            <div>
              <div style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(59, 130, 246, 0.1))', borderRadius: 12, padding: 15, marginBottom: 15, border: '1px solid rgba(124, 58, 237, 0.3)' }}>
                <input className="input-field" placeholder="🔍 AI-Powered Search... (100% FREE!)" value={aiSearchQuery} onChange={(e) => setAiSearchQuery(e.target.value)} style={{ width: '100%', marginBottom: 10 }} data-testid="ai-search-input" />
                <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'center' }}>
                  <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Logic:</span>
                  {['AND/OR', 'AND', 'OR'].map(logic => (
                    <label key={logic} style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer' }}>
                      <input type="radio" name="logic" checked={searchLogic === logic} onChange={() => setSearchLogic(logic)} />
                      <span style={{ color: searchLogic === logic ? '#10b981' : '#71717a' }}>{logic}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, marginBottom: 15 }}>
                <select className="input" value={sortBy} onChange={(e) => setSortBy(e.target.value)} style={{ maxWidth: 200 }}>
                  <option value="popular">Most Popular</option>
                  <option value="newest">Newest</option>
                  <option value="price_low">Price: Low to High</option>
                  <option value="price_high">Price: High to Low</option>
                  <option value="rating">Highest Rated</option>
                </select>
                <span style={{ color: '#a1a1aa', alignSelf: 'center' }}>{filteredProtocols.length} protocols found</span>
              </div>

              {loading ? (
                <p style={{ textAlign: 'center', color: '#a1a1aa' }}>Loading...</p>
              ) : filteredProtocols.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
                  <div style={{ fontSize: '3rem', marginBottom: 15 }}>🔍</div>
                  <p style={{ color: '#a1a1aa', marginBottom: 15 }}>No protocols found. Be the first to sell!</p>
                  <button className="btn btn-primary" onClick={() => setActiveTab('sell')}>List Your Protocol - It's FREE!</button>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 15 }}>
                  {filteredProtocols.map(protocol => (
                    <ProtocolCard key={protocol.id} protocol={protocol} onCopyFree={handleCopyFreeProtocol} onPurchase={handlePurchase} showToast={showToast} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bundles Tab */}
      {activeTab === 'bundles' && <ProtocolBundlesSection showToast={showToast} />}

      {/* Sell Tab */}
      {activeTab === 'sell' && <SellForm newProtocol={newProtocol} setNewProtocol={setNewProtocol} onSubmit={handleListProtocol} adminPercent={adminPercent} />}

      {/* Purchases Tab */}
      {activeTab === 'purchases' && (
        <div>
          {purchases.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>No purchases yet. Browse FREE to find amazing protocols!</p>
              <button className="btn btn-primary" onClick={() => setActiveTab('browse')}>Browse Protocols</button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              {purchases.map(purchase => (
                <div key={purchase.id} style={{ background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12, padding: 20, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h3 style={{ color: '#f472b6', marginBottom: 5 }}>{purchase.protocol_name}</h3>
                      <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Purchased: {new Date(purchase.purchased_at).toLocaleDateString()}</p>
                    </div>
                    <span style={{ color: '#10b981', fontWeight: 700 }}>${purchase.price.toFixed(2)}</span>
                  </div>
                  <div style={{ marginTop: 15, padding: 15, background: 'rgba(0,0,0,0.3)', borderRadius: 8 }}>
                    <p style={{ color: '#a1a1aa', fontSize: '0.8rem', marginBottom: 5 }}>Protocol:</p>
                    <code style={{ color: '#10b981', fontSize: '0.85rem' }}>{purchase.protocol_string}</code>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && <DashboardTab dashboard={dashboard} adminPercent={adminPercent} />}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && <ProtocolAnalyticsDashboard showToast={showToast} />}

      {/* Purchase Modal */}
      {purchaseModal && (
        <div className="modal-overlay" onClick={() => setPurchaseModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h2>Complete Purchase</h2>
              <button className="modal-close" onClick={() => setPurchaseModal(null)}>×</button>
            </div>
            <div style={{ padding: 20 }}>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>Complete your PayPal payment, then click the button below to confirm.</p>
              <button className="btn btn-primary" onClick={confirmPurchase} style={{ width: '100%' }}>I've Completed Payment</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketplacePage;
