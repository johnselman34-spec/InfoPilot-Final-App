import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../utils/api';

const PushNotifications = ({ showToast }) => {
  const { token, user } = useAuth();
  const [permission, setPermission] = useState('default');
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(false);
  const [supported, setSupported] = useState(false);

  // Check for existing push subscription
  const checkExistingSubscription = useCallback(async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const existingSubscription = await registration.pushManager.getSubscription();
      setSubscription(existingSubscription);
    } catch (e) {
      console.error('Error checking subscription:', e);
    }
  }, []);

  // Check if push notifications are supported
  useEffect(() => {
    const isSupported = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
    setSupported(isSupported);
    
    if (isSupported) {
      setPermission(Notification.permission);
      checkExistingSubscription();
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
  }, [checkExistingSubscription]);

  // Request notification permission and subscribe
  const enablePushNotifications = async () => {
    if (!supported) {
      showToast('Push notifications not supported in this browser', 'error');
      return;
    }

    setLoading(true);
    try {
      // Request permission
      const permissionResult = await Notification.requestPermission();
      setPermission(permissionResult);
      
      if (permissionResult !== 'granted') {
        showToast('Notification permission denied', 'error');
        setLoading(false);
        return;
      }

      // Get service worker registration
      const registration = await navigator.serviceWorker.ready;
      
      // Subscribe to push notifications
      // Note: In production, you'd use your own VAPID keys
      const subscriptionOptions = {
        userVisibleOnly: true,
        // Using a placeholder VAPID key - in production this would be your server's public key
        applicationServerKey: urlBase64ToUint8Array(
          'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U'
        )
      };

      try {
        const pushSubscription = await registration.pushManager.subscribe(subscriptionOptions);
        setSubscription(pushSubscription);
        
        // Send subscription to backend
        await savePushSubscription(pushSubscription);
        
        showToast('Push notifications enabled!', 'success');
        
        // Show a test notification
        showTestNotification();
      } catch (subscribeError) {
        console.error('Push subscription error:', subscribeError);
        // If VAPID key fails, still enable local notifications
        showToast('Notifications enabled (browser-only)', 'success');
      }
      
    } catch (e) {
      console.error('Push notification error:', e);
      showToast('Failed to enable notifications', 'error');
    }
    setLoading(false);
  };

  // Disable push notifications
  const disablePushNotifications = async () => {
    setLoading(true);
    try {
      if (subscription) {
        await subscription.unsubscribe();
        setSubscription(null);
        
        // Remove from backend
        await removePushSubscription();
      }
      showToast('Push notifications disabled', 'success');
    } catch (e) {
      console.error('Error disabling notifications:', e);
      showToast('Failed to disable notifications', 'error');
    }
    setLoading(false);
  };

  // Save subscription to backend
  const savePushSubscription = async (sub) => {
    try {
      await fetch(`${API}/push/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          subscription: sub.toJSON()
        })
      });
    } catch (e) {
      console.error('Error saving subscription:', e);
    }
  };

  // Remove subscription from backend
  const removePushSubscription = async () => {
    try {
      await fetch(`${API}/push/unsubscribe`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
    } catch (e) {
      console.error('Error removing subscription:', e);
    }
  };

  // Show a test notification
  const showTestNotification = () => {
    if (Notification.permission === 'granted') {
      new Notification('InfoPilot', {
        body: 'Push notifications are now enabled! You\'ll receive alerts for friend requests, messages, and protocol sales.',
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: 'test-notification'
      });
    }
  };

  // Send test push notification via backend
  const sendTestPush = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/push/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (res.ok) {
        showToast('Test notification sent!', 'success');
      } else {
        showToast('Failed to send test notification', 'error');
      }
    } catch (e) {
      // Fallback to local notification
      showTestNotification();
      showToast('Showing local test notification', 'info');
    }
    setLoading(false);
  };

  if (!user) return null;

  return (
    <div className="bg-gray-900/50 border border-gray-700 rounded-xl p-6" data-testid="push-notifications-panel">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        Push Notifications
      </h3>

      {!supported ? (
        <div className="text-gray-400 text-sm">
          <p>Push notifications are not supported in this browser.</p>
          <p className="mt-2 text-xs">Try using Chrome, Firefox, Edge, or Safari on a compatible device.</p>
        </div>
      ) : (
        <>
          <p className="text-gray-400 text-sm mb-4">
            Get instant alerts for friend requests, new messages, protocol sales, and achievements - even when the app is closed.
          </p>

          {/* Permission Status */}
          <div className="flex items-center gap-3 mb-4 p-3 bg-gray-800/50 rounded-lg">
            <div className={`w-3 h-3 rounded-full ${
              permission === 'granted' ? 'bg-green-500' : 
              permission === 'denied' ? 'bg-red-500' : 'bg-yellow-500'
            }`}></div>
            <div>
              <span className="text-white text-sm">
                {permission === 'granted' ? 'Notifications Enabled' : 
                 permission === 'denied' ? 'Notifications Blocked' : 'Notifications Not Set Up'}
              </span>
              {permission === 'denied' && (
                <p className="text-xs text-gray-500 mt-1">
                  Please enable notifications in your browser settings.
                </p>
              )}
            </div>
          </div>

          {/* Notification Types */}
          <div className="mb-4 space-y-2">
            <p className="text-xs text-gray-500 font-medium">You'll be notified about:</p>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
              <div className="flex items-center gap-2">
                <span>👤</span> Friend Requests
              </div>
              <div className="flex items-center gap-2">
                <span>💬</span> New Messages
              </div>
              <div className="flex items-center gap-2">
                <span>💰</span> Protocol Sales
              </div>
              <div className="flex items-center gap-2">
                <span>🏆</span> Badges & Level Ups
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            {permission !== 'granted' || !subscription ? (
              <button
                onClick={enablePushNotifications}
                disabled={loading || permission === 'denied'}
                className="flex-1 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-lg hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                )}
                {permission === 'denied' ? 'Blocked by Browser' : 'Enable Notifications'}
              </button>
            ) : (
              <>
                <button
                  onClick={sendTestPush}
                  disabled={loading}
                  className="flex-1 py-2.5 bg-gray-700 text-white font-medium rounded-lg hover:bg-gray-600 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  Test
                </button>
                <button
                  onClick={disablePushNotifications}
                  disabled={loading}
                  className="py-2.5 px-4 bg-red-600/20 text-red-400 font-medium rounded-lg hover:bg-red-600/30 transition-all disabled:opacity-50"
                >
                  Disable
                </button>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
};

// Helper function to convert VAPID key
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export default PushNotifications;
