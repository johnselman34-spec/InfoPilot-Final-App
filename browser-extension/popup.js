// InfoJet - Popup Script
// Handles the main extension popup functionality

const API_BASE = 'https://info-explorer-hub.preview.emergentagent.com/api';

// State
let selectedProtocol = null;
let userToken = null;
let protocols = [];

// DOM Elements
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const protocolList = document.getElementById('protocol-list');
const statsSection = document.getElementById('stats-section');
const searchesCount = document.getElementById('searches-count');
const protocolsCount = document.getElementById('protocols-count');
const openAppLink = document.getElementById('open-app');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  // Load saved token
  const stored = await chrome.storage.local.get(['token', 'protocols', 'stats']);
  userToken = stored.token;
  
  if (stored.protocols) {
    protocols = stored.protocols;
    renderProtocols();
  }
  
  if (stored.stats) {
    updateStats(stored.stats);
  }
  
  // Fetch fresh data if logged in
  if (userToken) {
    fetchProtocols();
    fetchStats();
  } else {
    showLoginPrompt();
  }
  
  // Set up event listeners
  searchBtn.addEventListener('click', performSearch);
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
  });
  
  openAppLink.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: API_BASE.replace('/api', '') });
  });
});

// Show login prompt
function showLoginPrompt() {
  document.getElementById('main-content').innerHTML = `
    <div class="login-prompt">
      <div style="font-size: 3rem; margin-bottom: 15px;">🔐</div>
      <h3 style="margin-bottom: 10px;">Connect Your Account</h3>
      <p style="color: #71717a; font-size: 0.85rem;">
        Log in to InfoPilot Explorer to access your protocols and search history.
      </p>
      <a href="${API_BASE.replace('/api', '')}" class="login-btn" id="login-link">
        Login to InfoPilot
      </a>
    </div>
  `;
  
  document.getElementById('login-link').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: API_BASE.replace('/api', '') });
  });
}

// Fetch user's protocols
async function fetchProtocols() {
  try {
    const res = await fetch(`${API_BASE}/categories`, {
      headers: { Authorization: `Bearer ${userToken}` }
    });
    
    if (res.ok) {
      const data = await res.json();
      protocols = data.categories || [];
      chrome.storage.local.set({ protocols });
      renderProtocols();
    } else if (res.status === 401) {
      // Token expired
      chrome.storage.local.remove(['token']);
      showLoginPrompt();
    }
  } catch (e) {
    console.error('Failed to fetch protocols:', e);
  }
}

// Fetch user stats
async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/user/stats`, {
      headers: { Authorization: `Bearer ${userToken}` }
    });
    
    if (res.ok) {
      const stats = await res.json();
      chrome.storage.local.set({ stats });
      updateStats(stats);
    }
  } catch (e) {
    console.error('Failed to fetch stats:', e);
  }
}

// Update stats display
function updateStats(stats) {
  statsSection.style.display = 'flex';
  searchesCount.textContent = stats.total_searches || 0;
  protocolsCount.textContent = stats.protocol_count || protocols.length;
}

// Render protocols list
function renderProtocols() {
  if (protocols.length === 0) {
    protocolList.innerHTML = `
      <div class="empty-state">
        No protocols yet. Create some in the full app!
      </div>
    `;
    return;
  }
  
  protocolList.innerHTML = protocols.slice(0, 5).map(p => `
    <div class="protocol-item ${selectedProtocol === p.id ? 'active' : ''}" 
         data-id="${p.id}" 
         data-protocol="${encodeURIComponent(p.protocol || '')}">
      <div class="protocol-name">${p.name}</div>
      <div class="protocol-desc">${p.protocol ? p.protocol.substring(0, 50) + '...' : 'No protocol defined'}</div>
    </div>
  `).join('');
  
  // Add click handlers
  document.querySelectorAll('.protocol-item').forEach(item => {
    item.addEventListener('click', () => {
      // Toggle selection
      if (selectedProtocol === item.dataset.id) {
        selectedProtocol = null;
        item.classList.remove('active');
      } else {
        document.querySelectorAll('.protocol-item').forEach(i => i.classList.remove('active'));
        selectedProtocol = item.dataset.id;
        item.classList.add('active');
      }
    });
  });
}

// Perform search
async function performSearch() {
  const query = searchInput.value.trim();
  if (!query) return;
  
  // Get selected protocol
  let protocolString = '';
  if (selectedProtocol) {
    const selected = protocols.find(p => p.id === selectedProtocol);
    if (selected) {
      protocolString = selected.protocol || '';
    }
  }
  
  // Build search URL
  const searchUrl = `${API_BASE.replace('/api', '')}/search?q=${encodeURIComponent(query)}${protocolString ? `&protocol=${encodeURIComponent(protocolString)}` : ''}`;
  
  // Open in new tab
  chrome.tabs.create({ url: searchUrl });
  
  // Track the search
  if (userToken) {
    try {
      await fetch(`${API_BASE}/search/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${userToken}`
        },
        body: JSON.stringify({
          query,
          protocol_id: selectedProtocol,
          source: 'extension'
        })
      });
    } catch (e) {
      console.error('Failed to track search:', e);
    }
  }
}
