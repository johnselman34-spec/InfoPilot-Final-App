/**
 * PayPal Wallet / Payout Dashboard
 * Shows user's accumulated earnings and payout history
 * Also admin view for managing all payouts
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';

const PayPalWalletPage = ({ showToast, onBack }) => {
  const { token, user } = useAuth();
  const [wallet, setWallet] = useState(null);
  const [payoutHistory, setPayoutHistory] = useState([]);
  const [allWallets, setAllWallets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingPayout, setProcessingPayout] = useState(false);
  const [paypalEmail, setPaypalEmail] = useState('');
  const [minPayout, setMinPayout] = useState(1.00);
  const isAdmin = user?.is_admin;
  
  // Fetch user's wallet
  const fetchWallet = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/marketplace/my-earnings`, {
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
  
  // Fetch admin settings
  const fetchAdminSettings = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/admin/settings/public`);
      if (res.ok) {
        const data = await res.json();
        setMinPayout(data.paypal_min_payout || 1.00);
      }
    } catch (e) {
      console.error('Failed to fetch settings:', e);
    }
  }, []);
  
  // Fetch all wallets (admin only)
  const fetchAllWallets = useCallback(async () => {
    if (!isAdmin) return;
    try {
      const res = await fetch(`${API}/api/admin/paypal-wallets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAllWallets(data.wallets || []);
      }
    } catch (e) {
      console.error('Failed to fetch all wallets:', e);
    }
  }, [token, isAdmin]);
  
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchWallet(), fetchAdminSettings(), fetchAllWallets()]);
      setLoading(false);
    };
    loadData();
  }, [fetchWallet, fetchAdminSettings, fetchAllWallets]);
  
  // Update PayPal email
  const updatePayPalEmail = async () => {
    if (!paypalEmail.trim()) {
      showToast('Please enter a valid PayPal email', 'error');
      return;
    }
    
    try {
      const res = await fetch(`${API}/api/marketplace/my-paypal-email`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ paypal_email: paypalEmail })
      });
      
      if (res.ok) {
        showToast('PayPal email updated!', 'success');
        fetchWallet();
      } else {
        showToast('Failed to update PayPal email', 'error');
      }
    } catch (e) {
      showToast('Failed to update PayPal email', 'error');
    }
  };
  
  // Request payout (for users)
  const requestPayout = async () => {
    if (!wallet?.paypal_email) {
      showToast('Please set your PayPal email first', 'error');
      return;
    }
    
    if (wallet.pending_balance < minPayout) {
      showToast(`Minimum payout is $${minPayout.toFixed(2)}. Keep earning!`, 'info');
      return;
    }
    
    setProcessingPayout(true);
    try {
      const res = await fetch(`${API}/api/marketplace/request-payout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast('Payout requested! You will receive funds within 3-5 business days.', 'success');
        fetchWallet();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to request payout', 'error');
      }
    } catch (e) {
      showToast('Failed to request payout', 'error');
    } finally {
      setProcessingPayout(false);
    }
  };
  
  // Process all eligible payouts (admin)
  const processAllPayouts = async () => {
    if (!window.confirm('Process all eligible payouts? This will send payments to all users with balance >= $' + minPayout.toFixed(2))) return;
    
    setProcessingPayout(true);
    try {
      const res = await fetch(`${API}/api/admin/paypal-wallets/process-payouts`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(`Processed ${data.processed_count} payouts!`, 'success');
        fetchAllWallets();
      } else {
        showToast('Failed to process payouts', 'error');
      }
    } catch (e) {
      showToast('Failed to process payouts', 'error');
    } finally {
      setProcessingPayout(false);
    }
  };

  if (loading) {
    return (
      <div className="card" style={{ padding: 40, textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: 15 }}>💰</div>
        <p style={{ color: '#a1a1aa' }}>Loading wallet information...</p>
      </div>
    );
  }

  return (
    <div className="card" data-testid="paypal-wallet-page">
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #0070ba, #003087)',
        padding: '25px 30px',
        borderRadius: '12px 12px 0 0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 15
      }}>
        <div>
          <h2 style={{ color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            💰 PayPal Wallet & Payouts
          </h2>
          <p style={{ color: '#a3d3ff', margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Manage your earnings and request payouts
          </p>
        </div>
        {onBack && (
          <button className="btn btn-secondary" onClick={onBack}>
            ← Back
          </button>
        )}
      </div>
      
      <div style={{ padding: 25 }}>
        {/* User Wallet Summary */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 20,
          marginBottom: 30
        }}>
          {/* Pending Balance */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2))',
            borderRadius: 12,
            padding: 20,
            border: '1px solid rgba(16, 185, 129, 0.3)',
            textAlign: 'center'
          }}>
            <div style={{ color: '#71717a', fontSize: '0.85rem', marginBottom: 5 }}>
              Pending Balance
            </div>
            <div style={{ color: '#10b981', fontSize: '2.5rem', fontWeight: 700 }}>
              ${wallet?.pending_balance?.toFixed(2) || '0.00'}
            </div>
            <div style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 5 }}>
              Min payout: ${minPayout.toFixed(2)}
            </div>
          </div>
          
          {/* Total Earned */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(139, 92, 246, 0.2))',
            borderRadius: 12,
            padding: 20,
            border: '1px solid rgba(124, 58, 237, 0.3)',
            textAlign: 'center'
          }}>
            <div style={{ color: '#71717a', fontSize: '0.85rem', marginBottom: 5 }}>
              Total Earned (All Time)
            </div>
            <div style={{ color: '#a78bfa', fontSize: '2.5rem', fontWeight: 700 }}>
              ${wallet?.total_earned?.toFixed(2) || '0.00'}
            </div>
            <div style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 5 }}>
              From {wallet?.total_sales || 0} sales
            </div>
          </div>
          
          {/* Total Paid Out */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.2))',
            borderRadius: 12,
            padding: 20,
            border: '1px solid rgba(59, 130, 246, 0.3)',
            textAlign: 'center'
          }}>
            <div style={{ color: '#71717a', fontSize: '0.85rem', marginBottom: 5 }}>
              Total Paid Out
            </div>
            <div style={{ color: '#3b82f6', fontSize: '2.5rem', fontWeight: 700 }}>
              ${wallet?.total_paid_out?.toFixed(2) || '0.00'}
            </div>
            <div style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 5 }}>
              {wallet?.payout_count || 0} payouts
            </div>
          </div>
        </div>
        
        {/* PayPal Email Setup */}
        <div style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          padding: 20,
          marginBottom: 20,
          border: '1px solid rgba(124, 58, 237, 0.3)'
        }}>
          <h3 style={{ color: '#f472b6', marginTop: 0, marginBottom: 15 }}>
            📧 PayPal Email
          </h3>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <input
              type="email"
              className="input-field"
              value={paypalEmail}
              onChange={(e) => setPaypalEmail(e.target.value)}
              placeholder="your-paypal@email.com"
              style={{ flex: 1, minWidth: 250 }}
              data-testid="paypal-email-input"
            />
            <button
              className="btn btn-primary"
              onClick={updatePayPalEmail}
              data-testid="update-paypal-email-btn"
            >
              💾 Save Email
            </button>
          </div>
          <p style={{ color: '#71717a', fontSize: '0.8rem', marginTop: 10, marginBottom: 0 }}>
            This is where your payouts will be sent. Make sure it&apos;s a valid PayPal account!
          </p>
        </div>
        
        {/* Request Payout Button */}
        <div style={{
          background: wallet?.pending_balance >= minPayout 
            ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2))'
            : 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          padding: 20,
          marginBottom: 20,
          border: wallet?.pending_balance >= minPayout 
            ? '2px solid #10b981'
            : '1px solid rgba(124, 58, 237, 0.3)',
          textAlign: 'center'
        }}>
          {wallet?.pending_balance >= minPayout ? (
            <>
              <h3 style={{ color: '#10b981', marginTop: 0 }}>
                🎉 You&apos;re eligible for a payout!
              </h3>
              <button
                className="btn btn-primary"
                onClick={requestPayout}
                disabled={processingPayout}
                style={{
                  background: 'linear-gradient(135deg, #10b981, #059669)',
                  padding: '15px 40px',
                  fontSize: '1.1rem'
                }}
                data-testid="request-payout-btn"
              >
                {processingPayout ? '⏳ Processing...' : `💸 Request Payout ($${wallet?.pending_balance?.toFixed(2)})`}
              </button>
            </>
          ) : (
            <>
              <h3 style={{ color: '#f59e0b', marginTop: 0 }}>
                ⏳ Keep Earning!
              </h3>
              <p style={{ color: '#a1a1aa', marginBottom: 10 }}>
                You need ${(minPayout - (wallet?.pending_balance || 0)).toFixed(2)} more to request a payout.
              </p>
              <p style={{ color: '#71717a', fontSize: '0.85rem', margin: 0 }}>
                Due to PayPal&apos;s minimum transaction requirements, we accumulate earnings until they reach ${minPayout.toFixed(2)}.
              </p>
            </>
          )}
        </div>
        
        {/* Important Notice */}
        <div style={{
          background: 'rgba(245, 158, 11, 0.1)',
          borderRadius: 12,
          padding: 15,
          marginBottom: 20,
          border: '1px solid rgba(245, 158, 11, 0.3)'
        }}>
          <p style={{ color: '#f59e0b', margin: 0, fontSize: '0.9rem' }}>
            <strong>💡 How Payouts Work:</strong> Due to PayPal&apos;s $1.00 minimum transaction requirement, 
            your earnings are accumulated in your wallet until they reach the minimum threshold. 
            Once you&apos;re eligible, you can request a payout anytime. Payments typically process within 3-5 business days.
          </p>
        </div>
        
        {/* Admin Section */}
        {isAdmin && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1))',
            borderRadius: 12,
            padding: 20,
            border: '1px solid rgba(239, 68, 68, 0.3)',
            marginTop: 30
          }}>
            <h3 style={{ color: '#ef4444', marginTop: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
              👑 Admin: All Wallets
            </h3>
            
            <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
              <button
                className="btn btn-primary"
                onClick={processAllPayouts}
                disabled={processingPayout}
                style={{ background: '#ef4444' }}
                data-testid="process-all-payouts-btn"
              >
                {processingPayout ? '⏳ Processing...' : '💸 Process All Eligible Payouts'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={fetchAllWallets}
              >
                🔄 Refresh
              </button>
            </div>
            
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(239, 68, 68, 0.3)' }}>
                    <th style={{ padding: 10, textAlign: 'left', color: '#ef4444' }}>User</th>
                    <th style={{ padding: 10, textAlign: 'right', color: '#ef4444' }}>Pending</th>
                    <th style={{ padding: 10, textAlign: 'right', color: '#ef4444' }}>Total Earned</th>
                    <th style={{ padding: 10, textAlign: 'left', color: '#ef4444' }}>PayPal Email</th>
                    <th style={{ padding: 10, textAlign: 'center', color: '#ef4444' }}>Eligible</th>
                  </tr>
                </thead>
                <tbody>
                  {allWallets.map(w => (
                    <tr key={w.user_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: 10, color: '#e5e7eb' }}>{w.username}</td>
                      <td style={{ padding: 10, textAlign: 'right', color: '#10b981' }}>${w.pending_balance?.toFixed(2)}</td>
                      <td style={{ padding: 10, textAlign: 'right', color: '#a78bfa' }}>${w.total_earned?.toFixed(2)}</td>
                      <td style={{ padding: 10, color: '#71717a', fontSize: '0.85rem' }}>{w.paypal_email || 'Not set'}</td>
                      <td style={{ padding: 10, textAlign: 'center' }}>
                        {w.pending_balance >= minPayout && w.paypal_email ? (
                          <span style={{ color: '#10b981' }}>✓</span>
                        ) : (
                          <span style={{ color: '#ef4444' }}>✗</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PayPalWalletPage;
