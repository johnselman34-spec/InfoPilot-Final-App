import React, { useState, useEffect, useCallback } from 'react';
import { API } from '../../utils/api';

/**
 * UnpaidPriceControlsAdmin - Admin control panel for unpaid user price limits
 * Feature is OFF by default - must be enabled by admin
 */
const UnpaidPriceControlsAdmin = ({ token, showToast }) => {
  const [settings, setSettings] = useState({
    unpaid_price_control_enabled: false,
    unpaid_max_protocol_price: 5.00,
    unpaid_max_bundle_price: 10.00,
    unpaid_can_sell: true
  });
  const [stats, setStats] = useState({ unpaid_sellers: 0 });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch(`${API}/admin/unpaid-price-controls`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSettings(data.settings || {});
        setStats(data.stats || {});
      }
    } catch (e) {
      console.error('Failed to fetch price controls:', e);
    }
    setLoading(false);
  }, [token]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const saveSettings = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API}/admin/unpaid-price-controls`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(settings)
      });

      if (res.ok) {
        showToast('Price controls updated!', 'success');
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to update', 'error');
      }
    } catch (e) {
      showToast('Failed to save settings', 'error');
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <div style={{ fontSize: '2rem', marginBottom: 15 }}>💰</div>
        Loading price controls...
      </div>
    );
  }

  return (
    <div>
      <h3 style={{ color: '#f472b6', marginBottom: 20 }}>💰 Unpaid User Price Controls</h3>
      
      <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
        Control the maximum prices that unpaid (free) users can charge for protocols and bundles.
        This feature is <strong style={{ color: settings.unpaid_price_control_enabled ? '#10b981' : '#ef4444' }}>
          {settings.unpaid_price_control_enabled ? 'ENABLED' : 'DISABLED'}
        </strong> by default.
      </p>

      {/* Stats */}
      <div style={{
        padding: 15,
        background: 'rgba(124, 58, 237, 0.1)',
        borderRadius: 10,
        border: '1px solid rgba(124, 58, 237, 0.3)',
        marginBottom: 20
      }}>
        <div style={{ display: 'flex', gap: 30 }}>
          <div>
            <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Unpaid Users Selling:</span>
            <span style={{ color: '#f472b6', fontWeight: 600, marginLeft: 10 }}>{stats.unpaid_sellers}</span>
          </div>
        </div>
      </div>

      {/* Master Toggle */}
      <div style={{
        padding: 20,
        background: settings.unpaid_price_control_enabled 
          ? 'rgba(16, 185, 129, 0.1)' 
          : 'rgba(239, 68, 68, 0.1)',
        borderRadius: 12,
        border: settings.unpaid_price_control_enabled 
          ? '2px solid rgba(16, 185, 129, 0.5)' 
          : '2px solid rgba(239, 68, 68, 0.5)',
        marginBottom: 20
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h4 style={{ 
              color: settings.unpaid_price_control_enabled ? '#10b981' : '#ef4444', 
              margin: '0 0 5px 0' 
            }}>
              {settings.unpaid_price_control_enabled ? '✅ Price Controls ENABLED' : '❌ Price Controls DISABLED'}
            </h4>
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: 0 }}>
              {settings.unpaid_price_control_enabled 
                ? 'Unpaid users are limited to the prices set below.'
                : 'Unpaid users can charge any price up to $99.99 (same as paid users).'}
            </p>
          </div>
          <button
            onClick={() => setSettings(prev => ({
              ...prev, 
              unpaid_price_control_enabled: !prev.unpaid_price_control_enabled
            }))}
            style={{
              padding: '12px 24px',
              borderRadius: 8,
              border: 'none',
              background: settings.unpaid_price_control_enabled 
                ? 'linear-gradient(135deg, #ef4444, #dc2626)' 
                : 'linear-gradient(135deg, #10b981, #059669)',
              color: '#fff',
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: '0.95rem'
            }}
          >
            {settings.unpaid_price_control_enabled ? 'Disable Controls' : 'Enable Controls'}
          </button>
        </div>
      </div>

      {/* Settings (only shown when enabled) */}
      {settings.unpaid_price_control_enabled && (
        <div style={{
          padding: 20,
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          border: '1px solid rgba(124, 58, 237, 0.3)',
          marginBottom: 20
        }}>
          <h4 style={{ color: '#a78bfa', margin: '0 0 20px 0' }}>⚙️ Price Limit Settings</h4>

          {/* Can Sell Toggle */}
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={settings.unpaid_can_sell}
                onChange={(e) => setSettings(prev => ({ ...prev, unpaid_can_sell: e.target.checked }))}
                style={{ width: 20, height: 20, accentColor: '#10b981' }}
              />
              <div>
                <span style={{ color: '#e2e8f0', fontWeight: 500 }}>
                  Allow unpaid users to sell
                </span>
                <p style={{ color: '#a1a1aa', fontSize: '0.8rem', margin: '4px 0 0 0' }}>
                  If disabled, unpaid users cannot list any protocols for sale.
                </p>
              </div>
            </label>
          </div>

          {settings.unpaid_can_sell && (
            <>
              {/* Max Protocol Price */}
              <div style={{ marginBottom: 20 }}>
                <label style={{ color: '#f472b6', fontWeight: 500, display: 'block', marginBottom: 8 }}>
                  Max Price per Protocol ($)
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <input
                    type="number"
                    value={settings.unpaid_max_protocol_price}
                    onChange={(e) => setSettings(prev => ({ 
                      ...prev, 
                      unpaid_max_protocol_price: parseFloat(e.target.value) || 0 
                    }))}
                    min="0"
                    max="99.99"
                    step="0.01"
                    style={{
                      padding: '10px 15px',
                      borderRadius: 8,
                      border: '1px solid rgba(124, 58, 237, 0.3)',
                      background: 'rgba(30, 20, 50, 0.5)',
                      color: '#fff',
                      width: 150,
                      fontSize: '1.1rem'
                    }}
                  />
                  <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                    (Paid users: up to $99.99)
                  </span>
                </div>
                <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 5 }}>
                  Unpaid users cannot charge more than this for a single protocol.
                </p>
              </div>

              {/* Max Bundle Price */}
              <div style={{ marginBottom: 20 }}>
                <label style={{ color: '#f472b6', fontWeight: 500, display: 'block', marginBottom: 8 }}>
                  Max Price per Bundle ($)
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <input
                    type="number"
                    value={settings.unpaid_max_bundle_price}
                    onChange={(e) => setSettings(prev => ({ 
                      ...prev, 
                      unpaid_max_bundle_price: parseFloat(e.target.value) || 0 
                    }))}
                    min="0"
                    max="99.99"
                    step="0.01"
                    style={{
                      padding: '10px 15px',
                      borderRadius: 8,
                      border: '1px solid rgba(124, 58, 237, 0.3)',
                      background: 'rgba(30, 20, 50, 0.5)',
                      color: '#fff',
                      width: 150,
                      fontSize: '1.1rem'
                    }}
                  />
                  <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                    (Paid users: up to $99.99)
                  </span>
                </div>
                <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 5 }}>
                  Unpaid users cannot charge more than this for a bundle of protocols.
                </p>
              </div>
            </>
          )}

          {/* Save Button */}
          <button
            onClick={saveSettings}
            disabled={saving}
            style={{
              width: '100%',
              padding: '14px 24px',
              borderRadius: 10,
              border: 'none',
              background: 'linear-gradient(135deg, #7c3aed, #a78bfa)',
              color: '#fff',
              fontWeight: 600,
              cursor: saving ? 'wait' : 'pointer',
              fontSize: '1rem',
              opacity: saving ? 0.7 : 1
            }}
          >
            {saving ? 'Saving...' : '💾 Save Price Controls'}
          </button>
        </div>
      )}

      {/* Info Box */}
      <div style={{
        padding: 15,
        background: 'rgba(59, 130, 246, 0.1)',
        borderRadius: 10,
        border: '1px solid rgba(59, 130, 246, 0.3)'
      }}>
        <p style={{ color: '#3b82f6', fontSize: '0.85rem', margin: 0 }}>
          💡 <strong>How it works:</strong><br />
          • When enabled, these limits apply to all users without an active subscription<br />
          • Users trying to list above the limit will see an error with the max allowed price<br />
          • Existing listings are not affected - only new listings are validated<br />
          • FREE protocols ($0) are always allowed regardless of settings
        </p>
      </div>
    </div>
  );
};

export default UnpaidPriceControlsAdmin;
