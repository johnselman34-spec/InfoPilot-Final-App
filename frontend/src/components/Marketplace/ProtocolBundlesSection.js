/**
 * Protocol Bundles UI Component
 * Allows users to view, create, and purchase protocol bundles at discounted prices
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

// Bundle Card Component
const BundleCard = ({ bundle, onPurchase, showToast }) => {
  const { token } = useAuth();
  const [purchasing, setPurchasing] = useState(false);

  const handlePurchase = async () => {
    if (!token) {
      showToast('Please login to purchase bundles', 'error');
      return;
    }
    setPurchasing(true);
    try {
      await onPurchase(bundle);
    } finally {
      setPurchasing(false);
    }
  };

  return (
    <div 
      style={{
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%)',
        borderRadius: 16,
        padding: 20,
        border: '2px solid rgba(124, 58, 237, 0.4)',
        position: 'relative',
        overflow: 'hidden'
      }}
      data-testid={`bundle-card-${bundle.id}`}
    >
      {/* Discount Badge */}
      <div style={{
        position: 'absolute',
        top: 10,
        right: 10,
        background: 'linear-gradient(135deg, #f472b6 0%, #ec4899 100%)',
        color: '#fff',
        padding: '6px 14px',
        borderRadius: 20,
        fontSize: '0.85rem',
        fontWeight: 700,
        boxShadow: '0 4px 15px rgba(236, 72, 153, 0.4)'
      }}>
        {bundle.discount_percent}% OFF
      </div>

      <h3 style={{ color: '#f472b6', marginBottom: 10, marginTop: 0 }}>
        📦 {bundle.name}
      </h3>
      
      <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 15 }}>
        {bundle.description}
      </p>

      {/* Protocols in bundle */}
      <div style={{ marginBottom: 15 }}>
        <p style={{ color: '#c4b5fd', fontSize: '0.8rem', marginBottom: 8 }}>
          {bundle.protocol_count} Protocols Included:
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {bundle.protocols?.slice(0, 5).map((p, i) => (
            <span 
              key={i}
              style={{
                background: 'rgba(124, 58, 237, 0.3)',
                color: '#a78bfa',
                padding: '4px 10px',
                borderRadius: 15,
                fontSize: '0.75rem'
              }}
            >
              {p.name}
            </span>
          ))}
          {bundle.protocols?.length > 5 && (
            <span style={{
              background: 'rgba(16, 185, 129, 0.3)',
              color: '#10b981',
              padding: '4px 10px',
              borderRadius: 15,
              fontSize: '0.75rem'
            }}>
              +{bundle.protocols.length - 5} more
            </span>
          )}
        </div>
      </div>

      {/* Pricing */}
      <div style={{
        background: 'rgba(0, 0, 0, 0.3)',
        borderRadius: 12,
        padding: 15,
        marginBottom: 15
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <span style={{ color: '#71717a', textDecoration: 'line-through' }}>
            Original: ${bundle.original_price?.toFixed(2)}
          </span>
          <span style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 700 }}>
            ${bundle.bundle_price?.toFixed(2)}
          </span>
        </div>
        <div style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%)',
          borderRadius: 8,
          padding: '8px 12px',
          textAlign: 'center'
        }}>
          <span style={{ color: '#10b981', fontWeight: 600 }}>
            💰 You save ${bundle.savings?.toFixed(2)}!
          </span>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 15, fontSize: '0.85rem' }}>
        <span style={{ color: '#a1a1aa' }}>
          📊 {bundle.total_sales || 0} sold
        </span>
        <span style={{ color: '#a1a1aa' }}>
          📁 {bundle.category}
        </span>
      </div>

      {/* Purchase Button */}
      <button
        onClick={handlePurchase}
        disabled={purchasing}
        className="btn btn-primary"
        style={{
          width: '100%',
          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          border: 'none',
          padding: '12px 20px',
          fontSize: '1rem',
          fontWeight: 600,
          cursor: purchasing ? 'wait' : 'pointer',
          opacity: purchasing ? 0.7 : 1
        }}
        data-testid={`buy-bundle-${bundle.id}`}
      >
        {purchasing ? '⏳ Processing...' : '🛒 Buy Bundle'}
      </button>
    </div>
  );
};

