import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons, ProtocolCopyButtons, AISuggestions } from '../components/shared';
import ProtocolAnalyticsDashboard from '../components/Admin/ProtocolAnalyticsDashboard';
import ProtocolBundlesSection from '../components/Marketplace/ProtocolBundlesSection';
import BundleOfTheWeek from '../components/Marketplace/BundleOfTheWeek';
// Import from discrete Marketplace components
import { 
  FREE_MESSAGES, 
  CATEGORY_COLORS, 
  LOCATIONS,
  FreeBanner,
  RevenueInfo,
  WorldWideMap,
  CategoryTree,
  ProtocolCard,
  SellForm,
  SellerDashboard,
  CommunityLeaderboard,
  ProtocolRecommendationEngine,
  PerformanceInsights
} from '../components/Marketplace';

// Main Marketplace Page Component
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
    const loadData = async () => {
      await fetchProtocols();
      await fetchCategories();
      if (token) { 
        await fetchPurchases(); 
        await fetchDashboard(); 
      }
    };
    loadData();
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
        {['browse', 'bundles', 'leaderboard', 'recommendations', 'sell', 'purchases', 'dashboard', 'analytics'].map(tab => (
          <button key={tab} className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActiveTab(tab)} data-testid={`marketplace-tab-${tab}`}>
            {tab === 'browse' && '🔍 Browse FREE'}
            {tab === 'bundles' && '📦 Bundles'}
            {tab === 'leaderboard' && '🏆 Leaderboard'}
            {tab === 'recommendations' && '🤖 AI Picks'}
            {tab === 'sell' && '💰 Sell & Earn'}
            {tab === 'purchases' && '📦 My Purchases'}
            {tab === 'dashboard' && '📊 My Earnings'}
            {tab === 'analytics' && '📈 Analytics'}
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
          
          {/* Category Filtered Results - Bottom Center Display */}
          {selectedCategories.length > 0 && (
            <div style={{ 
              marginBottom: 20,
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(59, 130, 246, 0.15))',
              borderRadius: 16,
              padding: 20,
              border: '2px solid rgba(16, 185, 129, 0.4)',
              boxShadow: '0 4px 20px rgba(16, 185, 129, 0.2)'
            }} data-testid="marketplace-category-filtered-results">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
                <h3 style={{ color: '#10b981', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
                  🏷️ Category Results ({filteredProtocols.length})
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    {selectedCategories.slice(0, 3).map((cat, idx) => (
                      <span key={idx} style={{ 
                        fontSize: '0.7rem', 
                        background: 'rgba(16, 185, 129, 0.2)', 
                        padding: '3px 10px', 
                        borderRadius: 20,
                        color: '#10b981'
                      }}>
                        {cat}
                      </span>
                    ))}
                    {selectedCategories.length > 3 && (
                      <span style={{ fontSize: '0.7rem', color: '#71717a' }}>+{selectedCategories.length - 3} more</span>
                    )}
                  </div>
                </h3>
                <button 
                  onClick={() => setSelectedCategories([])}
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#f87171',
                    padding: '6px 14px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    fontSize: '0.8rem'
                  }}
                >
                  ✕ Clear Filters
                </button>
              </div>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                gap: 12, 
                maxHeight: 300, 
                overflowY: 'auto',
                paddingRight: 5
              }}>
                {filteredProtocols.slice(0, 20).map((protocol, idx) => {
                  const categoryColor = protocol.category ? 
                    ['#f472b6', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899'][categories.findIndex(c => c.name === protocol.category) % 8] 
                    : '#7c3aed';
                  
                  return (
                    <div 
                      key={protocol.id || `filtered-protocol-${idx}`}
                      data-testid={`filtered-marketplace-result-${idx}`}
                      style={{
                        padding: 12,
                        background: 'rgba(15, 10, 35, 0.8)',
                        borderRadius: 10,
                        border: `2px solid ${categoryColor}40`,
                        cursor: 'pointer', 
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = categoryColor;
                        e.currentTarget.style.boxShadow = `0 0 15px ${categoryColor}40`;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = `${categoryColor}40`;
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <div style={{
                          width: 10, height: 10, borderRadius: '50%',
                          background: categoryColor,
                          boxShadow: `0 0 8px ${categoryColor}`
                        }} />
                        <span style={{ 
                          background: protocol.price === 0 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(251, 191, 36, 0.2)',
                          color: protocol.price === 0 ? '#10b981' : '#fbbf24',
                          padding: '2px 8px',
                          borderRadius: 10,
                          fontSize: '0.65rem',
                          fontWeight: 700
                        }}>
                          {protocol.price === 0 ? '🆓 FREE' : `$${protocol.price.toFixed(2)}`}
                        </span>
                        <span style={{ color: categoryColor, fontSize: '0.65rem', marginLeft: 'auto' }}>
                          {protocol.category}
                        </span>
                      </div>
                      <div style={{ color: '#fff', fontWeight: 600, fontSize: '0.85rem', marginBottom: 5, lineHeight: 1.3 }}>
                        {protocol.name}
                      </div>
                      <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: '0 0 8px 0', lineHeight: 1.4 }}>
                        {protocol.description?.substring(0, 80) || ''}...
                      </p>
                      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                        {protocol.tags?.slice(0, 3).map((tag, tagIdx) => (
                          <span key={tagIdx} style={{
                            background: 'rgba(124, 58, 237, 0.2)',
                            color: '#a78bfa',
                            padding: '2px 6px',
                            borderRadius: 4,
                            fontSize: '0.6rem'
                          }}>
                            #{tag}
                          </span>
                        ))}
                      </div>
                      <div style={{ display: 'flex', gap: 5, marginTop: 8 }}>
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleCopyFreeProtocol(protocol); }}
                          style={{
                            flex: 1,
                            padding: '5px 8px',
                            background: 'linear-gradient(135deg, #10b981, #059669)',
                            border: 'none',
                            borderRadius: 6,
                            color: '#fff',
                            fontSize: '0.7rem',
                            fontWeight: 600,
                            cursor: 'pointer'
                          }}
                        >
                          📋 Copy Protocol
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
              {filteredProtocols.length === 0 && (
                <p style={{ color: '#71717a', textAlign: 'center', padding: 20 }}>
                  No protocols found for selected categories. Try selecting different categories!
                </p>
              )}
            </div>
          )}
          
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
                  <button className="btn btn-primary" onClick={() => setActiveTab('sell')}>List Your Protocol - FREE</button>
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

      {/* Community Leaderboard Tab */}
      {activeTab === 'leaderboard' && <CommunityLeaderboard showToast={showToast} />}

      {/* AI Recommendations Tab */}
      {activeTab === 'recommendations' && <ProtocolRecommendationEngine showToast={showToast} />}

      {/* Sell Tab */}
      {activeTab === 'sell' && <SellForm newProtocol={newProtocol} setNewProtocol={setNewProtocol} onSubmit={handleListProtocol} adminPercent={adminPercent} />}

      {/* Purchases Tab */}
      {activeTab === 'purchases' && (
        <div>
          {purchases.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>No purchases yet. Browse FREE to find amazing protocols.</p>
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
      {activeTab === 'dashboard' && (
        <div>
          <PerformanceInsights showToast={showToast} />
          <div style={{ marginTop: 25 }}>
            <SellerDashboard dashboard={dashboard} adminPercent={adminPercent} />
          </div>
        </div>
      )}

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
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>Complete your PayPal payment, then click the button below.</p>
              <button className="btn btn-primary" onClick={confirmPurchase} style={{ width: '100%' }}>Payment Completed</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketplacePage;
