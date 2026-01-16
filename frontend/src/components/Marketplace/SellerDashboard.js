/**
 * Seller Dashboard Component
 * Shows seller's earnings, sales stats, and listed protocols
 */
import React from 'react';

const DashboardTab = ({ dashboard, adminPercent }) => {
  if (!dashboard) {
    return <p style={{ color: '#a1a1aa' }}>Loading dashboard...</p>;
  }
  
  return (
    <div>
      {/* Stats Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: 20, marginBottom: 30 
      }}>
        {/* Earnings */}
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1))', 
          borderRadius: 12, padding: 20, textAlign: 'center' 
        }}>
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Your Earnings</p>
          <p style={{ color: '#10b981', fontSize: '2.5rem', fontWeight: 700 }}>
            ${(dashboard.total_earnings || 0).toFixed(2)}
          </p>
          <p style={{ color: '#71717a', fontSize: '0.75rem' }}>
            {dashboard.total_earnings < 1 ? 'Accumulating... (PayPal min: $1.00)' : 'Ready for payout!'}
          </p>
        </div>
        
        {/* Total Sales */}
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(124, 58, 237, 0.1))', 
          borderRadius: 12, padding: 20, textAlign: 'center' 
        }}>
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Total Sales</p>
          <p style={{ color: '#a78bfa', fontSize: '2.5rem', fontWeight: 700 }}>
            {dashboard.total_sales || 0}
          </p>
        </div>
        
        {/* Protocol Count */}
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(236, 72, 153, 0.1))', 
          borderRadius: 12, padding: 20, textAlign: 'center' 
        }}>
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Your Protocols</p>
          <p style={{ color: '#f472b6', fontSize: '2.5rem', fontWeight: 700 }}>
            {dashboard.protocol_count || 0}
          </p>
        </div>
        
        {/* Average Rating */}
        <div style={{ 
          background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.1))', 
          borderRadius: 12, padding: 20, textAlign: 'center' 
        }}>
          <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Avg Rating</p>
          <p style={{ color: '#fbbf24', fontSize: '2.5rem', fontWeight: 700 }}>
            {'★'.repeat(Math.round(dashboard.avg_rating || 0))}
          </p>
        </div>
      </div>
      
      {/* Listed Protocols */}
      {dashboard.protocols?.length > 0 && (
        <div>
          <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Your Listed Protocols</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            {dashboard.protocols.map(p => (
              <div 
                key={p.id} 
                style={{ 
                  background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12, 
                  padding: 20, border: '1px solid rgba(124, 58, 237, 0.3)' 
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h4 style={{ color: '#f472b6', marginBottom: 5 }}>{p.name}</h4>
                    <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                      {p.total_sales} sales • {p.price === 0 ? 'FREE' : `$${p.price.toFixed(2)}`}
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ color: '#10b981', fontSize: '1.2rem', fontWeight: 700 }}>
                      ${(p.earnings || 0).toFixed(2)}
                    </p>
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

export default DashboardTab;
