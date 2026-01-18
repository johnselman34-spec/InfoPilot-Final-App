// InfoPilot Explorer - Background Service Worker

const APP_URL = 'https://search-pilot.preview.emergentagent.com';

// Create context menu on install
chrome.runtime.onInstalled.addListener(() => {
  // Remove existing menu items first
  chrome.contextMenus.removeAll(() => {
    // Create context menu for selected text
    chrome.contextMenus.create({
      id: 'infopilot-search',
      title: 'Search with InfoPilot: "%s"',
      contexts: ['selection']
    });

    // Create context menu for links
    chrome.contextMenus.create({
      id: 'infopilot-search-link',
      title: 'Search link with InfoPilot',
      contexts: ['link']
    });

    // Create context menu for page
    chrome.contextMenus.create({
      id: 'infopilot-open',
      title: 'Open InfoPilot Explorer',
      contexts: ['page']
    });
  });

  console.log('InfoPilot Explorer extension installed');
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  switch (info.menuItemId) {
    case 'infopilot-search':
      if (info.selectionText) {
        const searchUrl = `${APP_URL}/search?q=${encodeURIComponent(info.selectionText)}`;
        chrome.tabs.create({ url: searchUrl });
      }
      break;
    
    case 'infopilot-search-link':
      if (info.linkUrl) {
        const searchUrl = `${APP_URL}/search?q=${encodeURIComponent(info.linkUrl)}`;
        chrome.tabs.create({ url: searchUrl });
      }
      break;
    
    case 'infopilot-open':
      chrome.tabs.create({ url: APP_URL });
      break;
  }
});

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'openSearch') {
    const searchUrl = `${APP_URL}/search?q=${encodeURIComponent(request.query)}`;
    chrome.tabs.create({ url: searchUrl });
    sendResponse({ success: true });
  }
  
  if (request.action === 'getToken') {
    chrome.storage.local.get('authToken', (result) => {
      sendResponse({ token: result.authToken || null });
    });
    return true; // Keep message channel open for async response
  }
  
  if (request.action === 'setToken') {
    chrome.storage.local.set({ authToken: request.token }, () => {
      sendResponse({ success: true });
    });
    return true;
  }
});

// Handle keyboard shortcut (if configured)
chrome.commands?.onCommand?.addListener((command) => {
  if (command === 'open-infopilot') {
    chrome.tabs.create({ url: APP_URL });
  }
});
