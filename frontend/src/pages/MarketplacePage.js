import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons } from '../components/shared';

const MarketplacePage = ({ showToast }) => {
  const { token } = useAuth();
  const [protocols, setProtocols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('browse'); // browse, sell, purchases, dashboard
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [sortBy, setSortBy] = useState('popular');
  
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
      // Initiate purchase on backend
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
        // Open PayPal payment in new window
        window.open(data.payment_url, '_blank', 'width=600,height=700');
        
        // Show confirmation modal with pending info
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
    
    // Prompt for transaction ID
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
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Shop />
          Protocol Marketplace
        </h2>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
          Buy and sell search protocols • 90% to creators
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

      {/* Browse Tab */}
      {activeTab === 'browse' && (
        <div>
          {/* Filters */}
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

          {/* Protocol Grid */}
          {loading ? (
            <p style={{ textAlign: 'center', color: '#a1a1aa' }}>Loading protocols...</p>
          ) : protocols.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>No protocols listed yet. Be the first to sell!</p>
              <button className="btn btn-primary" onClick={() => setActiveTab('sell')}>
                List Your Protocol
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
              {protocols.map(protocol => (
                <div 
                  key={protocol.id}
                  style={{
                    background: 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 12,
                    padding: 20,
                    border: protocol.is_featured ? '2px solid #f472b6' : '1px solid rgba(124, 58, 237, 0.3)',
                    position: 'relative'
                  }}
                  data-testid={`protocol-card-${protocol.id}`}
                >
                  {protocol.is_featured && (
                    <span style={{
                      position: 'absolute', top: -10, right: 10,
                      background: '#f472b6', color: '#fff', padding: '4px 10px',
                      borderRadius: 20, fontSize: '0.7rem', fontWeight: 700
                    }}>
                      FEATURED
                    </span>
                  )}
                  
                  <h3 style={{ color: '#f472b6', marginBottom: 8 }}>{protocol.name}</h3>
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
                        onClick={() => handlePurchase(protocol)}
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
              ))}
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
                  <option>Health & Medical</option>
                  <option>Education</option>
                  <option>Entertainment</option>
                </select>
              </div>
            </div>
            <input
              className="input"
              placeholder="Tags (comma separated)"
              value={newProtocol.tags}
              onChange={(e) => setNewProtocol({ ...newProtocol, tags: e.target.value })}
              data-testid="protocol-tags-input"
            />
            <button className="btn btn-primary" onClick={handleListProtocol} data-testid="list-protocol-btn">
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
                Browse Marketplace
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              {purchases.map(purchase => (
                <div 
                  key={purchase.id}
                  style={{
                    background: 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 12,
                    padding: 20,
                    border: '1px solid rgba(16, 185, 129, 0.3)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div>
                      <h3 style={{ color: '#f472b6', marginBottom: 5 }}>{purchase.name}</h3>
                      <span style={{ color: '#71717a', fontSize: '0.8rem' }}>{purchase.category}</span>
                    </div>
                    <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                      Purchased: {new Date(purchase.purchased_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div style={{ 
                    marginTop: 15, padding: 15, 
                    background: 'rgba(16, 185, 129, 0.1)', 
                    borderRadius: 8,
                    fontFamily: 'monospace',
                    color: '#10b981'
                  }}>
                    {purchase.protocol}
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
          {dashboard && (
            <>
              {/* Stats Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 15, marginBottom: 25 }}>
                <div style={{ background: 'rgba(124, 58, 237, 0.2)', padding: 20, borderRadius: 12, textAlign: 'center' }}>
                  <div style={{ color: '#a78bfa', fontSize: '2rem', fontWeight: 700 }}>{dashboard.total_listings}</div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Listings</div>
                </div>
                <div style={{ background: 'rgba(236, 72, 153, 0.2)', padding: 20, borderRadius: 12, textAlign: 'center' }}>
                  <div style={{ color: '#f472b6', fontSize: '2rem', fontWeight: 700 }}>{dashboard.total_sales}</div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Total Sales</div>
                </div>
                <div style={{ background: 'rgba(16, 185, 129, 0.2)', padding: 20, borderRadius: 12, textAlign: 'center' }}>
                  <div style={{ color: '#10b981', fontSize: '2rem', fontWeight: 700 }}>${dashboard.total_earnings?.toFixed(2) || '0.00'}</div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Your Earnings (90%)</div>
                </div>
              </div>

              {/* Listings */}
              <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Your Listings</h3>
              {dashboard.listings?.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 30, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
                  <p style={{ color: '#a1a1aa', marginBottom: 15 }}>You haven't listed any protocols yet.</p>
                  <button className="btn btn-primary" onClick={() => setActiveTab('sell')}>
                    Create Your First Listing
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {dashboard.listings?.map(listing => (
                    <div 
                      key={listing.id}
                      style={{
                        background: 'rgba(30, 20, 50, 0.5)',
                        borderRadius: 10,
                        padding: 15,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <h4 style={{ color: '#fff', marginBottom: 5 }}>{listing.name}</h4>
                        <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                          ${listing.price.toFixed(2)} • {listing.sales} sales • ${listing.earnings?.toFixed(2) || '0.00'} earned
                        </span>
                      </div>
                      <span style={{ 
                        color: listing.status === 'active' ? '#10b981' : '#f59e0b',
                        fontSize: '0.8rem',
                        textTransform: 'uppercase'
                      }}>
                        {listing.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Purchase Confirmation Modal */}
      {purchaseModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
            borderRadius: 20, padding: 30, maxWidth: 450, width: '90%',
            border: '2px solid rgba(124, 58, 237, 0.5)'
          }}>
            <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Confirm Purchase</h3>
            <p style={{ color: '#fff', marginBottom: 10 }}>
              <strong>{purchaseModal.protocol.name}</strong>
            </p>
            <p style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700, marginBottom: 20 }}>
              ${purchaseModal.protocol.price.toFixed(2)}
            </p>
            
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 20 }}>
              Please complete your PayPal payment, then click "Confirm Purchase" below.
            </p>
            
            <div style={{ display: 'flex', gap: 10 }}>
              <button 
                className="btn btn-secondary" 
                onClick={() => setPurchaseModal(null)}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                onClick={confirmPurchase}
                style={{ flex: 1 }}
                data-testid="confirm-purchase-btn"
              >
                Confirm Purchase
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketplacePage;
