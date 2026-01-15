import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons } from '../components/shared';

// Simple map component for marketplace
const MarketplaceMap = ({ protocols, selectedProtocols, onProtocolClick }) => {
  const mapRef = React.useRef(null);
  
  // Generate mock locations for protocols (in a real app, these would come from the backend)
  const getProtocolLocation = (protocol, index) => {
    const locations = [
      { lat: 40.7128, lng: -74.0060, city: 'New York' },
      { lat: 34.0522, lng: -118.2437, city: 'Los Angeles' },
      { lat: 41.8781, lng: -87.6298, city: 'Chicago' },
      { lat: 29.7604, lng: -95.3698, city: 'Houston' },
      { lat: 33.4484, lng: -112.0740, city: 'Phoenix' },
      { lat: 43.9108, lng: -69.9669, city: 'Brunswick, ME' },
      { lat: 51.5074, lng: -0.1278, city: 'London' },
      { lat: 48.8566, lng: 2.3522, city: 'Paris' },
    ];
    return locations[index % locations.length];
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(20, 10, 40, 0.9), rgba(30, 20, 60, 0.9))',
      borderRadius: 15,
      padding: 20,
      marginBottom: 20,
      border: '2px solid rgba(124, 58, 237, 0.3)'
    }}>
      <h3 style={{ color: '#f472b6', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 10 }}>
        🗺️ World Wide Protocol Map
        <span style={{ fontSize: '0.8rem', color: '#a1a1aa', fontWeight: 400 }}>
          ({protocols.length} protocols worldwide)
        </span>
      </h3>
      
      {/* Simple visual map representation */}
      <div ref={mapRef} style={{
        background: 'linear-gradient(135deg, #1a365d 0%, #2d3748 50%, #1a202c 100%)',
        borderRadius: 10,
        height: 250,
        position: 'relative',
        overflow: 'hidden',
        border: '1px solid rgba(124, 58, 237, 0.5)'
      }}>
        {/* World outline effect */}
        <div style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.1,
          background: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 50'%3E%3Cellipse cx='50' cy='25' rx='45' ry='20' fill='none' stroke='%237c3aed' stroke-width='0.5'/%3E%3C/svg%3E")`,
          backgroundSize: 'cover'
        }} />
        
        {/* Protocol markers */}
        {protocols.slice(0, 8).map((protocol, index) => {
          const loc = getProtocolLocation(protocol, index);
          const isSelected = selectedProtocols.includes(protocol.id);
          const x = ((loc.lng + 180) / 360) * 100;
          const y = ((90 - loc.lat) / 180) * 100;
          
          return (
            <div
              key={protocol.id}
              onClick={() => onProtocolClick(protocol.id)}
              style={{
                position: 'absolute',
                left: `${Math.min(90, Math.max(10, x))}%`,
                top: `${Math.min(85, Math.max(15, y))}%`,
                transform: 'translate(-50%, -50%)',
                cursor: 'pointer',
                zIndex: isSelected ? 10 : 1
              }}
            >
              <div style={{
                width: isSelected ? 20 : 14,
                height: isSelected ? 20 : 14,
                borderRadius: '50%',
                background: isSelected 
                  ? 'linear-gradient(135deg, #10b981, #059669)' 
                  : 'linear-gradient(135deg, #f472b6, #ec4899)',
                border: '2px solid white',
                boxShadow: isSelected 
                  ? '0 0 20px rgba(16, 185, 129, 0.8)' 
                  : '0 0 10px rgba(244, 114, 182, 0.5)',
                animation: isSelected ? 'pulse 2s infinite' : 'none'
              }} />
              <div style={{
                position: 'absolute',
                top: '100%',
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'rgba(0,0,0,0.8)',
                color: '#fff',
                padding: '2px 6px',
                borderRadius: 4,
                fontSize: '0.65rem',
                whiteSpace: 'nowrap',
                marginTop: 4
              }}>
                {protocol.name.substring(0, 15)}
              </div>
            </div>
          );
        })}
        
        {/* Legend */}
        <div style={{
          position: 'absolute',
          bottom: 10,
          right: 10,
          background: 'rgba(0,0,0,0.7)',
          padding: '8px 12px',
          borderRadius: 8,
          fontSize: '0.7rem'
        }}>
          <div style={{ color: '#f472b6', marginBottom: 4 }}>● Available</div>
          <div style={{ color: '#10b981' }}>● Selected</div>
        </div>
      </div>
    </div>
  );
};

