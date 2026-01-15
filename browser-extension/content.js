// InfoJet - Content Script
// Runs on all pages, enables quick selection search

// Listen for messages from background/popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_SELECTION') {
    const selection = window.getSelection().toString().trim();
    sendResponse({ text: selection });
  }
});

// Add keyboard shortcut listener (Ctrl/Cmd + Shift + S)
document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S') {
    e.preventDefault();
    const selection = window.getSelection().toString().trim();
    if (selection) {
      chrome.runtime.sendMessage({
        type: 'QUICK_SEARCH',
        query: selection
      });
    }
  }
});

// Optional: Add floating search button on text selection
let floatingButton = null;

document.addEventListener('mouseup', (e) => {
  const selection = window.getSelection().toString().trim();
  
  // Remove existing button
  if (floatingButton) {
    floatingButton.remove();
    floatingButton = null;
  }
  
  // Show button if text is selected
  if (selection && selection.length > 2 && selection.length < 200) {
    floatingButton = document.createElement('div');
    floatingButton.className = 'infojet-float-btn';
    floatingButton.innerHTML = '🚀';
    floatingButton.title = 'Search with InfoJet';
    floatingButton.style.cssText = `
      position: fixed;
      left: ${e.clientX + 10}px;
      top: ${e.clientY - 30}px;
      z-index: 999999;
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #7c3aed, #a855f7);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(124, 58, 237, 0.5);
      font-size: 14px;
      animation: infojet-pop 0.2s ease-out;
    `;
    
    floatingButton.addEventListener('click', () => {
      const API_BASE = 'https://protocol-market-1.preview.emergentagent.com';
      window.open(`${API_BASE}/search?q=${encodeURIComponent(selection)}&source=extension`, '_blank');
      floatingButton.remove();
      floatingButton = null;
    });
    
    document.body.appendChild(floatingButton);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
      if (floatingButton) {
        floatingButton.remove();
        floatingButton = null;
      }
    }, 3000);
  }
});

// Remove button on click elsewhere
document.addEventListener('mousedown', (e) => {
  if (floatingButton && !floatingButton.contains(e.target)) {
    floatingButton.remove();
    floatingButton = null;
  }
});

console.log('InfoJet content script loaded');
