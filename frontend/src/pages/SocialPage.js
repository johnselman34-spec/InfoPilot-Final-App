import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { Icons } from '../components/shared';
import { GroupsSection, PagesSection } from '../components/social';

const SocialPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [activeTab, setActiveTab] = useState('feed');
  const [friends, setFriends] = useState([]);
  const [feedPosts, setFeedPosts] = useState([]);
  const [newPost, setNewPost] = useState('');
  const [postingFeed, setPostingFeed] = useState(false);

  useEffect(() => {
    if (activeTab === 'friends') fetchFriends();
    if (activeTab === 'feed') fetchFeed();
  }, [activeTab]);

  const fetchFriends = async () => {
    try {
      const res = await fetch(`${API}/friends`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFriends(data.friends || []);
      }
    } catch (e) {
      console.error('Failed to fetch friends:', e);
    }
  };

  const fetchFeed = async () => {
    try {
      const res = await fetch(`${API}/feed`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFeedPosts(data.posts || []);
      }
    } catch (e) {
      console.error('Failed to fetch feed:', e);
    }
  };

  const createFeedPost = async () => {
    if (!newPost.trim()) return;
    setPostingFeed(true);
    try {
      const res = await fetch(`${API}/feed/post`, {
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
        fetchFeed();
      }
    } catch (e) {
      showToast('Failed to create post', 'error');
    }
    setPostingFeed(false);
  };

  return (
    <div className="card" data-testid="social-page">
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Icons.Users />
          Social Network
        </h2>
      </div>

      <div className="tabs" style={{ marginBottom: 20 }}>
        {['feed', 'friends', 'groups', 'pages'].map(tab => (
          <div
            key={tab}
            className={`tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
            data-testid={`social-tab-${tab}`}
          >
            {tab === 'feed' && '📰 '}
            {tab === 'friends' && '👥 '}
            {tab === 'groups' && '🏘️ '}
            {tab === 'pages' && '📄 '}
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </div>
        ))}
      </div>

      {activeTab === 'feed' && (
        <div>
          {/* Create Post */}
          <div style={{ 
            marginBottom: 25, 
            padding: 20,
            background: 'rgba(30, 20, 50, 0.5)',
            borderRadius: 12
          }}>
            <textarea
              className="input"
              placeholder="What's on your mind?"
              rows={3}
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
              data-testid="feed-post-input"
            />
            <button 
              className="btn btn-primary" 
              style={{ marginTop: 10 }}
              onClick={createFeedPost}
              disabled={postingFeed || !newPost.trim()}
              data-testid="feed-post-btn"
            >
              {postingFeed ? 'Posting...' : 'Post'}
            </button>
          </div>

          {/* Feed Posts */}
          {feedPosts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
              <div style={{ fontSize: '3rem', marginBottom: 15 }}>📰</div>
              <p>Your feed is empty. Join groups to see posts!</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              {feedPosts.map(post => (
                <div key={post.id} className="post-card" style={{
                  padding: 20,
                  background: 'rgba(30, 20, 50, 0.5)',
                  borderRadius: 12,
                  border: '1px solid rgba(124, 58, 237, 0.2)'
                }}>
                  <div className="post-header" style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                    <div className="post-avatar" style={{
                      width: 40, height: 40, borderRadius: '50%',
                      background: 'linear-gradient(135deg, #f472b6, #7c3aed)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontWeight: 700, color: '#fff'
                    }}>
                      {post.author_name?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <strong style={{ color: '#fff' }}>{post.author_name}</strong>
                      {post.group_name && (
                        <span style={{ color: '#a1a1aa' }}> in <span style={{ color: '#f472b6' }}>{post.group_name}</span></span>
                      )}
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 2 }}>
                        {new Date(post.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="post-content" style={{ color: '#e5e7eb', marginBottom: 15, lineHeight: 1.6 }}>
                    {post.content}
                  </div>
                  <div className="post-actions" style={{ display: 'flex', gap: 15 }}>
                    <button className="reaction-btn" style={{
                      background: post.is_liked ? 'rgba(236, 72, 153, 0.2)' : 'transparent',
                      border: 'none',
                      color: post.is_liked ? '#f472b6' : '#a1a1aa',
                      cursor: 'pointer',
                      padding: '6px 12px',
                      borderRadius: 20,
                      fontSize: '0.85rem'
                    }}>
                      👍 {post.likes || 0}
                    </button>
                    <button className="reaction-btn" style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#a1a1aa',
                      cursor: 'pointer',
                      padding: '6px 12px',
                      borderRadius: 20,
                      fontSize: '0.85rem'
                    }}>
                      💬 {post.comment_count || 0}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'friends' && (
        <div>
          <div style={{ marginBottom: 20 }}>
            <input className="input" placeholder="Search for users..." data-testid="friend-search-input" />
          </div>
          {friends.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <div style={{ fontSize: '3rem', marginBottom: 15 }}>👥</div>
              <p style={{ color: '#a1a1aa' }}>No friends yet. Start connecting with other users!</p>
            </div>
          ) : (
            friends.map(friend => (
              <div key={friend.id} className="conversation-item" style={{
                display: 'flex',
                alignItems: 'center',
                gap: 15,
                padding: 15,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 10,
                marginBottom: 10
              }}>
                <div className="post-avatar" style={{
                  width: 45, height: 45, borderRadius: '50%',
                  background: 'linear-gradient(135deg, #10b981, #3b82f6)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 700, color: '#fff'
                }}>
                  {friend.username?.[0]?.toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <strong style={{ color: '#fff' }}>{friend.username}</strong>
                </div>
                <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
                  View Profile
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'groups' && (
        <GroupsSection showToast={showToast} token={token} user={user} />
      )}

      {activeTab === 'pages' && (
        <PagesSection showToast={showToast} token={token} user={user} />
      )}
    </div>
  );
};

export default SocialPage;