// Statistics Dashboard Component
const MarketplaceStats = ({ protocols, purchases, dashboard }) => {
  const totalProtocols = protocols.length;
  const totalSales = protocols.reduce((sum, p) => sum + (p.total_sales || 0), 0);
  const avgPrice = protocols.length > 0 
    ? (protocols.reduce((sum, p) => sum + p.price, 0) / protocols.length).toFixed(2) 
    : '0.00';
  const topCategory = protocols.length > 0
    ? [...protocols].sort((a, b) => (b.total_sales || 0) - (a.total_sales || 0))[0]?.category || 'N/A'
    : 'N/A';

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
      gap: 15,
      marginBottom: 20
    }}>
      {[
        { label: 'Total Protocols', value: totalProtocols, icon: '📦', color: '#7c3aed' },
        { label: 'Total Sales', value: totalSales, icon: '💰', color: '#10b981' },
        { label: 'Avg Price', value: `$${avgPrice}`, icon: '📊', color: '#f59e0b' },
        { label: 'Top Category', value: topCategory, icon: '🏆', color: '#f472b6' }
      ].map((stat, i) => (
        <div key={i} style={{
          background: `linear-gradient(135deg, ${stat.color}20, ${stat.color}10)`,
          borderRadius: 12,
          padding: 15,
          border: `1px solid ${stat.color}40`,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', marginBottom: 5 }}>{stat.icon}</div>
          <div style={{ color: stat.color, fontSize: '1.2rem', fontWeight: 700 }}>{stat.value}</div>
          <div style={{ color: '#a1a1aa', fontSize: '0.75rem' }}>{stat.label}</div>
        </div>
      ))}
    </div>
  );
};

