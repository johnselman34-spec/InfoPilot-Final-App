/**
 * Protocol Card Component
 * Displays individual protocol in marketplace grid
 */
import React from 'react';
import { ProtocolCopyButtons } from '../shared';

const ProtocolCard = ({ protocol, onCopyFree, onPurchase, showToast }) => (
  <div 
    style={{ 
      background: 'rgba(30, 20, 50, 0.5)', 
      borderRadius: 12, 
      padding: 15, 
      border: protocol.is_featured ? '2px solid #f472b6' : '1px solid rgba(124, 58, 237, 0.3)', 
      position: 'relative' 
    }} 
    data-testid={`protocol-card-${protocol.id}`}
  >
    {protocol.is_featured && (
      <span style={{ 
        position: 'absolute', top: -8, right: 10, 
        background: '#f472b6', color: '#fff', 
        padding: '3px 10px', borderRadius: 15, 
        fontSize: '0.65rem', fontWeight: 700 
      }}>
        FEATURED
      </span>
    )}
    
    <h4 style={{ color: '#f472b6', marginBottom: 8 }}>{protocol.name}</h4>
    <p style={{ color: '#a1a1aa', fontSize: '0.8rem', marginBottom: 10 }}>
      {protocol.description?.substring(0, 80)}...
    </p>
    
    <ProtocolCopyButtons 
      title={protocol.name} 
      protocol={protocol.protocol_string} 
      hasAccess={protocol.is_owned || protocol.price === 0 || protocol.is_free} 
      showToast={showToast} 
      style={{ marginBottom: 10 }} 
    />
    
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
        {'★'.repeat(Math.round(protocol.rating))}{'☆'.repeat(5 - Math.round(protocol.rating))} ({protocol.review_count})
      </span>
      <span style={{ color: '#71717a', fontSize: '0.75rem' }}>{protocol.total_sales} sales</span>
    </div>
    
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      {protocol.price === 0 || protocol.is_free ? (
        <span style={{ 
          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 
          color: '#fff', padding: '4px 12px', borderRadius: 20, 
          fontSize: '0.85rem', fontWeight: 700 
        }}>
          🆓 FREE!
        </span>
      ) : (
        <span style={{ color: '#10b981', fontSize: '1.2rem', fontWeight: 700 }}>
          ${protocol.price.toFixed(2)}
        </span>
      )}
      
      {protocol.is_owned ? (
        <span style={{ color: '#10b981', fontSize: '0.85rem' }}>✓ Owned</span>
      ) : protocol.price === 0 || protocol.is_free ? (
        <button 
          className="btn btn-primary" 
          onClick={() => onCopyFree(protocol)} 
          style={{ 
            padding: '6px 15px', fontSize: '0.85rem', 
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' 
          }}
        >
          📋 Copy FREE
        </button>
      ) : (
        <button 
          className="btn btn-primary" 
          onClick={() => onPurchase(protocol)} 
          style={{ padding: '6px 15px', fontSize: '0.85rem' }}
        >
          Buy Now
        </button>
      )}
    </div>
  </div>
);

export default ProtocolCard;
