import React, { useState } from 'react';

/**
 * Group Card Component
 */
export const GroupCard = ({ 
  group, 
  onJoin, 
  onLeave,
  onView,
  isMember = false,
  isOwner = false 
}) => {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.2)',
      borderRadius: 12,
      padding: 18,
      border: isOwner 
        ? '2px solid rgba(251, 191, 36, 0.3)'
        : '1px solid rgba(59, 130, 246, 0.2)',
      transition: 'all 0.2s',
      cursor: 'pointer'
    }}
    onClick={() => onView && onView(group)}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 12 }}>
        <div style={{
          width: 50,
          height: 50,
          borderRadius: 12,
          background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.5rem',
          flexShrink: 0
        }}>
          👥
        </div>
        <div style={{ flex: 1 }}>
          <h4 style={{ 
            color: '#fff', 
            margin: 0, 
            fontSize: '1.05rem',
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            {group.name}
            {isOwner && (
              <span style={{
                background: 'rgba(251, 191, 36, 0.2)',
                color: '#fbbf24',
                padding: '2px 8px',
                borderRadius: 10,
                fontSize: '0.65rem',
                fontWeight: 600
              }}>
                OWNER
              </span>
            )}
          </h4>
          <p style={{ 
            color: '#a1a1aa', 
            margin: '4px 0 0 0', 
            fontSize: '0.85rem',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}>
            {group.description || 'No description'}
          </p>
        </div>
      </div>

      {/* Stats */}
      <div style={{ 
        display: 'flex', 
        gap: 15, 
        marginBottom: 12,
        paddingBottom: 12,
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <span style={{ color: '#71717a', fontSize: '0.8rem' }}>
          👤 {group.member_count || 0} members
        </span>
        <span style={{ color: '#71717a', fontSize: '0.8rem' }}>
          📝 {group.post_count || 0} posts
        </span>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 8 }} onClick={(e) => e.stopPropagation()}>
        {isMember ? (
          <>
            <button
              onClick={() => onView && onView(group)}
              style={{
                flex: 1,
                background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                border: 'none',
                borderRadius: 8,
                padding: '10px 16px',
                color: '#fff',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              Open Group
            </button>
            {!isOwner && (
              <button
                onClick={() => onLeave && onLeave(group.id || group._id)}
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 8,
                  padding: '10px 14px',
                  color: '#f87171',
                  fontSize: '0.85rem',
                  cursor: 'pointer'
                }}
              >
                Leave
              </button>
            )}
          </>
        ) : (
          <button
            onClick={() => onJoin && onJoin(group.id || group._id)}
            style={{
              flex: 1,
              background: 'linear-gradient(135deg, #10b981, #059669)',
              border: 'none',
              borderRadius: 8,
              padding: '10px 16px',
              color: '#fff',
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
          >
            + Join Group
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * Page Card Component
 */
export const PageCard = ({ 
  page, 
  onFollow, 
  onUnfollow,
  onView,
  isFollowing = false,
  isOwner = false 
}) => {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.2)',
      borderRadius: 12,
      padding: 18,
      border: isOwner 
        ? '2px solid rgba(236, 72, 153, 0.3)'
        : '1px solid rgba(236, 72, 153, 0.2)',
      transition: 'all 0.2s',
      cursor: 'pointer'
    }}
    onClick={() => onView && onView(page)}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 12 }}>
        <div style={{
          width: 50,
          height: 50,
          borderRadius: 12,
          background: 'linear-gradient(135deg, #ec4899, #be185d)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.5rem',
          flexShrink: 0
        }}>
          📄
        </div>
        <div style={{ flex: 1 }}>
          <h4 style={{ 
            color: '#fff', 
            margin: 0, 
            fontSize: '1.05rem',
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            {page.name}
            {isOwner && (
              <span style={{
                background: 'rgba(236, 72, 153, 0.2)',
                color: '#ec4899',
                padding: '2px 8px',
                borderRadius: 10,
                fontSize: '0.65rem',
                fontWeight: 600
              }}>
                ADMIN
              </span>
            )}
          </h4>
          <p style={{ 
            color: '#a1a1aa', 
            margin: '4px 0 0 0', 
            fontSize: '0.85rem',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}>
            {page.description || 'No description'}
          </p>
        </div>
      </div>

      {/* Stats */}
      <div style={{ 
        display: 'flex', 
        gap: 15, 
        marginBottom: 12,
        paddingBottom: 12,
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <span style={{ color: '#71717a', fontSize: '0.8rem' }}>
          ❤️ {page.follower_count || 0} followers
        </span>
        <span style={{ color: '#71717a', fontSize: '0.8rem' }}>
          📝 {page.post_count || 0} posts
        </span>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 8 }} onClick={(e) => e.stopPropagation()}>
        {isOwner ? (
          <button
            onClick={() => onView && onView(page)}
            style={{
              flex: 1,
              background: 'linear-gradient(135deg, #ec4899, #be185d)',
              border: 'none',
              borderRadius: 8,
              padding: '10px 16px',
              color: '#fff',
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
          >
            Manage Page
          </button>
        ) : isFollowing ? (
          <>
            <button
              onClick={() => onView && onView(page)}
              style={{
                flex: 1,
                background: 'linear-gradient(135deg, #ec4899, #be185d)',
                border: 'none',
                borderRadius: 8,
                padding: '10px 16px',
                color: '#fff',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              View Page
            </button>
            <button
              onClick={() => onUnfollow && onUnfollow(page.id || page._id)}
              style={{
                background: 'rgba(107, 114, 128, 0.2)',
                border: '1px solid rgba(107, 114, 128, 0.3)',
                borderRadius: 8,
                padding: '10px 14px',
                color: '#9ca3af',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              Unfollow
            </button>
          </>
        ) : (
          <button
            onClick={() => onFollow && onFollow(page.id || page._id)}
            style={{
              flex: 1,
              background: 'linear-gradient(135deg, #ec4899, #be185d)',
              border: 'none',
              borderRadius: 8,
              padding: '10px 16px',
              color: '#fff',
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
          >
            + Follow
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * Create Group/Page Modal
 */
export const CreateEntityModal = ({ 
  type = 'group', // 'group' or 'page'
  onClose, 
  onCreate,
  isLoading = false 
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    await onCreate({ name: name.trim(), description: description.trim() });
  };

  const isGroup = type === 'group';
  const color = isGroup ? '#3b82f6' : '#ec4899';

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: 20
    }}
    onClick={onClose}
    >
      <div 
        style={{
          background: '#1a1a2e',
          borderRadius: 16,
          padding: 25,
          maxWidth: 500,
          width: '100%',
          border: `1px solid ${color}30`
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ color: '#fff', marginBottom: 20 }}>
          {isGroup ? '👥 Create New Group' : '📄 Create New Page'}
        </h2>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 15 }}>
            <label style={{ color: '#a1a1aa', display: 'block', marginBottom: 5, fontSize: '0.9rem' }}>
              {isGroup ? 'Group' : 'Page'} Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={`Enter ${type} name...`}
              required
              style={{
                width: '100%',
                padding: '12px 16px',
                borderRadius: 10,
                border: `2px solid ${color}30`,
                background: 'rgba(0,0,0,0.3)',
                color: '#fff',
                fontSize: '1rem'
              }}
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ color: '#a1a1aa', display: 'block', marginBottom: 5, fontSize: '0.9rem' }}>
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your group..."
              rows={3}
              style={{
                width: '100%',
                padding: '12px 16px',
                borderRadius: 10,
                border: `2px solid ${color}30`,
                background: 'rgba(0,0,0,0.3)',
                color: '#fff',
                fontSize: '1rem',
                resize: 'vertical'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                flex: 1,
                background: 'rgba(255,255,255,0.1)',
                border: 'none',
                borderRadius: 10,
                padding: '12px',
                color: '#a1a1aa',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !name.trim()}
              style={{
                flex: 1,
                background: `linear-gradient(135deg, ${color}, ${isGroup ? '#1d4ed8' : '#be185d'})`,
                border: 'none',
                borderRadius: 10,
                padding: '12px',
                color: '#fff',
                fontWeight: 600,
                cursor: isLoading ? 'wait' : 'pointer',
                opacity: !name.trim() ? 0.5 : 1
              }}
            >
              {isLoading ? 'Creating...' : `Create ${isGroup ? 'Group' : 'Page'}`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
