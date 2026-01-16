/**
 * Search Result Comments Component
 * Display and manage comments on search results
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { API } from '../../utils/api';

const SearchResultComments = ({ resultId, showToast, onClose }) => {
  const { token, user } = useAuth();
  const { isDarkMode, currentAccent } = useTheme();
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Fetch comments
  const fetchComments = useCallback(async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API}/search-results/${resultId}/comments`, { headers });
      if (res.ok) {
        const data = await res.json();
        setComments(data.comments || []);
      }
    } catch (e) {
      console.error('Failed to fetch comments:', e);
    }
    setLoading(false);
  }, [resultId, token]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  // Add comment
  const addComment = async () => {
    if (!newComment.trim()) return;
    if (!token) {
      showToast?.('Please log in to comment', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API}/search-results/${resultId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          content: newComment,
          parent_id: replyingTo
        })
      });

      if (res.ok) {
        setNewComment('');
        setReplyingTo(null);
        fetchComments();
        showToast?.('Comment added!', 'success');
      } else {
        const data = await res.json();
        showToast?.(data.detail || 'Failed to add comment', 'error');
      }
    } catch (e) {
      showToast?.('Failed to add comment', 'error');
    }
    setSubmitting(false);
  };

  // Delete comment
  const deleteComment = async (commentId) => {
    if (!window.confirm('Delete this comment?')) return;

    try {
      const res = await fetch(`${API}/api/search-results/${resultId}/comments/${commentId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        fetchComments();
        showToast?.('Comment deleted', 'success');
      }
    } catch (e) {
      showToast?.('Failed to delete comment', 'error');
    }
  };

  // Like comment
  const likeComment = async (commentId) => {
    if (!token) {
      showToast?.('Please log in to like comments', 'error');
      return;
    }

    try {
      await fetch(`${API}/api/search-results/${resultId}/comments/${commentId}/like`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchComments();
    } catch (e) {
      console.error('Failed to like comment:', e);
    }
  };

  // Organize comments into threads
  const getCommentThreads = () => {
    const topLevel = comments.filter(c => !c.parent_id);
    const replies = comments.filter(c => c.parent_id);
    
    return topLevel.map(comment => ({
      ...comment,
      replies: replies.filter(r => r.parent_id === comment.id)
    }));
  };

  // Render single comment
  const CommentItem = ({ comment, isReply = false }) => (
    <div
      style={{
        marginLeft: isReply ? 30 : 0,
        marginBottom: 15,
        padding: 15,
        background: isDarkMode ? 'rgba(30, 20, 50, 0.5)' : 'rgba(248, 250, 252, 0.9)',
        borderRadius: 10,
        border: `1px solid ${isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
        borderLeft: isReply ? `3px solid ${currentAccent?.primary || '#7c3aed'}` : undefined
      }}
      data-testid={`comment-${comment.id}`}
    >
      {/* Author */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: '50%',
          background: currentAccent?.gradient || 'linear-gradient(135deg, #7c3aed, #ec4899)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 700,
          fontSize: '0.8rem'
        }}>
          {comment.author?.avatar_url 
            ? <img src={comment.author.avatar_url} alt="" style={{ width: '100%', height: '100%', borderRadius: '50%' }} />
            : comment.author?.username?.charAt(0)?.toUpperCase() || '?'}
        </div>
        <div style={{ flex: 1 }}>
          <span style={{ 
            color: isDarkMode ? '#f472b6' : '#7c3aed', 
            fontWeight: 600,
            fontSize: '0.9rem'
          }}>
            {comment.author?.username || 'Anonymous'}
          </span>
          <span style={{ 
            color: isDarkMode ? '#71717a' : '#94a3b8', 
            fontSize: '0.75rem',
            marginLeft: 10
          }}>
            {comment.created_at 
              ? new Date(comment.created_at).toLocaleDateString() 
              : 'Just now'}
          </span>
        </div>
      </div>

      {/* Content */}
      <p style={{ 
        color: isDarkMode ? '#d1d5db' : '#374151', 
        margin: '0 0 12px 0',
        fontSize: '0.9rem',
        lineHeight: 1.5
      }}>
        {comment.content}
      </p>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 15 }}>
        <button
          onClick={() => likeComment(comment.id)}
          style={{
            background: 'transparent',
            border: 'none',
            color: isDarkMode ? '#a1a1aa' : '#64748b',
            cursor: 'pointer',
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: 4
          }}
        >
          ❤️ {comment.likes || 0}
        </button>
        
        {!isReply && (
          <button
            onClick={() => setReplyingTo(comment.id)}
            style={{
              background: 'transparent',
              border: 'none',
              color: currentAccent?.primary || '#7c3aed',
              cursor: 'pointer',
              fontSize: '0.8rem'
            }}
          >
            💬 Reply
          </button>
        )}

        {comment.is_mine && (
          <button
            onClick={() => deleteComment(comment.id)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#ef4444',
              cursor: 'pointer',
              fontSize: '0.8rem'
            }}
          >
            🗑️ Delete
          </button>
        )}
      </div>

      {/* Reply form */}
      {replyingTo === comment.id && (
        <div style={{ marginTop: 15, paddingTop: 15, borderTop: `1px solid ${isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}` }}>
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder={`Reply to ${comment.author?.username}...`}
            className="input"
            rows={2}
            style={{ marginBottom: 10, fontSize: '0.85rem' }}
          />
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={addComment}
              disabled={submitting || !newComment.trim()}
              className="btn btn-primary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            >
              {submitting ? '...' : '↩️ Reply'}
            </button>
            <button
              onClick={() => { setReplyingTo(null); setNewComment(''); }}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Nested replies */}
      {comment.replies?.map(reply => (
        <CommentItem key={reply.id} comment={reply} isReply={true} />
      ))}
    </div>
  );

  const threads = getCommentThreads();

  return (
    <div
      style={{
        position: 'fixed',
        right: 0,
        top: 0,
        bottom: 0,
        width: 400,
        maxWidth: '100vw',
        background: isDarkMode ? 'rgba(15, 10, 31, 0.98)' : 'rgba(255, 255, 255, 0.98)',
        borderLeft: `1px solid ${currentAccent?.border || 'rgba(124, 58, 237, 0.3)'}`,
        display: 'flex',
        flexDirection: 'column',
        zIndex: 1000,
        boxShadow: '-5px 0 30px rgba(0,0,0,0.3)'
      }}
      data-testid="comments-panel"
    >
      {/* Header */}
      <div style={{
        padding: '15px 20px',
        borderBottom: `1px solid ${isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h3 style={{ 
          color: isDarkMode ? '#f472b6' : '#7c3aed', 
          margin: 0,
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}>
          💬 Comments ({comments.length})
        </h3>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: isDarkMode ? '#a1a1aa' : '#64748b',
            fontSize: '1.5rem',
            cursor: 'pointer'
          }}
        >
          ×
        </button>
      </div>

      {/* Comments List */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: 20 
      }}>
        {loading ? (
          <p style={{ color: isDarkMode ? '#a1a1aa' : '#64748b', textAlign: 'center' }}>
            Loading comments...
          </p>
        ) : threads.length > 0 ? (
          threads.map(comment => (
            <CommentItem key={comment.id} comment={comment} />
          ))
        ) : (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <p style={{ color: isDarkMode ? '#71717a' : '#94a3b8', marginBottom: 10 }}>
              No comments yet
            </p>
            <p style={{ color: isDarkMode ? '#52525b' : '#cbd5e1', fontSize: '0.85rem' }}>
              Be the first to share your thoughts!
            </p>
          </div>
        )}
      </div>

      {/* New Comment Form */}
      {!replyingTo && (
        <div style={{
          padding: 20,
          borderTop: `1px solid ${isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`
        }}>
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder={token ? "Add a comment..." : "Log in to comment"}
            className="input"
            rows={3}
            disabled={!token}
            style={{ marginBottom: 10 }}
            data-testid="new-comment-input"
          />
          <button
            onClick={addComment}
            disabled={submitting || !newComment.trim() || !token}
            className="btn btn-primary"
            style={{ width: '100%' }}
            data-testid="submit-comment-btn"
          >
            {submitting ? '⏳ Posting...' : '💬 Post Comment'}
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchResultComments;
