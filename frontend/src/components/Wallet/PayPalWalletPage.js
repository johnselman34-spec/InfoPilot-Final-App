/**
 * PayPal Wallet & Payout UI
 * Full UI for users to view balance, earnings history, and request withdrawals
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

const PayPalWalletPage = ({ showToast, onBack }) => {
  const { token, user } = useAuth();
  const [wallet, setWallet] = useState(null);
  const [earnings, setEarnings] = useState([]);
  const [payouts, setPayouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [requestingPayout, setRequestingPayout] = useState(false);
  const [paypalEmail, setPaypalEmail] = useState('');
  const [showPaypalForm, setShowPaypalForm] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [minPayout, setMinPayout] = useState(1.00);

  // Fetch wallet data
  const fetchWallet = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/marketplace/seller/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setWallet(data);
        setPaypalEmail(data.paypal_email || '');
      }
    } catch (e) {
      console.error('Failed to fetch wallet:', e);
    }
  }, [token]);

  // Fetch earnings history
  const fetchEarnings = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/marketplace/earnings-history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setEarnings(data.earnings || []);
      }
    } catch (e) {
      console.error('Failed to fetch earnings:', e);
    }
  }, [token]);

  // Fetch payout history
  const fetchPayouts = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/marketplace/payout-history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPayouts(data.payouts || []);
      }
    } catch (e) {
      console.error('Failed to fetch payouts:', e);
    }
  }, [token]);

  // Fetch min payout setting
  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/settings/paypal_min_payout`);
      if (res.ok) {
        const data = await res.json();
        setMinPayout(parseFloat(data.value) || 1.00);
      }
    } catch (e) {
      console.error('Failed to fetch settings:', e);
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchWallet(), fetchEarnings(), fetchPayouts(), fetchSettings()]);
      setLoading(false);
    };
    loadData();
  }, [fetchWallet, fetchEarnings, fetchPayouts, fetchSettings]);

  // Save PayPal email
  const savePaypalEmail = async () => {
    try {
      const res = await fetch(`${API}/api/marketplace/seller/paypal`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ paypal_email: paypalEmail })
      });
      if (res.ok) {
        showToast('PayPal email saved successfully!', 'success');
        setShowPaypalForm(false);
        fetchWallet();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to save PayPal email', 'error');
      }
    } catch (e) {
      showToast('Failed to save PayPal email', 'error');
    }
  };

  // Request payout
  const requestPayout = async () => {
    if (!wallet?.paypal_email) {
      showToast('Please add your PayPal email first', 'error');
      setShowPaypalForm(true);
      return;
    }
    
    if ((wallet?.available_balance || 0) < minPayout) {
      showToast(`Minimum payout is $${minPayout.toFixed(2)}. Keep earning!`, 'error');
      return;
    }

    setRequestingPayout(true);
    try {
      const res = await fetch(`${API}/api/marketplace/request-payout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        }
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`Payout of $${data.amount?.toFixed(2) || wallet.available_balance.toFixed(2)} requested!`, 'success');
        fetchWallet();
        fetchPayouts();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to request payout', 'error');
      }
    } catch (e) {
      showToast('Failed to request payout', 'error');
    }
    setRequestingPayout(false);
  };

  if (loading) {
    return (
      <div style={{ padding: 20, textAlign: 'center' }}>
        <p style={{ color: '#a1a1aa' }}>Loading wallet...</p>
      </div>
    );
  }

  const availableBalance = wallet?.available_balance || wallet?.total_earnings || 0;
  const pendingBalance = wallet?.pending_balance || 0;
  const totalEarned = wallet?.total_earnings || 0;
  const canRequestPayout = availableBalance >= minPayout && wallet?.paypal_email;

  return (
    <div style={{ padding: 20 }} data-testid="paypal-wallet-page">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 25 }}>
        <div>
          <h1 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            💰 PayPal Wallet
          </h1>
          <p style={{ color: '#a1a1aa', margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Manage your earnings and request payouts
          </p>
        </div>
        {onBack && (
          <button 
            onClick={onBack} 
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem' }}
          >
            ← Back to Settings
          </button>
        )}
      </div>

      {/* Balance Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: 20, 
        marginBottom: 30 
      }}>
        {/* Available Balance */}
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))',
          borderRadius: 15,
          padding: 25,
          border: '1px solid rgba(16, 185, 129, 0.3)',
          textAlign: 'center'
        }} data-testid="available-balance-card">
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '0 0 10px 0' }}>Available Balance</p>
          <p style={{ color: '#10b981', fontSize: '2.8rem', fontWeight: 700, margin: 0 }}>
            ${availableBalance.toFixed(2)}
          </p>
          {availableBalance < minPayout && (
            <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 8 }}>
              Min payout: ${minPayout.toFixed(2)}
            </p>
          )}
        </div>

        {/* Pending Balance */}
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(245, 158, 11, 0.1))',
          borderRadius: 15,
          padding: 25,
          border: '1px solid rgba(245, 158, 11, 0.3)',
          textAlign: 'center'
        }} data-testid="pending-balance-card">
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '0 0 10px 0' }}>Pending</p>
          <p style={{ color: '#f59e0b', fontSize: '2.8rem', fontWeight: 700, margin: 0 }}>
            ${pendingBalance.toFixed(2)}
          </p>
          <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 8 }}>
            Processing payouts
          </p>
        </div>

        {/* Total Earned */}
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(124, 58, 237, 0.1))',
          borderRadius: 15,
          padding: 25,
          border: '1px solid rgba(124, 58, 237, 0.3)',
          textAlign: 'center'
        }} data-testid="total-earned-card">
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '0 0 10px 0' }}>Total Earned</p>
          <p style={{ color: '#a78bfa', fontSize: '2.8rem', fontWeight: 700, margin: 0 }}>
            ${totalEarned.toFixed(2)}
          </p>
          <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 8 }}>
            Lifetime earnings
          </p>
        </div>

        {/* Total Sales */}
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(236, 72, 153, 0.1))',
          borderRadius: 15,
          padding: 25,
          border: '1px solid rgba(236, 72, 153, 0.3)',
          textAlign: 'center'
        }} data-testid="total-sales-card">
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: '0 0 10px 0' }}>Total Sales</p>
          <p style={{ color: '#f472b6', fontSize: '2.8rem', fontWeight: 700, margin: 0 }}>
            {wallet?.total_sales || 0}
          </p>
          <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 8 }}>
            Protocols sold
          </p>
        </div>
      </div>

      {/* PayPal Email Setup */}
      <div style={{ 
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 15,
        padding: 20,
        marginBottom: 20,
        border: '1px solid rgba(124, 58, 237, 0.3)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
          <h3 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '1.3rem' }}>📧</span> PayPal Account
          </h3>
          {!showPaypalForm && wallet?.paypal_email && (
            <button 
              onClick={() => setShowPaypalForm(true)}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            >
              Edit
            </button>
          )}
        </div>

        {wallet?.paypal_email && !showPaypalForm ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ color: '#10b981' }}>✓</span>
            <span style={{ color: '#e5e7eb' }}>{wallet.paypal_email}</span>
            <span style={{ 
              background: 'rgba(16, 185, 129, 0.2)', 
              color: '#10b981', 
              padding: '2px 8px', 
              borderRadius: 10,
              fontSize: '0.75rem'
            }}>Connected</span>
          </div>
        ) : (
          <div>
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 15 }}>
              {wallet?.paypal_email ? 'Update your PayPal email for payouts:' : 'Enter your PayPal email to receive payouts:'}
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <input
                type="email"
                value={paypalEmail}
                onChange={(e) => setPaypalEmail(e.target.value)}
                placeholder="your-paypal@email.com"
                className="input"
                style={{ flex: 1 }}
                data-testid="paypal-email-input"
              />
              <button 
                onClick={savePaypalEmail}
                className="btn btn-primary"
                disabled={!paypalEmail.includes('@')}
                data-testid="save-paypal-btn"
              >
                Save
              </button>
              {showPaypalForm && wallet?.paypal_email && (
                <button 
                  onClick={() => { setShowPaypalForm(false); setPaypalEmail(wallet.paypal_email); }}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Request Payout Section */}
      <div style={{ 
        background: canRequestPayout 
          ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(59, 130, 246, 0.15))'
          : 'rgba(30, 20, 50, 0.5)',
        borderRadius: 15,
        padding: 20,
        marginBottom: 25,
        border: `1px solid ${canRequestPayout ? 'rgba(16, 185, 129, 0.4)' : 'rgba(124, 58, 237, 0.3)'}`
      }}>
        <h3 style={{ color: canRequestPayout ? '#10b981' : '#f472b6', margin: '0 0 15px 0' }}>
          💸 Request Payout
        </h3>
        
        {!wallet?.paypal_email ? (
          <p style={{ color: '#f59e0b', fontSize: '0.9rem' }}>
            ⚠️ Please add your PayPal email above to request payouts.
          </p>
        ) : availableBalance < minPayout ? (
          <div>
            <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
              Your balance is below the minimum payout threshold of <strong style={{ color: '#10b981' }}>${minPayout.toFixed(2)}</strong>.
            </p>
            <div style={{ 
              background: 'rgba(0,0,0,0.2)', 
              borderRadius: 10, 
              padding: 15, 
              marginTop: 10 
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                <span style={{ color: '#71717a', fontSize: '0.85rem' }}>Progress to payout:</span>
                <span style={{ color: '#10b981', fontSize: '0.85rem' }}>
                  ${availableBalance.toFixed(2)} / ${minPayout.toFixed(2)}
                </span>
              </div>
              <div style={{ 
                background: 'rgba(16, 185, 129, 0.2)', 
                borderRadius: 10, 
                height: 8, 
                overflow: 'hidden' 
              }}>
                <div style={{ 
                  background: 'linear-gradient(90deg, #10b981, #34d399)', 
                  width: `${Math.min(100, (availableBalance / minPayout) * 100)}%`,
                  height: '100%',
                  borderRadius: 10,
                  transition: 'width 0.5s'
                }} />
              </div>
              <p style={{ color: '#71717a', fontSize: '0.75rem', margin: '8px 0 0 0', textAlign: 'center' }}>
                ${(minPayout - availableBalance).toFixed(2)} more to unlock payout!
              </p>
            </div>
          </div>
        ) : (
          <div>
            <p style={{ color: '#e5e7eb', fontSize: '0.95rem', marginBottom: 15 }}>
              🎉 You have <strong style={{ color: '#10b981' }}>${availableBalance.toFixed(2)}</strong> available for withdrawal!
            </p>
            <button
              onClick={requestPayout}
              disabled={requestingPayout}
              className="btn btn-primary"
              style={{ 
                background: 'linear-gradient(135deg, #10b981, #059669)',
                fontSize: '1.1rem',
                padding: '15px 30px'
              }}
              data-testid="request-payout-btn"
            >
              {requestingPayout ? '⏳ Processing...' : `💰 Request $${availableBalance.toFixed(2)} Payout`}
            </button>
            <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
              Payouts are typically processed within 1-3 business days.
            </p>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        {['overview', 'earnings', 'payouts'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 20px',
              background: activeTab === tab 
                ? 'linear-gradient(135deg, #7c3aed, #ec4899)'
                : 'rgba(30, 20, 50, 0.5)',
              border: activeTab === tab 
                ? 'none' 
                : '1px solid rgba(124, 58, 237, 0.3)',
              borderRadius: 10,
              color: activeTab === tab ? '#fff' : '#a1a1aa',
              cursor: 'pointer',
              fontWeight: activeTab === tab ? 600 : 400,
              transition: 'all 0.3s',
              fontSize: '0.9rem'
            }}
            data-testid={`tab-${tab}`}
          >
            {tab === 'overview' && '📊 Overview'}
            {tab === 'earnings' && '💵 Earnings History'}
            {tab === 'payouts' && '📤 Payout History'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ 
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 15,
        padding: 20,
        border: '1px solid rgba(124, 58, 237, 0.3)',
        minHeight: 300
      }}>
        {activeTab === 'overview' && (
          <div>
            <h3 style={{ color: '#f472b6', marginBottom: 20 }}>📊 Earnings Overview</h3>
            
            {wallet?.protocols?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
                {wallet.protocols.map((p, i) => (
                  <div key={i} style={{ 
                    background: 'rgba(0,0,0,0.2)', 
                    borderRadius: 10, 
                    padding: 15,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <h4 style={{ color: '#e5e7eb', margin: '0 0 5px 0' }}>{p.name}</h4>
                      <p style={{ color: '#71717a', fontSize: '0.85rem', margin: 0 }}>
                        {p.total_sales} sales • {p.price === 0 ? 'FREE' : `$${p.price?.toFixed(2)}`}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <p style={{ color: '#10b981', fontSize: '1.3rem', fontWeight: 700, margin: 0 }}>
                        ${(p.earnings || 0).toFixed(2)}
                      </p>
                      <p style={{ color: '#71717a', fontSize: '0.75rem', margin: 0 }}>earned</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <p style={{ color: '#71717a', fontSize: '1rem' }}>
                  No protocols listed yet. Start selling to see earnings here!
                </p>
                <button className="btn btn-primary" style={{ marginTop: 15 }}>
                  🚀 List Your First Protocol
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'earnings' && (
          <div>
            <h3 style={{ color: '#f472b6', marginBottom: 20 }}>💵 Earnings History</h3>
            
            {earnings.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {earnings.map((e, i) => (
                  <div key={i} style={{ 
                    background: 'rgba(0,0,0,0.2)', 
                    borderRadius: 10, 
                    padding: 15,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <p style={{ color: '#e5e7eb', margin: '0 0 5px 0' }}>{e.protocol_name || 'Protocol Sale'}</p>
                      <p style={{ color: '#71717a', fontSize: '0.8rem', margin: 0 }}>
                        {new Date(e.created_at).toLocaleDateString()} • {e.buyer_name || 'Buyer'}
                      </p>
                    </div>
                    <span style={{ color: '#10b981', fontWeight: 700 }}>+${(e.amount || 0).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#71717a', textAlign: 'center', padding: 40 }}>
                No earnings yet. Sales will appear here once you make them!
              </p>
            )}
          </div>
        )}

        {activeTab === 'payouts' && (
          <div>
            <h3 style={{ color: '#f472b6', marginBottom: 20 }}>📤 Payout History</h3>
            
            {payouts.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {payouts.map((p, i) => (
                  <div key={i} style={{ 
                    background: 'rgba(0,0,0,0.2)', 
                    borderRadius: 10, 
                    padding: 15,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <p style={{ color: '#e5e7eb', margin: '0 0 5px 0' }}>
                        Payout to {p.paypal_email || wallet?.paypal_email}
                      </p>
                      <p style={{ color: '#71717a', fontSize: '0.8rem', margin: 0 }}>
                        {new Date(p.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ color: '#10b981', fontWeight: 700 }}>${(p.amount || 0).toFixed(2)}</span>
                      <span style={{ 
                        marginLeft: 10,
                        background: p.status === 'completed' 
                          ? 'rgba(16, 185, 129, 0.2)' 
                          : p.status === 'pending'
                          ? 'rgba(245, 158, 11, 0.2)'
                          : 'rgba(239, 68, 68, 0.2)',
                        color: p.status === 'completed' 
                          ? '#10b981' 
                          : p.status === 'pending'
                          ? '#f59e0b'
                          : '#ef4444',
                        padding: '2px 8px',
                        borderRadius: 10,
                        fontSize: '0.75rem'
                      }}>
                        {p.status || 'pending'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#71717a', textAlign: 'center', padding: 40 }}>
                No payouts yet. Request your first payout when your balance reaches ${minPayout.toFixed(2)}!
              </p>
            )}
          </div>
        )}
      </div>

      {/* Info Footer */}
      <div style={{ 
        marginTop: 20, 
        padding: 15, 
        background: 'rgba(59, 130, 246, 0.1)', 
        borderRadius: 10,
        border: '1px solid rgba(59, 130, 246, 0.2)'
      }}>
        <p style={{ color: '#60a5fa', fontSize: '0.85rem', margin: 0 }}>
          💡 <strong>Tip:</strong> You earn 90% of every sale! The more protocols you sell, the more you earn. 
          Payouts are processed via PayPal within 1-3 business days.
        </p>
      </div>
    </div>
  );
};

export default PayPalWalletPage;
