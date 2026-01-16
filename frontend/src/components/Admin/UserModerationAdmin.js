import React, { useState, useEffect } from 'react';
import { API } from '../../utils/api';

const UserModerationAdmin = ({ token, showToast }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [moderationHistory, setModerationHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  
  // Moderation form state
  const [moderationAction, setModerationAction] = useState('');
  const [reason, setReason] = useState('');
  const [personalNote, setPersonalNote] = useState('');
  const [muteDuration, setMuteDuration] = useState(24);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUsers(data.users || []);
      }
    } catch (e) {
      console.error('Failed to fetch users:', e);
    }
    setLoading(false);
  };

  const fetchModerationHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch(`${API}/admin/moderation/actions?limit=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setModerationHistory(data.actions || []);
      }
    } catch (e) {
      console.error('Failed to fetch moderation history:', e);
    }
    setHistoryLoading(false);
  };

  useEffect(() => {
    fetchUsers();
    fetchModerationHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredUsers = users.filter(user => 
    user.username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleModeration = async () => {
    if (!selectedUser || !moderationAction) {
      showToast('Please select a user and action', 'error');
      return;
    }

    setActionLoading(true);
    
    try {
      let endpoint = '';
      let method = moderationAction === 'delete' ? 'DELETE' : 'POST';
      let body = {};

      switch (moderationAction) {
        case 'ban':
          endpoint = `/admin/users/${selectedUser.id}/ban`;
          body = { reason, personal_note: personalNote };
          break;
        case 'unban':
          endpoint = `/admin/users/${selectedUser.id}/unban`;
          break;
        case 'mute':
          endpoint = `/admin/users/${selectedUser.id}/mute`;
          body = { reason, personal_note: personalNote, duration_hours: muteDuration };
          break;
        case 'unmute':
          endpoint = `/admin/users/${selectedUser.id}/unmute`;
          break;
        case 'delete':
          endpoint = `/admin/users/${selectedUser.id}`;
          body = { reason, personal_note: personalNote };
          break;
        default:
          showToast('Invalid action', 'error');
          setActionLoading(false);
          return;
      }

      const res = await fetch(`${API}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: method !== 'GET' ? JSON.stringify(body) : undefined
      });

      if (res.ok) {
        const data = await res.json();
        showToast(data.message || `User ${moderationAction}ed successfully!`, 'success');
        setSelectedUser(null);
        setModerationAction('');
        setReason('');
        setPersonalNote('');
        fetchUsers();
        fetchModerationHistory();
      } else {
        const err = await res.json();
        showToast(err.detail || `Failed to ${moderationAction} user`, 'error');
      }
    } catch (e) {
      showToast(`Error: ${e.message}`, 'error');
    }
    
    setActionLoading(false);
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'ban_user': return '#ef4444';
      case 'unban_user': return '#10b981';
      case 'mute_user': return '#f59e0b';
      case 'unmute_user': return '#3b82f6';
      case 'delete_user': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'ban_user': return '🚫';
      case 'unban_user': return '✅';
      case 'mute_user': return '🔇';
      case 'unmute_user': return '🔊';
      case 'delete_user': return '🗑️';
      default: return '📋';
    }
  };

  return (
    <div>
      <h3 style={{ marginBottom: 20, color: '#f472b6' }}>🛡️ User Moderation</h3>
      <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
        Manage users across the entire platform. Ban, mute, or remove users who violate the User Agreement.
      </p>

      {/* User Search */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(59, 130, 246, 0.15))',
        borderRadius: 12,
        padding: 20,
        marginBottom: 25,
        border: '1px solid rgba(124, 58, 237, 0.3)'
      }}>
        <h4 style={{ color: '#a78bfa', margin: '0 0 15px 0' }}>🔍 Find User</h4>
        <input
          type="text"
          placeholder="Search by username or email..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '12px 15px',
            borderRadius: 8,
            border: '1px solid rgba(124, 58, 237, 0.3)',
            background: 'rgba(30, 20, 50, 0.5)',
            color: '#fff',
            marginBottom: 15
          }}
          data-testid="user-search-input"
        />
        
        {loading ? (
          <div style={{ color: '#a1a1aa', textAlign: 'center', padding: 20 }}>Loading users...</div>
        ) : (
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {filteredUsers.length === 0 ? (
              <div style={{ color: '#a1a1aa', textAlign: 'center', padding: 20 }}>
                {searchQuery ? 'No users found matching your search' : 'No users to display'}
              </div>
            ) : (
              filteredUsers.slice(0, 20).map(user => (
                <div
                  key={user.id}
                  onClick={() => setSelectedUser(user)}
                  style={{
                    padding: '12px 15px',
                    marginBottom: 8,
                    borderRadius: 8,
                    background: selectedUser?.id === user.id 
                      ? 'rgba(124, 58, 237, 0.3)' 
                      : 'rgba(255, 255, 255, 0.05)',
                    border: selectedUser?.id === user.id 
                      ? '2px solid #7c3aed' 
                      : '1px solid rgba(255, 255, 255, 0.1)',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  data-testid={`user-row-${user.id}`}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ 
                        color: user.is_admin ? '#f472b6' : '#fff', 
                        fontWeight: user.is_admin ? 600 : 400 
                      }}>
                        {user.username || 'No username'}
                        {user.is_admin && <span style={{ marginLeft: 8, fontSize: '0.7rem', background: '#f472b6', padding: '2px 6px', borderRadius: 4, color: '#fff' }}>ADMIN</span>}
                      </span>
                      <div style={{ color: '#a1a1aa', fontSize: '0.8rem' }}>{user.email}</div>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {user.is_banned && (
                        <span style={{ fontSize: '0.7rem', background: 'rgba(239, 68, 68, 0.2)', padding: '3px 8px', borderRadius: 4, color: '#ef4444' }}>
                          BANNED
                        </span>
                      )}
                      {user.is_muted && (
                        <span style={{ fontSize: '0.7rem', background: 'rgba(245, 158, 11, 0.2)', padding: '3px 8px', borderRadius: 4, color: '#f59e0b' }}>
                          MUTED
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Moderation Actions */}
      {selectedUser && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(245, 158, 11, 0.1))',
          borderRadius: 12,
          padding: 20,
          marginBottom: 25,
          border: '2px solid rgba(239, 68, 68, 0.3)'
        }}>
          <h4 style={{ color: '#ef4444', margin: '0 0 15px 0' }}>
            ⚠️ Moderate User: {selectedUser.username || selectedUser.email}
          </h4>

          {selectedUser.is_admin ? (
            <div style={{ 
              background: 'rgba(239, 68, 68, 0.2)', 
              padding: 15, 
              borderRadius: 8, 
              color: '#fca5a5',
              textAlign: 'center'
            }}>
              🛡️ Cannot moderate admin users. Remove admin status first.
            </div>
          ) : (
            <>
              {/* Action Selection */}
              <div style={{ marginBottom: 15 }}>
                <label style={{ color: '#f472b6', fontWeight: 600, display: 'block', marginBottom: 8 }}>
                  Select Action:
                </label>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  {[
                    { id: 'ban', label: '🚫 Ban', color: '#ef4444', disabled: selectedUser.is_banned },
                    { id: 'unban', label: '✅ Unban', color: '#10b981', disabled: !selectedUser.is_banned },
                    { id: 'mute', label: '🔇 Mute', color: '#f59e0b', disabled: selectedUser.is_muted },
                    { id: 'unmute', label: '🔊 Unmute', color: '#3b82f6', disabled: !selectedUser.is_muted },
                    { id: 'delete', label: '🗑️ Delete', color: '#dc2626', disabled: false }
                  ].map(action => (
                    <button
                      key={action.id}
                      onClick={() => setModerationAction(action.id)}
                      disabled={action.disabled}
                      style={{
                        padding: '10px 16px',
                        borderRadius: 8,
                        border: moderationAction === action.id 
                          ? `2px solid ${action.color}` 
                          : '1px solid rgba(255, 255, 255, 0.2)',
                        background: moderationAction === action.id 
                          ? `${action.color}30` 
                          : 'rgba(255, 255, 255, 0.05)',
                        color: action.disabled ? '#6b7280' : action.color,
                        cursor: action.disabled ? 'not-allowed' : 'pointer',
                        opacity: action.disabled ? 0.5 : 1,
                        fontWeight: moderationAction === action.id ? 600 : 400,
                        transition: 'all 0.2s'
                      }}
                      data-testid={`action-${action.id}`}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Mute Duration (only for mute action) */}
              {moderationAction === 'mute' && (
                <div style={{ marginBottom: 15 }}>
                  <label style={{ color: '#f59e0b', fontWeight: 600, display: 'block', marginBottom: 8 }}>
                    Mute Duration (hours):
                  </label>
                  <select
                    value={muteDuration}
                    onChange={(e) => setMuteDuration(parseInt(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '10px 15px',
                      borderRadius: 8,
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      background: 'rgba(30, 20, 50, 0.5)',
                      color: '#fff'
                    }}
                  >
                    <option value={1}>1 hour</option>
                    <option value={6}>6 hours</option>
                    <option value={12}>12 hours</option>
                    <option value={24}>24 hours (1 day)</option>
                    <option value={72}>72 hours (3 days)</option>
                    <option value={168}>168 hours (1 week)</option>
                    <option value={720}>720 hours (30 days)</option>
                  </select>
                </div>
              )}

              {/* Reason */}
              {['ban', 'mute', 'delete'].includes(moderationAction) && (
                <>
                  <div style={{ marginBottom: 15 }}>
                    <label style={{ color: '#f472b6', fontWeight: 600, display: 'block', marginBottom: 8 }}>
                      Reason (shown to user):
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., Violation of User Agreement, Spamming, Harassment..."
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 15px',
                        borderRadius: 8,
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        background: 'rgba(30, 20, 50, 0.5)',
                        color: '#fff'
                      }}
                      data-testid="reason-input"
                    />
                  </div>

                  <div style={{ marginBottom: 15 }}>
                    <label style={{ color: '#a78bfa', fontWeight: 600, display: 'block', marginBottom: 8 }}>
                      Personal Note (admin only, not shown to user):
                    </label>
                    <textarea
                      placeholder="Internal notes about this action..."
                      value={personalNote}
                      onChange={(e) => setPersonalNote(e.target.value)}
                      rows={2}
                      style={{
                        width: '100%',
                        padding: '10px 15px',
                        borderRadius: 8,
                        border: '1px solid rgba(124, 58, 237, 0.3)',
                        background: 'rgba(30, 20, 50, 0.5)',
                        color: '#fff',
                        resize: 'vertical'
                      }}
                      data-testid="personal-note-input"
                    />
                  </div>
                </>
              )}

              {/* Confirmation */}
              {moderationAction && (
                <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
                  <button
                    onClick={() => {
                      setSelectedUser(null);
                      setModerationAction('');
                      setReason('');
                      setPersonalNote('');
                    }}
                    style={{
                      flex: 1,
                      padding: '12px 20px',
                      borderRadius: 8,
                      border: '1px solid rgba(107, 114, 128, 0.3)',
                      background: 'rgba(107, 114, 128, 0.2)',
                      color: '#9ca3af',
                      cursor: 'pointer',
                      fontWeight: 600
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      if (moderationAction === 'delete') {
                        if (!window.confirm(`⚠️ PERMANENT ACTION: Delete user "${selectedUser.username}" and ALL their data? This cannot be undone!`)) {
                          return;
                        }
                      }
                      handleModeration();
                    }}
                    disabled={actionLoading}
                    style={{
                      flex: 1,
                      padding: '12px 20px',
                      borderRadius: 8,
                      border: 'none',
                      background: moderationAction === 'delete' 
                        ? 'linear-gradient(135deg, #dc2626, #ef4444)' 
                        : 'linear-gradient(135deg, #7c3aed, #a78bfa)',
                      color: '#fff',
                      cursor: actionLoading ? 'wait' : 'pointer',
                      fontWeight: 600,
                      opacity: actionLoading ? 0.7 : 1
                    }}
                    data-testid="confirm-moderation-btn"
                  >
                    {actionLoading ? 'Processing...' : `Confirm ${moderationAction.charAt(0).toUpperCase() + moderationAction.slice(1)}`}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Moderation History */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(6, 182, 212, 0.1))',
        borderRadius: 12,
        padding: 20,
        border: '1px solid rgba(59, 130, 246, 0.3)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
          <h4 style={{ color: '#3b82f6', margin: 0 }}>📜 Moderation History</h4>
          <button
            onClick={fetchModerationHistory}
            style={{
              padding: '6px 12px',
              borderRadius: 6,
              border: '1px solid rgba(59, 130, 246, 0.3)',
              background: 'rgba(59, 130, 246, 0.2)',
              color: '#3b82f6',
              cursor: 'pointer',
              fontSize: '0.85rem'
            }}
          >
            🔄 Refresh
          </button>
        </div>

        {historyLoading ? (
          <div style={{ color: '#a1a1aa', textAlign: 'center', padding: 20 }}>Loading history...</div>
        ) : moderationHistory.length === 0 ? (
          <div style={{ color: '#a1a1aa', textAlign: 'center', padding: 30 }}>
            <div style={{ fontSize: '2rem', marginBottom: 10 }}>🛡️</div>
            <p>No moderation actions yet</p>
          </div>
        ) : (
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {moderationHistory.map((action) => (
              <div
                key={action.id}
                style={{
                  padding: '12px 15px',
                  marginBottom: 8,
                  borderRadius: 8,
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderLeft: `3px solid ${getActionColor(action.action)}`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 5 }}>
                  <div>
                    <span style={{ fontSize: '1.2rem', marginRight: 8 }}>{getActionIcon(action.action)}</span>
                    <span style={{ color: getActionColor(action.action), fontWeight: 600 }}>
                      {action.action?.replace('_', ' ').toUpperCase()}
                    </span>
                    <span style={{ color: '#fff', marginLeft: 10 }}>
                      {action.target_username}
                    </span>
                  </div>
                  <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>
                    {action.created_at ? new Date(action.created_at).toLocaleString() : 'Unknown date'}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>
                  by {action.admin_username}
                  {action.reason && <span style={{ marginLeft: 10 }}>| {action.reason}</span>}
                </div>
                {action.personal_note && (
                  <div style={{ 
                    fontSize: '0.75rem', 
                    color: '#a78bfa', 
                    marginTop: 5,
                    fontStyle: 'italic',
                    background: 'rgba(124, 58, 237, 0.1)',
                    padding: '5px 10px',
                    borderRadius: 4
                  }}>
                    📝 Note: {action.personal_note}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Box */}
      <div style={{ 
        marginTop: 25, 
        padding: 15, 
        background: 'rgba(16, 185, 129, 0.1)', 
        borderRadius: 10, 
        border: '1px solid rgba(16, 185, 129, 0.3)' 
      }}>
        <p style={{ fontSize: '0.85rem', color: '#10b981', margin: 0 }}>
          💡 <strong>Moderation Guide:</strong><br/>
          • <strong>Ban:</strong> User cannot access the platform at all<br/>
          • <strong>Mute:</strong> User can browse but cannot post, comment, or chat<br/>
          • <strong>Delete:</strong> Permanently removes user and all their data<br/>
          • All actions are logged with timestamps and admin notes
        </p>
      </div>
    </div>
  );
};

export default UserModerationAdmin;
