/**
 * Price Controls Admin Panel
 * UI for managing global and unpaid user price controls
 */
import React, { useState, useEffect, useCallback } from 'react';
import { API } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';

const PriceControlsAdmin = ({ showToast }) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Global Price Controls
  const [globalControls, setGlobalControls] = useState({
    global_price_control_enabled: false,
    global_max_protocol_price: 99.99,
    global_max_bundle_price: 199.99,
    global_min_protocol_price: 0.00
  });
  
  // Unpaid User Price Controls
  const [unpaidControls, setUnpaidControls] = useState({
    unpaid_price_control_enabled: false,
    unpaid_max_protocol_price: 5.00,
    unpaid_max_bundle_price: 10.00,
    unpaid_can_sell: true
  });
  
  const fetchControls = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    
    try {
      // Fetch global controls
      const globalRes = await fetch(`${API}/admin/global-price-controls`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (globalRes.ok) {
        const data = await globalRes.json();
        setGlobalControls(data.settings);
      }
      
      // Fetch unpaid controls
      const unpaidRes = await fetch(`${API}/admin/unpaid-price-controls`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (unpaidRes.ok) {
        const data = await unpaidRes.json();
        setUnpaidControls(data.settings);
      }
    } catch (err) {
      console.error('Failed to fetch price controls:', err);
      showToast?.('Failed to load price controls', 'error');
    }
    
    setLoading(false);
  }, [token, showToast]);
  
  useEffect(() => {
    fetchControls();
  }, [fetchControls]);
  
  const saveGlobalControls = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API}/admin/global-price-controls`, {
        method: 'PUT',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(globalControls)
      });
      
      if (res.ok) {
        showToast?.('Global price controls saved!', 'success');
      } else {
        const data = await res.json();
        showToast?.(data.detail || 'Failed to save', 'error');
      }
    } catch (err) {
      showToast?.('Failed to save global controls', 'error');
    }
    setSaving(false);
  };
  
  const saveUnpaidControls = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API}/admin/unpaid-price-controls`, {
        method: 'PUT',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(unpaidControls)
      });
      
      if (res.ok) {
        showToast?.('Unpaid user price controls saved!', 'success');
      } else {
        const data = await res.json();
        showToast?.(data.detail || 'Failed to save', 'error');
      }
    } catch (err) {
      showToast?.('Failed to save unpaid controls', 'error');
    }
    setSaving(false);
  };
  
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <div style={{ fontSize: '2rem', marginBottom: 10 }}>⏳</div>
        <p style={{ color: '#a1a1aa' }}>Loading price controls...</p>
      </div>
    );
  }
  
  return (
    <div data-testid="price-controls-admin">
      {/* Global Price Controls Section */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1))',
        borderRadius: 15,
        padding: 25,
        marginBottom: 25,
        border: '1px solid rgba(59, 130, 246, 0.3)'
      }}>
        <h3 style={{ color: '#60a5fa', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
          🌍 Global Price Controls
          <span style={{ fontSize: '0.75rem', color: '#a1a1aa', fontWeight: 400 }}>
            (Applies to ALL users)
          </span>
        </h3>
        
        {/* Master Toggle */}
        <div style={{ 
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: 15, marginBottom: 20
        }}>
          <div>
            <span style={{ color: '#fff', fontWeight: 600 }}>Enable Global Price Controls</span>
            <p style={{ color: '#71717a', fontSize: '0.8rem', margin: '5px 0 0 0' }}>
              When enabled, all users must follow these price limits
            </p>
          </div>
          <label style={{ cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={globalControls.global_price_control_enabled}
              onChange={(e) => setGlobalControls({
                ...globalControls,
                global_price_control_enabled: e.target.checked
              })}
              style={{ width: 20, height: 20, accentColor: '#3b82f6' }}
            />
          </label>
        </div>
        
        {/* Price Settings */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15 }}>
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
              Max Protocol Price ($)
            </label>
            <input
              type="number"
              min="0"
              max="999.99"
              step="0.01"
              value={globalControls.global_max_protocol_price}
              onChange={(e) => setGlobalControls({
                ...globalControls,
                global_max_protocol_price: parseFloat(e.target.value) || 0
              })}
              className="input"
              disabled={!globalControls.global_price_control_enabled}
              style={{ opacity: globalControls.global_price_control_enabled ? 1 : 0.5 }}
            />
          </div>
          
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
              Max Bundle Price ($)
            </label>
            <input
              type="number"
              min="0"
              max="999.99"
              step="0.01"
              value={globalControls.global_max_bundle_price}
              onChange={(e) => setGlobalControls({
                ...globalControls,
                global_max_bundle_price: parseFloat(e.target.value) || 0
              })}
              className="input"
              disabled={!globalControls.global_price_control_enabled}
              style={{ opacity: globalControls.global_price_control_enabled ? 1 : 0.5 }}
            />
          </div>
          
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
              Min Protocol Price ($)
            </label>
            <input
              type="number"
              min="0"
              max="999.99"
              step="0.01"
              value={globalControls.global_min_protocol_price}
              onChange={(e) => setGlobalControls({
                ...globalControls,
                global_min_protocol_price: parseFloat(e.target.value) || 0
              })}
              className="input"
              disabled={!globalControls.global_price_control_enabled}
              style={{ opacity: globalControls.global_price_control_enabled ? 1 : 0.5 }}
            />
            <p style={{ color: '#71717a', fontSize: '0.7rem', margin: '5px 0 0 0' }}>
              Set to 0 to allow FREE protocols
            </p>
          </div>
        </div>
        
        <button 
          className="btn btn-primary" 
          onClick={saveGlobalControls}
          disabled={saving}
          style={{ marginTop: 20 }}
        >
          {saving ? '⏳ Saving...' : '💾 Save Global Controls'}
        </button>
      </div>
      
      {/* Unpaid User Price Controls Section */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(239, 68, 68, 0.1))',
        borderRadius: 15,
        padding: 25,
        border: '1px solid rgba(251, 191, 36, 0.3)'
      }}>
        <h3 style={{ color: '#fbbf24', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
          👤 Unpaid User Price Controls
          <span style={{ fontSize: '0.75rem', color: '#a1a1aa', fontWeight: 400 }}>
            (OFF by default)
          </span>
        </h3>
        
        {/* Master Toggle */}
        <div style={{ 
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: 15, marginBottom: 20
        }}>
          <div>
            <span style={{ color: '#fff', fontWeight: 600 }}>Enable Unpaid User Restrictions</span>
            <p style={{ color: '#71717a', fontSize: '0.8rem', margin: '5px 0 0 0' }}>
              Limit what unpaid users can charge for protocols
            </p>
          </div>
          <label style={{ cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={unpaidControls.unpaid_price_control_enabled}
              onChange={(e) => setUnpaidControls({
                ...unpaidControls,
                unpaid_price_control_enabled: e.target.checked
              })}
              style={{ width: 20, height: 20, accentColor: '#f59e0b' }}
            />
          </label>
        </div>
        
        {/* Can Sell Toggle */}
        <div style={{ 
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: 15, marginBottom: 20
        }}>
          <div>
            <span style={{ color: '#fff', fontWeight: 600 }}>Allow Unpaid Users to Sell</span>
            <p style={{ color: '#71717a', fontSize: '0.8rem', margin: '5px 0 0 0' }}>
              If disabled, unpaid users cannot list protocols for sale
            </p>
          </div>
          <label style={{ cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={unpaidControls.unpaid_can_sell}
              onChange={(e) => setUnpaidControls({
                ...unpaidControls,
                unpaid_can_sell: e.target.checked
              })}
              disabled={!unpaidControls.unpaid_price_control_enabled}
              style={{ 
                width: 20, height: 20, accentColor: '#10b981',
                opacity: unpaidControls.unpaid_price_control_enabled ? 1 : 0.5
              }}
            />
          </label>
        </div>
        
        {/* Price Settings */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15 }}>
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
              Max Protocol Price ($)
            </label>
            <input
              type="number"
              min="0"
              max="99.99"
              step="0.01"
              value={unpaidControls.unpaid_max_protocol_price}
              onChange={(e) => setUnpaidControls({
                ...unpaidControls,
                unpaid_max_protocol_price: parseFloat(e.target.value) || 0
              })}
              className="input"
              disabled={!unpaidControls.unpaid_price_control_enabled}
              style={{ opacity: unpaidControls.unpaid_price_control_enabled ? 1 : 0.5 }}
            />
          </div>
          
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
              Max Bundle Price ($)
            </label>
            <input
              type="number"
              min="0"
              max="99.99"
              step="0.01"
              value={unpaidControls.unpaid_max_bundle_price}
              onChange={(e) => setUnpaidControls({
                ...unpaidControls,
                unpaid_max_bundle_price: parseFloat(e.target.value) || 0
              })}
              className="input"
              disabled={!unpaidControls.unpaid_price_control_enabled}
              style={{ opacity: unpaidControls.unpaid_price_control_enabled ? 1 : 0.5 }}
            />
          </div>
        </div>
        
        <button 
          className="btn btn-primary" 
          onClick={saveUnpaidControls}
          disabled={saving}
          style={{ marginTop: 20, background: 'linear-gradient(135deg, #f59e0b, #d97706)' }}
        >
          {saving ? '⏳ Saving...' : '💾 Save Unpaid User Controls'}
        </button>
      </div>
    </div>
  );
};

export default PriceControlsAdmin;
