/**
 * Personal Report Creator Component
 * Allows users to create Personal Reports (Organic) with topic, content, image, and location
 */
import React, { useState, useEffect } from 'react';
import { API } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';

const PersonalReportCreator = ({ onReportCreated, showToast, categories = [] }) => {
  const { token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState({
    title: '',
    content: '',
    topic: '',
    location_name: '',
    latitude: null,
    longitude: null,
    category_ids: []
  });
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  
  // Auto-detect location
  const detectLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setReport(prev => ({
            ...prev,
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          }));
          showToast?.('Location detected!', 'success');
        },
        (error) => {
          console.error('Geolocation error:', error);
          showToast?.('Could not detect location', 'error');
        }
      );
    }
  };
  
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };
  
  const handleSubmit = async () => {
    if (!report.title || !report.content) {
      showToast?.('Please provide a title and content', 'error');
      return;
    }
    
    setLoading(true);
    
    try {
      // Create the report
      const res = await fetch(`${API}/personal-reports`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(report)
      });
      
      if (!res.ok) {
        throw new Error('Failed to create report');
      }
      
      const data = await res.json();
      const reportId = data.report_id;
      
      // Upload image if provided
      if (imageFile && reportId) {
        const formData = new FormData();
        formData.append('file', imageFile);
        
        await fetch(`${API}/personal-reports/${reportId}/image`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData
        });
      }
      
      showToast?.('Personal Report created successfully!', 'success');
      setIsOpen(false);
      setReport({
        title: '',
        content: '',
        topic: '',
        location_name: '',
        latitude: null,
        longitude: null,
        category_ids: []
      });
      setImageFile(null);
      setImagePreview(null);
      onReportCreated?.();
      
    } catch (err) {
      console.error('Error creating report:', err);
      showToast?.('Failed to create report', 'error');
    }
    
    setLoading(false);
  };
  
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        data-testid="create-personal-report-btn"
        className="btn btn-primary"
        style={{
          background: 'linear-gradient(135deg, #10b981, #059669)',
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}
      >
        ✍️ Create Personal Report
      </button>
    );
  }
  
  return (
    <div 
      data-testid="personal-report-creator"
      style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.05))',
        borderRadius: 15,
        padding: 25,
        border: '1px solid rgba(16, 185, 129, 0.3)',
        marginBottom: 20
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ color: '#10b981', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          ✍️ Create Personal Report (Organic)
        </h3>
        <button
          onClick={() => setIsOpen(false)}
          style={{
            background: 'rgba(239, 68, 68, 0.2)',
            border: 'none',
            color: '#f87171',
            padding: '6px 12px',
            borderRadius: 8,
            cursor: 'pointer'
          }}
        >
          ✕ Cancel
        </button>
      </div>
      
      <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 20 }}>
        Share your first-hand experiences, observations, and insights with the community.
      </p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        {/* Title */}
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            Title *
          </label>
          <input
            type="text"
            className="input"
            placeholder="Give your report a compelling title..."
            value={report.title}
            onChange={(e) => setReport({ ...report, title: e.target.value })}
            data-testid="report-title-input"
          />
        </div>
        
        {/* Topic */}
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            Topic/Category
          </label>
          <input
            type="text"
            className="input"
            placeholder="What is this report about?"
            value={report.topic}
            onChange={(e) => setReport({ ...report, topic: e.target.value })}
          />
        </div>
        
        {/* Content */}
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            Content *
          </label>
          <textarea
            className="input"
            rows={6}
            placeholder="Share your experience, observations, and insights..."
            value={report.content}
            onChange={(e) => setReport({ ...report, content: e.target.value })}
            data-testid="report-content-input"
            style={{ resize: 'vertical' }}
          />
          <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 5 }}>
            {report.content.length} characters • {report.content.split(' ').filter(w => w).length} words
          </p>
        </div>
        
        {/* Location */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 10 }}>
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
              📍 Location Name
            </label>
            <input
              type="text"
              className="input"
              placeholder="e.g., Brunswick, Maine"
              value={report.location_name}
              onChange={(e) => setReport({ ...report, location_name: e.target.value })}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
            <button
              onClick={detectLocation}
              className="btn btn-secondary"
              style={{ height: 42 }}
              title="Detect my current location"
            >
              🎯 Auto-Detect
            </button>
          </div>
        </div>
        
        {report.latitude && report.longitude && (
          <div style={{ background: 'rgba(0,0,0,0.2)', padding: 10, borderRadius: 8, fontSize: '0.8rem', color: '#a1a1aa' }}>
            📍 Coordinates: {report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}
          </div>
        )}
        
        {/* Image Upload */}
        <div>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
            📷 Add Image (optional)
          </label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            onChange={handleImageChange}
            style={{ color: '#a1a1aa' }}
          />
          {imagePreview && (
            <div style={{ marginTop: 10 }}>
              <img 
                src={imagePreview} 
                alt="Preview" 
                style={{ maxWidth: 200, maxHeight: 150, borderRadius: 8, border: '1px solid rgba(124, 58, 237, 0.3)' }}
              />
            </div>
          )}
        </div>
        
        {/* Category Selection */}
        {categories.length > 0 && (
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>
              📁 Add to Categories (optional)
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, maxHeight: 150, overflowY: 'auto' }}>
              {categories.slice(0, 20).map(cat => (
                <label 
                  key={cat.id} 
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 6,
                    background: report.category_ids.includes(cat.id) ? 'rgba(16, 185, 129, 0.2)' : 'rgba(0,0,0,0.2)',
                    padding: '4px 10px',
                    borderRadius: 20,
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    color: report.category_ids.includes(cat.id) ? '#10b981' : '#a1a1aa'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={report.category_ids.includes(cat.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setReport({ ...report, category_ids: [...report.category_ids, cat.id] });
                      } else {
                        setReport({ ...report, category_ids: report.category_ids.filter(id => id !== cat.id) });
                      }
                    }}
                    style={{ accentColor: '#10b981' }}
                  />
                  {cat.name}
                </label>
              ))}
            </div>
          </div>
        )}
        
        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={loading || !report.title || !report.content}
          className="btn btn-primary"
          data-testid="submit-report-btn"
          style={{
            marginTop: 10,
            padding: 15,
            fontSize: '1rem',
            background: loading || !report.title || !report.content 
              ? 'rgba(124, 58, 237, 0.3)' 
              : 'linear-gradient(135deg, #10b981, #059669)'
          }}
        >
          {loading ? '⏳ Creating Report...' : '✨ Publish Personal Report'}
        </button>
      </div>
    </div>
  );
};

export default PersonalReportCreator;
