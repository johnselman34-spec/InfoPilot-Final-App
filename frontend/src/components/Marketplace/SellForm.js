/**
 * Sell Protocol Form Component
 * Form for listing new protocols on the marketplace
 */
import React from 'react';

const SellForm = ({ newProtocol, setNewProtocol, onSubmit, adminPercent }) => (
  <div style={{ maxWidth: 600 }}>
    <div style={{ 
      background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))', 
      padding: 20, borderRadius: 12, marginBottom: 20 
    }}>
      <h3 style={{ color: '#10b981', marginBottom: 10 }}>💰 Earn HUNDREDS or THOUSANDS of Easy Dollars!</h3>
      <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
        List your search protocols and earn <strong style={{ color: '#10b981' }}>{100 - adminPercent}%</strong> of every sale!
        <br/><span style={{ color: '#71717a', fontSize: '0.8rem' }}>Platform fee: {adminPercent}% • Listing is FREE • No monthly fees • Ever!</span>
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
          <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Price ($0.00 FREE or $0.01 - $99.99)</label>
          <input 
            className="input" 
            type="number" 
            min="0" max="99.99" step="0.01" 
            value={newProtocol.price} 
            onChange={(e) => setNewProtocol({ ...newProtocol, price: parseFloat(e.target.value) || 0 })} 
          />
          {newProtocol.price === 0 && (
            <div style={{ 
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 
              color: '#fff', padding: '8px 12px', borderRadius: 8, 
              marginTop: 8, fontSize: '0.85rem', textAlign: 'center' 
            }}>
              🆓 Your protocol will be FREE TO COPY! Great for building reputation!
            </div>
          )}
        </div>
        
        <div style={{ flex: 1 }}>
          <label style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>Category</label>
          <select 
            className="input" 
            value={newProtocol.category} 
            onChange={(e) => setNewProtocol({ ...newProtocol, category: e.target.value })}
          >
            {['General', 'News & Media', 'Science & Research', 'Business & Finance', 'Technology', 'Entertainment', 'History & Politics', 'Aviation & Military', 'Education', 'Health & Medical'].map(cat => (
              <option key={cat}>{cat}</option>
            ))}
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
        background: 'rgba(251, 191, 36, 0.1)', padding: 15, 
        borderRadius: 10, border: '1px solid rgba(251, 191, 36, 0.3)' 
      }}>
        <p style={{ color: '#fbbf24', fontSize: '0.9rem', margin: 0 }}>
          💵 You will earn: <strong>${((newProtocol.price || 0.99) * (100 - adminPercent) / 100).toFixed(2)}</strong> per sale
        </p>
      </div>
      
      <button 
        className="btn btn-primary" 
        onClick={onSubmit} 
        style={{ marginTop: 10, fontSize: '1.1rem', padding: '15px' }}
      >
        🚀 List Protocol & Start Earning!
      </button>
    </div>
  </div>
);

export default SellForm;
