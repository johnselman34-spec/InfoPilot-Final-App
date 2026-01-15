import React, { useState } from 'react';

/**
 * Friend Card Component
 */
export const FriendCard = ({ 
  friend, 
  onMessage, 
  onRemove,
  onViewProfile,
  isSelf = false 
}) => {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.2)',
      borderRadius: 12,
      padding: 15,
      display: 'flex',
      alignItems: 'center',
      gap: 15,
      border: '1px solid rgba(139, 92, 246, 0.2)',
      transition: 'all 0.2s'
    }}>
      {/* Avatar */}
      <div style={{
        width: 50,
        height: 50,
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '1.2rem',
        color: '#fff',
        fontWeight: 600
      }}>
        {(friend.username || friend.email || 'U')[0].toUpperCase()}
      </div>

      {/* Info */}
      <div style={{ flex: 1 }}>
        <h4 style={{ color: '#fff', margin: 0, fontSize: '1rem' }}>
          {friend.username || 'User'}
          {isSelf && <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}> (You)</span>}
        </h4>
        <p style={{ color: '#a1a1aa', margin: '3px 0 0 0', fontSize: '0.85rem' }}>
          {friend.email}
        </p>
        {friend.status && (
          <span style={{
            display: 'inline-block',
            background: friend.status === 'online' ? '#10b981' : '#6b7280',
            width: 8,
            height: 8,
            borderRadius: '50%',
            marginRight: 5
          }} />
        )}
      </div>

      {/* Actions */}
      {!isSelf && (
        <div style={{ display: 'flex', gap: 8 }}>
          {onMessage && (
            <button
              onClick={() => onMessage(friend)}
              style={{
                background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
                border: 'none',
                borderRadius: 8,
                padding: '8px 16px',
                color: '#fff',
                fontSize: '0.8rem',
                cursor: 'pointer'
              }}
            >
              💬 Message
            </button>
          )}
          {onRemove && (
            <button
              onClick={() => onRemove(friend.id || friend._id)}
              style={{
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: 8,
                padding: '8px 12px',
                color: '#f87171',
                fontSize: '0.8rem',
                cursor: 'pointer'
              }}
            >
              ✕
            </button>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Friend Request Card
 */
export const FriendRequestCard = ({ 
  request, 
  onAccept, 
  onDecline,
  type = 'received' // 'received' or 'sent'
}) => {
  return (
    <div style={{
      background: 'rgba(251, 191, 36, 0.1)',
      borderRadius: 12,
      padding: 15,
      display: 'flex',
      alignItems: 'center',
      gap: 15,
      border: '1px solid rgba(251, 191, 36, 0.2)'
    }}>
      {/* Avatar */}
      <div style={{
        width: 45,
        height: 45,
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #f59e0b, #d97706)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '1rem',
        color: '#fff',
        fontWeight: 600
      }}>
        {(request.from_username || request.to_username || 'U')[0].toUpperCase()}
      </div>

      {/* Info */}
      <div style={{ flex: 1 }}>
        <h4 style={{ color: '#fff', margin: 0, fontSize: '0.95rem' }}>
          {type === 'received' ? request.from_username : request.to_username}
        </h4>
        <p style={{ color: '#a1a1aa', margin: '2px 0 0 0', fontSize: '0.8rem' }}>
          {type === 'received' ? 'Wants to be friends' : 'Pending acceptance'}
        </p>
      </div>

      {/* Actions */}
      {type === 'received' ? (
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => onAccept(request.id || request._id)}
            style={{
              background: 'linear-gradient(135deg, #10b981, #059669)',
              border: 'none',
              borderRadius: 8,
              padding: '8px 14px',
              color: '#fff',
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            ✓ Accept
          </button>
          <button
            onClick={() => onDecline(request.id || request._id)}
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 8,
              padding: '8px 14px',
              color: '#f87171',
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            ✕ Decline
          </button>
        </div>
      ) : (
        <span style={{
          background: 'rgba(251, 191, 36, 0.2)',
          padding: '6px 12px',
          borderRadius: 15,
          color: '#fbbf24',
          fontSize: '0.75rem'
        }}>
          Pending
        </span>
      )}
    </div>
  );
};

/**
 * Add Friend Form
 */
export const AddFriendForm = ({ onSendRequest, isLoading = false }) => {
  const [email, setEmail] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    
    await onSendRequest(email.trim());
    setEmail('');
  };

  return (
    <form onSubmit={handleSubmit} style={{
      display: 'flex',
      gap: 10,
      marginBottom: 20
    }}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter friend's email..."
        style={{
          flex: 1,
          padding: '12px 16px',
          borderRadius: 10,
          border: '2px solid rgba(139, 92, 246, 0.3)',
          background: 'rgba(0,0,0,0.3)',
          color: '#fff',
          fontSize: '0.95rem'
        }}
      />
      <button
        type="submit"
        disabled={isLoading || !email.trim()}
        style={{
          background: isLoading 
            ? 'rgba(139, 92, 246, 0.5)'
            : 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
          border: 'none',
          borderRadius: 10,
          padding: '12px 24px',
          color: '#fff',
          fontWeight: 600,
          cursor: isLoading ? 'wait' : 'pointer',
          opacity: !email.trim() ? 0.5 : 1
        }}
      >
        {isLoading ? 'Sending...' : '+ Add Friend'}
      </button>
    </form>
  );
};