// Create Bundle Form Component
const CreateBundleForm = ({ userProtocols, onCreateBundle, showToast }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedProtocols, setSelectedProtocols] = useState([]);
  const [discountPercent, setDiscountPercent] = useState(15);
  const [category, setCategory] = useState('General');
  const [creating, setCreating] = useState(false);

  const categories = ['General', 'Technology', 'Business & Finance', 'Science & Research', 'Education', 'Entertainment'];

  const calculateTotal = () => {
    const selected = userProtocols.filter(p => selectedProtocols.includes(p.id));
    const original = selected.reduce((sum, p) => sum + (p.price || 0), 0);
    const discounted = original * (1 - discountPercent / 100);
    return { original, discounted, savings: original - discounted };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedProtocols.length < 2) {
      showToast('Select at least 2 protocols for a bundle', 'error');
      return;
    }
    if (!name.trim()) {
      showToast('Please enter a bundle name', 'error');
      return;
    }

    setCreating(true);
    try {
      await onCreateBundle({
        name,
        description,
        protocol_ids: selectedProtocols,
        discount_percent: discountPercent,
        category
      });
      setName('');
      setDescription('');
      setSelectedProtocols([]);
      setDiscountPercent(15);
    } finally {
      setCreating(false);
    }
  };

  const toggleProtocol = (id) => {
    setSelectedProtocols(prev => 
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

  const totals = calculateTotal();

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 600 }}>
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))',
        padding: 20,
        borderRadius: 12,
        marginBottom: 20,
        border: '1px solid rgba(16, 185, 129, 0.3)'
      }}>
        <h3 style={{ color: '#10b981', marginBottom: 10, marginTop: 0 }}>📦 Create a Protocol Bundle</h3>
        <p style={{ color: '#a1a1aa', fontSize: '0.9rem', margin: 0 }}>
          Bundle multiple protocols together and offer them at a discount! 
          Attract more buyers with package deals.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        <input
          className="input"
          placeholder="Bundle Name * (e.g., 'Ultimate Research Pack')"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          data-testid="bundle-name-input"
        />
        
        <textarea
          className="input"
          placeholder="Description - Tell buyers why this bundle is amazing! *"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />

        {/* Protocol Selection */}
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 8, display: 'block' }}>
            Select Protocols for Bundle (minimum 2):
          </label>
          <div style={{
            maxHeight: 200,
            overflowY: 'auto',
            background: 'rgba(30, 20, 50, 0.5)',
            borderRadius: 8,
            padding: 10
          }}>
            {userProtocols.length === 0 ? (
              <p style={{ color: '#71717a', textAlign: 'center', margin: 10 }}>
                You have not created any protocols yet. Create some first!
              </p>
            ) : (
              userProtocols.map(protocol => (
                <div
                  key={protocol.id}
                  onClick={() => toggleProtocol(protocol.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '10px 12px',
                    background: selectedProtocols.includes(protocol.id) ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
                    borderRadius: 8,
                    cursor: 'pointer',
                    marginBottom: 5,
                    border: selectedProtocols.includes(protocol.id) ? '1px solid rgba(16, 185, 129, 0.5)' : '1px solid transparent'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedProtocols.includes(protocol.id)}
                    onChange={() => {}}
                    style={{ accentColor: '#10b981' }}
                  />
                  <span style={{ color: '#e2e8f0', flex: 1 }}>{protocol.name}</span>
                  <span style={{ color: '#10b981', fontWeight: 600 }}>
                    ${protocol.price?.toFixed(2) || '0.00'}
                  </span>
                </div>
              ))
            )}
          </div>
          <p style={{ color: '#71717a', fontSize: '0.8rem', marginTop: 5 }}>
            Selected: {selectedProtocols.length} protocols
          </p>
        </div>

        <div style={{ display: 'flex', gap: 15 }}>
          <div style={{ flex: 1 }}>
            <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Discount (%)</label>
            <input
              className="input"
              type="number"
              min="5"
              max="50"
              value={discountPercent}
              onChange={(e) => setDiscountPercent(Math.max(5, Math.min(50, parseInt(e.target.value) || 15)))}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Category</label>
            <select
              className="input"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Price Preview */}
        {selectedProtocols.length >= 2 && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.1))',
            padding: 15,
            borderRadius: 10,
            border: '1px solid rgba(251, 191, 36, 0.3)'
          }}>
            <h4 style={{ color: '#fbbf24', marginBottom: 10, marginTop: 0 }}>💰 Bundle Preview</h4>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
              <span style={{ color: '#a1a1aa' }}>Original Total:</span>
              <span style={{ color: '#71717a', textDecoration: 'line-through' }}>${totals.original.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
              <span style={{ color: '#a1a1aa' }}>Bundle Price ({discountPercent}% off):</span>
              <span style={{ color: '#10b981', fontWeight: 700 }}>${totals.discounted.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#a1a1aa' }}>Buyers Save:</span>
              <span style={{ color: '#f472b6', fontWeight: 600 }}>${totals.savings.toFixed(2)}</span>
            </div>
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={creating || selectedProtocols.length < 2}
          style={{
            marginTop: 10,
            fontSize: '1.1rem',
            padding: 15,
            opacity: (creating || selectedProtocols.length < 2) ? 0.6 : 1
          }}
          data-testid="create-bundle-btn"
        >
          {creating ? '⏳ Creating...' : '🚀 Create Bundle'}
        </button>
      </div>
    </form>
  );
};

