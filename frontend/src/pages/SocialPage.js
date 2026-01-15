import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import PollCard, { CreatePollModal } from '../components/shared/PollCard';

// Import refactored components
import { 
  PostCard, 
  CreatePostForm, 
  FriendCard, 
  FriendRequestCard, 
  GroupCard, 
  PageCard 
} from '../components/Social';

const REACTION_TYPES = [
  { type: 'like', emoji: '👍', label: 'Like' },
  { type: 'love', emoji: '❤️', label: 'Love' },
  { type: 'haha', emoji: '😂', label: 'Haha' },
  { type: 'wow', emoji: '😮', label: 'Wow' },
  { type: 'sad', emoji: '😢', label: 'Sad' },
  { type: 'angry', emoji: '😠', label: 'Angry' }
];

// Sub-components
const TabButton = ({ active, onClick, children, badge }) => (
  <button
    onClick={onClick}
    style={{
      background: active ? 'linear-gradient(135deg, #8b5cf6, #ec4899)' : 'rgba(30, 20, 50, 0.5)',
      border: active ? 'none' : '1px solid rgba(124, 58, 237, 0.3)',
      color: active ? '#fff' : '#a1a1aa',
      padding: '10px 20px',
      borderRadius: 12,
      cursor: 'pointer',
      fontWeight: active ? 600 : 400,
      transition: 'all 0.2s',
      position: 'relative'
    }}
  >
    {children}
    {badge > 0 && (
      <span style={{
        position: 'absolute', top: -5, right: -5,
        background: '#ef4444', color: '#fff',
        fontSize: '0.7rem', fontWeight: 700,
        padding: '2px 6px', borderRadius: 10
      }}>{badge}</span>
    )}
  </button>
);

const SearchUserInput = ({ searchQuery, setSearchQuery, onSearch, searchResults, onSendRequest, currentUserId }) => (
  <div style={{ marginBottom: 20 }}>
    <div style={{ display: 'flex', gap: 10, marginBottom: 15 }}>
      <input
        type="text"
        placeholder="Search users by name or email..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && onSearch()}
        className="input-field"
        style={{ flex: 1 }}
      />
      <button className="btn btn-primary" onClick={onSearch}>🔍 Search</button>
    </div>
    {searchResults.length > 0 && (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {searchResults.map(user => (
          <div key={user.id} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: 15, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 45, height: 45, borderRadius: '50%',
                background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 'bold', fontSize: '1.1rem'
              }}>
                {(user.username || 'U')[0].toUpperCase()}
              </div>
              <div>
                <div style={{ fontWeight: 600, color: '#e2e8f0' }}>{user.username}</div>
                <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>{user.email}</div>
              </div>
            </div>
            {user.id !== currentUserId && (
              <button className="btn btn-primary" onClick={() => onSendRequest(user.id)} style={{ padding: '8px 16px' }}>
                + Add Friend
              </button>
            )}
          </div>
        ))}
      </div>
    )}
  </div>
);

const CreateGroupModal = ({ show, onClose, groupName, setGroupName, groupDesc, setGroupDesc, onCreate }) => {
  if (!show) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
        <div className="modal-header">
          <h2>Create Group</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div style={{ padding: 20 }}>
          <input type="text" placeholder="Group Name *" value={groupName} onChange={(e) => setGroupName(e.target.value)} className="input-field" style={{ marginBottom: 15 }} />
          <textarea placeholder="Description (optional)" value={groupDesc} onChange={(e) => setGroupDesc(e.target.value)} className="input-field" style={{ minHeight: 100, marginBottom: 15 }} />
          <button className="btn btn-primary" onClick={onCreate} style={{ width: '100%' }}>Create Group</button>
        </div>
      </div>
    </div>
  );
};

