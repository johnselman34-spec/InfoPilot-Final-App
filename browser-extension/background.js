// InfoJet - Background Service Worker
// Handles context menu, keyboard shortcuts, and message passing

const API_BASE = 'https://infopilot-explorer.preview.emergentagent.com/api';

// Create context menu on install
chrome.runtime.onInstalled.addListener(() => {
  // Create context menu for selected text
  chrome.contextMenus.create({
    id: 'infojet-search',
    title: 'Search with InfoJet: "%s"',
    contexts: ['selection']
  });
  
  chrome.contextMenus.create({
    id: 'infojet-search-page',
    title: 'Search this page with InfoJet',
    contexts: ['page']
  });
  
  console.log('InfoJet extension installed!');
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'infojet-search') {
    const query = info.selectionText;
    openInfoJetSearch(query);
  } else if (info.menuItemId === 'infojet-search-page') {
    // Get page title as search query
    const query = tab.title;
    openInfoJetSearch(query);
  }
});

// Open InfoJet search in new tab
function openInfoJetSearch(query) {
  const searchUrl = `${API_BASE.replace('/api', '')}/search?q=${encodeURIComponent(query)}&source=extension`;
  chrome.tabs.create({ url: searchUrl });
}

// Listen for messages from popup/content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'LOGIN_SUCCESS') {
    // Store token from main app
    chrome.storage.local.set({ token: message.token });
    sendResponse({ success: true });
  } else if (message.type === 'LOGOUT') {
    chrome.storage.local.remove(['token', 'protocols', 'stats']);
    sendResponse({ success: true });
  } else if (message.type === 'GET_SELECTED_TEXT') {
    // Get selected text from active tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { type: 'GET_SELECTION' }, (response) => {
        sendResponse(response);
      });
    });
    return true; // Keep channel open for async response
  }
});

// Handle keyboard shortcuts
chrome.commands.onCommand.addListener((command) => {
  if (command === 'quick-search') {
    // Open popup
    chrome.action.openPopup();
  }
});

// Track extension usage for analytics
async function trackExtensionUsage(event) {
  const stored = await chrome.storage.local.get(['token']);
  if (!stored.token) return;
  
  try {
    await fetch(`${API_BASE}/analytics/extension`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${stored.token}`
      },
      body: JSON.stringify({
        event,
        timestamp: new Date().toISOString(),
        version: chrome.runtime.getManifest().version
      })
    });
  } catch (e) {
    // Silently fail
  }
}

// Log extension startup
trackExtensionUsage('startup');
