import React, { useState, useEffect } from 'react';
import { API } from '../../utils/api';
import { Icons } from '../shared';

const GroupsSection = ({ showToast, token, user }) => {
  const [groups, setGroups] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [newGroup, setNewGroup] = useState({ name: '', description: '', is_public: true });
  const [newPost, setNewPost] = useState('');
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API}/groups`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setGroups(data);
      }
    } catch (e) {
      console.error('Failed to fetch groups');
    }
    setLoading(false);
  };

  const fetchGroupDetails = async (groupId) => {
    try {
      const res = await fetch(`${API}/groups/${groupId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedGroup(data);
      }
    } catch (e) {
      showToast('Failed to load group', 'error');
    }
  };

  const createGroup = async () => {
    if (!newGroup.name) {
      showToast('Group name is required', 'error');
      return;
    }
    try {
      const res = await fetch(`${API}/groups`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newGroup)
      });
      if (res.ok) {
        showToast('Group created!', 'success');
        setShowCreateModal(false);
        setNewGroup({ name: '', description: '', is_public: true });
        fetchGroups();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to create group', 'error');
      }
    } catch (e) {
      showToast('Failed to create group', 'error');
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
        if (selectedGroup?.id === groupId) {
          fetchGroupDetails(groupId);
        }
      }
    } catch (e) {
      showToast('Failed to join group', 'error');
    }
  };

  const leaveGroup = async (groupId) => {
    try {
      const res = await fetch(`${API}/groups/${groupId}/leave`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Left group', 'success');
        fetchGroups();
        if (selectedGroup?.id === groupId) {
          fetchGroupDetails(groupId);
        }
      }
    } catch (e) {
      showToast('Failed to leave group', 'error');
    }
  };

  const createPost = async () => {
    if (!newPost.trim() || !selectedGroup) return;
    setPosting(true);
    try {
      const res = await fetch(`${API}/groups/${selectedGroup.id}/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: newPost })
      });
      if (res.ok) {
        showToast('Post created! +5 XP', 'success');
        setNewPost('');
        fetchGroupDetails(selectedGroup.id);
      }
    } catch (e) {
      showToast('Failed to create post', 'error');
    }
    setPosting(false);
  };

  const likePost = async (postId) => {
    try {
      await fetch(`${API}/groups/${selectedGroup.id}/posts/${postId}/like`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchGroupDetails(selectedGroup.id);
    } catch (e) {
      console.error('Failed to like post');
    }
  };

  if (loading) {
    return <div className="loading-spinner"><div className="spinner"></div></div>;
  }

  // Group Detail View
  if (selectedGroup) {
    return (
      <div>
        <button 
          className="btn btn-secondary" 
          onClick={() => setSelectedGroup(null)}
          style={{ marginBottom: 20 }}
        >
          ← Back to Groups
        </button>

        <div style={{ 
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.3), rgba(236, 72, 153, 0.2))',
          borderRadius: 16, padding: 25, marginBottom: 25
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <h2 style={{ color: '#f472b6', margin: 0, marginBottom: 8 }}>{selectedGroup.name}</h2>
              <p style={{ color: '#a1a1aa', marginBottom: 10 }}>{selectedGroup.description || 'No description'}</p>
              <span style={{ color: '#6b7280', fontSize: '0.85rem' }}>
                👤 {selectedGroup.member_count} members • {selectedGroup.is_public ? '🌐 Public' : '🔒 Private'}
              </span>
            </div>
            {selectedGroup.is_member ? (
              !selectedGroup.is_creator && (
                <button className="btn btn-secondary" onClick={() => leaveGroup(selectedGroup.id)}>
                  Leave Group
                </button>
              )
            ) : (
              <button className="btn btn-primary" onClick={() => joinGroup(selectedGroup.id)}>
                Join Group
              </button>
            )}
          </div>
        </div>

        {/* Create Post (if member) */}
        {(selectedGroup.is_member || selectedGroup.is_public) && (
          <div style={{ marginBottom: 25, padding: 20, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
            <textarea
              className="input"
              placeholder="Share something with the group..."
              rows={3}
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
              data-testid="group-post-input"
            />
            <button 
              className="btn btn-primary" 
              style={{ marginTop: 10 }}
              onClick={createPost}
              disabled={posting || !newPost.trim()}
              data-testid="group-post-btn"
            >
              {posting ? 'Posting...' : 'Post to Group'}
            </button>
          </div>
        )}

        {/* Group Posts */}
        <h3 style={{ color: '#f472b6', marginBottom: 15 }}>Posts</h3>
        {selectedGroup.posts?.length === 0 ? (
          <p style={{ color: '#a1a1aa', textAlign: 'center', padding: 30 }}>
            No posts yet. Be the first to post!
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            {selectedGroup.posts?.map(post => (
              <div key={post.id} style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(124, 58, 237, 0.2)'
              }}>
                <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: '50%',
                    background: 'linear-gradient(135deg, #f472b6, #7c3aed)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, color: '#fff'
                  }}>
                    {post.author_name?.[0]?.toUpperCase() || '?'}
                  </div>
                  <div>
                    <strong style={{ color: '#fff' }}>{post.author_name}</strong>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 2 }}>
                      {new Date(post.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <p style={{ color: '#e5e7eb', marginBottom: 15, lineHeight: 1.6 }}>{post.content}</p>
                <div style={{ display: 'flex', gap: 15 }}>
                  <button 
                    onClick={() => likePost(post.id)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#a1a1aa',
                      cursor: 'pointer',
                      padding: '6px 12px',
                      borderRadius: 20,
                      fontSize: '0.85rem'
                    }}
                  >
                    👍 {post.likes?.length || 0}
                  </button>
                  <button style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#a1a1aa',
                    cursor: 'pointer',
                    padding: '6px 12px',
                    borderRadius: 20,
                    fontSize: '0.85rem'
                  }}>
                    💬 {post.comments?.length || 0}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Groups List View
  return (
    <div>
      <button 
        className="btn btn-primary" 
        style={{ marginBottom: 20 }}
        onClick={() => setShowCreateModal(true)}
        data-testid="create-group-btn"
      >
        <Icons.Plus /> Create Group
      </button>

      {groups.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: '3rem', marginBottom: 15 }}>🏘️</div>
          <p style={{ color: '#a1a1aa' }}>No groups yet. Create one to start collaborating!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {groups.map(group => (
            <div 
              key={group.id} 
              style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(124, 58, 237, 0.3)',
                cursor: 'pointer',
                transition: 'transform 0.2s, border-color 0.2s'
              }}
              onClick={() => fetchGroupDetails(group.id)}
              data-testid={`group-card-${group.id}`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 10 }}>
                <h3 style={{ color: '#f472b6', margin: 0 }}>{group.name}</h3>
                <span style={{ 
                  fontSize: '0.7rem', 
                  padding: '3px 8px', 
                  borderRadius: 10,
                  background: group.is_public ? 'rgba(16, 185, 129, 0.2)' : 'rgba(124, 58, 237, 0.2)',
                  color: group.is_public ? '#10b981' : '#a78bfa'
                }}>
                  {group.is_public ? '🌐 Public' : '🔒 Private'}
                </span>
              </div>
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 15 }}>
                {group.description || 'No description'}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>
                  👤 {group.member_count || 1} members
                </span>
                <span style={{ color: '#7c3aed', fontSize: '0.8rem' }}>View →</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Group Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>Create New Group</h3>
            <input
              type="text"
              placeholder="Group Name"
              className="input"
              value={newGroup.name}
              onChange={e => setNewGroup({...newGroup, name: e.target.value})}
              style={{ marginBottom: 15 }}
              data-testid="group-name-input"
            />
            <textarea
              placeholder="Description (optional)"
              className="input"
              value={newGroup.description}
              onChange={e => setNewGroup({...newGroup, description: e.target.value})}
              rows={3}
              style={{ marginBottom: 15 }}
              data-testid="group-description-input"
            />
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, color: '#a1a1aa' }}>
              <input
                type="checkbox"
                checked={newGroup.is_public}
                onChange={e => setNewGroup({...newGroup, is_public: e.target.checked})}
              />
              Public group (anyone can join)
            </label>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={createGroup} data-testid="submit-group-btn">Create Group</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupsSection;
