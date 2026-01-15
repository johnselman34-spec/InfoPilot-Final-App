import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import PollCard, { CreatePollModal } from '../components/shared/PollCard';

const REACTION_TYPES = [
  { type: 'like', emoji: '👍', label: 'Like' },
  { type: 'love', emoji: '❤️', label: 'Love' },
  { type: 'haha', emoji: '😂', label: 'Haha' },
  { type: 'wow', emoji: '😮', label: 'Wow' },
  { type: 'sad', emoji: '😢', label: 'Sad' },
  { type: 'angry', emoji: '😠', label: 'Angry' }
];

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
  
  // Polls state
  const [polls, setPolls] = useState({});  // { groupId: [polls], pageId: [polls] }
  const [showCreatePollModal, setShowCreatePollModal] = useState(false);
  const [pollContext, setPollContext] = useState({ type: null, id: null }); // For creating polls

  const fetchFeed = useCallback(async () => {
    try {
      const res = await fetch(`${API}/feed`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPosts(data.posts || []);
      }
    } catch (e) {
      console.error('Feed fetch error:', e);
    }
  }, [token]);

  const fetchFriends = useCallback(async () => {
    try {
      const [friendsRes, requestsRes] = await Promise.all([
        fetch(`${API}/friends`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/friends/requests`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      if (friendsRes.ok) {
        const data = await friendsRes.json();
        setFriends(data.friends || []);
      }
      if (requestsRes.ok) {
        const data = await requestsRes.json();
        setFriendRequests(data);
      }
    } catch (e) {
      console.error('Friends fetch error:', e);
    }
  }, [token]);

  const fetchGroups = useCallback(async () => {
    try {
      const res = await fetch(`${API}/groups`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setGroups(data.groups || []);
      }
    } catch (e) {
      console.error('Groups fetch error:', e);
    }
  }, [token]);

  const fetchPages = useCallback(async () => {
    try {
      const res = await fetch(`${API}/pages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPages(data.pages || []);
      }
    } catch (e) {
      console.error('Pages fetch error:', e);
    }
  }, [token]);

  // Fetch polls for a specific group or page
  const fetchPolls = useCallback(async (parentType, parentId) => {
    try {
      const res = await fetch(`${API}/polls/parent/${parentType}/${parentId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPolls(prev => ({
          ...prev,
          [`${parentType}_${parentId}`]: data.polls || []
        }));
      }
    } catch (e) {
      console.error('Polls fetch error:', e);
    }
  }, [token]);

  // Create a new poll
  const createPoll = async (pollData) => {
    try {
      const res = await fetch(`${API}/polls?parent_type=${pollData.parent_type}&parent_id=${pollData.parent_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          question: pollData.question,
          options: pollData.options,
          expires_in_hours: pollData.expires_in_hours,
          allow_multiple: pollData.allow_multiple
        })
      });
      
      if (res.ok) {
        showToast('Poll created! 📊', 'success');
        // Refresh polls for this parent
        fetchPolls(pollData.parent_type, pollData.parent_id);
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to create poll', 'error');
      }
    } catch (e) {
      showToast('Error creating poll', 'error');
    }
  };

  const handleDeletePoll = (pollId, parentType, parentId) => {
    setPolls(prev => ({
      ...prev,
      [`${parentType}_${parentId}`]: (prev[`${parentType}_${parentId}`] || []).filter(p => p.id !== pollId)
    }));
    showToast('Poll deleted', 'success');
  };

  const openCreatePollModal = (type, id) => {
    setPollContext({ type, id });
    setShowCreatePollModal(true);
  };

  useEffect(() => {
    if (token) {
      fetchFeed();
      fetchFriends();
      fetchGroups();
      fetchPages();
    }
  }, [token, fetchFeed, fetchFriends, fetchGroups, fetchPages]);

  // Fetch polls when viewing groups or pages
  useEffect(() => {
    if (token && activeTab === 'groups') {
      groups.forEach(group => {
        if (group.is_admin || group.is_member) {
          fetchPolls('group', group.id);
        }
      });
    }
    if (token && activeTab === 'pages') {
      pages.forEach(page => {
        if (page.is_admin || page.is_following) {
          fetchPolls('page', page.id);
        }
      });
    }
  }, [token, activeTab, groups, pages, fetchPolls]);

  const searchUsers = async () => {
    if (searchQuery.length < 2) return;
    try {
      const res = await fetch(`${API}/friends/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.users || []);
      }
    } catch (e) {
      console.error('Search error:', e);
    }
  };

  const sendFriendRequest = async (userId) => {
    try {
      const res = await fetch(`${API}/friends/request/${userId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Friend request sent!', 'success');
        searchUsers();
        fetchFriends();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to send request', 'error');
      }
    } catch (e) {
      showToast('Error sending request', 'error');
    }
  };

  const acceptFriendRequest = async (requestId) => {
    try {
      const res = await fetch(`${API}/friends/accept/${requestId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Friend request accepted!', 'success');
        fetchFriends();
      }
    } catch (e) {
      showToast('Error accepting request', 'error');
    }
  };

  const rejectFriendRequest = async (requestId) => {
    try {
      const res = await fetch(`${API}/friends/reject/${requestId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Request rejected', 'info');
        fetchFriends();
      }
    } catch (e) {
      showToast('Error rejecting request', 'error');
    }
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
        
        res = await fetch(`${API}/posts/with-photos`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData
        });
      } else {
        res = await fetch(`${API}/posts`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content: newPostContent })
        });
      }

      if (res.ok) {
        showToast('Post created!', 'success');
        setNewPostContent('');
        setSelectedPhotos([]);
        fetchFeed();
      }
    } catch (e) {
      showToast('Error creating post', 'error');
    } finally {
      setLoading(false);
    }
  };

  const reactToPost = async (postId, reactionType) => {
    try {
      const res = await fetch(`${API}/posts/${postId}/react?reaction_type=${reactionType}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchFeed();
      }
    } catch (e) {
      console.error('Reaction error:', e);
    }
  };

  const createGroup = async () => {
    if (!newGroupName.trim()) return;
    try {
      const res = await fetch(`${API}/groups`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newGroupName,
          description: newGroupDesc,
          is_private: false
        })
      });
      if (res.ok) {
        showToast('Group created!', 'success');
        setShowNewGroupModal(false);
        setNewGroupName('');
        setNewGroupDesc('');
        fetchGroups();
      }
    } catch (e) {
      showToast('Error creating group', 'error');
    }
  };

  const createPage = async () => {
    if (!newPageName.trim()) return;
    try {
      const res = await fetch(`${API}/pages`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newPageName,
          description: newPageDesc,
          category: newPageCategory
        })
      });
      if (res.ok) {
        showToast('Page created!', 'success');
        setShowNewPageModal(false);
        setNewPageName('');
        setNewPageDesc('');
        fetchPages();
      }
    } catch (e) {
      showToast('Error creating page', 'error');
    }
  };

  const joinGroup = async (groupId) => {
    try {
      const res = await fetch(`${API}/groups/${groupId}/join`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Joined group!', 'success');
        fetchGroups();
      }
    } catch (e) {
      showToast('Error joining group', 'error');
    }
  };

  const followPage = async (pageId) => {
    try {
      const res = await fetch(`${API}/pages/${pageId}/follow`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Following page!', 'success');
        fetchPages();
      }
    } catch (e) {
      showToast('Error following page', 'error');
    }
  };

  const handlePhotoSelect = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(f => f.size <= 6.9 * 1024 * 1024);
    if (validFiles.length < files.length) {
      showToast('Some files exceed 6.9MB limit', 'warning');
    }
    setSelectedPhotos(prev => [...prev, ...validFiles].slice(0, 10));
  };

  return (
    <div className="social-page" data-testid="social-page">
      <h1 style={{ color: '#f472b6', marginBottom: 20 }}>
        Social Hub
      </h1>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        {['feed', 'friends', 'groups', 'pages'].map(tab => (
          <button
            key={tab}
            className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab(tab)}
            data-testid={`tab-${tab}`}
          >
            {tab === 'feed' && '📰 '}
            {tab === 'friends' && '👥 '}
            {tab === 'groups' && '👨‍👩‍👧‍👦 '}
            {tab === 'pages' && '📄 '}
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab === 'friends' && friendRequests.incoming?.length > 0 && (
              <span style={{ 
                marginLeft: 5, 
                background: '#ef4444', 
                borderRadius: '50%', 
                padding: '2px 6px',
                fontSize: '0.7rem'
              }}>
                {friendRequests.incoming.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Feed Tab */}
      {activeTab === 'feed' && (
        <div>
          {/* Create Post */}
          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ color: '#a78bfa', marginBottom: 10 }}>Create Post</h3>
            <textarea
              value={newPostContent}
              onChange={(e) => setNewPostContent(e.target.value)}
              placeholder="What is on your mind?"
              style={{
                width: '100%',
                minHeight: 100,
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(124, 58, 237, 0.3)',
                borderRadius: 8,
                padding: 12,
                color: '#e2e8f0',
                marginBottom: 10,
                resize: 'vertical'
              }}
              data-testid="post-content-input"
            />
            
            {/* Photo previews */}
            {selectedPhotos.length > 0 && (
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
                {selectedPhotos.map((photo, idx) => (
                  <div key={idx} style={{ position: 'relative' }}>
                    <img
                      src={URL.createObjectURL(photo)}
                      alt={`Preview ${idx}`}
                      style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 8 }}
                    />
                    <button
                      onClick={() => setSelectedPhotos(prev => prev.filter((_, i) => i !== idx))}
                      style={{
                        position: 'absolute',
                        top: -5,
                        right: -5,
                        background: '#ef4444',
                        border: 'none',
                        borderRadius: '50%',
                        width: 20,
                        height: 20,
                        cursor: 'pointer',
                        color: 'white',
                        fontSize: '0.7rem'
                      }}
                    >
                      x
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <div style={{ display: 'flex', gap: 10 }}>
              <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
                Add Photos
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handlePhotoSelect}
                  style={{ display: 'none' }}
                />
              </label>
              <button
                className="btn btn-primary"
                onClick={createPost}
                disabled={loading || (!newPostContent.trim() && selectedPhotos.length === 0)}
                data-testid="create-post-btn"
              >
                {loading ? 'Posting...' : 'Post'}
              </button>
            </div>
          </div>

          {/* Posts Feed */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            {posts.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', color: '#a1a1aa' }}>
                <p>No posts yet. Add some friends or join groups to see posts!</p>
              </div>
            ) : (
              posts.map(post => (
                <div key={post.id} className="card" data-testid={`post-${post.id}`}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                    <div style={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #7c3aed, #f472b6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontWeight: 'bold'
                    }}>
                      {post.author_name?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, color: '#e2e8f0' }}>{post.author_name}</div>
                      <div style={{ fontSize: '0.75rem', color: '#71717a' }}>
                        {new Date(post.created_at).toLocaleString()}
                        {post.context && <span style={{ color: '#a78bfa' }}> {post.context}</span>}
                      </div>
                    </div>
                  </div>
                  
                  <p style={{ color: '#d1d5db', marginBottom: 10, whiteSpace: 'pre-wrap' }}>
                    {post.content}
                  </p>
                  
                  {/* Photos */}
                  {post.photos?.length > 0 && (
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: post.photos.length === 1 ? '1fr' : 'repeat(2, 1fr)',
                      gap: 10,
                      marginBottom: 10
                    }}>
                      {post.photos.map((photo, idx) => (
                        <img
                          key={idx}
                          src={`${API.replace('/api', '')}${photo}`}
                          alt={`Post photo ${idx + 1}`}
                          style={{
                            width: '100%',
                            maxHeight: 300,
                            objectFit: 'cover',
                            borderRadius: 8
                          }}
                        />
                      ))}
                    </div>
                  )}
                  
                  {/* Reactions */}
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    {REACTION_TYPES.map(reaction => (
                      <button
                        key={reaction.type}
                        onClick={() => reactToPost(post.id, reaction.type)}
                        style={{
                          background: post.user_reaction === reaction.type 
                            ? 'rgba(124, 58, 237, 0.3)' 
                            : 'rgba(255,255,255,0.05)',
                          border: post.user_reaction === reaction.type
                            ? '1px solid #7c3aed'
                            : '1px solid transparent',
                          borderRadius: 20,
                          padding: '4px 10px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4
                        }}
                        data-testid={`reaction-${reaction.type}-${post.id}`}
                      >
                        <span>{reaction.emoji}</span>
                        <span style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>
                          {post.reaction_counts?.[reaction.type] || 0}
                        </span>
                      </button>
                    ))}
                    <span style={{ marginLeft: 'auto', color: '#71717a', fontSize: '0.8rem' }}>
                      {post.comment_count || 0} comments
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Friends Tab */}
      {activeTab === 'friends' && (
        <div>
          {/* Search Users */}
          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ color: '#a78bfa', marginBottom: 10 }}>Find Friends</h3>
            <div style={{ display: 'flex', gap: 10 }}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchUsers()}
                placeholder="Search by username or email..."
                className="form-input"
                style={{ flex: 1 }}
                data-testid="friend-search-input"
              />
              <button className="btn btn-primary" onClick={searchUsers}>
                Search
              </button>
            </div>
            
            {searchResults.length > 0 && (
              <div style={{ marginTop: 15 }}>
                {searchResults.map(u => (
                  <div key={u.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: 10,
                    background: 'rgba(255,255,255,0.03)',
                    borderRadius: 8,
                    marginBottom: 8
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{
                        width: 36,
                        height: 36,
                        borderRadius: '50%',
                        background: '#7c3aed',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white'
                      }}>
                        {u.username?.[0]?.toUpperCase()}
                      </div>
                      <span style={{ color: '#e2e8f0' }}>{u.username}</span>
                    </div>
                    {u.friendship_status === 'none' && (
                      <button className="btn btn-primary btn-sm" onClick={() => sendFriendRequest(u.id)}>
                        Add Friend
                      </button>
                    )}
                    {u.friendship_status === 'pending_sent' && (
                      <span style={{ color: '#f59e0b' }}>Request Sent</span>
                    )}
                    {u.friendship_status === 'friends' && (
                      <span style={{ color: '#10b981' }}>Friends</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Friend Requests */}
          {friendRequests.incoming?.length > 0 && (
            <div className="card" style={{ marginBottom: 20 }}>
              <h3 style={{ color: '#f472b6', marginBottom: 10 }}>
                Friend Requests ({friendRequests.incoming.length})
              </h3>
              {friendRequests.incoming.map(req => (
                <div key={req.id} style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: 10,
                  background: 'rgba(244, 114, 182, 0.1)',
                  borderRadius: 8,
                  marginBottom: 8
                }}>
                  <span style={{ color: '#e2e8f0' }}>{req.from_username}</span>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button 
                      className="btn btn-primary btn-sm" 
                      onClick={() => acceptFriendRequest(req.id)}
                    >
                      Accept
                    </button>
                    <button 
                      className="btn btn-secondary btn-sm" 
                      onClick={() => rejectFriendRequest(req.id)}
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Friends List */}
          <div className="card">
            <h3 style={{ color: '#a78bfa', marginBottom: 15 }}>
              My Friends ({friends.length})
            </h3>
            {friends.length === 0 ? (
              <p style={{ color: '#71717a' }}>No friends yet. Search for users above!</p>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 15 }}>
                {friends.map(friend => (
                  <div key={friend.id} style={{
                    padding: 15,
                    background: 'rgba(255,255,255,0.03)',
                    borderRadius: 12,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10
                  }}>
                    <div style={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #7c3aed, #f472b6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      position: 'relative'
                    }}>
                      {friend.username?.[0]?.toUpperCase()}
                      {friend.is_online && (
                        <div style={{
                          position: 'absolute',
                          bottom: 0,
                          right: 0,
                          width: 10,
                          height: 10,
                          background: '#10b981',
                          borderRadius: '50%',
                          border: '2px solid #1e1b4b'
                        }} />
                      )}
                    </div>
                    <div>
                      <div style={{ color: '#e2e8f0', fontWeight: 500 }}>{friend.username}</div>
                      <div style={{ color: '#71717a', fontSize: '0.75rem' }}>
                        {friend.is_online ? 'Online' : 'Offline'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Groups Tab */}
      {activeTab === 'groups' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ color: '#a78bfa', margin: 0 }}>Groups</h2>
            <button className="btn btn-primary" onClick={() => setShowNewGroupModal(true)}>
              + Create Group
            </button>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 15 }}>
            {groups.map(group => (
              <div key={group.id} className="card" data-testid={`group-${group.id}`}>
                <h3 style={{ color: '#f472b6', marginBottom: 8 }}>{group.name}</h3>
                <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 10 }}>
                  {group.description || 'No description'}
                </p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <span style={{ color: '#71717a', fontSize: '0.8rem' }}>
                    {group.member_count} members
                  </span>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {group.is_admin && (
                      <button 
                        className="btn btn-secondary btn-sm" 
                        onClick={() => openCreatePollModal('group', group.id)}
                        data-testid={`create-poll-group-${group.id}`}
                        title="Create Poll"
                      >
                        📊 Poll
                      </button>
                    )}
                    {!group.is_member ? (
                      <button className="btn btn-primary btn-sm" onClick={() => joinGroup(group.id)}>
                        Join
                      </button>
                    ) : (
                      <span style={{ color: '#10b981', fontSize: '0.8rem' }}>Member</span>
                    )}
                  </div>
                </div>
                
                {/* Polls for this group */}
                {polls[`group_${group.id}`]?.length > 0 && (
                  <div style={{ marginTop: 10, borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: 10 }}>
                    {polls[`group_${group.id}`].slice(0, 2).map(poll => (
                      <PollCard 
                        key={poll.id} 
                        poll={poll}
                        onDelete={(pollId) => handleDeletePoll(pollId, 'group', group.id)}
                        showContext={false}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pages Tab */}
      {activeTab === 'pages' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ color: '#a78bfa', margin: 0 }}>Pages</h2>
            <button className="btn btn-primary" onClick={() => setShowNewPageModal(true)}>
              + Create Page
            </button>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 15 }}>
            {pages.map(page => (
              <div key={page.id} className="card" data-testid={`page-${page.id}`}>
                <h3 style={{ color: '#f472b6', marginBottom: 8 }}>{page.name}</h3>
                <span style={{ 
                  fontSize: '0.7rem', 
                  padding: '2px 6px', 
                  background: 'rgba(124, 58, 237, 0.3)',
                  borderRadius: 4,
                  color: '#a78bfa'
                }}>
                  {page.category}
                </span>
                <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 10, marginTop: 8 }}>
                  {page.description || 'No description'}
                </p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <span style={{ color: '#71717a', fontSize: '0.8rem' }}>
                    {page.follower_count} followers
                  </span>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {page.is_admin && (
                      <button 
                        className="btn btn-secondary btn-sm" 
                        onClick={() => openCreatePollModal('page', page.id)}
                        data-testid={`create-poll-page-${page.id}`}
                        title="Create Poll"
                      >
                        📊 Poll
                      </button>
                    )}
                    {!page.is_following ? (
                      <button className="btn btn-primary btn-sm" onClick={() => followPage(page.id)}>
                        Follow
                      </button>
                    ) : (
                      <span style={{ color: '#10b981', fontSize: '0.8rem' }}>Following</span>
                    )}
                  </div>
                </div>
                
                {/* Polls for this page */}
                {polls[`page_${page.id}`]?.length > 0 && (
                  <div style={{ marginTop: 10, borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: 10 }}>
                    {polls[`page_${page.id}`].slice(0, 2).map(poll => (
                      <PollCard 
                        key={poll.id} 
                        poll={poll}
                        onDelete={(pollId) => handleDeletePoll(pollId, 'page', page.id)}
                        showContext={false}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* New Group Modal */}
      {showNewGroupModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="card" style={{ width: '100%', maxWidth: 400 }}>
            <h2 style={{ color: '#f472b6', marginBottom: 20 }}>Create Group</h2>
            <input
              type="text"
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              placeholder="Group name"
              className="form-input"
              style={{ marginBottom: 10 }}
            />
            <textarea
              value={newGroupDesc}
              onChange={(e) => setNewGroupDesc(e.target.value)}
              placeholder="Description"
              className="form-input"
              style={{ marginBottom: 15, minHeight: 80 }}
            />
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowNewGroupModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={createGroup}>
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Page Modal */}
      {showNewPageModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="card" style={{ width: '100%', maxWidth: 400 }}>
            <h2 style={{ color: '#f472b6', marginBottom: 20 }}>Create Page</h2>
            <input
              type="text"
              value={newPageName}
              onChange={(e) => setNewPageName(e.target.value)}
              placeholder="Page name"
              className="form-input"
              style={{ marginBottom: 10 }}
            />
            <textarea
              value={newPageDesc}
              onChange={(e) => setNewPageDesc(e.target.value)}
              placeholder="Description"
              className="form-input"
              style={{ marginBottom: 10, minHeight: 80 }}
            />
            <select
              value={newPageCategory}
              onChange={(e) => setNewPageCategory(e.target.value)}
              className="form-input"
              style={{ marginBottom: 15 }}
            >
              <option value="General">General</option>
              <option value="Business">Business</option>
              <option value="Entertainment">Entertainment</option>
              <option value="Education">Education</option>
              <option value="News">News</option>
              <option value="Technology">Technology</option>
            </select>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowNewPageModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={createPage}>
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SocialPage;
