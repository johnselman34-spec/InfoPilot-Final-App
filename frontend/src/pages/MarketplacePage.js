import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons } from '../components/shared';

// Funny FREE messaging constants
const FREE_MESSAGES = [
  "💸 100% FREE - Your wallet just did a happy dance!",
  "🎉 ABSOLUTELY FREE - Even your piggy bank is celebrating!",
  "🚀 FREE AS A BIRD - Fly high without spending a dime!",
  "💰 ZERO DOLLARS - Math doesn't get easier than this!",
  "🎁 FREE FOREVER - Like a gift that keeps on giving!",
  "✨ COMPLETELY FREE - Your credit card is on vacation!",
];

// World Wide Map Component with all categories
const WorldWideMap = ({ protocols, categories, selectedCategories, onCategoryToggle, onDeselectAll, onSelectAll }) => {
  // Generate locations for protocols
  const getLocation = (index) => {
    const locations = [
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
    return locations[index % locations.length];
  };

  const getCategoryColor = (category) => {
    const colors = {
      'General': '#7c3aed',
      'News & Media': '#f59e0b',
      'Technology': '#3b82f6',
      'Science & Research': '#10b981',
      'Business & Finance': '#ef4444',
      'Entertainment': '#f472b6',
      'Sports': '#06b6d4',
      'Health & Medicine': '#84cc16'
    };
    return colors[category] || '#7c3aed';
  };

  const filteredProtocols = protocols.filter(p => 
    selectedCategories.length === 0 || selectedCategories.includes(p.category)
  );

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(20, 10, 40, 0.95), rgba(30, 20, 60, 0.95))',
      borderRadius: 15,
      padding: 20,
      marginBottom: 20,
      border: '2px solid rgba(124, 58, 237, 0.4)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15, flexWrap: 'wrap', gap: 10 }}>
        <h3 style={{ color: '#f472b6', display: 'flex', alignItems: 'center', gap: 10, margin: 0 }}>
          🗺️ World Wide Protocol Map
          <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 400 }}>
            LIVE • {filteredProtocols.length} protocols
          </span>
        </h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <button 
            onClick={onSelectAll}
            className="btn btn-primary"
            style={{ padding: '6px 12px', fontSize: '0.75rem' }}
          >
            ✓ Select All
          </button>
          <button 
            onClick={onDeselectAll}
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.75rem' }}
          >
            ✗ Deselect All
          </button>
        </div>
      </div>

      {/* Map Display */}
      <div style={{
        background: 'linear-gradient(135deg, #1a365d 0%, #2d3748 50%, #1a202c 100%)',
        borderRadius: 12,
        height: 280,
        position: 'relative',
        overflow: 'hidden',
        border: '1px solid rgba(124, 58, 237, 0.5)'
      }}>
        {/* World grid lines */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(124, 58, 237, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(124, 58, 237, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }} />

        {/* Protocol markers */}
        {filteredProtocols.map((protocol, index) => {
          const loc = getLocation(index);
          const x = ((loc.lng + 180) / 360) * 100;
          const y = ((90 - loc.lat) / 180) * 100;
          const color = getCategoryColor(protocol.category);
          
          return (
            <div
              key={protocol.id}
              style={{
                position: 'absolute',
                left: `${Math.min(92, Math.max(8, x))}%`,
                top: `${Math.min(88, Math.max(12, y))}%`,
                transform: 'translate(-50%, -50%)',
                cursor: 'pointer',
                zIndex: 10
              }}
              title={`${protocol.name} (${protocol.category})`}
            >
              <div style={{
                width: 16,
                height: 16,
                borderRadius: '50%',
                background: color,
                border: '2px solid white',
                boxShadow: `0 0 12px ${color}80`,
                animation: 'pulse 2s infinite'
              }} />
            </div>
          );
        })}

        {/* Legend */}
        <div style={{
          position: 'absolute',
          bottom: 10,
          right: 10,
          background: 'rgba(0,0,0,0.8)',
          padding: '10px 15px',
          borderRadius: 10,
          maxWidth: 200,
          maxHeight: 150,
          overflowY: 'auto'
        }}>
          <div style={{ color: '#fff', fontSize: '0.7rem', fontWeight: 600, marginBottom: 8 }}>Categories:</div>
          {categories.slice(0, 6).map((cat, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <div style={{ 
                width: 10, 
                height: 10, 
                borderRadius: '50%', 
                background: getCategoryColor(cat.name) 
              }} />
              <span style={{ color: '#a1a1aa', fontSize: '0.65rem' }}>{cat.name}</span>
            </div>
          ))}
        </div>

        {/* FREE Banner */}
        <div style={{
          position: 'absolute',
          top: 10,
          left: 10,
          background: 'linear-gradient(135deg, #10b981, #059669)',
          padding: '6px 12px',
          borderRadius: 20,
          color: '#fff',
          fontSize: '0.7rem',
          fontWeight: 700,
          boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)'
        }}>
          🆓 100% FREE TO BROWSE!
        </div>
      </div>
    </div>
  );
};

