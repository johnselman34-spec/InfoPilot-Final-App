/**
 * Personal Reports Page
 * Allows users to create, edit, and manage their organic personal reports
 * Each report can have a topic, content, up to 3 images (max 6.9MB each), and location
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';

const PersonalReportsPage = ({ showToast, onBack }) => {
  const { token, user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingReport, setEditingReport] = useState(null);
  const [categories, setCategories] = useState([]);
  
  // Form state
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [content, setContent] = useState('');
  const [location, setLocation] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [images, setImages] = useState([]);  // Array of files
  const [imagePreviews, setImagePreviews] = useState([]);  // Array of preview URLs
  const [uploadingImage, setUploadingImage] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Fetch user's personal reports
  const fetchReports = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/personal-reports`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setReports(data.reports || []);
      }
    } catch (e) {
      console.error('Failed to fetch reports:', e);
    } finally {
      setLoading(false);
    }
  }, [token]);
  
  // Fetch categories for assignment
  const fetchCategories = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data);
      }
    } catch (e) {
      console.error('Failed to fetch categories:', e);
    }
  }, [token]);
  
  useEffect(() => {
    fetchReports();
    fetchCategories();
  }, [fetchReports, fetchCategories]);
  
  // Auto-detect location
  const detectLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          try {
            // Try to reverse geocode
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`);
            if (res.ok) {
              const data = await res.json();
              const locationStr = data.address?.city || data.address?.town || data.address?.county || `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
              setLocation(`${locationStr}, ${data.address?.country || ''}`);
              showToast('Location detected!', 'success');
            }
          } catch (e) {
            setLocation(`${latitude.toFixed(4)}, ${longitude.toFixed(4)}`);
          }
        },
        () => showToast('Could not detect location', 'error')
      );
    }
  };
  
  // Handle image selection - supports up to 3 images
  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    const remainingSlots = 3 - imagePreviews.length;
    
    if (files.length > remainingSlots) {
      showToast(`You can only add ${remainingSlots} more image(s). Max 3 per report.`, 'error');
      return;
    }
    
    const validFiles = [];
    const newPreviews = [];
    
    for (const file of files) {
      if (file.size > 6.9 * 1024 * 1024) {
        showToast(`Image "${file.name}" exceeds 6.9MB limit`, 'error');
        continue;
      }
      validFiles.push(file);
      newPreviews.push(URL.createObjectURL(file));
    }
    
    if (validFiles.length > 0) {
      setImages(prev => [...prev, ...validFiles]);
      setImagePreviews(prev => [...prev, ...newPreviews]);
    }
  };
  
  // Remove a specific image by index
  const removeImage = (index) => {
    setImages(prev => prev.filter((_, i) => i !== index));
    setImagePreviews(prev => {
      URL.revokeObjectURL(prev[index]);  // Clean up
      return prev.filter((_, i) => i !== index);
    });
  };
  
  // Create or update report
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      showToast('Title and content are required', 'error');
      return;
    }
    
    setSubmitting(true);
    try {
      const url = editingReport 
        ? `${API}/api/personal-reports/${editingReport.id}`
        : `${API}/api/personal-reports`;
      
      const method = editingReport ? 'PUT' : 'POST';
      
      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          title,
          topic,
          content,
          location,
          category_id: categoryId || null
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        
        // Upload all images (up to 3)
        if (images.length > 0 && data.report?.id) {
          setUploadingImage(true);
          for (const img of images) {
            const formData = new FormData();
            formData.append('file', img);
            try {
              await fetch(`${API}/api/personal-reports/${data.report.id}/image`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` },
                body: formData
              });
            } catch (imgError) {
              console.error('Failed to upload image:', imgError);
            }
          }
          setUploadingImage(false);
        }
        
        showToast(editingReport ? 'Report updated!' : 'Report created!', 'success');
        resetForm();
        fetchReports();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Failed to save report', 'error');
      }
    } catch (e) {
      showToast('Failed to save report', 'error');
    } finally {
      setSubmitting(false);
    }
  };
  
  // Delete report
  const handleDelete = async (reportId) => {
    if (!window.confirm('Delete this report? This cannot be undone.')) return;
    
    try {
      const res = await fetch(`${API}/api/personal-reports/${reportId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast('Report deleted!', 'success');
        fetchReports();
      } else {
        showToast('Failed to delete report', 'error');
      }
    } catch (e) {
      showToast('Failed to delete report', 'error');
    }
  };
  
  // Edit report
  const handleEdit = (report) => {
    setEditingReport(report);
    setTitle(report.title || '');
    setTopic(report.topic || '');
    setContent(report.content || '');
    setLocation(report.location || '');
    setCategoryId(report.category_id || '');
    // Support both legacy single image and new multiple images
    const existingImages = report.image_urls || (report.image_url ? [report.image_url] : []);
    setImagePreviews(existingImages);
    setImages([]);  // Don't re-upload existing images
    setShowCreateForm(true);
  };
  
  // Reset form
  const resetForm = () => {
    setTitle('');
    setTopic('');
    setContent('');
    setLocation('');
    setCategoryId('');
    setImages([]);
    imagePreviews.forEach(url => {
      if (url.startsWith('blob:')) URL.revokeObjectURL(url);
    });
    setImagePreviews([]);
    setEditingReport(null);
    setShowCreateForm(false);
  };

  return (
    <div className="card" data-testid="personal-reports-page">
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
        padding: '25px 30px',
        borderRadius: '12px 12px 0 0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 15
      }}>
        <div>
          <h2 style={{ color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            📝 Personal Reports (Organic)
          </h2>
          <p style={{ color: '#e9d5ff', margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Share your knowledge, experiences, and insights with the world!
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {onBack && (
            <button 
              className="btn btn-secondary" 
              onClick={onBack}
              data-testid="back-from-reports-btn"
            >
              ← Back
            </button>
          )}
          <button 
            className="btn btn-primary" 
            onClick={() => setShowCreateForm(true)}
            style={{ background: '#fff', color: '#7c3aed' }}
            data-testid="create-personal-report-btn"
          >
            ✨ Create New Report
          </button>
        </div>
      </div>
      
      {/* Create/Edit Form */}
      {showCreateForm && (
        <div style={{
          background: 'rgba(124, 58, 237, 0.1)',
          padding: 25,
          borderBottom: '1px solid rgba(124, 58, 237, 0.3)'
        }}>
          <h3 style={{ color: '#f472b6', marginTop: 0, marginBottom: 20 }}>
            {editingReport ? '✏️ Edit Report' : '✨ Create New Report'}
          </h3>
          
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gap: 15 }}>
              {/* Title */}
              <div>
                <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5, display: 'block' }}>
                  Title *
                </label>
                <input
                  type="text"
                  className="input-field"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Give your report a catchy title..."
                  required
                  data-testid="report-title-input"
                />
              </div>
              
              {/* Topic */}
              <div>
                <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5, display: 'block' }}>
                  Topic
                </label>
                <input
                  type="text"
                  className="input-field"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="What's this report about? (e.g., Technology, Travel, Health)"
                  data-testid="report-topic-input"
                />
              </div>
              
              {/* Content */}
              <div>
                <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5, display: 'block' }}>
                  Content *
                </label>
                <textarea
                  className="input-field"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Share your knowledge, experience, or insights..."
                  rows={8}
                  required
                  style={{ resize: 'vertical', minHeight: 150 }}
                  data-testid="report-content-input"
                />
                <div style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 5, textAlign: 'right' }}>
                  {content.length} characters
                </div>
              </div>
              
              {/* Location */}
              <div>
                <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5, display: 'block' }}>
                  Location
                </label>
                <div style={{ display: 'flex', gap: 10 }}>
                  <input
                    type="text"
                    className="input-field"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="Where is this report from?"
                    style={{ flex: 1 }}
                    data-testid="report-location-input"
                  />
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={detectLocation}
                    style={{ whiteSpace: 'nowrap' }}
                    data-testid="detect-location-btn"
                  >
                    📍 Auto-Detect
                  </button>
                </div>
              </div>
              
              {/* Category */}
              <div>
                <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5, display: 'block' }}>
                  Category
                </label>
                <select
                  className="input-field"
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  data-testid="report-category-select"
                >
                  <option value="">-- Select a category (optional) --</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              
              {/* Image */}
              <div>
                <label style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 5, display: 'block' }}>
                  Image (1 per report, max 6.9MB)
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  style={{ 
                    background: 'rgba(30, 20, 50, 0.5)', 
                    border: '1px solid rgba(124, 58, 237, 0.3)',
                    borderRadius: 8,
                    padding: 10,
                    color: '#e5e7eb',
                    width: '100%'
                  }}
                  data-testid="report-image-input"
                />
                {imagePreview && (
                  <div style={{ marginTop: 10 }}>
                    <img 
                      src={imagePreview} 
                      alt="Preview" 
                      style={{ 
                        maxWidth: 200, 
                        maxHeight: 150, 
                        borderRadius: 8,
                        border: '2px solid rgba(124, 58, 237, 0.3)'
                      }} 
                    />
                    <button
                      type="button"
                      onClick={() => { setImage(null); setImagePreview(null); }}
                      style={{
                        background: 'rgba(239, 68, 68, 0.2)',
                        border: '1px solid #ef4444',
                        color: '#ef4444',
                        padding: '4px 10px',
                        borderRadius: 6,
                        fontSize: '0.75rem',
                        marginLeft: 10,
                        cursor: 'pointer'
                      }}
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            {/* Form Actions */}
            <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={submitting}
                data-testid="save-report-btn"
              >
                {submitting ? '⏳ Saving...' : editingReport ? '💾 Update Report' : '✨ Create Report'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={resetForm}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
      
      {/* Reports List */}
      <div style={{ padding: 20 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
            ⏳ Loading your reports...
          </div>
        ) : reports.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: 60, 
            background: 'rgba(124, 58, 237, 0.1)',
            borderRadius: 12
          }}>
            <div style={{ fontSize: '4rem', marginBottom: 15 }}>📝</div>
            <h3 style={{ color: '#f472b6', marginBottom: 10 }}>No Reports Yet!</h3>
            <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
              Share your knowledge and experiences with the InfoPilot community!
            </p>
            <button 
              className="btn btn-primary"
              onClick={() => setShowCreateForm(true)}
            >
              ✨ Create Your First Report
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 15 }}>
            {reports.map(report => (
              <div 
                key={report.id}
                style={{
                  background: 'rgba(30, 20, 50, 0.5)',
                  borderRadius: 12,
                  padding: 20,
                  border: '1px solid rgba(124, 58, 237, 0.3)'
                }}
                data-testid={`report-card-${report.id}`}
              >
                <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                  {/* Image */}
                  {report.image_url && (
                    <img 
                      src={report.image_url} 
                      alt={report.title}
                      style={{
                        width: 150,
                        height: 100,
                        objectFit: 'cover',
                        borderRadius: 8
                      }}
                    />
                  )}
                  
                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <h4 style={{ color: '#f472b6', margin: '0 0 8px 0' }}>
                      {report.title}
                    </h4>
                    
                    {report.topic && (
                      <span style={{
                        background: 'rgba(124, 58, 237, 0.2)',
                        color: '#a78bfa',
                        padding: '3px 10px',
                        borderRadius: 15,
                        fontSize: '0.75rem',
                        marginRight: 8
                      }}>
                        {report.topic}
                      </span>
                    )}
                    
                    {report.location && (
                      <span style={{
                        color: '#71717a',
                        fontSize: '0.8rem'
                      }}>
                        📍 {report.location}
                      </span>
                    )}
                    
                    <p style={{ 
                      color: '#d1d5db', 
                      fontSize: '0.9rem', 
                      marginTop: 10,
                      lineHeight: 1.6
                    }}>
                      {report.content?.substring(0, 200)}
                      {report.content?.length > 200 && '...'}
                    </p>
                    
                    <div style={{ 
                      display: 'flex', 
                      gap: 8, 
                      marginTop: 15,
                      alignItems: 'center',
                      flexWrap: 'wrap'
                    }}>
                      <span style={{ 
                        color: '#71717a', 
                        fontSize: '0.75rem',
                        background: 'rgba(16, 185, 129, 0.2)',
                        padding: '3px 8px',
                        borderRadius: 4
                      }}>
                        Personal Report (Organic)
                      </span>
                      <span style={{ color: '#71717a', fontSize: '0.75rem' }}>
                        {new Date(report.created_at).toLocaleDateString()}
                      </span>
                      
                      <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                        <button
                          className="btn btn-secondary"
                          onClick={() => handleEdit(report)}
                          style={{ padding: '5px 12px', fontSize: '0.8rem' }}
                          data-testid={`edit-report-${report.id}`}
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDelete(report.id)}
                          style={{
                            background: 'rgba(239, 68, 68, 0.2)',
                            border: '1px solid rgba(239, 68, 68, 0.3)',
                            color: '#ef4444',
                            padding: '5px 12px',
                            borderRadius: 6,
                            fontSize: '0.8rem',
                            cursor: 'pointer'
                          }}
                          data-testid={`delete-report-${report.id}`}
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PersonalReportsPage;