const CreatePageModal = ({ show, onClose, pageName, setPageName, pageDesc, setPageDesc, pageCategory, setPageCategory, onCreate }) => {
  if (!show) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
        <div className="modal-header">
          <h2>Create Page</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div style={{ padding: 20 }}>
          <input type="text" placeholder="Page Name *" value={pageName} onChange={(e) => setPageName(e.target.value)} className="input-field" style={{ marginBottom: 15 }} />
          <textarea placeholder="Description (optional)" value={pageDesc} onChange={(e) => setPageDesc(e.target.value)} className="input-field" style={{ minHeight: 100, marginBottom: 15 }} />
          <select value={pageCategory} onChange={(e) => setPageCategory(e.target.value)} className="input-field" style={{ marginBottom: 15 }}>
            {['General', 'Business', 'Entertainment', 'Sports', 'Technology', 'News', 'Community'].map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <button className="btn btn-primary" onClick={onCreate} style={{ width: '100%' }}>Create Page</button>
        </div>
      </div>
    </div>
  );
};

// Post Component (inline for complex logic)
const PostCardComponent = ({ post, currentUserId, onReact, onComment }) => {
  const [commentText, setCommentText] = useState('');
  const [showComments, setShowComments] = useState(false);
  
  const handleComment = async () => {
    if (commentText.trim()) {
      await onComment(post.id, commentText);
      setCommentText('');
    }
  };

  return (
    <div className="card" style={{ marginBottom: 15 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 15 }}>
        <div style={{
          width: 45, height: 45, borderRadius: '50%',
          background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 'bold', fontSize: '1.2rem'
        }}>
          {(post.author?.username || post.author_name || 'U')[0].toUpperCase()}
        </div>
        <div>
          <div style={{ fontWeight: 600, color: '#e2e8f0' }}>{post.author?.username || post.author_name || 'User'}</div>
          <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>{new Date(post.created_at).toLocaleString()}</div>
        </div>
      </div>

      <div style={{ marginBottom: 15, color: '#e2e8f0', lineHeight: 1.6 }}>{post.content}</div>

      {post.photos?.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: post.photos.length === 1 ? '1fr' : 'repeat(2, 1fr)', gap: 10, marginBottom: 15 }}>
          {post.photos.map((photo, idx) => (
            <img key={idx} src={photo} alt={`Post ${idx + 1}`} style={{ width: '100%', borderRadius: 12, maxHeight: 300, objectFit: 'cover' }} />
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, padding: '10px 0', borderTop: '1px solid rgba(124, 58, 237, 0.2)', borderBottom: '1px solid rgba(124, 58, 237, 0.2)', marginBottom: 10, flexWrap: 'wrap' }}>
        {REACTION_TYPES.map(reaction => {
          const count = post.reactions?.filter(r => r.type === reaction.type).length || 0;
          const userReacted = post.reactions?.some(r => r.type === reaction.type && r.user_id === currentUserId);
          return (
            <button key={reaction.type} onClick={() => onReact(post.id, reaction.type)}
              style={{
                display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px', borderRadius: 20,
                background: userReacted ? 'rgba(124, 58, 237, 0.3)' : 'rgba(30, 20, 50, 0.5)',
                border: userReacted ? '1px solid #7c3aed' : '1px solid transparent',
                color: userReacted ? '#a78bfa' : '#a1a1aa', cursor: 'pointer', fontSize: '0.85rem'
              }}>
              <span>{reaction.emoji}</span>
              {count > 0 && <span>{count}</span>}
            </button>
          );
        })}
      </div>

      <button onClick={() => setShowComments(!showComments)} style={{ background: 'none', border: 'none', color: '#a1a1aa', cursor: 'pointer', padding: 0, marginBottom: 10 }}>
        💬 {post.comments?.length || 0} comments {showComments ? '▲' : '▼'}
      </button>

      {showComments && (
        <div style={{ marginTop: 10 }}>
          <div style={{ display: 'flex', gap: 10, marginBottom: 15 }}>
            <input type="text" value={commentText} onChange={(e) => setCommentText(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleComment()} placeholder="Write a comment..." className="input-field" style={{ flex: 1 }} />
            <button className="btn btn-primary" onClick={handleComment}>Post</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {(post.comments || []).map((comment, idx) => (
              <div key={idx} style={{ padding: 12, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
                <div style={{ fontWeight: 600, color: '#a78bfa', fontSize: '0.9rem', marginBottom: 5 }}>{comment.author?.username || comment.author_name || 'User'}</div>
                <div style={{ color: '#e2e8f0', fontSize: '0.9rem' }}>{comment.content}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Main Component
const SocialPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [activeTab, setActiveTab] = useState('feed');
  const [posts, setPosts] = useState([]);
  const [friends, setFriends] = useState([]);
  const [friendRequests, setFriendRequests] = useState({ incoming: [], outgoing: [] });
  const [groups, setGroups] = useState([]);
  const [pages, setPages] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [newPostContent, setNewPostContent] = useState('');
  const [selectedPhotos, setSelectedPhotos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showNewGroupModal, setShowNewGroupModal] = useState(false);
  const [showNewPageModal, setShowNewPageModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [newPageName, setNewPageName] = useState('');
  const [newPageDesc, setNewPageDesc] = useState('');
  const [newPageCategory, setNewPageCategory] = useState('General');
  const [polls, setPolls] = useState({});
  const [showCreatePollModal, setShowCreatePollModal] = useState(false);
  const [pollContext, setPollContext] = useState({ type: null, id: null });

  // Fetch functions
  const fetchFeed = useCallback(async () => {
    try {
      const res = await fetch(`${API}/feed`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const data = await res.json(); setPosts(data.posts || []); }
    } catch (e) { console.error('Feed fetch error:', e); }
  }, [token]);

  const fetchFriends = useCallback(async () => {
    try {
      const [friendsRes, requestsRes] = await Promise.all([
        fetch(`${API}/friends`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/friends/requests`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      if (friendsRes.ok) { const data = await friendsRes.json(); setFriends(data.friends || []); }
      if (requestsRes.ok) { const data = await requestsRes.json(); setFriendRequests(data); }
    } catch (e) { console.error('Friends fetch error:', e); }
  }, [token]);

  const fetchGroups = useCallback(async () => {
    try {
      const res = await fetch(`${API}/groups`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const data = await res.json(); setGroups(data.groups || []); }
    } catch (e) { console.error('Groups fetch error:', e); }
  }, [token]);

  const fetchPages = useCallback(async () => {
    try {
      const res = await fetch(`${API}/pages`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const data = await res.json(); setPages(data.pages || []); }
    } catch (e) { console.error('Pages fetch error:', e); }
  }, [token]);

  const fetchPolls = useCallback(async (parentType, parentId) => {
    try {
      const res = await fetch(`${API}/polls/parent/${parentType}/${parentId}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const data = await res.json(); setPolls(prev => ({ ...prev, [`${parentType}_${parentId}`]: data.polls || [] })); }
    } catch (e) { console.error('Polls fetch error:', e); }
  }, [token]);

  useEffect(() => {
    if (token) { fetchFeed(); fetchFriends(); fetchGroups(); fetchPages(); }
  }, [token, fetchFeed, fetchFriends, fetchGroups, fetchPages]);

  useEffect(() => {
    if (token && activeTab === 'groups') {
      groups.forEach(group => { if (group.is_admin || group.is_member) fetchPolls('group', group.id); });
    }
    if (token && activeTab === 'pages') {
      pages.forEach(page => { if (page.is_admin || page.is_following) fetchPolls('page', page.id); });
    }
  }, [token, activeTab, groups, pages, fetchPolls]);

  // Action handlers
  const searchUsers = async () => {
    if (searchQuery.length < 2) return;
    try {
      const res = await fetch(`${API}/friends/search?q=${encodeURIComponent(searchQuery)}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const data = await res.json(); setSearchResults(data.users || []); }
    } catch (e) { console.error('Search error:', e); }
  };

  const sendFriendRequest = async (userId) => {
    try {
      const res = await fetch(`${API}/friends/request/${userId}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { showToast('Friend request sent!', 'success'); searchUsers(); fetchFriends(); }
      else { const data = await res.json(); showToast(data.detail || 'Failed to send request', 'error'); }
    } catch (e) { showToast('Error sending request', 'error'); }
  };

  const acceptFriendRequest = async (requestId) => {
    try {
      const res = await fetch(`${API}/friends/accept/${requestId}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { showToast('Friend request accepted!', 'success'); fetchFriends(); }
    } catch (e) { showToast('Error accepting request', 'error'); }
  };

  const rejectFriendRequest = async (requestId) => {
    try {
      const res = await fetch(`${API}/friends/reject/${requestId}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { showToast('Request rejected', 'info'); fetchFriends(); }
    } catch (e) { showToast('Error rejecting request', 'error'); }
  };

  const unfriend = async (friendId) => {
    try {
      const res = await fetch(`${API}/friends/${friendId}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { showToast('Friend removed', 'info'); fetchFriends(); }
    } catch (e) { showToast('Error removing friend', 'error'); }
  };

  const createPost = async () => {
    if (!newPostContent.trim() && selectedPhotos.length === 0) return;
    setLoading(true);
    try {
      let res;
      if (selectedPhotos.length > 0) {
        const formData = new FormData();
        formData.append('content', newPostContent);
        selectedPhotos.forEach(photo => formData.append('photos', photo));
        res = await fetch(`${API}/posts/with-photos`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: formData });
      } else {
        res = await fetch(`${API}/posts`, { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ content: newPostContent }) });
      }
      if (res.ok) { showToast('Post created!', 'success'); setNewPostContent(''); setSelectedPhotos([]); fetchFeed(); }
    } catch (e) { showToast('Error creating post', 'error'); }
    finally { setLoading(false); }
  };

  const reactToPost = async (postId, reactionType) => {
    try {
      const res = await fetch(`${API}/posts/${postId}/react?reaction_type=${reactionType}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) fetchFeed();
    } catch (e) { console.error('Reaction error:', e); }
  };

  const commentOnPost = async (postId, content) => {
    try {
      const res = await fetch(`${API}/posts/${postId}/comment`, { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ content }) });
      if (res.ok) fetchFeed();
    } catch (e) { console.error('Comment error:', e); }
  };

  const createGroup = async () => {
    if (!newGroupName.trim()) return;
    try {
      const res = await fetch(`${API}/groups`, { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newGroupName, description: newGroupDesc, is_private: false }) });
      if (res.ok) { showToast('Group created!', 'success'); setShowNewGroupModal(false); setNewGroupName(''); setNewGroupDesc(''); fetchGroups(); }
    } catch (e) { showToast('Error creating group', 'error'); }
  };

  const createPage = async () => {
    if (!newPageName.trim()) return;
    try {
      const res = await fetch(`${API}/pages`, { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newPageName, description: newPageDesc, category: newPageCategory }) });
      if (res.ok) { showToast('Page created!', 'success'); setShowNewPageModal(false); setNewPageName(''); setNewPageDesc(''); fetchPages(); }
    } catch (e) { showToast('Error creating page', 'error'); }
  };

  const joinGroup = async (groupId) => {
    try {
      const res = await fetch(`${API}/groups/${groupId}/join`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { showToast('Joined group!', 'success'); fetchGroups(); }
    } catch (e) { showToast('Error joining group', 'error'); }
  };

  const leaveGroup = async (groupId) => {
    try {
      const res = await fetch(`${API}/groups/${groupId}/leave`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { showToast('Left group', 'info'); fetchGroups(); }
    } catch (e) { showToast('Error leaving group', 'error'); }
  };

  const followPage = async (pageId) => {
    try {
      const res = await fetch(`${API}/pages/${pageId}/follow`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { showToast('Following page!', 'success'); fetchPages(); }
    } catch (e) { showToast('Error following page', 'error'); }
  };

  const unfollowPage = async (pageId) => {
    try {
      const res = await fetch(`${API}/pages/${pageId}/unfollow`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { showToast('Unfollowed page', 'info'); fetchPages(); }
    } catch (e) { showToast('Error unfollowing page', 'error'); }
  };

  const createPoll = async (pollData) => {
    try {
      const res = await fetch(`${API}/polls?parent_type=${pollData.parent_type}&parent_id=${pollData.parent_id}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question: pollData.question, options: pollData.options, expires_in_hours: pollData.expires_in_hours, allow_multiple: pollData.allow_multiple })
      });
      if (res.ok) { showToast('Poll created! 📊', 'success'); fetchPolls(pollData.parent_type, pollData.parent_id); }
      else { const data = await res.json(); showToast(data.detail || 'Failed to create poll', 'error'); }
    } catch (e) { showToast('Error creating poll', 'error'); }
  };

  const handleDeletePoll = (pollId, parentType, parentId) => {
    setPolls(prev => ({ ...prev, [`${parentType}_${parentId}`]: (prev[`${parentType}_${parentId}`] || []).filter(p => p.id !== pollId) }));
    showToast('Poll deleted', 'success');
  };

  const openCreatePollModal = (type, id) => { setPollContext({ type, id }); setShowCreatePollModal(true); };

  if (!token) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 40 }}>
        <h2 style={{ color: '#f472b6', marginBottom: 15 }}>🔐 Login Required</h2>
        <p style={{ color: '#a1a1aa' }}>Please login to access the Social Hub and connect with other pilots!</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 0' }} data-testid="social-page">
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(236, 72, 153, 0.2) 100%)', borderRadius: 20, padding: 25, marginBottom: 25, border: '1px solid rgba(139, 92, 246, 0.3)' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: 10, background: 'linear-gradient(135deg, #fff 0%, #f472b6 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          👥 Social Hub
        </h1>
        <p style={{ color: '#a1a1aa' }}>Connect with fellow InfoPilot explorers and share your discoveries!</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 25, flexWrap: 'wrap' }}>
        <TabButton active={activeTab === 'feed'} onClick={() => setActiveTab('feed')}>📰 Feed</TabButton>
        <TabButton active={activeTab === 'friends'} onClick={() => setActiveTab('friends')} badge={friendRequests.incoming?.length || 0}>👫 Friends</TabButton>
        <TabButton active={activeTab === 'groups'} onClick={() => setActiveTab('groups')}>👥 Groups</TabButton>
        <TabButton active={activeTab === 'pages'} onClick={() => setActiveTab('pages')}>📄 Pages</TabButton>
      </div>

      {/* Feed Tab */}
      {activeTab === 'feed' && (
        <div>
          {/* Create Post */}
          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ color: '#f472b6', marginBottom: 15 }}>📝 Create Post</h3>
            <textarea value={newPostContent} onChange={(e) => setNewPostContent(e.target.value)} placeholder="What's on your mind?" className="input-field" style={{ width: '100%', minHeight: 100, resize: 'vertical', marginBottom: 10 }} />
            <div style={{ display: 'flex', gap: 10, justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ cursor: 'pointer', color: '#a78bfa', display: 'flex', alignItems: 'center', gap: 8 }}>
                <input type="file" multiple accept="image/*" onChange={(e) => setSelectedPhotos([...e.target.files])} style={{ display: 'none' }} />
                📷 Add Photos {selectedPhotos.length > 0 && `(${selectedPhotos.length})`}
              </label>
              <button className="btn btn-primary" onClick={createPost} disabled={loading || (!newPostContent.trim() && selectedPhotos.length === 0)}>
                {loading ? '⏳ Posting...' : '🚀 Post'}
              </button>
            </div>
          </div>

          {/* Posts List */}
          {posts.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 40 }}>
              <p style={{ color: '#a1a1aa' }}>No posts yet. Be the first to share something!</p>
            </div>
          ) : (
            posts.map(post => (
              <PostCardComponent key={post.id} post={post} currentUserId={user?.id} onReact={reactToPost} onComment={commentOnPost} />
            ))
          )}
        </div>
      )}

      {/* Friends Tab */}
      {activeTab === 'friends' && (
        <div>
          <SearchUserInput searchQuery={searchQuery} setSearchQuery={setSearchQuery} onSearch={searchUsers} searchResults={searchResults} onSendRequest={sendFriendRequest} currentUserId={user?.id} />

          {/* Incoming Requests */}
          {friendRequests.incoming?.length > 0 && (
            <div className="card" style={{ marginBottom: 20 }}>
              <h3 style={{ color: '#10b981', marginBottom: 15 }}>📥 Friend Requests ({friendRequests.incoming.length})</h3>
              {friendRequests.incoming.map(request => (
                <div key={request.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 15, background: 'rgba(16, 185, 129, 0.1)', borderRadius: 12, marginBottom: 10, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 45, height: 45, borderRadius: '50%', background: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                      {(request.username || 'U')[0].toUpperCase()}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, color: '#e2e8f0' }}>{request.username}</div>
                      <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>👋 Wants to be friends</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-primary" onClick={() => acceptFriendRequest(request.id)}>✓ Accept</button>
                    <button className="btn btn-secondary" onClick={() => rejectFriendRequest(request.id)}>✕</button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Friends List */}
          <div className="card">
            <h3 style={{ color: '#f472b6', marginBottom: 15 }}>👫 My Friends ({friends.length})</h3>
            {friends.length === 0 ? (
              <p style={{ color: '#a1a1aa', textAlign: 'center', padding: 20 }}>No friends yet. Search and add some!</p>
            ) : (
              friends.map(friend => (
                <div key={friend.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 15, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12, marginBottom: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 50, height: 50, borderRadius: '50%', background: 'linear-gradient(135deg, #10b981, #3b82f6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '1.2rem' }}>
                      {(friend.username || 'F')[0].toUpperCase()}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, color: '#e2e8f0' }}>{friend.username}</div>
                      <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>{friend.callsign || friend.email}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>💬 Message</button>
                    <button className="btn btn-secondary" onClick={() => unfriend(friend.id)} style={{ padding: '8px 16px', fontSize: '0.85rem' }}>✕</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Groups Tab */}
      {activeTab === 'groups' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3 style={{ color: '#f472b6', margin: 0 }}>👥 Groups</h3>
            <button className="btn btn-primary" onClick={() => setShowNewGroupModal(true)}>+ Create Group</button>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 15 }}>
            {groups.map(group => (
              <div key={group.id} className="card" style={{ padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <h4 style={{ margin: 0, color: '#e2e8f0' }}>{group.name}</h4>
                  <span style={{ padding: '3px 10px', background: 'rgba(124, 58, 237, 0.2)', borderRadius: 15, fontSize: '0.75rem', color: '#a78bfa' }}>
                    {group.member_count || group.members?.length || 0} members
                  </span>
                </div>
                <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 15 }}>{group.description || 'No description'}</p>
                
                {/* Group Polls */}
                {polls[`group_${group.id}`]?.length > 0 && (
                  <div style={{ marginBottom: 15 }}>
                    <h5 style={{ color: '#a78bfa', fontSize: '0.85rem', marginBottom: 10 }}>📊 Active Polls</h5>
                    {polls[`group_${group.id}`].slice(0, 2).map(poll => (
                      <PollCard key={poll.id} poll={poll} showToast={showToast} onDelete={() => handleDeletePoll(poll.id, 'group', group.id)} onVote={() => fetchPolls('group', group.id)} />
                    ))}
                  </div>
                )}
                
                <div style={{ display: 'flex', gap: 10 }}>
                  {group.is_member ? (
                    <>
                      <button className="btn btn-secondary" onClick={() => leaveGroup(group.id)} style={{ flex: 1 }}>Leave</button>
                      {group.is_admin && <button className="btn btn-primary" onClick={() => openCreatePollModal('group', group.id)}>📊 Poll</button>}
                    </>
                  ) : (
                    <button className="btn btn-primary" onClick={() => joinGroup(group.id)} style={{ flex: 1 }}>Join Group</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pages Tab */}
      {activeTab === 'pages' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3 style={{ color: '#f472b6', margin: 0 }}>📄 Pages</h3>
            <button className="btn btn-primary" onClick={() => setShowNewPageModal(true)}>+ Create Page</button>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 15 }}>
            {pages.map(page => (
              <div key={page.id} className="card" style={{ padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <h4 style={{ margin: 0, color: '#e2e8f0' }}>{page.name}</h4>
                  <span style={{ padding: '3px 10px', background: 'rgba(236, 72, 153, 0.2)', borderRadius: 15, fontSize: '0.75rem', color: '#f472b6' }}>
                    {page.category || 'General'}
                  </span>
                </div>
                <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 10 }}>{page.description || 'No description'}</p>
                <div style={{ fontSize: '0.8rem', color: '#10b981', marginBottom: 15 }}>👥 {page.follower_count || page.followers?.length || 0} followers</div>
                
                {/* Page Polls */}
                {polls[`page_${page.id}`]?.length > 0 && (
                  <div style={{ marginBottom: 15 }}>
                    <h5 style={{ color: '#f472b6', fontSize: '0.85rem', marginBottom: 10 }}>📊 Active Polls</h5>
                    {polls[`page_${page.id}`].slice(0, 2).map(poll => (
                      <PollCard key={poll.id} poll={poll} showToast={showToast} onDelete={() => handleDeletePoll(poll.id, 'page', page.id)} onVote={() => fetchPolls('page', page.id)} />
                    ))}
                  </div>
                )}
                
                <div style={{ display: 'flex', gap: 10 }}>
                  {page.is_following ? (
                    <>
                      <button className="btn btn-secondary" onClick={() => unfollowPage(page.id)} style={{ flex: 1 }}>Unfollow</button>
                      {page.is_admin && <button className="btn btn-primary" onClick={() => openCreatePollModal('page', page.id)}>📊 Poll</button>}
                    </>
                  ) : (
                    <button className="btn btn-primary" onClick={() => followPage(page.id)} style={{ flex: 1, background: 'linear-gradient(135deg, #ec4899, #f472b6)' }}>+ Follow</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modals */}
      <CreateGroupModal show={showNewGroupModal} onClose={() => setShowNewGroupModal(false)} groupName={newGroupName} setGroupName={setNewGroupName} groupDesc={newGroupDesc} setGroupDesc={setNewGroupDesc} onCreate={createGroup} />
      <CreatePageModal show={showNewPageModal} onClose={() => setShowNewPageModal(false)} pageName={newPageName} setPageName={setNewPageName} pageDesc={newPageDesc} setPageDesc={setNewPageDesc} pageCategory={newPageCategory} setPageCategory={setNewPageCategory} onCreate={createPage} />
      
      {showCreatePollModal && (
        <CreatePollModal
          onClose={() => setShowCreatePollModal(false)}
          onSubmit={(pollData) => { createPoll({ ...pollData, parent_type: pollContext.type, parent_id: pollContext.id }); setShowCreatePollModal(false); }}
          parentType={pollContext.type}
          parentId={pollContext.id}
        />
      )}
    </div>
  );
};

export default SocialPage;