// Expandable Category Tree Component
const CategoryTree = ({ categories, selectedCategories, onToggle, expanded, onExpandToggle }) => {
  return (
    <div style={{
      background: 'rgba(30, 20, 50, 0.5)',
      borderRadius: 12,
      padding: 15,
      marginBottom: 15
    }}>
      <h4 style={{ color: '#f472b6', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
        📁 Categories
        <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 400 }}>
          (All checked by default!)
        </span>
      </h4>
      <div style={{ maxHeight: 250, overflowY: 'auto' }}>
        {categories.map((cat, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 8,
              padding: '8px 10px',
              background: selectedCategories.includes(cat.name) 
                ? 'rgba(124, 58, 237, 0.2)' 
                : 'rgba(0,0,0,0.2)',
              borderRadius: 8,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}>
              {/* Expand button */}
              <button
                onClick={() => onExpandToggle(cat.name)}
                style={{
                  width: 20,
                  height: 20,
                  borderRadius: 4,
                  border: 'none',
                  background: 'rgba(124, 58, 237, 0.3)',
                  color: '#a78bfa',
                  cursor: 'pointer',
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {expanded[cat.name] ? '−' : '+'}
              </button>
              
              {/* Checkbox */}
              <input
                type="checkbox"
                checked={selectedCategories.includes(cat.name)}
                onChange={() => onToggle(cat.name)}
                style={{ accentColor: '#7c3aed' }}
              />
              
              <span style={{ 
                color: selectedCategories.includes(cat.name) ? '#fff' : '#a1a1aa',
                flex: 1
              }}>
                {cat.name}
              </span>
              
              <span style={{ 
                background: 'rgba(16, 185, 129, 0.2)',
                color: '#10b981',
                padding: '2px 8px',
                borderRadius: 10,
                fontSize: '0.7rem'
              }}>
                {cat.count}
              </span>
            </div>
            
            {/* Expanded subcategories (simulated) */}
            {expanded[cat.name] && (
              <div style={{ marginLeft: 30, marginTop: 5 }}>
                {['Sub-category A', 'Sub-category B', 'Sub-category C'].map((sub, j) => (
                  <div key={j} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '4px 10px',
                    color: '#71717a',
                    fontSize: '0.85rem'
                  }}>
                    <input type="checkbox" defaultChecked style={{ accentColor: '#7c3aed' }} />
                    {sub}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// Revenue Distribution Info Component
const RevenueInfo = ({ adminPercent = 10 }) => {
  const creatorPercent = 100 - adminPercent;
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))',
      borderRadius: 12,
      padding: 15,
      marginBottom: 15,
      border: '1px solid rgba(16, 185, 129, 0.3)'
    }}>
      <h4 style={{ color: '#10b981', marginBottom: 10 }}>💸 Revenue Distribution</h4>
      <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 120 }}>
          <div style={{ 
            fontSize: '1.5rem', 
            fontWeight: 700, 
            color: '#10b981' 
          }}>
            {creatorPercent}%
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>To Protocol Creator</div>
        </div>
        <div style={{ flex: 1, minWidth: 120 }}>
          <div style={{ 
            fontSize: '1.5rem', 
            fontWeight: 700, 
            color: '#f59e0b' 
          }}>
            {adminPercent}%
          </div>
          <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Platform Fee</div>
        </div>
      </div>
      <div style={{ 
        marginTop: 10, 
        padding: 10, 
        background: 'rgba(0,0,0,0.2)', 
        borderRadius: 8,
        fontSize: '0.75rem',
        color: '#a1a1aa'
      }}>
        💡 <strong>PayPal Note:</strong> Earnings under $1.00 are accumulated until they reach the minimum payout threshold.
        Your earnings are always tracked and will be paid out when eligible!
      </div>
    </div>
  );
};

const MarketplacePage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [protocols, setProtocols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('browse');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [sortBy, setSortBy] = useState('popular');
  
  // Category selection state
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [expandedCategories, setExpandedCategories] = useState({});
  
  // Enhanced filter states
  const [aiSearchQuery, setAiSearchQuery] = useState('');
  const [searchLogic, setSearchLogic] = useState('AND/OR');
  const [docTypes, setDocTypes] = useState({
    webpage: true,
    news: true,
    pdf: true,
    msword: true
  });
  
  // Admin revenue settings
  const [adminPercent, setAdminPercent] = useState(10);
  
  // Sell form state
  const [newProtocol, setNewProtocol] = useState({
    name: '', description: '', protocol: '', price: 0.99, category: 'General', tags: ''
  });
  
  // Purchase state
  const [purchaseModal, setPurchaseModal] = useState(null);
  const [purchases, setPurchases] = useState([]);
  const [dashboard, setDashboard] = useState(null);

  // Random FREE message
  const [freeMessage] = useState(FREE_MESSAGES[Math.floor(Math.random() * FREE_MESSAGES.length)]);

  const fetchProtocols = useCallback(async () => {
    try {
      let url = `${API}/marketplace/protocols?sort=${sortBy}`;
      if (selectedCategory) url += `&category=${selectedCategory}`;
      
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await res.json();
      setProtocols(data.protocols || []);
    } catch (e) {
      console.error('Failed to fetch protocols:', e);
    }
    setLoading(false);
  }, [token, sortBy, selectedCategory]);

  const fetchCategories = useCallback(async () => {
    try {
      const res = await fetch(`${API}/marketplace/categories`);
      const data = await res.json();
      const cats = data.categories || [];
      setCategories(cats);
      // Select all categories by default
      setSelectedCategories(cats.map(c => c.name));
    } catch (e) {
      console.error('Failed to fetch categories:', e);
    }
  }, []);

  const fetchPurchases = useCallback(async () => {
    try {
      const res = await fetch(`${API}/marketplace/purchases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setPurchases(data.purchases || []);
    } catch (e) {
      console.error('Failed to fetch purchases:', e);
    }
  }, [token]);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API}/marketplace/seller/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setDashboard(data);
    } catch (e) {
      console.error('Failed to fetch dashboard:', e);
    }
  }, [token]);

  // Fetch admin revenue settings
  useEffect(() => {
    const fetchRevenueSettings = async () => {
      if (user?.is_admin && token) {
        try {
          const res = await fetch(`${API}/marketplace/admin/revenue-settings`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setAdminPercent(data.admin_percent || 10);
          }
        } catch (e) {
          console.error('Failed to fetch revenue settings:', e);
        }
      }
    };
    fetchRevenueSettings();
  }, [user, token]);

  useEffect(() => {
    fetchProtocols();
    fetchCategories();
    if (token) {
      fetchPurchases();
      fetchDashboard();
    }
  }, [fetchProtocols, fetchCategories, fetchPurchases, fetchDashboard, token]);

  const toggleCategory = (category) => {
    setSelectedCategories(prev => 
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const toggleExpand = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  const selectAllCategories = () => {
    setSelectedCategories(categories.map(c => c.name));
  };

  const deselectAllCategories = () => {
    setSelectedCategories([]);
  };

  // Filter protocols
  const filteredProtocols = protocols.filter(protocol => {
    // Category filter
    if (selectedCategories.length > 0 && !selectedCategories.includes(protocol.category)) {
      return false;
    }
    
    // AI search filter
    if (aiSearchQuery.trim()) {
      const query = aiSearchQuery.toLowerCase();
      const searchTerms = query.split(/\s+/);
      const text = `${protocol.name} ${protocol.description} ${protocol.category} ${(protocol.tags || []).join(' ')}`.toLowerCase();
      
      if (searchLogic === 'AND') {
        if (!searchTerms.every(term => text.includes(term))) return false;
      } else if (searchLogic === 'OR') {
        if (!searchTerms.some(term => text.includes(term))) return false;
      } else {
        const matches = searchTerms.filter(term => text.includes(term));
        if (matches.length < Math.ceil(searchTerms.length / 2)) return false;
      }
    }
    
    return true;
  });

  const handleListProtocol = async () => {
    if (!newProtocol.name || !newProtocol.protocol || !newProtocol.description) {
      showToast('Please fill in all required fields', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/marketplace/protocols`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...newProtocol,
          tags: newProtocol.tags.split(',').map(t => t.trim()).filter(t => t)
        })
      });

      const data = await res.json();
      
      if (res.ok) {
        showToast('🎉 Protocol listed successfully! Start earning money!', 'success');
        setNewProtocol({ name: '', description: '', protocol: '', price: 0.99, category: 'General', tags: '' });
        fetchProtocols();
        fetchDashboard();
        setActiveTab('dashboard');
      } else {
        showToast(data.detail || 'Failed to list protocol', 'error');
      }
    } catch (e) {
      showToast('Failed to list protocol', 'error');
    }
  };

  const handlePurchase = async (protocol) => {
    try {
      const res = await fetch(`${API}/marketplace/initiate-purchase`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ protocol_id: protocol.id })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        window.open(data.payment_url, '_blank', 'width=600,height=700');
        setPurchaseModal({
          protocol,
          pending_id: data.pending_id,
          payment_url: data.payment_url,
          step: 'confirm'
        });
      } else {
        showToast(data.detail || 'Failed to initiate purchase', 'error');
      }
    } catch (e) {
      showToast('Failed to initiate purchase', 'error');
    }
  };

  const confirmPurchase = async () => {
    if (!purchaseModal) return;
    
    const transactionId = prompt('Enter your PayPal Transaction ID:');
    if (!transactionId) {
      showToast('Transaction ID is required', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/marketplace/confirm-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          protocol_id: purchaseModal.protocol.id,
          transaction_id: transactionId,
          amount: purchaseModal.protocol.price
        })
      });

      const data = await res.json();
      
      if (res.ok) {
        showToast('🎉 Protocol purchased! You\'re amazing!', 'success');
        setPurchaseModal(null);
        fetchProtocols();
        fetchPurchases();
      } else {
        showToast(data.detail || 'Purchase confirmation failed', 'error');
      }
    } catch (e) {
      showToast('Purchase confirmation failed', 'error');
    }
  };

  const renderStars = (rating) => {
    return '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
  };

  return (
    <div className="card" data-testid="marketplace-page">
      {/* MEGA FREE BANNER */}
      <div style={{
        background: 'linear-gradient(135deg, #10b981, #059669, #047857)',
        padding: '20px',
        textAlign: 'center',
        borderRadius: '12px 12px 0 0',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.05) 10px, rgba(255,255,255,0.05) 20px)'
        }} />
        <h1 style={{ 
          color: '#fff', 
          fontSize: '2rem', 
          fontWeight: 900, 
          margin: 0,
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
          position: 'relative'
        }}>
          🆓 COMPLETELY FREE TO USE! 🆓
        </h1>
        <p style={{ 
          color: '#d1fae5', 
          margin: '10px 0 0 0', 
          fontSize: '1.1rem',
          position: 'relative'
        }}>
          {freeMessage}
        </p>
        <div style={{
          marginTop: 15,
          display: 'flex',
          justifyContent: 'center',
          gap: 20,
          flexWrap: 'wrap',
          position: 'relative'
        }}>
          <span style={{ color: '#fff', fontSize: '0.9rem' }}>✓ Browse FREE</span>
          <span style={{ color: '#fff', fontSize: '0.9rem' }}>✓ Search FREE</span>
          <span style={{ color: '#fff', fontSize: '0.9rem' }}>✓ Create Categories FREE</span>
          <span style={{ color: '#fff', fontSize: '0.9rem' }}>✓ Earn Money Selling!</span>
        </div>
      </div>

      {/* Top Pilot Enterprises Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #1a0a30, #2d1b4e)',
        padding: '10px 20px',
        textAlign: 'center',
        borderBottom: '2px solid rgba(251, 191, 36, 0.5)'
      }}>
        <span style={{ color: '#fbbf24', fontSize: '0.8rem', fontWeight: 700, letterSpacing: '1px' }}>
          ✈️ WORLD WIDE MARKETPLACE • Powered by TOP PILOT ENTERPRISES, INC. ✈️
        </span>
      </div>

      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Shop />
          Protocol Marketplace
          <span style={{
            background: '#10b981',
            color: '#fff',
            padding: '4px 12px',
            borderRadius: 20,
            fontSize: '0.75rem',
            fontWeight: 700
          }}>
            100% FREE
          </span>
        </h2>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Make HUNDREDS or even THOUSANDS of easy dollars! 💰
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {['browse', 'sell', 'purchases', 'dashboard'].map(tab => (
          <button
            key={tab}
            className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab(tab)}
            data-testid={`marketplace-tab-${tab}`}
          >
            {tab === 'browse' && '🔍 Browse FREE'}
            {tab === 'sell' && '💰 Sell & Earn'}
            {tab === 'purchases' && '📦 My Purchases'}
            {tab === 'dashboard' && '📊 My Earnings'}
          </button>
        ))}
        {user?.is_admin && (
          <button
            className={`btn ${activeTab === 'admin' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('admin')}
            style={{ marginLeft: 'auto' }}
          >
            ⚙️ Admin Settings
          </button>
        )}
      </div>

      {/* Browse Tab */}
      {activeTab === 'browse' && (
        <div>
          {/* World Wide Map */}
          <WorldWideMap 
            protocols={filteredProtocols}
            categories={categories}
            selectedCategories={selectedCategories}
            onCategoryToggle={toggleCategory}
            onDeselectAll={deselectAllCategories}
            onSelectAll={selectAllCategories}
          />

          <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20 }}>
            {/* Sidebar with Categories */}
            <div>
              <CategoryTree 
                categories={categories}
                selectedCategories={selectedCategories}
                onToggle={toggleCategory}
                expanded={expandedCategories}
                onExpandToggle={toggleExpand}
              />
              
              <RevenueInfo adminPercent={adminPercent} />
              
              {/* Earn Money CTA */}
              <div style={{
                background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.2))',
                borderRadius: 12,
                padding: 15,
                border: '1px solid rgba(251, 191, 36, 0.3)',
                textAlign: 'center'
              }}>
                <h4 style={{ color: '#fbbf24', margin: '0 0 10px 0' }}>💵 Want to Earn Money?</h4>
                <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '0 0 10px 0' }}>
                  List your protocols and earn {100 - adminPercent}% of every sale!
                </p>
                <button 
                  className="btn btn-primary"
                  onClick={() => setActiveTab('sell')}
                  style={{ width: '100%' }}
                >
                  Start Selling Now!
                </button>
              </div>
            </div>

            {/* Main Content */}
            <div>
              {/* AI Search */}
              <div style={{
                background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(59, 130, 246, 0.1))',
                borderRadius: 12,
                padding: 15,
                marginBottom: 15,
                border: '1px solid rgba(124, 58, 237, 0.3)'
              }}>
                <input
                  className="input-field"
                  placeholder="🔍 AI-Powered Search... (100% FREE!)"
                  value={aiSearchQuery}
                  onChange={(e) => setAiSearchQuery(e.target.value)}
                  style={{ width: '100%', marginBottom: 10 }}
                  data-testid="ai-search-input"
                />
                
                <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'center' }}>
                  <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Logic:</span>
                  {['AND/OR', 'AND', 'OR'].map(logic => (
                    <label key={logic} style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="logic"
                        checked={searchLogic === logic}
                        onChange={() => setSearchLogic(logic)}
                      />
                      <span style={{ color: searchLogic === logic ? '#10b981' : '#71717a' }}>{logic}</span>
                    </label>
                  ))}
                  
                  <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                    {['webpage', 'news', 'pdf', 'msword'].map(type => (
                      <label key={type} style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '4px 10px',
                        background: docTypes[type] ? 'rgba(16, 185, 129, 0.2)' : 'rgba(0,0,0,0.2)',
                        borderRadius: 15,
                        cursor: 'pointer',
                        fontSize: '0.75rem'
                      }}>
                        <input
                          type="checkbox"
                          checked={docTypes[type]}
                          onChange={(e) => setDocTypes({...docTypes, [type]: e.target.checked})}
                          style={{ width: 12, height: 12 }}
                        />
                        <span style={{ color: docTypes[type] ? '#10b981' : '#71717a' }}>
                          {type === 'webpage' ? '🌐' : type === 'news' ? '📰' : type === 'pdf' ? '📄' : '📝'}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Sort */}
              <div style={{ display: 'flex', gap: 10, marginBottom: 15 }}>
                <select
                  className="input"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  style={{ maxWidth: 200 }}
                >
                  <option value="popular">Most Popular</option>
                  <option value="newest">Newest</option>
                  <option value="price_low">Price: Low to High</option>
                  <option value="price_high">Price: High to Low</option>
                  <option value="rating">Highest Rated</option>
                </select>
                <span style={{ color: '#a1a1aa', alignSelf: 'center' }}>
                  {filteredProtocols.length} protocols found
                </span>
              </div>

              {/* Protocol Grid */}
              {loading ? (
                <p style={{ textAlign: 'center', color: '#a1a1aa' }}>Loading...</p>
              ) : filteredProtocols.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
                  <div style={{ fontSize: '3rem', marginBottom: 15 }}>🔍</div>
                  <p style={{ color: '#a1a1aa', marginBottom: 15 }}>No protocols found. Be the first to sell!</p>
                  <button className="btn btn-primary" onClick={() => setActiveTab('sell')}>
                    List Your Protocol - It's FREE!
                  </button>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 15 }}>
                  {filteredProtocols.map(protocol => (
                    <div 
                      key={protocol.id}
                      style={{
                        background: 'rgba(30, 20, 50, 0.5)',
                        borderRadius: 12,
                        padding: 15,
                        border: protocol.is_featured 
                          ? '2px solid #f472b6' 
                          : '1px solid rgba(124, 58, 237, 0.3)',
                        position: 'relative'
                      }}
                      data-testid={`protocol-card-${protocol.id}`}
                    >
                      {protocol.is_featured && (
                        <span style={{
                          position: 'absolute', top: -8, right: 10,
                          background: '#f472b6', color: '#fff', padding: '3px 10px',
                          borderRadius: 15, fontSize: '0.65rem', fontWeight: 700
                        }}>
                          FEATURED
                        </span>
                      )}
                      
                      <h4 style={{ color: '#f472b6', marginBottom: 8 }}>{protocol.name}</h4>
                      <p style={{ color: '#a1a1aa', fontSize: '0.8rem', marginBottom: 10 }}>
                        {protocol.description?.substring(0, 80)}...
                      </p>
                      
                      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 10 }}>
                        <span style={{ 
                          background: 'rgba(124, 58, 237, 0.2)', 
                          color: '#a78bfa', 
                          padding: '2px 8px', 
                          borderRadius: 10, 
                          fontSize: '0.7rem' 
                        }}>
                          {protocol.category}
                        </span>
                      </div>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                        <span style={{ color: '#fbbf24', fontSize: '0.8rem' }}>
                          {renderStars(protocol.rating)} ({protocol.review_count})
                        </span>
                        <span style={{ color: '#71717a', fontSize: '0.75rem' }}>{protocol.total_sales} sales</span>
                      </div>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: '#10b981', fontSize: '1.2rem', fontWeight: 700 }}>
                          ${protocol.price.toFixed(2)}
                        </span>
                        {protocol.is_owned ? (
                          <span style={{ color: '#10b981', fontSize: '0.85rem' }}>✓ Owned</span>
                        ) : (
                          <button 
                            className="btn btn-primary"
                            onClick={() => handlePurchase(protocol)}
                            style={{ padding: '6px 15px', fontSize: '0.85rem' }}
                          >
                            Buy Now
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Sell Tab */}
      {activeTab === 'sell' && (
        <div style={{ maxWidth: 600 }}>
          <div style={{ 
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))',
            padding: 20, borderRadius: 12, marginBottom: 20
          }}>
            <h3 style={{ color: '#10b981', marginBottom: 10 }}>
              💰 Earn HUNDREDS or THOUSANDS of Easy Dollars!
            </h3>
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
              List your search protocols and earn <strong style={{ color: '#10b981' }}>{100 - adminPercent}%</strong> of every sale!
              <br/>
              <span style={{ color: '#71717a', fontSize: '0.8rem' }}>
                Platform fee: {adminPercent}% • Listing is FREE • No monthly fees • Ever!
              </span>
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            <input
              className="input"
              placeholder="Protocol Name * (Make it catchy!)"
              value={newProtocol.name}
              onChange={(e) => setNewProtocol({ ...newProtocol, name: e.target.value })}
            />
            <textarea
              className="input"
              placeholder="Description - Tell buyers why they need this! *"
              rows={3}
              value={newProtocol.description}
              onChange={(e) => setNewProtocol({ ...newProtocol, description: e.target.value })}
            />
            <textarea
              className="input"
              placeholder="Protocol String - Your secret sauce! *"
              rows={2}
              value={newProtocol.protocol}
              onChange={(e) => setNewProtocol({ ...newProtocol, protocol: e.target.value })}
              style={{ fontFamily: 'monospace' }}
            />
            <div style={{ display: 'flex', gap: 15 }}>
              <div style={{ flex: 1 }}>
                <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Price ($0.99 - $99.99)</label>
                <input
                  className="input"
                  type="number"
                  min="0.99"
                  max="99.99"
                  step="0.01"
                  value={newProtocol.price}
                  onChange={(e) => setNewProtocol({ ...newProtocol, price: parseFloat(e.target.value) || 0.99 })}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Category</label>
                <select
                  className="input"
                  value={newProtocol.category}
                  onChange={(e) => setNewProtocol({ ...newProtocol, category: e.target.value })}
                >
                  <option>General</option>
                  <option>News & Media</option>
                  <option>Science & Research</option>
                  <option>Business & Finance</option>
                  <option>Technology</option>
                  <option>Entertainment</option>
                </select>
              </div>
            </div>
            <input
              className="input"
              placeholder="Tags (comma-separated)"
              value={newProtocol.tags}
              onChange={(e) => setNewProtocol({ ...newProtocol, tags: e.target.value })}
            />
            
            <div style={{ 
              background: 'rgba(251, 191, 36, 0.1)', 
              padding: 15, 
              borderRadius: 10,
              border: '1px solid rgba(251, 191, 36, 0.3)'
            }}>
              <p style={{ color: '#fbbf24', fontSize: '0.9rem', margin: 0 }}>
                💵 You'll earn: <strong>${((newProtocol.price || 0.99) * (100 - adminPercent) / 100).toFixed(2)}</strong> per sale
              </p>
            </div>
            
            <button 
              className="btn btn-primary"
              onClick={handleListProtocol}
              style={{ marginTop: 10, fontSize: '1.1rem', padding: '15px' }}
            >
              🚀 List Protocol & Start Earning!
            </button>
          </div>
        </div>
      )}

      {/* Purchases Tab */}
      {activeTab === 'purchases' && (
        <div>
          {purchases.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>No purchases yet. Browse FREE to find amazing protocols!</p>
              <button className="btn btn-primary" onClick={() => setActiveTab('browse')}>
                Browse Protocols
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              {purchases.map(purchase => (
                <div key={purchase.id} style={{
                  background: 'rgba(30, 20, 50, 0.5)',
                  borderRadius: 12,
                  padding: 20,
                  border: '1px solid rgba(16, 185, 129, 0.3)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h3 style={{ color: '#f472b6', marginBottom: 5 }}>{purchase.protocol_name}</h3>
                      <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                        Purchased: {new Date(purchase.purchased_at).toLocaleDateString()}
                      </p>
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
      {activeTab === 'dashboard' && dashboard && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginBottom: 30 }}>
            <div style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))',
              borderRadius: 12, padding: 20, textAlign: 'center'
            }}>
              <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Your Earnings</p>
              <p style={{ color: '#10b981', fontSize: '2.5rem', fontWeight: 700 }}>
                ${(dashboard.total_earnings || 0).toFixed(2)}
              </p>
              <p style={{ color: '#71717a', fontSize: '0.75rem' }}>
                {dashboard.total_earnings < 1 
                  ? `Accumulating... (PayPal min: $1.00)` 
                  : 'Ready for payout!'}
              </p>
            </div>
            <div style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(124, 58, 237, 0.1))',
              borderRadius: 12, padding: 20, textAlign: 'center'
            }}>
              <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Total Sales</p>
              <p style={{ color: '#a78bfa', fontSize: '2.5rem', fontWeight: 700 }}>{dashboard.total_sales || 0}</p>
            </div>
            <div style={{
              background: 'linear-gradient(135deg, rgba(244, 114, 182, 0.2), rgba(244, 114, 182, 0.1))',
              borderRadius: 12, padding: 20, textAlign: 'center'
            }}>
              <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Listed Protocols</p>
              <p style={{ color: '#f472b6', fontSize: '2.5rem', fontWeight: 700 }}>{dashboard.listed_protocols || dashboard.total_listings || 0}</p>
            </div>
          </div>
          
          <div style={{
            background: 'rgba(251, 191, 36, 0.1)',
            padding: 15,
            borderRadius: 10,
            marginBottom: 20,
            border: '1px solid rgba(251, 191, 36, 0.3)'
          }}>
            <p style={{ color: '#fbbf24', margin: 0, fontSize: '0.9rem' }}>
              💡 <strong>Pro Tip:</strong> Earnings under $1.00 are accumulated until they reach PayPal's minimum payout threshold.
              Your money is safe and tracked - it'll be paid out as soon as you hit $1.00!
            </p>
          </div>
        </div>
      )}

      {/* Admin Settings Tab */}
      {activeTab === 'admin' && user?.is_admin && (
        <div style={{ maxWidth: 600 }}>
          <h3 style={{ color: '#f472b6', marginBottom: 20 }}>⚙️ Admin Revenue Settings</h3>
          
          <div style={{ marginBottom: 20 }}>
            <label style={{ color: '#a1a1aa', display: 'block', marginBottom: 8 }}>
              Platform Fee Percentage (Admin Share)
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
              <input
                type="range"
                min="5"
                max="30"
                value={adminPercent}
                onChange={(e) => setAdminPercent(parseInt(e.target.value))}
                style={{ flex: 1 }}
              />
              <span style={{ 
                color: '#f59e0b', 
                fontWeight: 700, 
                fontSize: '1.2rem',
                minWidth: 50 
              }}>
                {adminPercent}%
              </span>
            </div>
          </div>
          
          <div style={{ 
            background: 'rgba(30, 20, 50, 0.5)', 
            padding: 20, 
            borderRadius: 12,
            marginBottom: 20
          }}>
            <h4 style={{ color: '#fff', marginBottom: 15 }}>Revenue Split Preview:</h4>
            <div style={{ display: 'flex', gap: 20 }}>
              <div style={{ flex: 1, textAlign: 'center' }}>
                <div style={{ color: '#10b981', fontSize: '2rem', fontWeight: 700 }}>
                  {100 - adminPercent}%
                </div>
                <div style={{ color: '#a1a1aa' }}>To Creator</div>
              </div>
              <div style={{ flex: 1, textAlign: 'center' }}>
                <div style={{ color: '#f59e0b', fontSize: '2rem', fontWeight: 700 }}>
                  {adminPercent}%
                </div>
                <div style={{ color: '#a1a1aa' }}>To Admin</div>
              </div>
            </div>
          </div>
          
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            padding: 15,
            borderRadius: 10,
            border: '1px solid rgba(239, 68, 68, 0.3)',
            marginBottom: 20
          }}>
            <p style={{ color: '#ef4444', margin: 0, fontSize: '0.85rem' }}>
              ⚠️ <strong>PayPal Note:</strong> PayPal requires minimum $1.00 per payout. 
              For transactions where your {adminPercent}% share is less than $1.00, 
              earnings are accumulated until they reach the minimum.
              <br/><br/>
              Example: A $5.00 protocol sale gives you ${(5 * adminPercent / 100).toFixed(2)}.
              This accumulates with other sales until reaching $1.00.
            </p>
          </div>
          
          <button 
            className="btn btn-primary" 
            style={{ marginTop: 10, width: '100%' }}
            onClick={async () => {
              try {
                const res = await fetch(`${API}/marketplace/admin/revenue-settings`, {
                  method: 'PUT',
                  headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                  },
                  body: JSON.stringify({ admin_percent: adminPercent })
                });
                if (res.ok) {
                  showToast('Revenue settings saved successfully!', 'success');
                } else {
                  showToast('Failed to save settings', 'error');
                }
              } catch (e) {
                showToast('Failed to save settings', 'error');
              }
            }}
          >
            💾 Save Revenue Settings
          </button>

          {/* Payout Management Section */}
          <div style={{ marginTop: 30 }}>
            <h3 style={{ color: '#f472b6', marginBottom: 15 }}>💳 Payout Management</h3>
            <button 
              className="btn btn-secondary"
              onClick={async () => {
                try {
                  const res = await fetch(`${API}/marketplace/admin/payouts`, {
                    headers: { Authorization: `Bearer ${token}` }
                  });
                  const data = await res.json();
                  alert(`Ready for Payout: ${data.ready_for_payout?.length || 0} users ($${data.total_ready_amount?.toFixed(2) || '0.00'})\nAccumulating: ${data.accumulating?.length || 0} users ($${data.total_accumulating_amount?.toFixed(2) || '0.00'})\nAdmin Platform Fees: $${data.admin_platform_fees?.toFixed(2) || '0.00'}`);
                } catch (e) {
                  showToast('Failed to fetch payout data', 'error');
                }
              }}
            >
              📊 View Pending Payouts
            </button>
          </div>
        </div>
      )}

      {/* Purchase Modal */}
      {purchaseModal && (
        <div className="modal-overlay" onClick={() => setPurchaseModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 450 }}>
            <div className="modal-header">
              <h2>Complete Purchase</h2>
              <button className="modal-close" onClick={() => setPurchaseModal(null)}>×</button>
            </div>
            <div style={{ padding: 20 }}>
              <div style={{ 
                background: 'rgba(16, 185, 129, 0.1)', 
                padding: 15, 
                borderRadius: 10,
                marginBottom: 20
              }}>
                <p style={{ color: '#10b981', fontWeight: 600 }}>{purchaseModal.protocol.name}</p>
                <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>Price: ${purchaseModal.protocol.price.toFixed(2)}</p>
              </div>
              
              <ol style={{ color: '#a1a1aa', paddingLeft: 20, marginBottom: 20 }}>
                <li style={{ marginBottom: 10 }}>Complete payment in PayPal</li>
                <li style={{ marginBottom: 10 }}>Copy your Transaction ID</li>
                <li>Click "Confirm Purchase"</li>
              </ol>
              
              <div style={{ display: 'flex', gap: 10 }}>
                <button 
                  className="btn btn-primary"
                  onClick={confirmPurchase}
                  style={{ flex: 1 }}
                >
                  Confirm Purchase
                </button>
                <button 
                  className="btn btn-secondary"
                  onClick={() => setPurchaseModal(null)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.2); opacity: 0.8; }
        }
      `}</style>
    </div>
  );
};

export default MarketplacePage;
