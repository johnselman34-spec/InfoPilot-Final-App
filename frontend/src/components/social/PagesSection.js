import React, { useState, useEffect } from 'react';
import { API } from '../../utils/api';
import { Icons } from '../shared';

const PagesSection = ({ showToast, token, user }) => {
  const [pages, setPages] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPage, setSelectedPage] = useState(null);
  const [newPage, setNewPage] = useState({ name: '', description: '', category: 'General' });
  const [newPost, setNewPost] = useState('');
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);

  const categories = ['General', 'Technology', 'Science', 'History', 'Entertainment', 'Sports', 'News', 'Other'];

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      const res = await fetch(`${API}/pages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPages(data);
      }
    } catch (e) {
      console.error('Failed to fetch pages');
    }
    setLoading(false);
  };

  const fetchPageDetails = async (pageId) => {
    try {
      const res = await fetch(`${API}/pages/${pageId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedPage(data);
      }
    } catch (e) {
      showToast('Failed to load page', 'error');
    }
  };

  const createPage = async () => {
    if (!newPage.name) {
      showToast('Page name is required', 'error');
      return;
    }
    try {
      const res = await fetch(`${API}/pages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newPage)
      });
      if (res.ok) {
        showToast('Page created!', 'success');
        setShowCreateModal(false);
        setNewPage({ name: '', description: '', category: 'General' });
        fetchPages();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to create page', 'error');
      }
    } catch (e) {
      showToast('Failed to create page', 'error');
    }
  };

  const likePage = async (pageId) => {
    try {
      await fetch(`${API}/pages/${pageId}/like`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchPages();
      if (selectedPage?.id === pageId) {
        fetchPageDetails(pageId);
      }
    } catch (e) {
      console.error('Failed to like page');
    }
  };

  const followPage = async (pageId) => {
    try {
      await fetch(`${API}/pages/${pageId}/follow`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (selectedPage?.id === pageId) {
        fetchPageDetails(pageId);
      }
    } catch (e) {
      console.error('Failed to follow page');
    }
  };

  const createPost = async () => {
    if (!newPost.trim() || !selectedPage) return;
    setPosting(true);
    try {
      const res = await fetch(`${API}/pages/${selectedPage.id}/posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: newPost })
      });
      if (res.ok) {
        showToast('Post created!', 'success');
        setNewPost('');
        fetchPageDetails(selectedPage.id);
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to create post', 'error');
      }
    } catch (e) {
      showToast('Failed to create post', 'error');
    }
    setPosting(false);
  };

  if (loading) {
    return <div className="loading-spinner"><div className="spinner"></div></div>;
  }

  // Page Detail View
  if (selectedPage) {
    return (
      <div>
        <button 
          className="btn btn-secondary" 
          onClick={() => setSelectedPage(null)}
          style={{ marginBottom: 20 }}
        >
          ← Back to Pages
        </button>

        <div style={{ 
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(59, 130, 246, 0.2))',
          borderRadius: 16, padding: 25, marginBottom: 25
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <h2 style={{ color: '#ec4899', margin: 0, marginBottom: 8 }}>{selectedPage.name}</h2>
              <p style={{ color: '#a1a1aa', marginBottom: 10 }}>{selectedPage.description || 'No description'}</p>
              <span style={{ 
                fontSize: '0.7rem', 
                padding: '3px 8px', 
                borderRadius: 10,
                background: 'rgba(59, 130, 246, 0.2)',
                color: '#3b82f6',
                marginRight: 10
              }}>
                {selectedPage.category}
              </span>
              <span style={{ color: '#6b7280', fontSize: '0.85rem' }}>
                ❤️ {selectedPage.likes} likes • 👥 {selectedPage.followers} followers
              </span>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button 
                className={`btn ${selectedPage.is_liked ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => likePage(selectedPage.id)}
              >
                {selectedPage.is_liked ? '❤️ Liked' : '🤍 Like'}
              </button>
              <button 
                className={`btn ${selectedPage.is_following ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => followPage(selectedPage.id)}
              >
                {selectedPage.is_following ? '✓ Following' : '+ Follow'}
              </button>
            </div>
          </div>
        </div>

        {/* Create Post (if page owner) */}
        {selectedPage.is_creator && (
          <div style={{ marginBottom: 25, padding: 20, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 12 }}>
            <textarea
              className="input"
              placeholder="Share an update with your followers..."
              rows={3}
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
              data-testid="page-post-input"
            />
            <button 
              className="btn btn-primary" 
              style={{ marginTop: 10 }}
              onClick={createPost}
              disabled={posting || !newPost.trim()}
              data-testid="page-post-btn"
            >
              {posting ? 'Posting...' : 'Post Update'}
            </button>
          </div>
        )}

        {/* Page Posts */}
        <h3 style={{ color: '#ec4899', marginBottom: 15 }}>Updates</h3>
        {selectedPage.posts?.length === 0 ? (
          <p style={{ color: '#a1a1aa', textAlign: 'center', padding: 30 }}>
            No updates yet.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
            {selectedPage.posts?.map(post => (
              <div key={post.id} style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(236, 72, 153, 0.2)'
              }}>
                <p style={{ color: '#e5e7eb', marginBottom: 15, lineHeight: 1.6 }}>{post.content}</p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                    {new Date(post.created_at).toLocaleString()}
                  </span>
                  <button style={{
                    background: post.is_liked ? 'rgba(236, 72, 153, 0.2)' : 'transparent',
                    border: 'none',
                    color: post.is_liked ? '#ec4899' : '#a1a1aa',
                    cursor: 'pointer',
                    padding: '6px 12px',
                    borderRadius: 20,
                    fontSize: '0.85rem'
                  }}>
                    ❤️ {post.likes || 0}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Pages List View
  return (
    <div>
      <button 
        className="btn btn-primary" 
        style={{ marginBottom: 20 }}
        onClick={() => setShowCreateModal(true)}
        data-testid="create-page-btn"
      >
        <Icons.Plus /> Create Page
      </button>

      {pages.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: '3rem', marginBottom: 15 }}>📄</div>
          <p style={{ color: '#a1a1aa' }}>No pages yet. Create one to share your content!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {pages.map(page => (
            <div 
              key={page.id} 
              style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(236, 72, 153, 0.3)',
                cursor: 'pointer'
              }}
              onClick={() => fetchPageDetails(page.id)}
              data-testid={`page-card-${page.id}`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 10 }}>
                <h3 style={{ color: '#ec4899', margin: 0 }}>{page.name}</h3>
                <span style={{ 
                  fontSize: '0.7rem', 
                  padding: '3px 8px', 
                  borderRadius: 10,
                  background: 'rgba(59, 130, 246, 0.2)',
                  color: '#3b82f6'
                }}>
                  {page.category}
                </span>
              </div>
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 15 }}>
                {page.description || 'No description'}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>
                  ❤️ {page.likes || 0} likes
                </span>
                <span style={{ color: '#ec4899', fontSize: '0.8rem' }}>View →</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Page Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: 20, color: '#ec4899' }}>Create New Page</h3>
            <input
              type="text"
              placeholder="Page Name"
              className="input"
              value={newPage.name}
              onChange={e => setNewPage({...newPage, name: e.target.value})}
              style={{ marginBottom: 15 }}
              data-testid="page-name-input"
            />
            <textarea
              placeholder="Description (optional)"
              className="input"
              value={newPage.description}
              onChange={e => setNewPage({...newPage, description: e.target.value})}
              rows={3}
              style={{ marginBottom: 15 }}
              data-testid="page-description-input"
            />
            <select
              className="input"
              value={newPage.category}
              onChange={e => setNewPage({...newPage, category: e.target.value})}
              style={{ marginBottom: 20 }}
              data-testid="page-category-input"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={createPage} data-testid="submit-page-btn">Create Page</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PagesSection;