// Main Bundles Section Component
const ProtocolBundlesSection = ({ showToast }) => {
  const { token, user } = useAuth();
  const [bundles, setBundles] = useState([]);
  const [userProtocols, setUserProtocols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('browse'); // 'browse' or 'create'
  const [sortBy, setSortBy] = useState('popular');

  const fetchBundles = useCallback(async () => {
    try {
      const res = await fetch(`${API}/bundles?sort=${sortBy}`);
      if (res.ok) {
        const data = await res.json();
        setBundles(data.bundles || []);
      }
    } catch (error) {
      console.error('Failed to fetch bundles:', error);
    }
    setLoading(false);
  }, [sortBy]);

  const fetchUserProtocols = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/marketplace/seller/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUserProtocols(data.listings || []);
      }
    } catch (error) {
      console.error('Failed to fetch user protocols:', error);
    }
  }, [token]);

  useEffect(() => {
    fetchBundles();
  }, [fetchBundles]);

  useEffect(() => {
    if (token && activeView === 'create') {
      fetchUserProtocols();
    }
  }, [token, activeView, fetchUserProtocols]);

  const handleCreateBundle = async (bundleData) => {
    try {
      const res = await fetch(`${API}/bundles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(bundleData)
      });
      
      if (res.ok) {
        showToast('🎉 Bundle created successfully!', 'success');
        fetchBundles();
        setActiveView('browse');
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to create bundle', 'error');
      }
    } catch (error) {
      showToast('Failed to create bundle', 'error');
    }
  };

  const handlePurchaseBundle = async (bundle) => {
    try {
      const res = await fetch(`${API}/bundles/purchase`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ bundle_id: bundle.id })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        if (data.payment_url) {
          window.open(data.payment_url, '_blank', 'width=600,height=700');
          showToast('Complete your PayPal payment to receive the protocols!', 'info');
        } else {
          showToast('🎉 Bundle purchased successfully!', 'success');
        }
      } else {
        showToast(data.detail || 'Failed to purchase bundle', 'error');
      }
    } catch (error) {
      showToast('Failed to purchase bundle', 'error');
    }
  };

  return (
    <div data-testid="protocol-bundles-section">
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(236, 72, 153, 0.2))',
        borderRadius: 16,
        padding: 20,
        marginBottom: 20,
        border: '1px solid rgba(124, 58, 237, 0.3)'
      }}>
        <h2 style={{ color: '#f472b6', marginBottom: 10, marginTop: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          📦 Protocol Bundles
          <span style={{
            background: 'linear-gradient(135deg, #10b981, #059669)',
            color: '#fff',
            padding: '4px 12px',
            borderRadius: 20,
            fontSize: '0.75rem',
            fontWeight: 700
          }}>
            SAVE MORE!
          </span>
        </h2>
        <p style={{ color: '#a1a1aa', margin: 0 }}>
          Get more for less! Bundle deals offer multiple protocols at a discounted price.
        </p>
      </div>

      {/* View Toggle */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        <button
          className={`btn ${activeView === 'browse' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveView('browse')}
          data-testid="bundles-browse-tab"
        >
          🔍 Browse Bundles
        </button>
        {token && (
          <button
            className={`btn ${activeView === 'create' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveView('create')}
            data-testid="bundles-create-tab"
          >
            ➕ Create Bundle
          </button>
        )}
      </div>

      {/* Browse View */}
      {activeView === 'browse' && (
        <div>
          {/* Sort Controls */}
          <div style={{ marginBottom: 20, display: 'flex', gap: 10, alignItems: 'center' }}>
            <span style={{ color: '#a1a1aa' }}>Sort by:</span>
            <select
              className="input"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{ maxWidth: 180 }}
            >
              <option value="popular">Most Popular</option>
              <option value="newest">Newest</option>
              <option value="discount">Highest Discount</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
            </select>
          </div>

          {/* Bundles Grid */}
          {loading ? (
            <p style={{ textAlign: 'center', color: '#a1a1aa' }}>Loading bundles...</p>
          ) : bundles.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: 40,
              background: 'rgba(30, 20, 50, 0.5)',
              borderRadius: 12
            }}>
              <div style={{ fontSize: '3rem', marginBottom: 15 }}>📦</div>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>No bundles available yet.</p>
              {token && (
                <button
                  className="btn btn-primary"
                  onClick={() => setActiveView('create')}
                >
                  Create the First Bundle!
                </button>
              )}
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: 20
            }}>
              {bundles.map(bundle => (
                <BundleCard
                  key={bundle.id}
                  bundle={bundle}
                  onPurchase={handlePurchaseBundle}
                  showToast={showToast}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create View */}
      {activeView === 'create' && token && (
        <CreateBundleForm
          userProtocols={userProtocols}
          onCreateBundle={handleCreateBundle}
          showToast={showToast}
        />
      )}

      {/* Not logged in for create */}
      {activeView === 'create' && !token && (
        <div style={{
          textAlign: 'center',
          padding: 40,
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12
        }}>
          <p style={{ color: '#a1a1aa' }}>Please login to create bundles.</p>
        </div>
      )}
    </div>
  );
};

export default ProtocolBundlesSection;
