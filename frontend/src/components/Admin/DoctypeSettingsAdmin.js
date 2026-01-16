/**
 * Document Type Settings Admin Panel
 * UI for managing document type classification protocols (InfoJet 2.0)
 */
import React, { useState, useEffect, useCallback } from 'react';
import { API } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';

const DoctypeSettingsAdmin = ({ showToast }) => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({});
  const [documentTypes, setDocumentTypes] = useState([]);
  const [expandedType, setExpandedType] = useState(null);
  
  const fetchSettings = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    
    try {
      const res = await fetch(`${API}/admin/doctype-settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setSettings(data.settings);
        setDocumentTypes(data.document_types || []);
      }
    } catch (err) {
      console.error('Failed to fetch doctype settings:', err);
      showToast?.('Failed to load document type settings', 'error');
    }
    
    setLoading(false);
  }, [token, showToast]);
  
  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);
  
  const saveSettings = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API}/admin/doctype-settings`, {
        method: 'PUT',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      });
      
      if (res.ok) {
        showToast?.('Document type settings saved!', 'success');
      } else {
        const data = await res.json();
        showToast?.(data.detail || 'Failed to save', 'error');
      }
    } catch (err) {
      showToast?.('Failed to save settings', 'error');
    }
    setSaving(false);
  };
  
  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };
  
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <div style={{ fontSize: '2rem', marginBottom: 10 }}>⏳</div>
        <p style={{ color: '#a1a1aa' }}>Loading document type settings...</p>
      </div>
    );
  }
  
  return (
    <div data-testid="doctype-settings-admin">
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(59, 130, 246, 0.1))',
        borderRadius: 15,
        padding: 20,
        marginBottom: 25,
        border: '1px solid rgba(16, 185, 129, 0.3)'
      }}>
        <h3 style={{ color: '#10b981', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
          📄 InfoJet 2.0 Document Classification
        </h3>
        <p style={{ color: '#a1a1aa', margin: 0, fontSize: '0.9rem' }}>
          Configure how the Internet Robot classifies documents. Each document type has an InfoJet 2.0 protocol
          that determines how search results are categorized automatically.
        </p>
        
        {/* Auto-Categorize Toggle */}
        <div style={{ 
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: 15, marginTop: 15
        }}>
          <div>
            <span style={{ color: '#fff', fontWeight: 600 }}>Auto-Categorize by Document Type</span>
            <p style={{ color: '#71717a', fontSize: '0.8rem', margin: '5px 0 0 0' }}>
              Automatically classify search results into document types
            </p>
          </div>
          <label style={{ cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.doctype_auto_categorize !== false}
              onChange={(e) => updateSetting('doctype_auto_categorize', e.target.checked)}
              style={{ width: 20, height: 20, accentColor: '#10b981' }}
            />
          </label>
        </div>
      </div>
      
      {/* Document Types Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
        
        {/* PhD Informative */}
        <DocumentTypeCard
          title="PhD Informative"
          icon="🎓"
          color="#8b5cf6"
          description="Academic content by credentialed professionals (Ph.D., D.Phil., Dr.)"
          expanded={expandedType === 'phd'}
          onToggle={() => setExpandedType(expandedType === 'phd' ? null : 'phd')}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15, marginTop: 15 }}>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                PhD Protocol (Keywords)
              </label>
              <input
                type="text"
                value={settings.doctype_phd_protocol || ''}
                onChange={(e) => updateSetting('doctype_phd_protocol', e.target.value)}
                className="input"
                placeholder="(Ph.D. or PhD or D.Phil. or Dr.)"
                style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                Min Keyword Count
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={settings.doctype_phd_keyword_count || 3}
                onChange={(e) => updateSetting('doctype_phd_keyword_count', parseInt(e.target.value))}
                className="input"
              />
            </div>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                Min Word Count
              </label>
              <input
                type="number"
                min="100"
                max="10000"
                value={settings.doctype_phd_min_words || 1500}
                onChange={(e) => updateSetting('doctype_phd_min_words', parseInt(e.target.value))}
                className="input"
              />
            </div>
          </div>
          <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
            Rule: Must FIRST be classified as Informative, THEN contain PhD keywords {settings.doctype_phd_keyword_count || 3}+ times, 
            AND have {settings.doctype_phd_min_words || 1500}+ words.
          </p>
        </DocumentTypeCard>
        
        {/* Informative */}
        <DocumentTypeCard
          title="Informative"
          icon="📚"
          color="#3b82f6"
          description="Educational content meeting informative protocol criteria"
          expanded={expandedType === 'informative'}
          onToggle={() => setExpandedType(expandedType === 'informative' ? null : 'informative')}
        >
          <div style={{ marginTop: 15 }}>
            <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
              Informative Protocol (InfoJet 2.0)
            </label>
            <textarea
              value={settings.doctype_informative_protocol || ''}
              onChange={(e) => updateSetting('doctype_informative_protocol', e.target.value)}
              className="input"
              rows={3}
              placeholder="(there are or there is) & (may have or might have) & ..."
              style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
            />
            <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 5 }}>
              Format: (word1 or word2) & (word3 or word4) - ALL groups must match
            </p>
          </div>
        </DocumentTypeCard>
        
        {/* News Article */}
        <DocumentTypeCard
          title="News Article"
          icon="📰"
          color="#ef4444"
          description="Current events and journalism (default fallback)"
          expanded={expandedType === 'news'}
          onToggle={() => setExpandedType(expandedType === 'news' ? null : 'news')}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15, marginTop: 15 }}>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                News Protocol
              </label>
              <input
                type="text"
                value={settings.doctype_news_protocol || ''}
                onChange={(e) => updateSetting('doctype_news_protocol', e.target.value)}
                className="input"
                placeholder="(news) & (news or story or news story)"
                style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                Min Protocol Matches
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={settings.doctype_news_min_instances || 3}
                onChange={(e) => updateSetting('doctype_news_min_instances', parseInt(e.target.value))}
                className="input"
              />
            </div>
          </div>
          <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
            Rule: If protocol matches {settings.doctype_news_min_instances || 3}+ times OR no other type matches → News Article
          </p>
        </DocumentTypeCard>
        
        {/* Blog Post */}
        <DocumentTypeCard
          title="Blog Post"
          icon="✍️"
          color="#f472b6"
          description="Personal blogs and opinion pieces"
          expanded={expandedType === 'blog'}
          onToggle={() => setExpandedType(expandedType === 'blog' ? null : 'blog')}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15, marginTop: 15 }}>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                Blog Protocol
              </label>
              <input
                type="text"
                value={settings.doctype_blog_protocol || ''}
                onChange={(e) => updateSetting('doctype_blog_protocol', e.target.value)}
                className="input"
                placeholder="(blog)"
                style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                Min Instances (1 must be in title)
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={settings.doctype_blog_min_instances || 3}
                onChange={(e) => updateSetting('doctype_blog_min_instances', parseInt(e.target.value))}
                className="input"
              />
            </div>
          </div>
          <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
            Rule: Must contain &apos;blog&apos; {settings.doctype_blog_min_instances || 3}+ times, with at least 1 in the title
          </p>
        </DocumentTypeCard>
        
        {/* Forum */}
        <DocumentTypeCard
          title="Forum"
          icon="💬"
          color="#06b6d4"
          description="Discussion boards (forum in title)"
          expanded={expandedType === 'forum'}
          onToggle={() => setExpandedType(expandedType === 'forum' ? null : 'forum')}
        >
          <div style={{ marginTop: 15 }}>
            <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
              Forum Protocol
            </label>
            <input
              type="text"
              value={settings.doctype_forum_protocol || ''}
              onChange={(e) => updateSetting('doctype_forum_protocol', e.target.value)}
              className="input"
              placeholder="(forum)"
              style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
            />
            <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 5 }}>
              Rule: Protocol keyword(s) MUST appear in the page TITLE
            </p>
          </div>
        </DocumentTypeCard>
        
        {/* Personal Report (Collected) */}
        <DocumentTypeCard
          title="Personal Report (Collected)"
          icon="👤"
          color="#f59e0b"
          description="Extracted personal narratives from articles"
          expanded={expandedType === 'personal'}
          onToggle={() => setExpandedType(expandedType === 'personal' ? null : 'personal')}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 15, marginTop: 15 }}>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                Personal Protocol
              </label>
              <input
                type="text"
                value={settings.doctype_personal_collected_protocol || ''}
                onChange={(e) => updateSetting('doctype_personal_collected_protocol', e.target.value)}
                className="input"
                placeholder="(I)"
                style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                Min 'I' Count (outside quotes)
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={settings.doctype_personal_min_i_count || 3}
                onChange={(e) => updateSetting('doctype_personal_min_i_count', parseInt(e.target.value))}
                className="input"
              />
            </div>
            <div>
              <label style={{ color: '#a1a1aa', fontSize: '0.8rem', display: 'block', marginBottom: 5 }}>
                Min Paragraph Words
              </label>
              <input
                type="number"
                min="10"
                max="500"
                value={settings.doctype_personal_min_paragraph_words || 75}
                onChange={(e) => updateSetting('doctype_personal_min_paragraph_words', parseInt(e.target.value))}
                className="input"
              />
            </div>
          </div>
          <p style={{ color: '#71717a', fontSize: '0.75rem', marginTop: 10 }}>
            Rule: 'I' appears {settings.doctype_personal_min_i_count || 3}+ times OUTSIDE quotations in a paragraph 
            with {settings.doctype_personal_min_paragraph_words || 75}+ words
          </p>
        </DocumentTypeCard>
        
        {/* Other Document Types (Read-only display) */}
        <div style={{
          background: 'rgba(30, 20, 50, 0.5)',
          borderRadius: 12,
          padding: 20,
          border: '1px solid rgba(124, 58, 237, 0.3)'
        }}>
          <h4 style={{ color: '#a78bfa', marginBottom: 15 }}>📋 Other Document Types (URL-based)</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
            {[
              { icon: '🎓', name: 'InfoPilot Exclusive', desc: 'Written by InfoPilot writers' },
              { icon: '📖', name: 'InfoBook Exclusive', desc: 'Written by InfoBook writers' },
              { icon: '✏️', name: 'Personal Report (Organic)', desc: 'Written by members' },
              { icon: '📄', name: 'Academic Paper', desc: '.edu, journal, research URLs' },
              { icon: '🏛️', name: 'Government', desc: '.gov URLs' },
              { icon: '📚', name: 'Wiki', desc: 'Wikipedia URLs' },
              { icon: '🎬', name: 'Video', desc: 'YouTube, Vimeo URLs' },
              { icon: '📑', name: 'PDF Document', desc: '.pdf URLs' },
              { icon: '🌐', name: 'Webpage', desc: 'Catch-all default' }
            ].map((type, i) => (
              <div key={i} style={{ 
                background: 'rgba(0,0,0,0.2)', 
                borderRadius: 8, 
                padding: 10,
                display: 'flex',
                alignItems: 'center',
                gap: 10
              }}>
                <span style={{ fontSize: '1.2rem' }}>{type.icon}</span>
                <div>
                  <div style={{ color: '#fff', fontSize: '0.85rem', fontWeight: 500 }}>{type.name}</div>
                  <div style={{ color: '#71717a', fontSize: '0.7rem' }}>{type.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Save Button */}
      <button 
        className="btn btn-primary" 
        onClick={saveSettings}
        disabled={saving}
        style={{ 
          marginTop: 25, 
          width: '100%',
          padding: 15,
          fontSize: '1.1rem',
          background: 'linear-gradient(135deg, #10b981, #059669)'
        }}
      >
        {saving ? '⏳ Saving...' : '💾 Save All Document Type Settings'}
      </button>
    </div>
  );
};

/**
 * Document Type Card - Expandable card for each document type
 */
const DocumentTypeCard = ({ title, icon, color, description, expanded, onToggle, children }) => (
  <div style={{
    background: expanded 
      ? `linear-gradient(135deg, ${color}20, ${color}10)` 
      : 'rgba(30, 20, 50, 0.5)',
    borderRadius: 12,
    padding: 15,
    border: `1px solid ${expanded ? color + '50' : 'rgba(124, 58, 237, 0.3)'}`,
    transition: 'all 0.2s'
  }}>
    <div 
      onClick={onToggle}
      style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        cursor: 'pointer'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: '1.5rem' }}>{icon}</span>
        <div>
          <h4 style={{ color, margin: 0 }}>{title}</h4>
          <p style={{ color: '#a1a1aa', fontSize: '0.8rem', margin: '2px 0 0 0' }}>{description}</p>
        </div>
      </div>
      <button style={{
        background: 'rgba(124, 58, 237, 0.3)',
        border: 'none',
        color: '#a78bfa',
        width: 30,
        height: 30,
        borderRadius: 8,
        cursor: 'pointer',
        fontSize: '1rem'
      }}>
        {expanded ? '−' : '+'}
      </button>
    </div>
    
    {expanded && children}
  </div>
);

export default DoctypeSettingsAdmin;
