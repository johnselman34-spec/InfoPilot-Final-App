// InfoPilot Service Worker - Offline Support, Caching & Push Notifications

const CACHE_NAME = 'infopilot-v2';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('InfoPilot SW: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name.startsWith('infopilot-') && name !== CACHE_NAME)
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip API requests (always fetch from network)
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clone the response
        const responseClone = response.clone();
        
        // Cache successful responses
        if (response.status === 200) {
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseClone);
            });
        }
        
        return response;
      })
      .catch(() => {
        // Network failed, try cache
        return caches.match(event.request)
          .then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            
            // Return offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }
            
            return new Response('Offline', { status: 503 });
          });
      })
  );
});

// ==================== PUSH NOTIFICATIONS ====================

// Handle push notifications
self.addEventListener('push', (event) => {
  console.log('Push received:', event);
  
  let notificationData = {
    title: 'InfoPilot',
    body: 'You have a new notification',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    tag: 'infopilot-notification',
    data: { url: '/' }
  };
  
  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = {
        title: data.title || 'InfoPilot',
        body: data.message || data.body || 'You have a new notification',
        icon: data.icon || '/favicon.ico',
        badge: '/favicon.ico',
        tag: data.tag || `infopilot-${Date.now()}`,
        data: {
          url: data.link || data.url || '/',
          type: data.type,
          notificationId: data.notificationId
        },
        actions: getNotificationActions(data.type),
        requireInteraction: data.type === 'friend_request' || data.type === 'protocol_sale',
        vibrate: [200, 100, 200]
      };
    } catch (e) {
      console.error('Failed to parse push data:', e);
      notificationData.body = event.data.text();
    }
  }
  
  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
  );
});

// Get appropriate actions based on notification type
function getNotificationActions(type) {
  switch (type) {
    case 'friend_request':
      return [
        { action: 'accept', title: '✓ Accept' },
        { action: 'view', title: 'View' }
      ];
    case 'new_message':
      return [
        { action: 'reply', title: 'Reply' },
        { action: 'view', title: 'View' }
      ];
    case 'protocol_sale':
      return [
        { action: 'view', title: 'View Sales' }
      ];
    default:
      return [
        { action: 'view', title: 'View' }
      ];
  }
}

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event.action);
  event.notification.close();
  
  const urlToOpen = event.notification.data?.url || '/';
  const action = event.action;
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // If app is already open, focus it and navigate
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.focus();
            // Send message to handle action
            client.postMessage({
              type: 'NOTIFICATION_CLICK',
              action: action,
              data: event.notification.data
            });
            return;
          }
        }
        
        // Otherwise open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Handle notification close
self.addEventListener('notificationclose', (event) => {
  console.log('Notification closed:', event.notification.tag);
  
  // Track notification dismissal if needed
  if (event.notification.data?.notificationId) {
    // Could send to analytics or mark as dismissed
  }
});

// Handle messages from the main app
self.addEventListener('message', (event) => {
  console.log('SW received message:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  // Handle subscription update
  if (event.data && event.data.type === 'PUSH_SUBSCRIPTION') {
    // Store subscription for later use
    console.log('Push subscription updated');
  }
});

console.log('InfoPilot Service Worker v2 loaded with Push Notifications');