const MarketplacePage = ({ showToast }) => {
  const { token } = useAuth();
  const [protocols, setProtocols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('browse');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [sortBy, setSortBy] = useState('popular');
  
  // Enhanced filter states
  const [aiSearchQuery, setAiSearchQuery] = useState('');
  const [searchLogic, setSearchLogic] = useState('AND/OR'); // AND/OR, AND, OR
  const [docTypes, setDocTypes] = useState({
    webpage: true,
    news: true,
    pdf: true,
    msword: true
  });
  const [selectedProtocols, setSelectedProtocols] = useState([]);
  const [showMap, setShowMap] = useState(true);
  const [showStats, setShowStats] = useState(true);
  
  // Sell form state
  const [newProtocol, setNewProtocol] = useState({
    name: '', description: '', protocol: '', price: 0.99, category: 'General', tags: ''
  });
  
  // Purchase state
  const [purchaseModal, setPurchaseModal] = useState(null);
  const [purchases, setPurchases] = useState([]);
  const [dashboard, setDashboard] = useState(null);

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
      setCategories(data.categories || []);
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

  useEffect(() => {
    fetchProtocols();
    fetchCategories();
    if (token) {
      fetchPurchases();
      fetchDashboard();
    }
  }, [fetchProtocols, fetchCategories, fetchPurchases, fetchDashboard, token]);

  // Filter protocols based on AI search and other filters
  const filteredProtocols = protocols.filter(protocol => {
    // AI search filter
    if (aiSearchQuery.trim()) {
      const query = aiSearchQuery.toLowerCase();
      const searchTerms = query.split(/\s+/);
      const text = `${protocol.name} ${protocol.description} ${protocol.category} ${(protocol.tags || []).join(' ')}`.toLowerCase();
      
      if (searchLogic === 'AND') {
        if (!searchTerms.every(term => text.includes(term))) return false;
      } else if (searchLogic === 'OR') {
        if (!searchTerms.some(term => text.includes(term))) return false;
      } else { // AND/OR - more flexible matching
        const matches = searchTerms.filter(term => text.includes(term));
        if (matches.length < Math.ceil(searchTerms.length / 2)) return false;
      }
    }
    
    return true;
  });

  const toggleProtocolSelection = (protocolId) => {
    setSelectedProtocols(prev => 
      prev.includes(protocolId) 
        ? prev.filter(id => id !== protocolId)
        : [...prev, protocolId]
    );
  };

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
        showToast('Protocol listed successfully!', 'success');
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
    
    const transactionId = prompt('Please enter your PayPal Transaction ID (found in your PayPal receipt):');
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
        showToast('🎉 Protocol purchased successfully! +10 XP', 'success');
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
      {/* Header with Top Pilot Enterprises branding */}
      <div style={{
        background: 'linear-gradient(135deg, #1a0a30, #2d1b4e)',
        padding: '12px 20px',
        marginBottom: 20,
        borderRadius: '12px 12px 0 0',
        borderBottom: '2px solid rgba(251, 191, 36, 0.5)'
      }}>
        <div style={{ color: '#fbbf24', fontSize: '0.8rem', fontWeight: 700, letterSpacing: '1px', textAlign: 'center' }}>
          ✈️ WORLD WIDE MARKETPLACE • Powered by TOP PILOT ENTERPRISES, INC. ✈️
        </div>
      </div>

      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Shop />
          Protocol Marketplace
        </h2>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Buy and sell search protocols • 90% to creators • InfoJet 2.0™ Powered
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
            {tab === 'browse' && '🔍 Browse'}
            {tab === 'sell' && '💰 Sell Protocol'}
            {tab === 'purchases' && '📦 My Purchases'}
            {tab === 'dashboard' && '📊 Seller Dashboard'}
          </button>
        ))}
      </div>

      {/* Browse Tab - Enhanced */}
      {activeTab === 'browse' && (
        <div>
          {/* Statistics Dashboard */}
          {showStats && (
            <MarketplaceStats protocols={protocols} purchases={purchases} dashboard={dashboard} />
          )}
          
          {/* Map Integration */}
          {showMap && protocols.length > 0 && (
            <MarketplaceMap 
              protocols={filteredProtocols} 
              selectedProtocols={selectedProtocols}
              onProtocolClick={toggleProtocolSelection}
            />
          )}

          {/* AI Search & Advanced Filters */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(59, 130, 246, 0.1))',
            borderRadius: 15,
            padding: 20,
            marginBottom: 20,
            border: '1px solid rgba(124, 58, 237, 0.3)'
          }}>
            <h4 style={{ color: '#a78bfa', marginBottom: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
              🤖 AI-Powered Search
            </h4>
            
            {/* AI Search Input */}
            <div style={{ marginBottom: 15 }}>
              <input
                className="input-field"
                placeholder="🔍 Search protocols with AI intelligence... (e.g., 'climate data statistics')"
                value={aiSearchQuery}
                onChange={(e) => setAiSearchQuery(e.target.value)}
                style={{ width: '100%', fontSize: '1rem' }}
                data-testid="ai-search-input"
              />
            </div>

            {/* Search Logic Radio Buttons */}
            <div style={{ display: 'flex', gap: 20, marginBottom: 15, flexWrap: 'wrap' }}>
              <span style={{ color: '#a1a1aa', fontWeight: 600 }}>Search Logic:</span>
              {['AND/OR', 'AND', 'OR'].map(logic => (
                <label key={logic} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 6, 
                  cursor: 'pointer',
                  color: searchLogic === logic ? '#10b981' : '#a1a1aa'
                }}>
                  <input
                    type="radio"
                    name="searchLogic"
                    value={logic}
                    checked={searchLogic === logic}
                    onChange={(e) => setSearchLogic(e.target.value)}
                    data-testid={`search-logic-${logic.toLowerCase()}`}
                  />
                  <span style={{ fontWeight: searchLogic === logic ? 700 : 400 }}>{logic}</span>
                </label>
              ))}
            </div>

            {/* Document Type Checkboxes */}
            <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap', marginBottom: 15 }}>
              <span style={{ color: '#a1a1aa', fontWeight: 600 }}>Document Types:</span>
              {[
                { key: 'webpage', label: '🌐 Webpage', color: '#3b82f6' },
                { key: 'news', label: '📰 News Article', color: '#f59e0b' },
                { key: 'pdf', label: '📄 PDF', color: '#ef4444' },
                { key: 'msword', label: '📝 MS Word', color: '#10b981' }
              ].map(({ key, label, color }) => (
                <label key={key} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 6, 
                  cursor: 'pointer',
                  padding: '6px 12px',
                  background: docTypes[key] ? `${color}20` : 'rgba(0,0,0,0.2)',
                  borderRadius: 20,
                  border: `1px solid ${docTypes[key] ? color : '#4b5563'}`,
                  transition: 'all 0.2s'
                }}>
                  <input
                    type="checkbox"
                    checked={docTypes[key]}
                    onChange={(e) => setDocTypes({ ...docTypes, [key]: e.target.checked })}
                    style={{ accentColor: color }}
                    data-testid={`doctype-${key}`}
                  />
                  <span style={{ color: docTypes[key] ? color : '#6b7280', fontSize: '0.85rem' }}>{label}</span>
                </label>
              ))}
            </div>

            {/* Toggle buttons */}
            <div style={{ display: 'flex', gap: 10 }}>
              <button 
                className={`btn ${showMap ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setShowMap(!showMap)}
                style={{ fontSize: '0.8rem' }}
              >
                {showMap ? '🗺️ Hide Map' : '🗺️ Show Map'}
              </button>
              <button 
                className={`btn ${showStats ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setShowStats(!showStats)}
                style={{ fontSize: '0.8rem' }}
              >
                {showStats ? '📊 Hide Stats' : '📊 Show Stats'}
              </button>
            </div>
          </div>

          {/* Standard Filters */}
          <div style={{ display: 'flex', gap: 15, marginBottom: 20, flexWrap: 'wrap' }}>
            <select
              className="input"
              style={{ flex: 1, minWidth: 150 }}
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              data-testid="marketplace-category-filter"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat.name} value={cat.name}>{cat.name} ({cat.count})</option>
              ))}
            </select>
            <select
              className="input"
              style={{ flex: 1, minWidth: 150 }}
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              data-testid="marketplace-sort"
            >
              <option value="popular">Most Popular</option>
              <option value="newest">Newest</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
              <option value="rating">Highest Rated</option>
            </select>
          </div>

          {/* Selected Protocols Action Bar */}
          {selectedProtocols.length > 0 && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))',
              padding: 15,
              borderRadius: 12,
              marginBottom: 20,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 10
            }}>
              <span style={{ color: '#10b981', fontWeight: 600 }}>
                ✓ {selectedProtocols.length} protocol(s) selected
              </span>
              <div style={{ display: 'flex', gap: 10 }}>
                <button 
                  className="btn btn-primary"
                  onClick={() => {
                    const total = protocols
                      .filter(p => selectedProtocols.includes(p.id))
                      .reduce((sum, p) => sum + p.price, 0);
                    alert(`Total: $${total.toFixed(2)} for ${selectedProtocols.length} protocols`);
                  }}
                >
                  Buy Selected (${protocols.filter(p => selectedProtocols.includes(p.id)).reduce((sum, p) => sum + p.price, 0).toFixed(2)})
                </button>
                <button 
                  className="btn btn-secondary"
                  onClick={() => setSelectedProtocols([])}
                >
                  Clear Selection
                </button>
              </div>
            </div>
          )}

          {/* Protocol Grid */}
          {loading ? (
            <p style={{ textAlign: 'center', color: '#a1a1aa' }}>Loading protocols...</p>
          ) : filteredProtocols.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>
                {aiSearchQuery ? 'No protocols match your search. Try different keywords!' : 'No protocols listed yet. Be the first to sell!'}
              </p>
              <button className="btn btn-primary" onClick={() => setActiveTab('sell')}>
                List Your Protocol
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
              {filteredProtocols.map(protocol => {
                const isSelected = selectedProtocols.includes(protocol.id);
                return (
                  <div 
                    key={protocol.id}
                    style={{
                      background: isSelected 
                        ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(30, 20, 50, 0.8))'
                        : 'rgba(30, 20, 50, 0.5)',
                      borderRadius: 12,
                      padding: 20,
                      border: isSelected 
                        ? '2px solid #10b981' 
                        : protocol.is_featured 
                          ? '2px solid #f472b6' 
                          : '1px solid rgba(124, 58, 237, 0.3)',
                      position: 'relative',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onClick={() => toggleProtocolSelection(protocol.id)}
                    data-testid={`protocol-card-${protocol.id}`}
                  >
                    {/* Selection checkbox */}
                    <div style={{
                      position: 'absolute',
                      top: 10,
                      left: 10,
                      width: 24,
                      height: 24,
                      borderRadius: 6,
                      background: isSelected ? '#10b981' : 'rgba(255,255,255,0.1)',
                      border: `2px solid ${isSelected ? '#10b981' : '#4b5563'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      {isSelected && <span style={{ color: '#fff' }}>✓</span>}
                    </div>
                    
                    {protocol.is_featured && (
                      <span style={{
                        position: 'absolute', top: -10, right: 10,
                        background: '#f472b6', color: '#fff', padding: '4px 10px',
                        borderRadius: 20, fontSize: '0.7rem', fontWeight: 700
                      }}>
                        FEATURED
                      </span>
                    )}
                    
                    <h3 style={{ color: '#f472b6', marginBottom: 8, marginLeft: 30 }}>{protocol.name}</h3>
                    <p style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 10 }}>
                      {protocol.description.substring(0, 100)}...
                    </p>
                    
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
                      <span style={{ background: 'rgba(124, 58, 237, 0.2)', color: '#a78bfa', padding: '3px 8px', borderRadius: 10, fontSize: '0.75rem' }}>
                        {protocol.category}
                      </span>
                      {protocol.tags?.slice(0, 2).map(tag => (
                        <span key={tag} style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', padding: '3px 8px', borderRadius: 10, fontSize: '0.75rem' }}>
                          {tag}
                        </span>
                      ))}
                    </div>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
                      <div>
                        <span style={{ color: '#fbbf24' }}>{renderStars(protocol.rating)}</span>
                        <span style={{ color: '#a1a1aa', fontSize: '0.8rem', marginLeft: 5 }}>({protocol.review_count})</span>
                      </div>
                      <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{protocol.total_sales} sales</span>
                    </div>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#10b981', fontSize: '1.3rem', fontWeight: 700 }}>${protocol.price.toFixed(2)}</span>
                      {protocol.is_owned ? (
                        <span style={{ color: '#10b981', fontSize: '0.9rem' }}>✓ Owned</span>
                      ) : (
                        <button 
                          className="btn btn-primary"
                          onClick={(e) => { e.stopPropagation(); handlePurchase(protocol); }}
                          data-testid={`buy-protocol-${protocol.id}`}
                        >
                          Buy Now
                        </button>
                      )}
                    </div>
                    
                    <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
                      by {protocol.creator_name}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Sell Tab */}
      {activeTab === 'sell' && (
        <div style={{ maxWidth: 600 }}>
          <div style={{ 
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))',
            padding: 20, borderRadius: 12, marginBottom: 20
          }}>
            <h3 style={{ color: '#10b981', marginBottom: 10 }}>💰 Earn Money from Your Protocols!</h3>
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
              List your search protocols and earn <strong>90%</strong> of every sale. 
              Set your own price between $0.99 - $99.99.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            <input
              className="input"
              placeholder="Protocol Name *"
              value={newProtocol.name}
              onChange={(e) => setNewProtocol({ ...newProtocol, name: e.target.value })}
              data-testid="protocol-name-input"
            />
            <textarea
              className="input"
              placeholder="Description - Explain what your protocol searches for *"
              rows={3}
              value={newProtocol.description}
              onChange={(e) => setNewProtocol({ ...newProtocol, description: e.target.value })}
              data-testid="protocol-description-input"
            />
            <textarea
              className="input"
              placeholder="Protocol String - e.g. (climate or weather) & (data or statistics)+ *"
              rows={2}
              value={newProtocol.protocol}
              onChange={(e) => setNewProtocol({ ...newProtocol, protocol: e.target.value })}
              data-testid="protocol-string-input"
            />
            <div style={{ display: 'flex', gap: 15 }}>
              <div style={{ flex: 1 }}>
                <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Price (USD)</label>
                <input
                  className="input"
                  type="number"
                  min="0.99"
                  max="99.99"
                  step="0.01"
                  value={newProtocol.price}
                  onChange={(e) => setNewProtocol({ ...newProtocol, price: parseFloat(e.target.value) || 0.99 })}
                  data-testid="protocol-price-input"
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Category</label>
                <select
                  className="input"
                  value={newProtocol.category}
                  onChange={(e) => setNewProtocol({ ...newProtocol, category: e.target.value })}
                  data-testid="protocol-category-input"
                >
                  <option>General</option>
                  <option>News & Media</option>
                  <option>Science & Research</option>
                  <option>Business & Finance</option>
                  <option>Technology</option>
                  <option>Entertainment</option>
                  <option>Sports</option>
                  <option>Health & Medicine</option>
                </select>
              </div>
            </div>
            <input
              className="input"
              placeholder="Tags (comma-separated)"
              value={newProtocol.tags}
              onChange={(e) => setNewProtocol({ ...newProtocol, tags: e.target.value })}
              data-testid="protocol-tags-input"
            />
            
            <button 
              className="btn btn-primary"
              onClick={handleListProtocol}
              style={{ marginTop: 10 }}
              data-testid="list-protocol-btn"
            >
              List Protocol for Sale
            </button>
          </div>
        </div>
      )}

      {/* Purchases Tab */}
      {activeTab === 'purchases' && (
        <div>
          {purchases.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>You haven't purchased any protocols yet.</p>
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
              <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Total Earnings</p>
              <p style={{ color: '#10b981', fontSize: '2rem', fontWeight: 700 }}>${(dashboard.total_earnings || 0).toFixed(2)}</p>
            </div>
            <div style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(124, 58, 237, 0.1))',
              borderRadius: 12, padding: 20, textAlign: 'center'
            }}>
              <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Total Sales</p>
              <p style={{ color: '#a78bfa', fontSize: '2rem', fontWeight: 700 }}>{dashboard.total_sales || 0}</p>
            </div>
            <div style={{
              background: 'linear-gradient(135deg, rgba(244, 114, 182, 0.2), rgba(244, 114, 182, 0.1))',
              borderRadius: 12, padding: 20, textAlign: 'center'
            }}>
              <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Listed Protocols</p>
              <p style={{ color: '#f472b6', fontSize: '2rem', fontWeight: 700 }}>{dashboard.listed_protocols || 0}</p>
            </div>
          </div>
          
          {dashboard.recent_sales?.length > 0 && (
            <div>
              <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Recent Sales</h3>
              {dashboard.recent_sales.map((sale, i) => (
                <div key={i} style={{
                  background: 'rgba(30, 20, 50, 0.5)',
                  borderRadius: 8, padding: 15, marginBottom: 10,
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                }}>
                  <div>
                    <p style={{ color: '#fff' }}>{sale.protocol_name}</p>
                    <p style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                      {new Date(sale.sold_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span style={{ color: '#10b981', fontWeight: 700 }}>+${sale.your_earnings.toFixed(2)}</span>
                </div>
              ))}
            </div>
          )}
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
                <li style={{ marginBottom: 10 }}>Complete payment in the PayPal window</li>
                <li style={{ marginBottom: 10 }}>Copy your Transaction ID from PayPal receipt</li>
                <li>Click "Confirm Purchase" below</li>
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

      {/* CSS for pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.2); }
        }
      `}</style>
    </div>
  );
};

export default MarketplacePage;
