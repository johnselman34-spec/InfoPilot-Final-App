import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

const NotificationBell = ({ showToast }) => {
  const { token, user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const wsRef = useRef(null);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/notifications?limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || []);
      }
    } catch (e) {
      console.error('Failed to fetch notifications:', e);
    }
  }, [token]);

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/notifications/unread-count`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUnreadCount(data.count || 0);
      }
    } catch (e) {
      console.error('Failed to fetch unread count:', e);
    }
  }, [token]);

  // WebSocket connection for real-time notifications
  useEffect(() => {
    if (!token || !user) return;

    const wsUrl = API.replace('http', 'ws').replace('/api', '') + `/api/ws/notifications?token=${token}`;
    
    const connectWebSocket = () => {
      try {
        wsRef.current = new WebSocket(wsUrl);
        
        wsRef.current.onopen = () => {
          console.log('Notifications WebSocket connected');
        };
        
        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'notification') {
              // Add new notification to list
              setNotifications(prev => [data.notification, ...prev.slice(0, 19)]);
              setUnreadCount(prev => prev + 1);
              
              // Show toast for new notification
              if (showToast) {
                showToast(data.notification.title, 'info');
              }
            } else if (data.type === 'unread_count') {
              setUnreadCount(data.count);
            }
          } catch (e) {
            // Handle ping/pong - only send if WebSocket is open
            if (event.data === 'ping' && wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send('pong');
            }
          }
        };
        
        wsRef.current.onclose = () => {
          console.log('Notifications WebSocket closed');
          // Reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };
        
        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
      } catch (e) {
        console.error('Failed to connect WebSocket:', e);
      }
    };

    connectWebSocket();
    
    // Initial fetch
    fetchNotifications();
    fetchUnreadCount();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [token, user, fetchNotifications, fetchUnreadCount, showToast]);

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      await fetch(`${API}/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (e) {
      console.error('Failed to mark as read:', e);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    setLoading(true);
    try {
      await fetch(`${API}/notifications/mark-all-read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (e) {
      console.error('Failed to mark all as read:', e);
    }
    setLoading(false);
  };

  // Get notification icon based on type
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'friend_request': return '👤';
      case 'friend_accepted': return '🤝';
      case 'new_message': return '💬';
      case 'post_like': return '❤️';
      case 'post_comment': return '💭';
      case 'group_join': return '👥';
      case 'protocol_sale': return '💰';
      case 'badge_earned': return '🏆';
      case 'level_up': return '⬆️';
      default: return '🔔';
    }
  };

  // Format time ago
  const timeAgo = (dateString) => {
    const now = new Date();
    const date = new Date(dateString);
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
  };

  if (!user) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon */}
      <button
        onClick={() => {
          setShowDropdown(!showDropdown);
          if (!showDropdown) fetchNotifications();
        }}
        className="relative p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-gray-800"
        data-testid="notification-bell"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-pink-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-80 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800">
            <h3 className="font-semibold text-white">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                disabled={loading}
                className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* Notification List */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <p>No notifications yet</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => !notification.read && markAsRead(notification.id)}
                  className={`px-4 py-3 border-b border-gray-800 hover:bg-gray-800 cursor-pointer transition-colors ${
                    !notification.read ? 'bg-gray-800/50' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xl">{getNotificationIcon(notification.type)}</span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${!notification.read ? 'text-white font-medium' : 'text-gray-300'}`}>
                        {notification.title}
                      </p>
                      <p className="text-xs text-gray-500 truncate">{notification.message}</p>
                      <p className="text-xs text-gray-600 mt-1">{timeAgo(notification.created_at)}</p>
                    </div>
                    {!notification.read && (
                      <span className="w-2 h-2 bg-purple-500 rounded-full mt-2"></span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-2 border-t border-gray-700 bg-gray-800">
              <button 
                onClick={() => {
                  setShowDropdown(false);
                  // Navigate to full notifications page if exists
                }}
                className="text-xs text-purple-400 hover:text-purple-300 w-full text-center"
              >
                View all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
