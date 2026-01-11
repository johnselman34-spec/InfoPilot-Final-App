import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';

const AdminPanel = ({ showToast }) => {
  const { token } = useAuth();
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('general');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API}/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
    } catch (e) {
      console.error('Failed to fetch settings:', e);
    }
    setLoading(false);
  };

  const updateSetting = async (key, value) => {
    try {
      await fetch(`${API}/admin/settings/${key}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(value)
      });
      showToast('Setting updated!', 'success');
      fetchSettings();
    } catch (e) {
      showToast('Failed to update setting', 'error');
    }
  };

  const getSetting = (key) => settings.find(s => s.key === key)?.value || '';

  // Newsletter state
  const [newsletterPreview, setNewsletterPreview] = useState(null);
  const [newsletterLoading, setNewsletterLoading] = useState(false);
  const [newsletterHistory, setNewsletterHistory] = useState([]);
  const [newsletterSchedule, setNewsletterSchedule] = useState({
    enabled: false,
    day_of_week: 'monday',
    hour: 9,
    last_scheduled_send: null
  });
  const [testEmail, setTestEmail] = useState('');

  const generateNewsletter = async () => {
    setNewsletterLoading(true);
    try {
      const res = await fetch(`${API}/newsletter/generate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNewsletterPreview(data.content);
        showToast('Newsletter generated!', 'success');
        fetchNewsletterHistory();
      } else {
        showToast('Failed to generate newsletter', 'error');
      }
    } catch (e) {
      showToast('Error generating newsletter', 'error');
    }
    setNewsletterLoading(false);
  };

  const sendNewsletter = async () => {
    if (!window.confirm('Send newsletter to all subscribed users?')) return;
    setNewsletterLoading(true);
    try {
      const res = await fetch(`${API}/newsletter/send`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`Newsletter sent to ${data.sent_count} users!`, 'success');
        fetchNewsletterHistory();
      } else {
        showToast('Failed to send newsletter', 'error');
      }
    } catch (e) {
      showToast('Error sending newsletter', 'error');
    }
    setNewsletterLoading(false);
  };

  const sendTestNewsletter = async () => {
    if (!testEmail) {
      showToast('Please enter an email address', 'error');
      return;
    }
    setNewsletterLoading(true);
    try {
      const res = await fetch(`${API}/newsletter/test-email`, {
        method: 'POST',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: testEmail })
      });
      if (res.ok) {
        showToast(`Test newsletter sent to ${testEmail}!`, 'success');
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to send test', 'error');
      }
    } catch (e) {
      showToast('Error sending test newsletter', 'error');
    }
    setNewsletterLoading(false);
  };

  const fetchNewsletterHistory = async () => {
    try {
      const res = await fetch(`${API}/newsletter/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNewsletterHistory(data);
      }
    } catch (e) {
      console.error('Failed to fetch newsletter history');
    }
  };

  const fetchNewsletterSchedule = async () => {
    try {
      const res = await fetch(`${API}/newsletter/schedule`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNewsletterSchedule(data);
      }
    } catch (e) {
      console.error('Failed to fetch newsletter schedule');
    }
  };

  const saveNewsletterSchedule = async () => {
    try {
      const res = await fetch(`${API}/newsletter/schedule`, {
        method: 'POST',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newsletterSchedule)
      });
      if (res.ok) {
        showToast(newsletterSchedule.enabled 
          ? `Newsletter scheduled for ${newsletterSchedule.day_of_week}s at ${newsletterSchedule.hour}:00 UTC`
          : 'Newsletter schedule disabled', 
          'success'
        );
      } else {
        showToast('Failed to save schedule', 'error');
      }
    } catch (e) {
      showToast('Error saving schedule', 'error');
    }
  };

  useEffect(() => {
    if (activeTab === 'newsletter') {
      fetchNewsletterHistory();
      fetchNewsletterSchedule();
    }
  }, [activeTab]);

  if (loading) {
    return <div className="loading-spinner"><div className="spinner"></div></div>;
  }

  return (
    <div className="admin-panel" data-testid="admin-panel">
      <div className="admin-panel-header">
        ⚙️ Admin Control Panel
      </div>
      <div className="admin-panel-content">
        <div className="tabs">
          {['general', 'search', 'pricing', 'newsletter', 'users', 'content'].map(tab => (
            <div
              key={tab}
              className={`tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
              data-testid={`admin-tab-${tab}`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </div>
          ))}
        </div>

        {activeTab === 'general' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>General Settings</h3>
            <div className="admin-setting">
              <label>Daily Collate Limit</label>
              <input
                type="number"
                defaultValue={getSetting('daily_collate_limit') || 10}
                onBlur={(e) => updateSetting('daily_collate_limit', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Max Category Levels</label>
              <input
                type="number"
                defaultValue={getSetting('max_category_levels') || 100}
                onBlur={(e) => updateSetting('max_category_levels', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Tutorial Video URL</label>
              <input
                type="text"
                defaultValue={getSetting('tutorial_video_url') || ''}
                onBlur={(e) => updateSetting('tutorial_video_url', e.target.value)}
                style={{ width: 250 }}
              />
            </div>
          </div>
        )}

        {activeTab === 'search' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>Search Settings</h3>
            <div className="admin-setting">
              <label>Results Per Page</label>
              <input
                type="number"
                defaultValue={getSetting('results_per_page') || 20}
                onBlur={(e) => updateSetting('results_per_page', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Max Search Pages (Admin/Paid)</label>
              <input
                type="number"
                min="1"
                max="99"
                defaultValue={getSetting('max_search_pages') || 99}
                onBlur={(e) => updateSetting('max_search_pages', Math.min(99, Math.max(1, parseInt(e.target.value))))}
              />
              <small style={{ color: '#a1a1aa', display: 'block', marginTop: 5 }}>
                Maximum pages to fetch during Search & Collate (1-99)
              </small>
            </div>
            <div className="admin-setting">
              <label>Unpaid User Max Pages</label>
              <input
                type="number"
                defaultValue={getSetting('unpaid_max_pages') || 3}
                onBlur={(e) => updateSetting('unpaid_max_pages', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Ph.D. Min Words</label>
              <input
                type="number"
                defaultValue={getSetting('phd_min_words') || 1500}
                onBlur={(e) => updateSetting('phd_min_words', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Ph.D. Keyword Count</label>
              <input
                type="number"
                defaultValue={getSetting('phd_keyword_count') || 3}
                onBlur={(e) => updateSetting('phd_keyword_count', parseInt(e.target.value))}
              />
            </div>
          </div>
        )}

        {activeTab === 'pricing' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>Pricing & Subscription</h3>
            <div className="admin-setting">
              <label>Subscription Price ($)</label>
              <input
                type="number"
                step="0.01"
                defaultValue={getSetting('subscription_price') || 0.99}
                onBlur={(e) => updateSetting('subscription_price', parseFloat(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>PayPal Business Email</label>
              <input
                type="email"
                defaultValue={getSetting('paypal_email') || 'JJSpilot24@gmail.com'}
                onBlur={(e) => updateSetting('paypal_email', e.target.value)}
                style={{ width: 300 }}
                placeholder="your-business@email.com"
              />
            </div>
            <div className="admin-setting">
              <label>PayPal Payment Link (fallback)</label>
              <input
                type="text"
                defaultValue={getSetting('paypal_link') || ''}
                onBlur={(e) => updateSetting('paypal_link', e.target.value)}
                style={{ width: 300 }}
              />
            </div>
            <div style={{ marginTop: 20, padding: 15, background: 'rgba(16, 185, 129, 0.1)', borderRadius: 10, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              <p style={{ fontSize: '0.85rem', color: '#10b981' }}>
                💡 Tips:<br/>
                • Enter your PayPal business email to accept "Pay What You Want" payments<br/>
                • Set "Unpaid User Max Pages" to more than 40 to make the app FREE
              </p>
            </div>
          </div>
        )}

        {activeTab === 'newsletter' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>📧 Weekly Newsletter</h3>
            <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
              Generate and send AI-powered funny newsletters to promote your book and app!
            </p>
            
            {/* Manual Send Controls */}
            <div style={{ display: 'flex', gap: 15, marginBottom: 25, flexWrap: 'wrap' }}>
              <button 
                className="btn btn-primary" 
                onClick={generateNewsletter}
                disabled={newsletterLoading}
                data-testid="generate-newsletter-btn"
              >
                {newsletterLoading ? '🤖 Generating...' : '🎨 Generate New Newsletter'}
              </button>
              <button 
                className="btn btn-success" 
                onClick={sendNewsletter}
                disabled={newsletterLoading}
                data-testid="send-newsletter-btn"
              >
                📤 Send to All Users
              </button>
            </div>

            {/* Test Email */}
            <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: 20, borderRadius: 12, marginBottom: 25, border: '1px solid rgba(59, 130, 246, 0.3)' }}>
              <h4 style={{ color: '#3b82f6', marginBottom: 15 }}>🧪 Send Test Email</h4>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <input 
                  type="email" 
                  placeholder="your@email.com"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  style={{ flex: 1, minWidth: 200 }}
                  data-testid="test-email-input"
                />
                <button 
                  className="btn btn-secondary"
                  onClick={sendTestNewsletter}
                  disabled={newsletterLoading}
                  data-testid="send-test-btn"
                >
                  📧 Send Test
                </button>
              </div>
            </div>

            {/* Automated Schedule */}
            <div style={{ background: 'rgba(124, 58, 237, 0.1)', padding: 20, borderRadius: 12, marginBottom: 25, border: '2px solid rgba(124, 58, 237, 0.3)' }}>
              <h4 style={{ color: '#a78bfa', marginBottom: 15 }}>⏰ Automated Weekly Schedule</h4>
              <div style={{ display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap', marginBottom: 15 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                  <input 
                    type="checkbox"
                    checked={newsletterSchedule.enabled}
                    onChange={(e) => setNewsletterSchedule({...newsletterSchedule, enabled: e.target.checked})}
                    style={{ width: 20, height: 20, accentColor: '#7c3aed' }}
                  />
                  <span style={{ color: newsletterSchedule.enabled ? '#10b981' : '#a1a1aa', fontWeight: 600 }}>
                    {newsletterSchedule.enabled ? '✅ Enabled' : '⏸️ Disabled'}
                  </span>
                </label>
                
                <select 
                  value={newsletterSchedule.day_of_week}
                  onChange={(e) => setNewsletterSchedule({...newsletterSchedule, day_of_week: e.target.value})}
                  style={{ padding: '8px 15px', borderRadius: 8, background: 'rgba(30, 20, 50, 0.8)', color: 'white', border: '1px solid rgba(124, 58, 237, 0.5)' }}
                >
                  <option value="monday">Monday</option>
                  <option value="tuesday">Tuesday</option>
                  <option value="wednesday">Wednesday</option>
                  <option value="thursday">Thursday</option>
                  <option value="friday">Friday</option>
                  <option value="saturday">Saturday</option>
                  <option value="sunday">Sunday</option>
                </select>
                
                <span style={{ color: '#a1a1aa' }}>at</span>
                
                <select 
                  value={newsletterSchedule.hour}
                  onChange={(e) => setNewsletterSchedule({...newsletterSchedule, hour: parseInt(e.target.value)})}
                  style={{ padding: '8px 15px', borderRadius: 8, background: 'rgba(30, 20, 50, 0.8)', color: 'white', border: '1px solid rgba(124, 58, 237, 0.5)' }}
                >
                  {[...Array(24)].map((_, i) => (
                    <option key={i} value={i}>{i.toString().padStart(2, '0')}:00 UTC</option>
                  ))}
                </select>
                
                <button 
                  className="btn btn-primary"
                  onClick={saveNewsletterSchedule}
                  style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)' }}
                >
                  💾 Save Schedule
                </button>
              </div>
              
              {newsletterSchedule.last_scheduled_send && (
                <p style={{ color: '#a78bfa', fontSize: '0.85rem' }}>
                  Last automated send: {new Date(newsletterSchedule.last_scheduled_send).toLocaleString()}
                </p>
              )}
              
              <p style={{ color: '#a1a1aa', fontSize: '0.8rem', marginTop: 10 }}>
                ℹ️ When enabled, newsletters are automatically generated with AI and sent every week at the scheduled time.
              </p>
            </div>

            {/* Newsletter Preview */}
            {newsletterPreview && (
              <div style={{ marginBottom: 25 }}>
                <h4 style={{ color: '#f472b6', marginBottom: 10 }}>Preview:</h4>
                <div 
                  style={{ 
                    background: '#fff', 
                    borderRadius: 12, 
                    padding: 20, 
                    maxHeight: 500, 
                    overflow: 'auto',
                    border: '2px solid rgba(236, 72, 153, 0.3)'
                  }}
                  dangerouslySetInnerHTML={{ __html: newsletterPreview }}
                />
              </div>
            )}

            {/* Newsletter History */}
            <div>
              <h4 style={{ color: '#f472b6', marginBottom: 15 }}>📜 Newsletter History</h4>
              {newsletterHistory.length === 0 ? (
                <p style={{ color: '#a1a1aa' }}>No newsletters sent yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {newsletterHistory.map((n) => (
                    <div key={n.id} style={{ 
                      padding: 15, 
                      background: 'rgba(30, 20, 50, 0.5)', 
                      borderRadius: 10,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: 10
                    }}>
                      <div>
                        <span style={{ color: n.ai_generated ? '#10b981' : '#f472b6' }}>
                          {n.ai_generated ? '🤖 AI Generated' : '📝 Template'}
                        </span>
                        <span style={{ color: '#a1a1aa', marginLeft: 15 }}>
                          {new Date(n.generated_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div>
                        {n.sent ? (
                          <span style={{ color: '#10b981' }}>
                            ✅ Sent to {n.sent_count} users {n.failed_count > 0 && `(${n.failed_count} failed)`}
                          </span>
                        ) : (
                          <span style={{ color: '#fbbf24' }}>⏳ Not sent</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ marginTop: 25, padding: 15, background: 'rgba(236, 72, 153, 0.1)', borderRadius: 10, border: '1px solid rgba(236, 72, 153, 0.3)' }}>
              <p style={{ fontSize: '0.85rem', color: '#f472b6' }}>
                💡 Newsletter promotes:<br/>
                • "Letters to Evelyn" by John Selman - $2.99 on Amazon (19 Five-Star Reviews!)<br/>
                • InfoPilot Premium subscriptions - Pay what you want!<br/>
                • Uses AI to create funny, engaging content with your book's actual reviews!<br/>
                • Includes your book advertisement images with rotating selection!
              </p>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>User Management</h3>
            <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
              Ban users or manage user accounts from here.
            </p>
            <div className="admin-setting">
              <label>Ban User by ID</label>
              <div style={{ display: 'flex', gap: 10 }}>
                <input type="text" placeholder="User ID" id="ban-user-id" />
                <button 
                  className="btn btn-danger"
                  onClick={async () => {
                    const userId = document.getElementById('ban-user-id').value;
                    if (userId) {
                      try {
                        await fetch(`${API}/admin/ban-user/${userId}`, {
                          method: 'POST',
                          headers: { Authorization: `Bearer ${token}` }
                        });
                        showToast('User banned!', 'success');
                      } catch (e) {
                        showToast('Failed to ban user', 'error');
                      }
                    }
                  }}
                >
                  Ban
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'content' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>Content Moderation</h3>
            <div className="admin-setting">
              <label>Add Blocked Word</label>
              <div style={{ display: 'flex', gap: 10 }}>
                <input type="text" placeholder="Word to block" id="block-word" />
                <button 
                  className="btn btn-danger"
                  onClick={async () => {
                    const word = document.getElementById('block-word').value;
                    if (word) {
                      try {
                        await fetch(`${API}/admin/ban-word`, {
                          method: 'POST',
                          headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${token}`
                          },
                          body: JSON.stringify(word)
                        });
                        showToast('Word blocked!', 'success');
                        document.getElementById('block-word').value = '';
                      } catch (e) {
                        showToast('Failed to block word', 'error');
                      }
                    }
                  }}
                >
                  Block
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;
