import React, { useState, useEffect, useCallback } from 'react';
import { API } from '../../utils/api';

/**
 * ModerationPanel - Admin/Moderator tools for managing group/page members
 * Provides UI for boot, ban, mute, unban, unmute operations
 */
const ModerationPanel = ({ 
  type, // 'group' or 'page'
  entityId, 
  entityName,
  token, 
  currentUserId,
  isOwner,
  isAdmin,
  isModerator,
  onClose,
  showToast 
}) => {
  const [members, setMembers] = useState([]);
  const [bannedMembers, setBannedMembers] = useState([]);
  const [mutedMembers, setMutedMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('members');
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoading, setActionLoading] = useState(null);
  const [banReason, setBanReason] = useState('');
  const [muteMinutes, setMuteMinutes] = useState(30);
  const [showBanModal, setShowBanModal] = useState(null);
  const [showMuteModal, setShowMuteModal] = useState(null);

  const canModerate = isOwner || isAdmin || isModerator;

  const fetchMembers = useCallback(async () => {
    if (!entityId || !token) return;
    setLoading(true);
    try {
      const endpoint = type === 'group' 
        ? `${API}/groups/${entityId}` 
        : `${API}/pages/${entityId}`;
      
      const res = await fetch(endpoint, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setMembers(data.members || []);
        setBannedMembers(data.banned_members || data.banned_users || []);
        setMutedMembers(data.muted_members || []);
      }
    } catch (e) {
      console.error('Failed to fetch members:', e);
    }
    setLoading(false);
  }, [entityId, token, type]);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  // Boot member (remove from group)
  const handleBoot = async (memberId, memberName) => {
    if (!window.confirm(`Are you sure you want to remove ${memberName} from the ${type}?`)) return;
    
    setActionLoading(memberId);
    try {
      const res = await fetch(`${API}/social/${type}s/${entityId}/members/${memberId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast(`${memberName} has been removed from the ${type}`, 'success');
        fetchMembers();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to remove member', 'error');
      }
    } catch (e) {
      showToast('Failed to remove member', 'error');
    }
    setActionLoading(null);
  };

  // Ban member
  const handleBan = async (memberId) => {
    setActionLoading(memberId);
    try {
      const endpoint = type === 'group'
        ? `${API}/social/groups/${entityId}/ban/${memberId}?reason=${encodeURIComponent(banReason)}`
        : `${API}/social/pages/${entityId}/ban/${memberId}?reason=${encodeURIComponent(banReason)}`;
      
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast('Member has been banned', 'success');
        setShowBanModal(null);
        setBanReason('');
        fetchMembers();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to ban member', 'error');
      }
    } catch (e) {
      showToast('Failed to ban member', 'error');
    }
    setActionLoading(null);
  };

  // Unban member
  const handleUnban = async (memberId, memberName) => {
    if (!window.confirm(`Unban ${memberName}?`)) return;
    
    setActionLoading(memberId);
    try {
      const endpoint = type === 'group'
        ? `${API}/social/groups/${entityId}/unban/${memberId}`
        : `${API}/social/pages/${entityId}/unban/${memberId}`;
      
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast(`${memberName} has been unbanned`, 'success');
        fetchMembers();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to unban member', 'error');
      }
    } catch (e) {
      showToast('Failed to unban member', 'error');
    }
    setActionLoading(null);
  };

  // Mute member (groups only)
  const handleMute = async (memberId) => {
    setActionLoading(memberId);
    try {
      const res = await fetch(`${API}/social/groups/${entityId}/mute/${memberId}?duration_minutes=${muteMinutes}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast(`Member has been muted for ${muteMinutes} minutes`, 'success');
        setShowMuteModal(null);
        setMuteMinutes(30);
        fetchMembers();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to mute member', 'error');
      }
    } catch (e) {
      showToast('Failed to mute member', 'error');
    }
    setActionLoading(null);
  };

  // Unmute member (groups only)
  const handleUnmute = async (memberId, memberName) => {
    setActionLoading(memberId);
    try {
      const res = await fetch(`${API}/social/groups/${entityId}/unmute/${memberId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        showToast(`${memberName} has been unmuted`, 'success');
        fetchMembers();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to unmute member', 'error');
      }
    } catch (e) {
      showToast('Failed to unmute member', 'error');
    }
    setActionLoading(null);
  };

  const filteredMembers = members.filter(m => 
    !searchQuery || 
    m.username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const tabStyle = (isActive) => ({
    padding: '10px 20px',
    background: isActive ? 'linear-gradient(135deg, #8b5cf6, #ec4899)' : 'rgba(30, 20, 50, 0.5)',
    border: isActive ? 'none' : '1px solid rgba(124, 58, 237, 0.3)',
    color: isActive ? '#fff' : '#a1a1aa',
    borderRadius: 8,
    cursor: 'pointer',
    fontWeight: isActive ? 600 : 400,
    transition: 'all 0.2s'
  });

  const buttonStyle = (variant = 'default') => ({
    padding: '6px 12px',
    borderRadius: 6,
    border: 'none',
    cursor: 'pointer',
    fontSize: '0.85rem',
    fontWeight: 500,
    transition: 'all 0.2s',
    ...(variant === 'danger' && { background: '#ef4444', color: '#fff' }),
    ...(variant === 'warning' && { background: '#f59e0b', color: '#000' }),
    ...(variant === 'success' && { background: '#10b981', color: '#fff' }),
    ...(variant === 'default' && { background: 'rgba(124, 58, 237, 0.3)', color: '#e2e8f0' })
  });

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: 'linear-gradient(135deg, rgba(30, 20, 50, 0.98), rgba(20, 10, 40, 0.98))',
        borderRadius: 16,
        width: '90%',
        maxWidth: 800,
        maxHeight: '90vh',
        overflow: 'hidden',
        border: '1px solid rgba(124, 58, 237, 0.3)'
      }}>
        {/* Header */}
        <div style={{
          padding: 20,
          borderBottom: '1px solid rgba(124, 58, 237, 0.2)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ margin: 0, color: '#e2e8f0' }}>
              🛡️ Moderation Panel
            </h2>
            <p style={{ margin: '5px 0 0', color: '#a1a1aa', fontSize: '0.9rem' }}>
              {entityName} - {type === 'group' ? 'Group' : 'Page'} Management
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#ef4444',
              padding: '8px 16px',
              borderRadius: 8,
              cursor: 'pointer'
            }}
          >
            ✕ Close
          </button>
        </div>

        {/* Tabs */}
        <div style={{ 
          padding: '15px 20px', 
          display: 'flex', 
          gap: 10,
          borderBottom: '1px solid rgba(124, 58, 237, 0.2)'
        }}>
          <button 
            onClick={() => setActiveTab('members')} 
            style={tabStyle(activeTab === 'members')}
          >
            👥 Members ({members.length})
          </button>
          <button 
            onClick={() => setActiveTab('banned')} 
            style={tabStyle(activeTab === 'banned')}
          >
            🚫 Banned ({bannedMembers.length})
          </button>
          {type === 'group' && (
            <button 
              onClick={() => setActiveTab('muted')} 
              style={tabStyle(activeTab === 'muted')}
            >
              🔇 Muted ({mutedMembers.length})
            </button>
          )}
        </div>

        {/* Search */}
        <div style={{ padding: '15px 20px' }}>
          <input
            type="text"
            placeholder="Search members..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 15px',
              borderRadius: 8,
              border: '1px solid rgba(124, 58, 237, 0.3)',
              background: 'rgba(30, 20, 50, 0.5)',
              color: '#e2e8f0',
              fontSize: '0.95rem'
            }}
          />
        </div>

        {/* Content */}
        <div style={{ 
          padding: '0 20px 20px', 
          overflowY: 'auto',
          maxHeight: 'calc(90vh - 280px)'
        }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
              Loading members...
            </div>
          ) : (
            <>
              {/* Members Tab */}
              {activeTab === 'members' && (
                <div>
                  {filteredMembers.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
                      No members found
                    </div>
                  ) : (
                    filteredMembers.map((member) => (
                      <div 
                        key={member.id || member.user_id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: 15,
                          background: 'rgba(30, 20, 50, 0.5)',
                          borderRadius: 10,
                          marginBottom: 10,
                          border: '1px solid rgba(124, 58, 237, 0.2)'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <div style={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 'bold'
                          }}>
                            {(member.username || 'U')[0].toUpperCase()}
                          </div>
                          <div>
                            <div style={{ color: '#e2e8f0', fontWeight: 500 }}>
                              {member.username || 'Unknown'}
                              {member.is_owner && <span style={{ marginLeft: 8, color: '#f59e0b' }}>👑 Owner</span>}
                              {member.is_admin && !member.is_owner && <span style={{ marginLeft: 8, color: '#3b82f6' }}>⭐ Admin</span>}
                              {member.is_moderator && <span style={{ marginLeft: 8, color: '#10b981' }}>🛡️ Mod</span>}
                            </div>
                            <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>
                              {member.email}
                            </div>
                          </div>
                        </div>
                        
                        {/* Actions - don't show for owner or self */}
                        {canModerate && member.user_id !== currentUserId && !member.is_owner && (
                          <div style={{ display: 'flex', gap: 8 }}>
                            {/* Moderators can't act on admins */}
                            {(!isModerator || !member.is_admin) && (
                              <>
                                <button
                                  onClick={() => handleBoot(member.user_id || member.id, member.username)}
                                  disabled={actionLoading === (member.user_id || member.id)}
                                  style={buttonStyle('default')}
                                  data-testid={`boot-${member.user_id || member.id}`}
                                >
                                  👢 Boot
                                </button>
                                <button
                                  onClick={() => setShowBanModal(member)}
                                  disabled={actionLoading === (member.user_id || member.id)}
                                  style={buttonStyle('danger')}
                                  data-testid={`ban-${member.user_id || member.id}`}
                                >
                                  🚫 Ban
                                </button>
                                {type === 'group' && (
                                  <button
                                    onClick={() => setShowMuteModal(member)}
                                    disabled={actionLoading === (member.user_id || member.id)}
                                    style={buttonStyle('warning')}
                                    data-testid={`mute-${member.user_id || member.id}`}
                                  >
                                    🔇 Mute
                                  </button>
                                )}
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Banned Tab */}
              {activeTab === 'banned' && (
                <div>
                  {bannedMembers.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
                      No banned members
                    </div>
                  ) : (
                    bannedMembers.map((banned) => (
                      <div 
                        key={banned.user_id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: 15,
                          background: 'rgba(239, 68, 68, 0.1)',
                          borderRadius: 10,
                          marginBottom: 10,
                          border: '1px solid rgba(239, 68, 68, 0.3)'
                        }}
                      >
                        <div>
                          <div style={{ color: '#e2e8f0', fontWeight: 500 }}>
                            {banned.username || banned.user_id}
                          </div>
                          <div style={{ fontSize: '0.8rem', color: '#ef4444' }}>
                            Banned {banned.banned_at && new Date(banned.banned_at).toLocaleDateString()}
                            {banned.reason && ` - Reason: ${banned.reason}`}
                          </div>
                        </div>
                        
                        {(isOwner || isAdmin) && (
                          <button
                            onClick={() => handleUnban(banned.user_id, banned.username)}
                            disabled={actionLoading === banned.user_id}
                            style={buttonStyle('success')}
                            data-testid={`unban-${banned.user_id}`}
                          >
                            ✓ Unban
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Muted Tab (Groups only) */}
              {activeTab === 'muted' && type === 'group' && (
                <div>
                  {mutedMembers.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 40, color: '#a1a1aa' }}>
                      No muted members
                    </div>
                  ) : (
                    mutedMembers.map((muted) => (
                      <div 
                        key={muted.user_id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: 15,
                          background: 'rgba(245, 158, 11, 0.1)',
                          borderRadius: 10,
                          marginBottom: 10,
                          border: '1px solid rgba(245, 158, 11, 0.3)'
                        }}
                      >
                        <div>
                          <div style={{ color: '#e2e8f0', fontWeight: 500 }}>
                            {muted.username || muted.user_id}
                          </div>
                          <div style={{ fontSize: '0.8rem', color: '#f59e0b' }}>
                            Muted until {muted.muted_until && new Date(muted.muted_until).toLocaleString()}
                          </div>
                        </div>
                        
                        {canModerate && (
                          <button
                            onClick={() => handleUnmute(muted.user_id, muted.username)}
                            disabled={actionLoading === muted.user_id}
                            style={buttonStyle('success')}
                            data-testid={`unmute-${muted.user_id}`}
                          >
                            🔊 Unmute
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Ban Modal */}
        {showBanModal && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <div style={{
              background: 'linear-gradient(135deg, rgba(30, 20, 50, 0.98), rgba(20, 10, 40, 0.98))',
              padding: 25,
              borderRadius: 12,
              width: '90%',
              maxWidth: 400,
              border: '1px solid rgba(239, 68, 68, 0.3)'
            }}>
              <h3 style={{ margin: '0 0 15px', color: '#ef4444' }}>
                🚫 Ban {showBanModal.username}?
              </h3>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>
                This will remove them from the {type} and prevent them from rejoining.
              </p>
              <textarea
                placeholder="Reason for ban (optional)"
                value={banReason}
                onChange={(e) => setBanReason(e.target.value)}
                style={{
                  width: '100%',
                  padding: 12,
                  borderRadius: 8,
                  border: '1px solid rgba(124, 58, 237, 0.3)',
                  background: 'rgba(30, 20, 50, 0.5)',
                  color: '#e2e8f0',
                  minHeight: 80,
                  resize: 'vertical',
                  marginBottom: 15
                }}
              />
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button
                  onClick={() => { setShowBanModal(null); setBanReason(''); }}
                  style={buttonStyle('default')}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleBan(showBanModal.user_id || showBanModal.id)}
                  disabled={actionLoading}
                  style={buttonStyle('danger')}
                  data-testid="confirm-ban-btn"
                >
                  {actionLoading ? 'Banning...' : 'Confirm Ban'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Mute Modal */}
        {showMuteModal && type === 'group' && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <div style={{
              background: 'linear-gradient(135deg, rgba(30, 20, 50, 0.98), rgba(20, 10, 40, 0.98))',
              padding: 25,
              borderRadius: 12,
              width: '90%',
              maxWidth: 400,
              border: '1px solid rgba(245, 158, 11, 0.3)'
            }}>
              <h3 style={{ margin: '0 0 15px', color: '#f59e0b' }}>
                🔇 Mute {showMuteModal.username}?
              </h3>
              <p style={{ color: '#a1a1aa', marginBottom: 15 }}>
                They will not be able to send messages for the specified duration.
              </p>
              <div style={{ marginBottom: 15 }}>
                <label style={{ display: 'block', color: '#a1a1aa', marginBottom: 8 }}>
                  Mute Duration:
                </label>
                <select
                  value={muteMinutes}
                  onChange={(e) => setMuteMinutes(Number(e.target.value))}
                  style={{
                    width: '100%',
                    padding: 12,
                    borderRadius: 8,
                    border: '1px solid rgba(124, 58, 237, 0.3)',
                    background: 'rgba(30, 20, 50, 0.5)',
                    color: '#e2e8f0'
                  }}
                >
                  <option value={5}>5 minutes</option>
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={60}>1 hour</option>
                  <option value={360}>6 hours</option>
                  <option value={1440}>24 hours</option>
                  <option value={10080}>1 week</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button
                  onClick={() => { setShowMuteModal(null); setMuteMinutes(30); }}
                  style={buttonStyle('default')}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleMute(showMuteModal.user_id || showMuteModal.id)}
                  disabled={actionLoading}
                  style={buttonStyle('warning')}
                  data-testid="confirm-mute-btn"
                >
                  {actionLoading ? 'Muting...' : 'Confirm Mute'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModerationPanel;
