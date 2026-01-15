import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import ReactMarkdown from 'react-markdown';
import YouTubePlayer, { VideoUrlInput } from '../components/shared/YouTubePlayer';

const TutorialsPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [tutorials, setTutorials] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedTutorial, setSelectedTutorial] = useState(null);
  const [userProgress, setUserProgress] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTutorials();
    if (token) {
      fetchUserProgress();
    }
  }, [token]);

  const fetchTutorials = async () => {
    try {
      const res = await fetch(`${API}/tutorials`);
      if (res.ok) {
        const data = await res.json();
        setTutorials(data.tutorials || []);
        setCategories(data.categories || []);
      }
    } catch (e) {
      console.error('Failed to fetch tutorials:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserProgress = async () => {
    try {
      const res = await fetch(`${API}/tutorials/user/progress`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUserProgress(data.progress || {});
      }
    } catch (e) {
      console.error('Failed to fetch progress:', e);
    }
  };

  const filteredTutorials = selectedCategory
    ? tutorials.filter(t => t.category === selectedCategory)
    : tutorials;

  const getProgressForTutorial = (tutorialId) => {
    return userProgress[tutorialId] || 0;
  };

  const markAsComplete = async (tutorialId) => {
    if (!token) return;
    try {
      await fetch(`${API}/tutorials/${tutorialId}/progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ progress: 100 })
      });
      setUserProgress({ ...userProgress, [tutorialId]: 100 });
      showToast('🎉 Tutorial completed!', 'success');
    } catch (e) {
      console.error('Failed to mark complete:', e);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <div style={{ fontSize: '3rem', marginBottom: 20 }}>📚</div>
        <p style={{ color: '#a1a1aa' }}>Loading tutorials...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 0' }}>
      {/* Hero Section */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(59, 130, 246, 0.2) 100%)',
        borderRadius: 20,
        padding: 30,
        marginBottom: 30,
        border: '1px solid rgba(139, 92, 246, 0.3)'
      }}>
        <h1 style={{ 
          fontSize: '2.5rem', 
          fontWeight: 800, 
          marginBottom: 10,
          background: 'linear-gradient(135deg, #fff 0%, #a78bfa 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          📚 Tutorials & Guides
        </h1>
        <p style={{ color: '#a1a1aa', fontSize: '1.1rem', marginBottom: 15 }}>
          Learn InfoPilot Explorer like a pro! Read our comprehensive guides and become a search master.
        </p>
        {user && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.2)',
            padding: '10px 20px',
            borderRadius: 10,
            display: 'inline-block'
          }}>
            <span style={{ color: '#10b981', fontWeight: 600 }}>
              Your Progress: {Object.values(userProgress).filter(p => p >= 100).length} / {tutorials.length} completed
            </span>
          </div>
        )}
      </div>

      {/* Category Filter */}
      <div style={{
        display: 'flex',
        gap: 10,
        marginBottom: 25,
        flexWrap: 'wrap'
      }}>
        <button
          onClick={() => { setSelectedCategory(null); setSelectedTutorial(null); }}
          style={{
            padding: '10px 20px',
            borderRadius: 25,
            border: 'none',
            background: !selectedCategory 
              ? 'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)' 
              : 'rgba(255,255,255,0.1)',
            color: '#fff',
            cursor: 'pointer',
            fontWeight: 600
          }}
        >
          All Tutorials
        </button>
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => { setSelectedCategory(cat.id); setSelectedTutorial(null); }}
            style={{
              padding: '10px 20px',
              borderRadius: 25,
              border: 'none',
              background: selectedCategory === cat.id 
                ? `linear-gradient(135deg, ${cat.color} 0%, ${cat.color}99 100%)`
                : 'rgba(255,255,255,0.1)',
              color: '#fff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            <span>{cat.icon}</span>
            <span>{cat.name}</span>
          </button>
        ))}
      </div>

      {/* Selected Tutorial Content */}
      {selectedTutorial && (
        <div style={{
          background: 'rgba(30, 20, 50, 0.8)',
          borderRadius: 20,
          padding: 30,
          marginBottom: 30,
          border: '1px solid rgba(139, 92, 246, 0.3)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                {categories.find(c => c.id === selectedTutorial.category) && (
                  <span style={{
                    background: `${categories.find(c => c.id === selectedTutorial.category).color}20`,
                    color: categories.find(c => c.id === selectedTutorial.category).color,
                    padding: '4px 12px',
                    borderRadius: 15,
                    fontSize: '0.8rem'
                  }}>
                    {categories.find(c => c.id === selectedTutorial.category).icon}{' '}
                    {categories.find(c => c.id === selectedTutorial.category).name}
                  </span>
                )}
                <span style={{ color: '#71717a', fontSize: '0.85rem' }}>
                  {selectedTutorial.duration}
                </span>
              </div>
              <h2 style={{ color: '#f472b6', marginBottom: 8 }}>{selectedTutorial.title}</h2>
              <p style={{ color: '#a1a1aa' }}>{selectedTutorial.description}</p>
            </div>
            <button
              onClick={() => setSelectedTutorial(null)}
              style={{
                background: 'rgba(255,255,255,0.1)',
                border: 'none',
                color: '#fff',
                padding: '8px 16px',
                borderRadius: 8,
                cursor: 'pointer'
              }}
            >
              ✕ Close
            </button>
          </div>

          {/* Admin: Video URL Management */}
          {user?.is_admin && (
            <VideoUrlInput
              tutorialId={selectedTutorial.id}
              currentVideoUrl={selectedTutorial.video_url}
              token={token}
              onUpdate={(data) => {
                if (data) {
                  setSelectedTutorial({ ...selectedTutorial, video_url: data.video_url, video_id: data.video_id });
                  const updatedTutorials = tutorials.map(t => 
                    t.id === selectedTutorial.id ? { ...t, video_url: data.video_url, video_id: data.video_id } : t
                  );
                  setTutorials(updatedTutorials);
                } else {
                  setSelectedTutorial({ ...selectedTutorial, video_url: null, video_id: null });
                  const updatedTutorials = tutorials.map(t => 
                    t.id === selectedTutorial.id ? { ...t, video_url: null, video_id: null } : t
                  );
                  setTutorials(updatedTutorials);
                }
                showToast('Video updated!', 'success');
              }}
            />
          )}

          {/* YouTube Video Player */}
          {(selectedTutorial.video_url || selectedTutorial.video_id) ? (
            <div style={{ marginBottom: 20 }}>
              <YouTubePlayer
                videoId={selectedTutorial.video_id}
                videoUrl={selectedTutorial.video_url}
                title={selectedTutorial.title}
              />
            </div>
          ) : (
            /* Tutorial Image (fallback when no video) */
            selectedTutorial.image_url && (
              <div style={{
                borderRadius: 12,
                overflow: 'hidden',
                marginBottom: 20,
                maxHeight: 300
              }}>
                <img 
                  src={selectedTutorial.image_url} 
                  alt={selectedTutorial.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
            )
          )}
          
          {/* Tutorial Content */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: 12,
            padding: 25,
            color: '#e2e8f0',
            lineHeight: 1.8
          }}>
            <div className="tutorial-content" style={{
              fontSize: '1rem'
            }}>
              {/* Render markdown content */}
              <ReactMarkdown
                components={{
                  h2: ({node, ...props}) => <h2 style={{ color: '#a78bfa', marginTop: 20, marginBottom: 10 }} {...props} />,
                  h3: ({node, ...props}) => <h3 style={{ color: '#f472b6', marginTop: 15, marginBottom: 8 }} {...props} />,
                  p: ({node, ...props}) => <p style={{ marginBottom: 12 }} {...props} />,
                  ul: ({node, ...props}) => <ul style={{ paddingLeft: 25, marginBottom: 15 }} {...props} />,
                  li: ({node, ...props}) => <li style={{ marginBottom: 6 }} {...props} />,
                  code: ({node, inline, ...props}) => 
                    inline 
                      ? <code style={{ background: 'rgba(124, 58, 237, 0.3)', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace' }} {...props} />
                      : <pre style={{ background: 'rgba(0,0,0,0.5)', padding: 15, borderRadius: 8, overflow: 'auto', marginBottom: 15 }}><code {...props} /></pre>,
                  strong: ({node, ...props}) => <strong style={{ color: '#10b981' }} {...props} />,
                }}
              >
                {selectedTutorial.content}
              </ReactMarkdown>
            </div>
          </div>
          
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginTop: 20,
            padding: '15px 0',
            borderTop: '1px solid rgba(255,255,255,0.1)'
          }}>
            <span style={{ color: '#71717a' }}>
              {selectedTutorial.duration}
            </span>
            {user && (
              <button
                onClick={() => markAsComplete(selectedTutorial.id)}
                disabled={getProgressForTutorial(selectedTutorial.id) >= 100}
                style={{
                  padding: '10px 20px',
                  borderRadius: 8,
                  border: 'none',
                  background: getProgressForTutorial(selectedTutorial.id) >= 100 
                    ? 'rgba(16, 185, 129, 0.3)' 
                    : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: '#fff',
                  cursor: getProgressForTutorial(selectedTutorial.id) >= 100 ? 'default' : 'pointer',
                  fontWeight: 600
                }}
              >
                {getProgressForTutorial(selectedTutorial.id) >= 100 ? '✓ Completed' : 'Mark as Complete'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Tutorials Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: 20
      }}>
        {filteredTutorials.map(tutorial => {
          const progress = getProgressForTutorial(tutorial.id);
          const category = categories.find(c => c.id === tutorial.category);
          
          return (
            <div
              key={tutorial.id}
              onClick={() => setSelectedTutorial(tutorial)}
              data-testid={`tutorial-${tutorial.id}`}
              style={{
                background: 'rgba(30, 20, 50, 0.6)',
                borderRadius: 16,
                overflow: 'hidden',
                border: progress >= 100 
                  ? '2px solid #10b981' 
                  : '1px solid rgba(139, 92, 246, 0.3)',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-5px)';
                e.currentTarget.style.boxShadow = '0 10px 30px rgba(124, 58, 237, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              {/* Thumbnail */}
              <div style={{
                position: 'relative',
                paddingBottom: '56.25%',
                background: tutorial.image_url 
                  ? `url(${tutorial.image_url}) center/cover`
                  : `linear-gradient(135deg, ${category?.color || '#7c3aed'} 0%, ${category?.color || '#7c3aed'}66 100%)`
              }}>
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'rgba(0,0,0,0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <div style={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    background: 'rgba(255,255,255,0.9)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem'
                  }}>
                    📖
                  </div>
                </div>
                
                {/* Duration badge */}
                <span style={{
                  position: 'absolute',
                  bottom: 10,
                  right: 10,
                  background: 'rgba(0,0,0,0.8)',
                  padding: '4px 8px',
                  borderRadius: 4,
                  fontSize: '0.75rem',
                  color: '#fff'
                }}>
                  {tutorial.duration}
                </span>
                
                {/* Completed badge */}
                {progress >= 100 && (
                  <span style={{
                    position: 'absolute',
                    top: 10,
                    right: 10,
                    background: '#10b981',
                    padding: '4px 10px',
                    borderRadius: 4,
                    fontSize: '0.75rem',
                    color: '#fff',
                    fontWeight: 600
                  }}>
                    ✓ Completed
                  </span>
                )}
              </div>
              
              {/* Content */}
              <div style={{ padding: 15 }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 8
                }}>
                  <span style={{
                    background: category ? `${category.color}20` : 'rgba(124, 58, 237, 0.2)',
                    color: category?.color || '#a78bfa',
                    padding: '3px 8px',
                    borderRadius: 12,
                    fontSize: '0.7rem'
                  }}>
                    {category?.icon} {category?.name || tutorial.category}
                  </span>
                </div>
                
                <h3 style={{ color: '#f472b6', fontSize: '1rem', marginBottom: 8 }}>
                  {tutorial.title}
                </h3>
                
                <p style={{ 
                  color: '#a1a1aa', 
                  fontSize: '0.85rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical'
                }}>
                  {tutorial.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {filteredTutorials.length === 0 && (
        <div style={{ textAlign: 'center', padding: 60, color: '#a1a1aa' }}>
          <div style={{ fontSize: '3rem', marginBottom: 15 }}>📚</div>
          <p>No tutorials found in this category.</p>
        </div>
      )}
    </div>
  );
};

export default TutorialsPage;
