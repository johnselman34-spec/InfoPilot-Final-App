// InfoPilot Explorer - Content Script
// Runs on all pages to provide quick search functionality

const APP_URL = 'https://search-pilot.preview.emergentagent.com';

// Listen for keyboard shortcut (Ctrl+Shift+I or Cmd+Shift+I)
document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'I') {
    e.preventDefault();
    
    // Get selected text
    const selectedText = window.getSelection().toString().trim();
    
    if (selectedText) {
      // Search selected text
      chrome.runtime.sendMessage({
        action: 'openSearch',
        query: selectedText
      });
    } else {
      // Open InfoPilot
      window.open(APP_URL, '_blank');
    }
  }
});

// Double-click to search (optional feature)
let doubleClickEnabled = false;

chrome.storage.local.get('doubleClickSearch', (result) => {
  doubleClickEnabled = result.doubleClickSearch || false;
});

document.addEventListener('dblclick', (e) => {
  if (!doubleClickEnabled) return;
  
  const selectedText = window.getSelection().toString().trim();
  if (selectedText && selectedText.length > 2 && selectedText.length < 100) {
    // Show small tooltip with search option
    showSearchTooltip(e.clientX, e.clientY, selectedText);
  }
});

function showSearchTooltip(x, y, text) {
  // Remove existing tooltip
  const existingTooltip = document.getElementById('infopilot-tooltip');
  if (existingTooltip) existingTooltip.remove();
  
  // Create tooltip
  const tooltip = document.createElement('div');
  tooltip.id = 'infopilot-tooltip';
  tooltip.innerHTML = `
    <button id="infopilot-search-btn">
      🐻 Search with InfoPilot
    </button>
  `;
  
  tooltip.style.cssText = `
    position: fixed;
    left: ${x}px;
    top: ${y + 10}px;
    z-index: 999999;
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #f59e0b;
    border-radius: 8px;
    padding: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    animation: fadeIn 0.2s ease-out;
  `;
  
  document.body.appendChild(tooltip);
  
  // Handle click
  document.getElementById('infopilot-search-btn').addEventListener('click', () => {
    chrome.runtime.sendMessage({
      action: 'openSearch',
      query: text
    });
    tooltip.remove();
  });
  
  // Auto-remove after 3 seconds
  setTimeout(() => tooltip.remove(), 3000);
  
  // Remove on click outside
  document.addEventListener('click', function handler(e) {
    if (!tooltip.contains(e.target)) {
      tooltip.remove();
      document.removeEventListener('click', handler);
    }
  });
}

// Inject auth token if on InfoPilot domain
if (window.location.hostname.includes('emergentagent.com')) {
  // Listen for auth changes
  window.addEventListener('storage', (e) => {
    if (e.key === 'token' && e.newValue) {
      chrome.runtime.sendMessage({
        action: 'setToken',
        token: e.newValue
      });
    }
  });
  
  // Check for existing token
  const token = localStorage.getItem('token');
  if (token) {
    chrome.runtime.sendMessage({
      action: 'setToken',
      token: token
    });
  }
}

console.log('InfoPilot Explorer content script loaded');
