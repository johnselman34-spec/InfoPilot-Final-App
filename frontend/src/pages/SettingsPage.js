import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API } from '../utils/api';
import { DataExport } from '../components/shared';

const SettingsPage = ({ showToast, setCurrentPage }) => {
  const { token, user, refreshUser } = useAuth();
  const [settings, setSettings] = useState({
    ultimate_search_public: user?.ultimate_search_public || false,
    friends_visible: user?.friends_visible || false
  });
  
  // Password change state
  const [hasPassword, setHasPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [showPasswordSection, setShowPasswordSection] = useState(false);

  // Check if user has password on mount
  useEffect(() => {
    const checkPassword = async () => {
      try {
        const res = await fetch(`${API}/users/has-password`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const data = await res.json();
        setHasPassword(data.has_password);
      } catch (e) {
        console.error('Failed to check password status');
      }
    };
    checkPassword();
  }, [token]);

  const updateSettings = async () => {
    try {
      const params = new URLSearchParams();
      params.append('ultimate_search_public', settings.ultimate_search_public);
      params.append('friends_visible', settings.friends_visible);
      
      await fetch(`${API}/users/settings?${params}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      });
      showToast('Settings saved!', 'success');
      refreshUser();
    } catch (e) {
      showToast('Failed to save settings', 'error');
    }
  };

  const handleChangePassword = async () => {
    // Validation
    if (newPassword.length < 6) {
      showToast('Password must be at least 6 characters', 'error');
      return;
    }
    if (newPassword !== confirmPassword) {
      showToast('Passwords do not match', 'error');
      return;
    }
    if (hasPassword && !currentPassword) {
      showToast('Current password is required', 'error');
      return;
    }

    setPasswordLoading(true);
    try {
      const res = await fetch(`${API}/users/change-password`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({
          current_password: hasPassword ? currentPassword : null,
          new_password: newPassword
        })
      });

      const data = await res.json();
      
      if (res.ok) {
        showToast('Password changed successfully!', 'success');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setShowPasswordSection(false);
        setHasPassword(true);
      } else {
        showToast(data.detail || 'Failed to change password', 'error');
      }
    } catch (e) {
      showToast('Failed to change password', 'error');
    }
    setPasswordLoading(false);
  };

  return (
    <div className="card" data-testid="settings-page">
      <div className="card-header">
        <h2>User Settings</h2>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div style={{ padding: 15, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.ultimate_search_public}
              onChange={(e) => setSettings({ ...settings, ultimate_search_public: e.target.checked })}
            />
            <div>
              <strong>Make Ultimate Search Page Public</strong>
              <p style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 4 }}>
                Allow other users to view your Ultimate Search page and public categories
              </p>
            </div>
          </label>
        </div>

        <div style={{ padding: 15, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.friends_visible}
              onChange={(e) => setSettings({ ...settings, friends_visible: e.target.checked })}
            />
            <div>
              <strong>Show Friends List to Others</strong>
              <p style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 4 }}>
                Allow other users to see your friends list
              </p>
            </div>
          </label>
        </div>

        <button className="btn btn-primary" onClick={updateSettings} data-testid="save-settings-btn">
          Save Settings
        </button>

        {/* Account Info */}
        <div style={{ marginTop: 20, padding: 20, background: 'rgba(124, 58, 237, 0.1)', borderRadius: 10 }}>
          <h3 style={{ marginBottom: 15, color: '#f472b6' }}>Account Information</h3>
          <p><strong>Username:</strong> {user?.username}</p>
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>Status:</strong> {user?.is_admin ? 'Admin' : (user?.is_paid ? 'Premium' : 'Free')}</p>
        </div>

        {/* Password Change Section */}
        <div style={{ padding: 20, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: showPasswordSection ? 15 : 0 }}>
            <h3 style={{ color: '#f472b6', margin: 0 }}>
              {hasPassword ? 'Change Password' : 'Set Password'}
            </h3>
            <button 
              className="btn btn-secondary"
              onClick={() => setShowPasswordSection(!showPasswordSection)}
              style={{ padding: '8px 16px', fontSize: '0.9rem' }}
              data-testid="toggle-password-section-btn"
            >
              {showPasswordSection ? 'Cancel' : hasPassword ? 'Change' : 'Set Password'}
            </button>
          </div>
          
          {!hasPassword && !showPasswordSection && (
            <p style={{ fontSize: '0.85rem', color: '#a1a1aa', marginTop: 10 }}>
              You signed in with Google. Set a password to also login with email.
            </p>
          )}
          
          {showPasswordSection && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {hasPassword && (
                <input
                  type="password"
                  placeholder="Current Password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="input"
                  data-testid="current-password-input"
                />
              )}
              <input
                type="password"
                placeholder="New Password (min 6 characters)"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input"
                data-testid="new-password-input"
              />
              <input
                type="password"
                placeholder="Confirm New Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input"
                data-testid="confirm-password-input"
              />
              <button 
                className="btn btn-primary"
                onClick={handleChangePassword}
                disabled={passwordLoading}
                data-testid="change-password-btn"
              >
                {passwordLoading ? 'Saving...' : (hasPassword ? 'Change Password' : 'Set Password')}
              </button>
            </div>
          )}
        </div>

        {/* Subscription */}
        {!user?.is_paid && !user?.is_admin && (
          <div style={{ padding: 20, background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(124, 58, 237, 0.2))', borderRadius: 10, border: '1px solid rgba(236, 72, 153, 0.3)' }}>
            <h3 style={{ marginBottom: 10, color: '#f472b6' }}>Upgrade to Premium</h3>
            <p style={{ fontSize: '0.9rem', color: '#a1a1aa', marginBottom: 15 }}>
              Get unlimited search results, access to the interactive map, and more!
            </p>
            <button className="btn btn-primary" onClick={() => setCurrentPage('subscribe')} data-testid="upgrade-premium-btn">Subscribe - Pay What You Want</button>
          </div>
        )}

        {/* Data Export Section */}
        <div style={{ marginTop: 20 }}>
          <DataExport showToast={showToast} />
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
