import React, { useState, useEffect, useCallback } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

const ViolationAlerts = ({ showToast }) => {
  const [settings, setSettings] = useState({
    enabled: false,
    threshold: 10,
    time_window_hours: 24,
    email_notifications: true,
    notification_emails: []
  });
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const token = localStorage.getItem('token');

  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/admin/violation-alerts/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
    } catch (e) {
      console.error('Failed to fetch alert settings:', e);
    }
  }, [token]);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/admin/alerts?limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAlerts(data.alerts || []);
      }
    } catch (e) {
      console.error('Failed to fetch alerts:', e);
    }
    setLoading(false);
  }, [token]);

  useEffect(() => {
    fetchSettings();
    fetchAlerts();
  }, [fetchSettings, fetchAlerts]);

  const saveSettings = async () => {
    try {
      const res = await fetch(`${API}/api/admin/violation-alerts/settings`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify(settings)
      });
      
      if (res.ok) {
        showToast('Alert settings saved!', 'success');
      } else {
        showToast('Failed to save settings', 'error');
      }
    } catch (e) {
      showToast('Failed to save settings', 'error');
    }
  };

  const checkNow = async () => {
    setChecking(true);
    try {
      const res = await fetch(`${API}/api/admin/violation-alerts/check`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        showToast(data.message, data.alert_triggered ? 'warning' : 'success');
        fetchAlerts();
      } else {
        showToast('Failed to check for alerts', 'error');
      }
    } catch (e) {
      showToast('Failed to check for alerts', 'error');
    }
    setChecking(false);
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      const res = await fetch(`${API}/api/admin/alerts/${alertId}/acknowledge`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast('Alert acknowledged', 'success');
        fetchAlerts();
      }
    } catch (e) {
      showToast('Failed to acknowledge alert', 'error');
    }
  };

  const addEmail = () => {
    if (newEmail && newEmail.includes('@') && !settings.notification_emails.includes(newEmail)) {
      setSettings({
        ...settings,
        notification_emails: [...settings.notification_emails, newEmail]
      });
      setNewEmail('');
    }
  };

  const removeEmail = (email) => {
    setSettings({
      ...settings,
      notification_emails: settings.notification_emails.filter(e => e !== email)
    });
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <div className="loading-spinner"><div className="spinner"></div></div>
        <p style={{ color: '#a1a1aa', marginTop: 15 }}>Loading alert settings...</p>
      </div>
    );
  }

  return (
    <div data-testid="violation-alerts-admin">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ color: '#ef4444', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          🚨 Violation Alerts
          <span style={{ 
            fontSize: '0.75rem', 
            background: settings.enabled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)', 
            padding: '4px 12px', 
            borderRadius: 20,
            color: settings.enabled ? '#10b981' : '#ef4444'
          }}>
            {settings.enabled ? 'ACTIVE' : 'DISABLED'}
          </span>
        </h3>
        <button 
          onClick={checkNow}
          disabled={checking}
          className="btn btn-primary"
          style={{ padding: '8px 16px' }}
        >
          {checking ? '🔄 Checking...' : '🔍 Check Now'}
        </button>
      </div>

      {/* Settings Card */}
      <div style={{
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 12,
        padding: 20,
        border: '1px solid rgba(124, 58, 237, 0.2)',
        marginBottom: 25
      }}>
        <h4 style={{ color: '#a78bfa', marginBottom: 15 }}>⚙️ Alert Configuration</h4>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginBottom: 20 }}>
          {/* Enable Toggle */}
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 8 }}>
              Alert Status
            </label>
            <button
              onClick={() => setSettings({ ...settings, enabled: !settings.enabled })}
              style={{
                padding: '10px 20px',
                borderRadius: 8,
                border: 'none',
                background: settings.enabled 
                  ? 'linear-gradient(135deg, #10b981, #059669)' 
                  : 'rgba(239, 68, 68, 0.2)',
                color: '#fff',
                fontWeight: 600,
                cursor: 'pointer',
                width: '100%'
              }}
            >
              {settings.enabled ? '✅ Enabled' : '❌ Disabled'}
            </button>
          </div>
          
          {/* Threshold */}
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 8 }}>
              Violation Threshold
            </label>
            <input
              type="number"
              value={settings.threshold}
              onChange={(e) => setSettings({ ...settings, threshold: parseInt(e.target.value) || 10 })}
              min="1"
              max="100"
              className="input"
              style={{ width: '100%' }}
            />
          </div>
          
          {/* Time Window */}
          <div>
            <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 8 }}>
              Time Window (hours)
            </label>
            <select
              value={settings.time_window_hours}
              onChange={(e) => setSettings({ ...settings, time_window_hours: parseInt(e.target.value) })}
              className="input"
              style={{ width: '100%' }}
            >
              <option value={1}>1 hour</option>
              <option value={6}>6 hours</option>
              <option value={12}>12 hours</option>
              <option value={24}>24 hours</option>
              <option value={48}>48 hours</option>
              <option value={72}>72 hours</option>
            </select>
          </div>
        </div>
        
        {/* Notification Emails */}
        <div style={{ marginBottom: 20 }}>
          <label style={{ color: '#a1a1aa', fontSize: '0.85rem', display: 'block', marginBottom: 8 }}>
            Notification Emails
          </label>
          <div style={{ display: 'flex', gap: 10, marginBottom: 10 }}>
            <input
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="Add email for alerts..."
              className="input"
              style={{ flex: 1 }}
              onKeyPress={(e) => e.key === 'Enter' && addEmail()}
            />
            <button onClick={addEmail} className="btn btn-secondary">+ Add</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {settings.notification_emails.map((email, idx) => (
              <span 
                key={idx}
                style={{
                  background: 'rgba(124, 58, 237, 0.2)',
                  padding: '6px 12px',
                  borderRadius: 20,
                  color: '#a78bfa',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8
                }}
              >
                {email}
                <button 
                  onClick={() => removeEmail(email)}
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    color: '#ef4444', 
                    cursor: 'pointer',
                    padding: 0,
                    fontSize: '1rem'
                  }}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
        
        <button onClick={saveSettings} className="btn btn-primary">
          💾 Save Settings
        </button>
      </div>

      {/* Alert Rule Description */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05))',
        borderRadius: 12,
        padding: 15,
        border: '1px solid rgba(245, 158, 11, 0.3)',
        marginBottom: 25
      }}>
        <p style={{ color: '#f59e0b', margin: 0, fontSize: '0.9rem' }}>
          ⚡ <strong>Alert Rule:</strong> Trigger alert when {settings.threshold}+ violations occur within {settings.time_window_hours} hour{settings.time_window_hours > 1 ? 's' : ''}
        </p>
      </div>

      {/* Recent Alerts */}
      <div style={{
        background: 'rgba(30, 20, 50, 0.5)',
        borderRadius: 12,
        padding: 20,
        border: '1px solid rgba(124, 58, 237, 0.2)'
      }}>
        <h4 style={{ color: '#ef4444', marginBottom: 15 }}>📋 Alert History</h4>
        
        {alerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: '#a1a1aa' }}>
            <div style={{ fontSize: '2rem', marginBottom: 10 }}>✨</div>
            <p>No alerts yet. Your community is behaving!</p>
          </div>
        ) : (
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {alerts.map((alert) => (
              <div 
                key={alert.id}
                style={{
                  padding: 12,
                  background: alert.acknowledged ? 'rgba(0,0,0,0.1)' : 'rgba(239, 68, 68, 0.1)',
                  borderRadius: 8,
                  marginBottom: 8,
                  borderLeft: `3px solid ${alert.acknowledged ? '#71717a' : '#ef4444'}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ 
                      fontSize: '0.85rem', 
                      fontWeight: 600, 
                      color: alert.acknowledged ? '#71717a' : '#ef4444' 
                    }}>
                      ⚠️ {alert.violations_count} violations
                    </span>
                    <span style={{ 
                      fontSize: '0.7rem', 
                      background: 'rgba(124, 58, 237, 0.2)',
                      padding: '2px 8px',
                      borderRadius: 4,
                      color: '#a78bfa'
                    }}>
                      Threshold: {alert.threshold}
                    </span>
                  </div>
                  <span style={{ color: '#71717a', fontSize: '0.75rem' }}>
                    {new Date(alert.created_at).toLocaleString()}
                  </span>
                </div>
                {!alert.acknowledged && (
                  <button 
                    onClick={() => acknowledgeAlert(alert.id)}
                    className="btn btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                  >
                    ✓ Acknowledge
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ViolationAlerts;
