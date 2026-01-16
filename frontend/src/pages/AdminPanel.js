import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import ABTestDashboard from '../components/ABTesting/ABTestDashboard';
import YouTubeTutorialAdmin from '../components/Admin/YouTubeTutorialAdmin';
import ABOptimizerAdmin from '../components/Admin/ABOptimizerAdmin';
import RevenueForecastAdmin from '../components/Admin/RevenueForecastAdmin';
import MarketplaceProtocolForecast from '../components/Admin/MarketplaceProtocolForecast';
import UserModerationAdmin from '../components/Admin/UserModerationAdmin';
import CategoryAnalyticsDashboard from '../components/Admin/CategoryAnalyticsDashboard';
import UnpaidPriceControlsAdmin from '../components/Admin/UnpaidPriceControlsAdmin';
import PriceControlsAdmin from '../components/Admin/PriceControlsAdmin';
import DoctypeSettingsAdmin from '../components/Admin/DoctypeSettingsAdmin';
import DoctypeTestingTool from '../components/Admin/DoctypeTestingTool';
import CleanAllCategoriesAdmin from '../components/Admin/CleanAllCategoriesAdmin';

const AdminPanel = ({ showToast }) => {
  const { token } = useAuth();
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('general');

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API}/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        // Handle both array and object responses
        if (Array.isArray(data)) {
          const settingsObj = {};
          data.forEach(s => { settingsObj[s.key] = s.value; });
          setSettings(settingsObj);
        } else {
          setSettings(data || {});
        }
      }
    } catch (e) {
      console.error('Failed to fetch settings:', e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSettings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  // Get setting value from object
  const getSetting = (key) => settings[key] || '';

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
  
  // AI Newsletter Optimization state
  const [aiOptimization, setAiOptimization] = useState(null);
  const [aiOptLoading, setAiOptLoading] = useState(false);

  const fetchAIOptimization = async () => {
    setAiOptLoading(true);
    try {
      const res = await fetch(`${API}/api/admin/newsletter/ai-optimize`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAiOptimization(data);
        if (data.success) {
          showToast('🤖 AI optimization analysis complete!', 'success');
        }
      }
    } catch (e) {
      console.error('AI optimization fetch failed:', e);
    }
    setAiOptLoading(false);
  };

  const applyAISchedule = async () => {
    if (!aiOptimization?.ai_recommendations) {
      showToast('No AI recommendations available', 'error');
      return;
    }
    
    try {
      const res = await fetch(`${API}/api/admin/newsletter/apply-ai-schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ recommendations: aiOptimization.ai_recommendations })
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          showToast('🤖 AI-optimized schedule applied!', 'success');
          fetchNewsletterSchedule();
        } else {
          showToast(data.error || 'Failed to apply schedule', 'error');
        }
      }
    } catch (e) {
      showToast('Error applying AI schedule', 'error');
    }
  };

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
          {['general', 'search', 'pricing', 'newsletter', 'users', 'moderation', 'price-controls', 'doctype-settings', 'category-analytics', 'clean-categories', 'content', 'polls', 'ab-testing', 'optimizer', 'forecast', 'protocol-forecast', 'email-reports', 'tutorials'].map(tab => (
            <div
              key={tab}
              className={`tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
              data-testid={`admin-tab-${tab}`}
            >
              {tab === 'ab-testing' ? 'A/B Testing' : tab === 'email-reports' ? 'Email Reports' : tab === 'tutorials' ? '🎬 Tutorials' : tab === 'optimizer' ? '🤖 Optimizer' : tab === 'forecast' ? '📈 Forecast' : tab === 'protocol-forecast' ? '🔮 Protocol Forecast' : tab === 'moderation' ? '🛡️ Moderation' : tab === 'price-controls' ? '💰 Price Controls' : tab === 'doctype-settings' ? '📄 Doc Types' : tab === 'category-analytics' ? '📊 Cat Analytics' : tab === 'clean-categories' ? '🧹 Clean' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </div>
          ))}
        </div>

        {activeTab === 'general' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>🎛️ General Settings</h3>
            
            {/* Collation Settings Section */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(59, 130, 246, 0.15))',
              borderRadius: 12,
              padding: 20,
              marginBottom: 25,
              border: '1px solid rgba(124, 58, 237, 0.3)'
            }}>
              <h4 style={{ color: '#a78bfa', margin: '0 0 15px 0' }}>🔍 Search & Collation Settings</h4>
              
              <div className="admin-setting">
                <label>Collation Limit (Per Search)</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  defaultValue={getSetting('collation_limit') || 40}
                  onBlur={(e) => updateSetting('collation_limit', Math.min(100, Math.max(1, parseInt(e.target.value))))}
                  data-testid="collation-limit-input"
                />
                <small style={{ color: '#a1a1aa', display: 'block', marginTop: 5 }}>
                  Results per Search & Collate (1-100, default: 40). Higher = more results but slower.
                </small>
              </div>
              
              <div className="admin-setting">
                <label>Daily Collate Limit (Total)</label>
                <input
                  type="number"
                  defaultValue={getSetting('daily_collate_limit') || 100}
                  onBlur={(e) => updateSetting('daily_collate_limit', parseInt(e.target.value))}
                />
              </div>
              
              <div className="admin-setting" style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
                <label style={{ margin: 0 }}>Allow Multiple Categories</label>
                <input
                  type="checkbox"
                  checked={getSetting('allow_multiple_categories') !== false}
                  onChange={(e) => updateSetting('allow_multiple_categories', e.target.checked)}
                  style={{ width: 20, height: 20, accentColor: '#10b981' }}
                />
                <span style={{ color: getSetting('allow_multiple_categories') !== false ? '#10b981' : '#ef4444', fontSize: '0.9rem' }}>
                  {getSetting('allow_multiple_categories') !== false ? '✅ Enabled' : '❌ Disabled'}
                </span>
              </div>
            </div>
            
            {/* Category Hierarchy Section */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.15))',
              borderRadius: 12,
              padding: 20,
              marginBottom: 25,
              border: '1px solid rgba(16, 185, 129, 0.3)'
            }}>
              <h4 style={{ color: '#10b981', margin: '0 0 15px 0' }}>📁 Category Hierarchy</h4>
              
              <div className="admin-setting">
                <label>Max Category Levels (Depth)</label>
                <input
                  type="number"
                  defaultValue={getSetting('max_category_levels') || 100}
                  onBlur={(e) => updateSetting('max_category_levels', parseInt(e.target.value))}
                />
                <small style={{ color: '#a1a1aa', display: 'block', marginTop: 5 }}>
                  Maximum sub-category depth (category → sub → sub-sub → ...)
                </small>
              </div>
            </div>
            
            {/* Payment Settings Section */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(239, 68, 68, 0.15))',
              borderRadius: 12,
              padding: 20,
              marginBottom: 25,
              border: '1px solid rgba(245, 158, 11, 0.3)'
            }}>
              <h4 style={{ color: '#f59e0b', margin: '0 0 15px 0' }}>💰 Payment Settings</h4>
              
              <div className="admin-setting">
                <label>Platform Fee %</label>
                <input
                  type="number"
                  min="5"
                  max="50"
                  defaultValue={getSetting('platform_fee_percent') || 15}
                  onBlur={(e) => updateSetting('platform_fee_percent', Math.min(50, Math.max(5, parseInt(e.target.value))))}
                />
                <small style={{ color: '#a1a1aa', display: 'block', marginTop: 5 }}>
                  Admin receives this % from protocol sales (default: 15%)
                </small>
              </div>
              
              <div className="admin-setting">
                <label>Min Payout Threshold ($)</label>
                <input
                  type="number"
                  min="1"
                  step="0.01"
                  defaultValue={getSetting('min_payout_threshold') || 1.00}
                  onBlur={(e) => updateSetting('min_payout_threshold', parseFloat(e.target.value))}
                />
                <small style={{ color: '#a1a1aa', display: 'block', marginTop: 5 }}>
                  PayPal minimum payout (default: $1.00). Earnings accumulate until threshold.
                </small>
              </div>
              
              <div style={{
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 8,
                padding: 12,
                marginTop: 15
              }}>
                <p style={{ color: '#fbbf24', margin: 0, fontSize: '0.85rem' }}>
                  💡 <strong>Note:</strong> With 15% fee, protocols priced below $6.67 will accumulate earnings until $1.00 is reached for payout.
                </p>
              </div>
            </div>
            
            {/* Bundle of the Week Section */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.15), rgba(124, 58, 237, 0.15))',
              borderRadius: 12,
              padding: 20,
              marginBottom: 25,
              border: '1px solid rgba(236, 72, 153, 0.3)'
            }}>
              <h4 style={{ color: '#f472b6', margin: '0 0 15px 0' }}>🏆 Bundle of the Week</h4>
              
              <div className="admin-setting">
                <label>Featured Bundle ID</label>
                <input
                  type="text"
                  defaultValue={getSetting('bundle_of_week_id') || ''}
                  onBlur={(e) => updateSetting('bundle_of_week_id', e.target.value)}
                  placeholder="Enter bundle ID to feature (leave empty for auto)"
                  style={{ width: 300 }}
                />
                <small style={{ color: '#a1a1aa', display: 'block', marginTop: 5 }}>
                  Leave empty to automatically feature the most popular bundle
                </small>
              </div>
            </div>
            
            {/* Newsletter Time Settings */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.15))',
              borderRadius: 12,
              padding: 20,
              marginBottom: 25,
              border: '1px solid rgba(16, 185, 129, 0.3)'
            }}>
              <h4 style={{ color: '#10b981', margin: '0 0 15px 0' }}>📬 Newsletter Schedule (UTC)</h4>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 15 }}>
                <div className="admin-setting">
                  <label>🌅 Morning</label>
                  <input
                    type="time"
                    defaultValue={getSetting('newsletter_time_1') || '05:42'}
                    onBlur={(e) => updateSetting('newsletter_time_1', e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div className="admin-setting">
                  <label>☀️ Mid-Morning</label>
                  <input
                    type="time"
                    defaultValue={getSetting('newsletter_time_2') || '08:37'}
                    onBlur={(e) => updateSetting('newsletter_time_2', e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div className="admin-setting">
                  <label>🌆 Afternoon</label>
                  <input
                    type="time"
                    defaultValue={getSetting('newsletter_time_3') || '16:41'}
                    onBlur={(e) => updateSetting('newsletter_time_3', e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>
              
              <div className="admin-setting" style={{ display: 'flex', alignItems: 'center', gap: 15, marginTop: 15 }}>
                <label style={{ margin: 0 }}>🤖 AI-Optimized Timing</label>
                <input
                  type="checkbox"
                  checked={getSetting('newsletter_ai_optimization') !== false}
                  onChange={(e) => updateSetting('newsletter_ai_optimization', e.target.checked)}
                  style={{ width: 20, height: 20, accentColor: '#10b981' }}
                />
                <span style={{ color: getSetting('newsletter_ai_optimization') !== false ? '#10b981' : '#ef4444', fontSize: '0.9rem' }}>
                  {getSetting('newsletter_ai_optimization') !== false ? '✅ AI will optimize for max engagement' : '❌ Using manual times'}
                </span>
              </div>
              
              <div style={{
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 8,
                padding: 12,
                marginTop: 15
              }}>
                <p style={{ color: '#6ee7b7', margin: 0, fontSize: '0.85rem' }}>
                  💡 <strong>Current Schedule:</strong> Newsletters send at 5:42 AM, 8:37 AM, and 4:41 PM UTC daily. Enable AI optimization to let the system find the best times for maximum engagement and revenue!
                </p>
              </div>
            </div>
            
            {/* Daily Laugh Goal Settings */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.15))',
              borderRadius: 12,
              padding: 20,
              marginBottom: 25,
              border: '1px solid rgba(251, 191, 36, 0.3)'
            }}>
              <h4 style={{ color: '#fbbf24', margin: '0 0 15px 0' }}>🎯 Daily Laugh Goal Settings</h4>
              
              <div className="admin-setting">
                <label>Default Daily Goal (new users)</label>
                <input
                  type="number"
                  min="5"
                  max="50"
                  defaultValue={getSetting('default_daily_laugh_goal') || 10}
                  onBlur={(e) => updateSetting('default_daily_laugh_goal', Math.min(50, Math.max(5, parseInt(e.target.value))))}
                  style={{ width: 100 }}
                />
                <small style={{ color: '#a1a1aa', display: 'block', marginTop: 5 }}>
                  Default number of laughs per day for new users (5-50)
                </small>
              </div>
              
              <div className="admin-setting">
                <label>Streak Bonus Multiplier</label>
                <input
                  type="number"
                  min="0.5"
                  max="5"
                  step="0.1"
                  defaultValue={getSetting('streak_bonus_multiplier') || 1.0}
                  onBlur={(e) => updateSetting('streak_bonus_multiplier', parseFloat(e.target.value))}
                  style={{ width: 100 }}
                />
                <small style={{ color: '#a1a1aa', display: 'block', marginTop: 5 }}>
                  Multiplier for streak XP bonuses (1.0 = normal, 2.0 = double)
                </small>
              </div>
            </div>
            
            {/* Other Settings */}
            <div className="admin-setting">
              <label>Tutorial Video URL</label>
              <input
                type="text"
                defaultValue={getSetting('tutorial_video_url') || ''}
                onBlur={(e) => updateSetting('tutorial_video_url', e.target.value)}
                style={{ width: 300 }}
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
            
            {/* Promotion Message for Users */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(239, 68, 68, 0.15))',
              borderRadius: 12,
              padding: 20,
              marginTop: 25,
              marginBottom: 25,
              border: '2px solid rgba(245, 158, 11, 0.3)'
            }}>
              <h4 style={{ color: '#f59e0b', margin: '0 0 15px 0' }}>📢 Promotion Message (Shown Near Upgrade Button)</h4>
              
              <div className="admin-setting">
                <label>Enable Promotion Message</label>
                <input
                  type="checkbox"
                  checked={getSetting('show_upgrade_promo') !== false}
                  onChange={(e) => updateSetting('show_upgrade_promo', e.target.checked)}
                  style={{ width: 20, height: 20, accentColor: '#f59e0b' }}
                />
              </div>
              
              <div className="admin-setting">
                <label>Promotion Title</label>
                <input
                  type="text"
                  defaultValue={getSetting('upgrade_promo_title') || '⚠️ Limited Time Offer!'}
                  onBlur={(e) => updateSetting('upgrade_promo_title', e.target.value)}
                  style={{ width: '100%' }}
                  placeholder="e.g., ⚠️ Limited Time Offer!"
                />
              </div>
              
              <div className="admin-setting">
                <label>Promotion Message</label>
                <textarea
                  defaultValue={getSetting('upgrade_promo_message') || 'Pay As You Go pricing is available while supplies last! We are testing our business model to see if we can sustain this incredible platform. Google Maps API keys and AI Search subscriptions are expensive - your support helps keep InfoPilot running!'}
                  onBlur={(e) => updateSetting('upgrade_promo_message', e.target.value)}
                  style={{ width: '100%', minHeight: 100, resize: 'vertical' }}
                  placeholder="Enter your promotional message..."
                />
              </div>
              
              <div style={{
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 8,
                padding: 12,
                marginTop: 10
              }}>
                <p style={{ color: '#fbbf24', margin: 0, fontSize: '0.85rem' }}>
                  💡 <strong>Preview:</strong> This message will appear near the Upgrade/Pay As You Go button to inform users about your business model and costs.
                </p>
              </div>
            </div>
            
            <div style={{ marginTop: 20, padding: 15, background: 'rgba(16, 185, 129, 0.1)', borderRadius: 10, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              <p style={{ fontSize: '0.85rem', color: '#10b981' }}>
                💡 Tips:<br/>
                • Enter your PayPal business email to accept Pay What You Want payments<br/>
                • Set Unpaid User Max Pages to more than 40 to make the app FREE
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

            {/* AI Newsletter Optimization */}
            <div style={{ 
              marginBottom: 25, 
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(236, 72, 153, 0.2))', 
              borderRadius: 15, 
              padding: 20,
              border: '2px solid rgba(124, 58, 237, 0.3)'
            }}>
              <h4 style={{ 
                color: '#a78bfa', 
                marginBottom: 15, 
                display: 'flex', 
                alignItems: 'center', 
                gap: 10 
              }}>
                🤖 AI Schedule Optimization
                <span style={{ 
                  fontSize: '0.65rem', 
                  background: 'linear-gradient(135deg, #7c3aed, #ec4899)', 
                  padding: '3px 8px', 
                  borderRadius: 4,
                  color: '#fff'
                }}>BETA</span>
              </h4>
              
              <p style={{ color: '#a1a1aa', fontSize: '0.85rem', marginBottom: 15 }}>
                Let AI analyze your newsletter performance data and recommend optimal send times for maximum engagement and revenue!
              </p>
              
              <button 
                className="btn btn-primary"
                onClick={fetchAIOptimization}
                disabled={aiOptLoading}
                style={{ 
                  background: 'linear-gradient(135deg, #7c3aed, #ec4899)',
                  marginRight: 10 
                }}
                data-testid="ai-optimize-btn"
              >
                {aiOptLoading ? '🔄 Analyzing...' : '🧠 Analyze & Optimize'}
              </button>
              
              {aiOptimization && aiOptimization.success && aiOptimization.ai_recommendations && (
                <button 
                  className="btn btn-success"
                  onClick={applyAISchedule}
                  style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)' }}
                  data-testid="apply-ai-schedule-btn"
                >
                  ✅ Apply AI Schedule
                </button>
              )}
              
              {aiOptimization && (
                <div style={{ 
                  marginTop: 15, 
                  padding: 15, 
                  background: 'rgba(30, 20, 50, 0.5)', 
                  borderRadius: 10 
                }}>
                  {aiOptimization.success && aiOptimization.ai_recommendations ? (
                    <>
                      <h5 style={{ color: '#10b981', marginBottom: 10 }}>📊 AI Recommendations:</h5>
                      <div style={{ display: 'grid', gap: 8 }}>
                        <div style={{ color: '#fff' }}>
                          <strong>Morning:</strong> {aiOptimization.ai_recommendations.recommended_morning_time}
                        </div>
                        <div style={{ color: '#fff' }}>
                          <strong>Mid-Morning:</strong> {aiOptimization.ai_recommendations.recommended_midmorning_time}
                        </div>
                        <div style={{ color: '#fff' }}>
                          <strong>Afternoon:</strong> {aiOptimization.ai_recommendations.recommended_afternoon_time}
                        </div>
                        {aiOptimization.ai_recommendations.reasoning && (
                          <div style={{ color: '#a1a1aa', fontSize: '0.85rem', marginTop: 5, fontStyle: 'italic' }}>
                            💡 {aiOptimization.ai_recommendations.reasoning}
                          </div>
                        )}
                        {aiOptimization.ai_recommendations.expected_improvement && (
                          <div style={{ color: '#f59e0b', fontSize: '0.9rem', marginTop: 5 }}>
                            📈 Expected Improvement: {aiOptimization.ai_recommendations.expected_improvement}
                          </div>
                        )}
                      </div>
                    </>
                  ) : aiOptimization.fallback_recommendation ? (
                    <>
                      <h5 style={{ color: '#f59e0b', marginBottom: 10 }}>⚠️ Using Fallback Recommendations:</h5>
                      <p style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                        {aiOptimization.fallback_recommendation.reason}
                      </p>
                    </>
                  ) : (
                    <p style={{ color: '#ef4444' }}>
                      ❌ {aiOptimization.error || 'Failed to generate recommendations'}
                    </p>
                  )}
                </div>
              )}
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
              View user accounts and toggle admin status. For advanced moderation (ban/mute/delete), use the 🛡️ Moderation tab.
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
                        await fetch(`${API}/admin/users/${userId}/ban`, {
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
            <div style={{ 
              marginTop: 20, 
              padding: 15, 
              background: 'rgba(124, 58, 237, 0.1)', 
              borderRadius: 10, 
              border: '1px solid rgba(124, 58, 237, 0.3)' 
            }}>
              <p style={{ fontSize: '0.85rem', color: '#a78bfa', margin: 0 }}>
                💡 <strong>Tip:</strong> Use the 🛡️ <strong>Moderation</strong> tab for a better experience with user search, detailed moderation actions, and history tracking.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'moderation' && (
          <UserModerationAdmin token={token} showToast={showToast} />
        )}

        {activeTab === 'price-controls' && (
          <PriceControlsAdmin showToast={showToast} />
        )}

        {activeTab === 'doctype-settings' && (
          <div>
            <DoctypeSettingsAdmin showToast={showToast} />
            <div style={{ marginTop: 30 }}>
              <DoctypeTestingTool showToast={showToast} />
            </div>
          </div>
        )}

        {activeTab === 'category-analytics' && (
          <CategoryAnalyticsDashboard token={token} showToast={showToast} />
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

        {activeTab === 'polls' && (
          <PollsAdminTab token={token} showToast={showToast} />
        )}

        {activeTab === 'ab-testing' && (
          <ABTestDashboard showToast={showToast} />
        )}

        {activeTab === 'optimizer' && (
          <ABOptimizerAdmin token={token} showToast={showToast} />
        )}

        {activeTab === 'forecast' && (
          <RevenueForecastAdmin token={token} showToast={showToast} />
        )}

        {activeTab === 'protocol-forecast' && (
          <MarketplaceProtocolForecast token={token} showToast={showToast} />
        )}

        {activeTab === 'email-reports' && (
          <EmailReportsTab token={token} showToast={showToast} />
        )}

        {activeTab === 'tutorials' && (
          <YouTubeTutorialAdmin token={token} showToast={showToast} />
        )}

        {activeTab === 'clean-categories' && (
          <CleanAllCategoriesAdmin showToast={showToast} />
        )}
      </div>
    </div>
  );
};

// Separate component for Polls Admin Tab
const PollsAdminTab = ({ token, showToast }) => {
  const [polls, setPolls] = useState([]);
  const [pollStats, setPollStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API}/polls/admin/statistics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPollStats(data);
      }
    } catch (e) {
      console.error('Failed to fetch poll stats:', e);
    }
  };

  const fetchPolls = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 10 });
      if (statusFilter) params.append('status', statusFilter);
      
      const res = await fetch(`${API}/polls/admin/all?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPolls(data.polls || []);
        setTotalPages(data.pages || 1);
      }
    } catch (e) {
      console.error('Failed to fetch polls:', e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPolls();
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, page]);

  const handleClosePoll = async (pollId) => {
    if (!window.confirm('Close this poll? Users will no longer be able to vote.')) return;
    try {
      const res = await fetch(`${API}/polls/admin/${pollId}?is_active=false`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Poll closed', 'success');
        fetchPolls();
        fetchStats();
      }
    } catch (e) {
      showToast('Failed to close poll', 'error');
    }
  };

  const handleDeletePoll = async (pollId) => {
    if (!window.confirm('Delete this poll permanently? This cannot be undone.')) return;
    try {
      const res = await fetch(`${API}/polls/admin/${pollId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        showToast('Poll deleted', 'success');
        fetchPolls();
        fetchStats();
      }
    } catch (e) {
      showToast('Failed to delete poll', 'error');
    }
  };

  return (
    <div>
      <h3 style={{ marginBottom: 20, color: '#f472b6' }}>📊 Poll Management</h3>
      
      {/* Stats Overview */}
      {pollStats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
          gap: 15,
          marginBottom: 25
        }}>
          {[
            { label: 'Total Polls', value: pollStats.total_polls, color: '#8b5cf6' },
            { label: 'Active', value: pollStats.active_polls, color: '#10b981' },
            { label: 'Closed', value: pollStats.closed_polls, color: '#6b7280' },
            { label: 'Total Votes', value: pollStats.total_votes, color: '#3b82f6' },
            { label: 'This Week', value: pollStats.polls_this_week, color: '#f59e0b' },
          ].map((stat, i) => (
            <div key={i} style={{
              background: `${stat.color}15`,
              borderRadius: 12,
              padding: '15px 12px',
              textAlign: 'center',
              border: `1px solid ${stat.color}30`
            }}>
              <div style={{ color: stat.color, fontSize: '1.5rem', fontWeight: 700 }}>{stat.value}</div>
              <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{stat.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filter Controls */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          style={{
            background: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 8,
            padding: '8px 12px',
            color: '#fff'
          }}
        >
          <option value="">All Polls</option>
          <option value="active">Active</option>
          <option value="closed">Closed</option>
          <option value="expired">Expired</option>
        </select>
        <button 
          className="btn btn-secondary"
          onClick={() => { fetchPolls(); fetchStats(); }}
          style={{ padding: '8px 16px' }}
        >
          🔄 Refresh
        </button>
      </div>

      {/* Polls List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 30, color: '#a1a1aa' }}>Loading polls...</div>
      ) : polls.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 30, color: '#a1a1aa' }}>
          <div style={{ fontSize: '2rem', marginBottom: 10 }}>📊</div>
          <p>No polls found</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {polls.map((poll) => (
            <div key={poll.id} style={{
              background: 'rgba(255,255,255,0.05)',
              borderRadius: 12,
              padding: 15,
              border: `1px solid ${poll.is_active ? 'rgba(16, 185, 129, 0.3)' : 'rgba(107, 114, 128, 0.3)'}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <h4 style={{ color: '#fff', margin: '0 0 5px 0', fontSize: '1rem' }}>
                    {poll.question}
                  </h4>
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', fontSize: '0.8rem' }}>
                    <span style={{ color: '#a1a1aa' }}>by {poll.creator_name}</span>
                    <span style={{ color: '#8b5cf6' }}>{poll.parent_type}</span>
                    <span style={{ color: '#3b82f6' }}>{poll.total_votes} votes</span>
                    <span style={{ color: poll.is_active ? '#10b981' : '#6b7280' }}>
                      {poll.is_active ? '🟢 Active' : poll.is_expired ? '⏰ Expired' : '🔴 Closed'}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  {poll.is_active && (
                    <button
                      onClick={() => handleClosePoll(poll.id)}
                      style={{
                        background: 'rgba(251, 191, 36, 0.2)',
                        border: '1px solid rgba(251, 191, 36, 0.3)',
                        color: '#fbbf24',
                        padding: '6px 12px',
                        borderRadius: 6,
                        cursor: 'pointer',
                        fontSize: '0.8rem'
                      }}
                    >
                      Close
                    </button>
                  )}
                  <button
                    onClick={() => handleDeletePoll(poll.id)}
                    style={{
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      color: '#ef4444',
                      padding: '6px 12px',
                      borderRadius: 6,
                      cursor: 'pointer',
                      fontSize: '0.8rem'
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#71717a' }}>
                Created: {new Date(poll.created_at).toLocaleDateString()}
                {poll.expires_at && ` • Expires: ${new Date(poll.expires_at).toLocaleDateString()}`}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 10, marginTop: 20 }}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn btn-secondary"
            style={{ padding: '6px 12px' }}
          >
            Previous
          </button>
          <span style={{ color: '#a1a1aa', alignSelf: 'center' }}>
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="btn btn-secondary"
            style={{ padding: '6px 12px' }}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

// Email Reports Admin Tab
const EmailReportsTab = ({ token, showToast }) => {
  const [status, setStatus] = useState(null);
  const [config, setConfig] = useState({
    enabled: false,
    frequency: 'weekly',
    recipients: ['jjspilot24@gmail.com'],
    day_of_week: 1,
    hour: 9
  });
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [preview, setPreview] = useState(null);
  const [testRecipient, setTestRecipient] = useState('jjspilot24@gmail.com');

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API}/email-reports/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
        if (data.frequency) {
          setConfig(prev => ({
            ...prev,
            enabled: data.reports_enabled,
            frequency: data.frequency,
            recipients: data.recipients || ['jjspilot24@gmail.com']
          }));
        }
      }
    } catch (e) {
      console.error('Failed to fetch email status:', e);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API}/email-reports/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setHistory(data.logs || []);
      }
    } catch (e) {
      console.error('Failed to fetch email history:', e);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchStatus(), fetchHistory()]);
      setLoading(false);
    };
    loadData();
  }, []);

  const saveConfig = async () => {
    try {
      const res = await fetch(`${API}/email-reports/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(config)
      });
      if (res.ok) {
        showToast('Email report configuration saved!', 'success');
        fetchStatus();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to save config', 'error');
      }
    } catch (e) {
      showToast('Error saving configuration', 'error');
    }
  };

  const sendTestEmail = async () => {
    setSending(true);
    try {
      const res = await fetch(`${API}/email-reports/send-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ recipient: testRecipient })
      });
      const data = await res.json();
      if (data.success) {
        showToast(`Test email sent to ${testRecipient}!`, 'success');
        fetchHistory();
      } else {
        showToast(data.error || 'Failed to send test email', 'error');
      }
    } catch (e) {
      showToast('Error sending test email', 'error');
    }
    setSending(false);
  };

  const sendNow = async () => {
    if (!window.confirm('Send A/B test report to all configured recipients now?')) return;
    setSending(true);
    try {
      const res = await fetch(`${API}/email-reports/send-now`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        showToast(`Report sent to ${data.sent_count} recipients!`, 'success');
        fetchHistory();
      } else {
        showToast(data.error || 'Failed to send report', 'error');
      }
    } catch (e) {
      showToast('Error sending report', 'error');
    }
    setSending(false);
  };

  const loadPreview = async () => {
    try {
      const res = await fetch(`${API}/email-reports/preview?days=7`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPreview(data);
      }
    } catch (e) {
      showToast('Error loading preview', 'error');
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>Loading email settings...</div>;
  }

  return (
    <div>
      <h3 style={{ marginBottom: 20, color: '#f472b6' }}>📧 A/B Test Email Reports</h3>
      <p style={{ color: '#a1a1aa', marginBottom: 25 }}>
        Automatically send A/B testing performance summaries to your email.
      </p>

      {/* Configuration Status */}
      <div style={{
        background: status?.email_configured ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
        border: `1px solid ${status?.email_configured ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
        borderRadius: 12,
        padding: 20,
        marginBottom: 25
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <span style={{ fontSize: '1.5rem' }}>{status?.email_configured ? '✅' : '⚠️'}</span>
          <span style={{ 
            color: status?.email_configured ? '#10b981' : '#ef4444',
            fontWeight: 600,
            fontSize: '1.1rem'
          }}>
            {status?.email_configured ? 'Email Configured' : 'Email Not Configured'}
          </span>
        </div>
        {status?.gmail_address && (
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem', margin: 0 }}>
            Sending from: {status.gmail_address}
          </p>
        )}
        {!status?.email_configured && (
          <div style={{ marginTop: 15, padding: 15, background: 'rgba(251, 191, 36, 0.1)', borderRadius: 8 }}>
            <p style={{ color: '#fbbf24', fontWeight: 600, margin: '0 0 10px 0' }}>⚠️ Gmail App Password Required</p>
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: 0, lineHeight: 1.6 }}>
              To send emails via Gmail, you need an <strong>App Password</strong> (not your regular Gmail password):<br/>
              1. Go to <a href="https://myaccount.google.com/security" target="_blank" rel="noreferrer" style={{ color: '#3b82f6' }}>myaccount.google.com/security</a><br/>
              2. Enable 2-Step Verification if not already enabled<br/>
              3. Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" style={{ color: '#3b82f6' }}>App Passwords</a><br/>
              4. Create a new app password for "Mail" → "Other (InfoPilot)"<br/>
              5. Copy the 16-character password and update the backend .env file
            </p>
          </div>
        )}
      </div>

      {/* Report Configuration */}
      <div style={{
        background: 'rgba(139, 92, 246, 0.1)',
        border: '1px solid rgba(139, 92, 246, 0.3)',
        borderRadius: 12,
        padding: 20,
        marginBottom: 25
      }}>
        <h4 style={{ color: '#a78bfa', marginBottom: 15 }}>⚙️ Report Settings</h4>
        
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'center', marginBottom: 15 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
              style={{ width: 20, height: 20, accentColor: '#8b5cf6' }}
            />
            <span style={{ color: config.enabled ? '#10b981' : '#a1a1aa', fontWeight: 600 }}>
              {config.enabled ? '✅ Reports Enabled' : '⏸️ Reports Disabled'}
            </span>
          </label>
        </div>

        <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap', alignItems: 'center', marginBottom: 15 }}>
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>Frequency</label>
            <select
              value={config.frequency}
              onChange={(e) => setConfig({ ...config, frequency: e.target.value })}
              style={{
                background: 'rgba(30, 20, 50, 0.8)',
                border: '1px solid rgba(139, 92, 246, 0.5)',
                borderRadius: 8,
                padding: '8px 12px',
                color: '#fff'
              }}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>Day of Week</label>
            <select
              value={config.day_of_week}
              onChange={(e) => setConfig({ ...config, day_of_week: parseInt(e.target.value) })}
              style={{
                background: 'rgba(30, 20, 50, 0.8)',
                border: '1px solid rgba(139, 92, 246, 0.5)',
                borderRadius: 8,
                padding: '8px 12px',
                color: '#fff'
              }}
            >
              <option value={1}>Monday</option>
              <option value={2}>Tuesday</option>
              <option value={3}>Wednesday</option>
              <option value={4}>Thursday</option>
              <option value={5}>Friday</option>
              <option value={6}>Saturday</option>
              <option value={0}>Sunday</option>
            </select>
          </div>

          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>Time (UTC)</label>
            <select
              value={config.hour}
              onChange={(e) => setConfig({ ...config, hour: parseInt(e.target.value) })}
              style={{
                background: 'rgba(30, 20, 50, 0.8)',
                border: '1px solid rgba(139, 92, 246, 0.5)',
                borderRadius: 8,
                padding: '8px 12px',
                color: '#fff'
              }}
            >
              {[...Array(24)].map((_, i) => (
                <option key={i} value={i}>{i.toString().padStart(2, '0')}:00</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 15 }}>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>Recipients (comma-separated)</label>
          <input
            type="text"
            value={config.recipients.join(', ')}
            onChange={(e) => setConfig({ ...config, recipients: e.target.value.split(',').map(r => r.trim()).filter(r => r) })}
            placeholder="email@example.com, another@example.com"
            style={{
              width: '100%',
              maxWidth: 400,
              background: 'rgba(30, 20, 50, 0.8)',
              border: '1px solid rgba(139, 92, 246, 0.5)',
              borderRadius: 8,
              padding: '10px 12px',
              color: '#fff'
            }}
          />
        </div>

        <button
          className="btn btn-primary"
          onClick={saveConfig}
          style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}
        >
          💾 Save Configuration
        </button>
      </div>

      {/* Send Controls */}
      <div style={{
        background: 'rgba(59, 130, 246, 0.1)',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: 12,
        padding: 20,
        marginBottom: 25
      }}>
        <h4 style={{ color: '#60a5fa', marginBottom: 15 }}>📤 Send Reports</h4>
        
        <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 15 }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 5 }}>Test Recipient</label>
            <input
              type="email"
              value={testRecipient}
              onChange={(e) => setTestRecipient(e.target.value)}
              placeholder="test@email.com"
              style={{
                width: '100%',
                background: 'rgba(30, 20, 50, 0.8)',
                border: '1px solid rgba(59, 130, 246, 0.5)',
                borderRadius: 8,
                padding: '10px 12px',
                color: '#fff'
              }}
            />
          </div>
          <button
            className="btn btn-secondary"
            onClick={sendTestEmail}
            disabled={sending || !status?.email_configured}
            style={{ padding: '10px 20px' }}
          >
            {sending ? '📧 Sending...' : '🧪 Send Test'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: 15, flexWrap: 'wrap' }}>
          <button
            className="btn btn-success"
            onClick={sendNow}
            disabled={sending || !status?.email_configured}
          >
            {sending ? '📧 Sending...' : '📤 Send Report Now'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={loadPreview}
          >
            👁️ Preview Report
          </button>
        </div>
      </div>

      {/* Preview */}
      {preview && (
        <div style={{ marginBottom: 25 }}>
          <h4 style={{ color: '#f472b6', marginBottom: 10 }}>📋 Report Preview</h4>
          <div style={{
            background: '#fff',
            borderRadius: 12,
            padding: 0,
            maxHeight: 500,
            overflow: 'auto',
            border: '2px solid rgba(236, 72, 153, 0.3)'
          }}>
            <div dangerouslySetInnerHTML={{ __html: preview.html_preview }} />
          </div>
          <div style={{ marginTop: 10, padding: 10, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 8 }}>
            <p style={{ color: '#a1a1aa', fontSize: '0.85rem', margin: 0 }}>
              <strong>Subject:</strong> {preview.subject}
            </p>
          </div>
        </div>
      )}

      {/* History */}
      <div>
        <h4 style={{ color: '#f472b6', marginBottom: 15 }}>📜 Send History</h4>
        {history.length === 0 ? (
          <p style={{ color: '#a1a1aa' }}>No emails sent yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {history.map((log) => (
              <div key={log.id} style={{
                padding: 15,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 10,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 10,
                border: `1px solid ${log.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
              }}>
                <div>
                  <span style={{ color: log.success ? '#10b981' : '#ef4444', marginRight: 10 }}>
                    {log.success ? '✅' : '❌'}
                  </span>
                  <span style={{ color: '#fff' }}>{log.recipient}</span>
                </div>
                <div style={{ display: 'flex', gap: 15, color: '#a1a1aa', fontSize: '0.85rem' }}>
                  <span>{log.period_days} days data</span>
                  <span>{new Date(log.sent_at).toLocaleString()}</span>
                </div>
                {log.error && (
                  <div style={{ width: '100%', color: '#ef4444', fontSize: '0.85rem' }}>
                    Error: {log.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Box */}
      <div style={{ marginTop: 25, padding: 15, background: 'rgba(236, 72, 153, 0.1)', borderRadius: 10, border: '1px solid rgba(236, 72, 153, 0.3)' }}>
        <p style={{ fontSize: '0.85rem', color: '#f472b6', margin: 0 }}>
          💡 <strong>A/B Test Reports Include:</strong><br/>
          • Summary of all active tests with variant performance<br/>
          • Conversion rates and impression counts<br/>
          • Leading variants for each test<br/>
          • Recommendations for optimizing marketing copy<br/>
          • Direct link to your admin dashboard
        </p>
      </div>
    </div>
  );
};

export default AdminPanel;
