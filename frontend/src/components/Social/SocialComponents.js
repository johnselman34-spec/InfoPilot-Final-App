import React from 'react';

const REACTION_TYPES = [
  { type: 'like', emoji: '👍', label: 'Like' },
  { type: 'love', emoji: '❤️', label: 'Love' },
  { type: 'haha', emoji: '😂', label: 'Haha' },
  { type: 'wow', emoji: '😮', label: 'Wow' },
  { type: 'sad', emoji: '😢', label: 'Sad' },
  { type: 'angry', emoji: '😠', label: 'Angry' }
];

/**
 * PostCard - Individual social post with reactions and comments
 */
export const PostCard = ({ post, onReaction, onComment, currentUserId }) => {
  const [commentText, setCommentText] = React.useState('');
  const [showComments, setShowComments] = React.useState(false);

  const handleComment = () => {
    if (commentText.trim()) {
      onComment(post.id, commentText);
      setCommentText('');
    }
  };

  return (
    <div className="card" style={{ marginBottom: 15 }}>
      {/* Post Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 15 }}>
        <div style={{
          width: 45,
          height: 45,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          fontSize: '1.2rem'
        }}>
          {(post.author?.username || 'U')[0].toUpperCase()}
        </div>
        <div>
          <div style={{ fontWeight: 600, color: '#e2e8f0' }}>
            {post.author?.username || 'Unknown User'}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>
            {new Date(post.created_at).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Post Content */}
      <div style={{ marginBottom: 15, color: '#e2e8f0', lineHeight: 1.6 }}>
        {post.content}
      </div>

      {/* Post Images */}
      {post.photos?.length > 0 && (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: post.photos.length === 1 ? '1fr' : 'repeat(2, 1fr)',
          gap: 10, 
          marginBottom: 15 
        }}>
          {post.photos.map((photo, idx) => (
            <img
              key={idx}
              src={photo}
              alt={`Post image ${idx + 1}`}
              style={{
                width: '100%',
                borderRadius: 12,
                maxHeight: 300,
                objectFit: 'cover'
              }}
            />
          ))}
        </div>
      )}

      {/* Reactions Bar */}
      <div style={{ 
        display: 'flex', 
        gap: 10, 
        padding: '10px 0', 
        borderTop: '1px solid rgba(124, 58, 237, 0.2)',
        borderBottom: '1px solid rgba(124, 58, 237, 0.2)',
        marginBottom: 10
      }}>
        {REACTION_TYPES.map(reaction => {
          const count = post.reactions?.filter(r => r.type === reaction.type).length || 0;
          const userReacted = post.reactions?.some(r => r.type === reaction.type && r.user_id === currentUserId);
          
          return (
            <button
              key={reaction.type}
              onClick={() => onReaction(post.id, reaction.type)}
              className={`reaction-btn ${userReacted ? 'active' : ''}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                padding: '6px 12px',
                borderRadius: 20,
                background: userReacted ? 'rgba(124, 58, 237, 0.3)' : 'rgba(30, 20, 50, 0.5)',
                border: userReacted ? '1px solid #7c3aed' : '1px solid transparent',
                color: userReacted ? '#a78bfa' : '#a1a1aa',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <span>{reaction.emoji}</span>
              {count > 0 && <span style={{ fontSize: '0.8rem' }}>{count}</span>}
            </button>
          );
        })}
      </div>

      {/* Comments Toggle */}
      <button
        onClick={() => setShowComments(!showComments)}
        style={{
          background: 'none',
          border: 'none',
          color: '#a1a1aa',
          cursor: 'pointer',
          padding: 0,
          marginBottom: 10
        }}
      >
        💬 {post.comments?.length || 0} comments {showComments ? '▲' : '▼'}
      </button>

      {/* Comments Section */}
      {showComments && (
        <div style={{ marginTop: 10 }}>
          {/* Comment Input */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 15 }}>
            <input
              type="text"
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleComment()}
              placeholder="Write a comment..."
              className="input-field"
              style={{ flex: 1 }}
            />
            <button className="btn btn-primary" onClick={handleComment}>
              Post
            </button>
          </div>

          {/* Comments List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {(post.comments || []).map((comment, idx) => (
              <div key={idx} style={{
                padding: 12,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 10
              }}>
                <div style={{ fontWeight: 600, color: '#a78bfa', fontSize: '0.9rem', marginBottom: 5 }}>
                  {comment.author?.username || 'User'}
                </div>
                <div style={{ color: '#e2e8f0', fontSize: '0.9rem' }}>
                  {comment.content}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * CreatePostForm - Form for creating new posts
 */
export const CreatePostForm = ({ onSubmit, loading }) => {
  const [content, setContent] = React.useState('');
  const [photos, setPhotos] = React.useState([]);

  const handleSubmit = () => {
    if (content.trim()) {
      onSubmit(content, photos);
      setContent('');
      setPhotos([]);
    }
  };

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3 style={{ color: '#f472b6', marginBottom: 15 }}>📝 Create Post</h3>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="What's on your mind?"
        className="input-field"
        style={{ width: '100%', minHeight: 100, resize: 'vertical', marginBottom: 10 }}
      />
      <div style={{ display: 'flex', gap: 10, justifyContent: 'space-between', alignItems: 'center' }}>
        <button className="btn btn-secondary" style={{ padding: '8px 16px' }}>
          📷 Add Photos
        </button>
        <button 
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={loading || !content.trim()}
        >
          {loading ? '⏳ Posting...' : '🚀 Post'}
        </button>
      </div>
    </div>
  );
};

/**
 * FriendCard - Individual friend display
 */
export const FriendCard = ({ friend, onMessage, onUnfriend }) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: 15,
      background: 'rgba(30, 20, 50, 0.5)',
      borderRadius: 12,
      marginBottom: 10
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 50,
          height: 50,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #10b981, #3b82f6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          fontSize: '1.2rem'
        }}>
          {(friend.username || 'F')[0].toUpperCase()}
        </div>
        <div>
          <div style={{ fontWeight: 600, color: '#e2e8f0' }}>{friend.username}</div>
          <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>{friend.email}</div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button 
          className="btn btn-primary" 
          onClick={() => onMessage(friend)}
          style={{ padding: '8px 16px', fontSize: '0.85rem' }}
        >
          💬 Message
        </button>
        <button 
          className="btn btn-secondary" 
          onClick={() => onUnfriend(friend.id)}
          style={{ padding: '8px 16px', fontSize: '0.85rem' }}
        >
          ✕
        </button>
      </div>
    </div>
  );
};

/**
 * FriendRequestCard - Incoming/outgoing friend request
 */
export const FriendRequestCard = ({ request, type, onAccept, onDecline, onCancel }) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: 15,
      background: type === 'incoming' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
      borderRadius: 12,
      marginBottom: 10,
      border: `1px solid ${type === 'incoming' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          width: 45,
          height: 45,
          borderRadius: '50%',
          background: type === 'incoming' ? '#10b981' : '#f59e0b',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold'
        }}>
          {(request.username || 'U')[0].toUpperCase()}
        </div>
        <div>
          <div style={{ fontWeight: 600, color: '#e2e8f0' }}>{request.username}</div>
          <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>
            {type === 'incoming' ? '👋 Wants to be friends' : '⏳ Request pending'}
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        {type === 'incoming' ? (
          <>
            <button className="btn btn-primary" onClick={() => onAccept(request.id)}>✓ Accept</button>
            <button className="btn btn-secondary" onClick={() => onDecline(request.id)}>✕ Decline</button>
          </>
        ) : (
          <button className="btn btn-secondary" onClick={() => onCancel(request.id)}>Cancel</button>
        )}
      </div>
    </div>
  );
};

/**
 * GroupCard - Group display card
 */
export const GroupCard = ({ group, onView, onLeave, isMember }) => {
  return (
    <div style={{
      padding: 20,
      background: 'rgba(30, 20, 50, 0.5)',
      borderRadius: 12,
      border: '1px solid rgba(124, 58, 237, 0.2)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <h4 style={{ margin: 0, color: '#e2e8f0' }}>{group.name}</h4>
        <span style={{
          padding: '3px 10px',
          background: 'rgba(124, 58, 237, 0.2)',
          borderRadius: 15,
          fontSize: '0.75rem',
          color: '#a78bfa'
        }}>
          {group.members?.length || 0} members
        </span>
      </div>
      <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 15 }}>
        {group.description || 'No description'}
      </p>
      <div style={{ display: 'flex', gap: 10 }}>
        <button className="btn btn-primary" onClick={() => onView(group)} style={{ flex: 1 }}>
          👁️ View
        </button>
        {isMember && (
          <button className="btn btn-secondary" onClick={() => onLeave(group.id)}>
            Leave
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * PageCard - Page display card
 */
export const PageCard = ({ page, onView, onFollow, isFollowing }) => {
  return (
    <div style={{
      padding: 20,
      background: 'rgba(30, 20, 50, 0.5)',
      borderRadius: 12,
      border: '1px solid rgba(236, 72, 153, 0.2)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <h4 style={{ margin: 0, color: '#e2e8f0' }}>{page.name}</h4>
        <span style={{
          padding: '3px 10px',
          background: 'rgba(236, 72, 153, 0.2)',
          borderRadius: 15,
          fontSize: '0.75rem',
          color: '#f472b6'
        }}>
          {page.category || 'General'}
        </span>
      </div>
      <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 10 }}>
        {page.description || 'No description'}
      </p>
      <div style={{ fontSize: '0.8rem', color: '#10b981', marginBottom: 15 }}>
        👥 {page.followers?.length || 0} followers
      </div>
      <div style={{ display: 'flex', gap: 10 }}>
        <button className="btn btn-primary" onClick={() => onView(page)} style={{ flex: 1 }}>
          👁️ View
        </button>
        <button 
          className={`btn ${isFollowing ? 'btn-secondary' : 'btn-primary'}`}
          onClick={() => onFollow(page.id)}
          style={{ background: isFollowing ? undefined : 'linear-gradient(135deg, #ec4899, #f472b6)' }}
        >
          {isFollowing ? 'Unfollow' : '+ Follow'}
        </button>
      </div>
    </div>
  );
};

export default PostCard;
