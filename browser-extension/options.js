// InfoJet - Options Page Script

const API_BASE = 'https://infopilot-explorer.preview.emergentagent.com/api';

// DOM Elements
const accountEmail = document.getElementById('account-email');
const accountStatus = document.getElementById('account-status');
const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');
const floatBtnEnabled = document.getElementById('float-btn-enabled');
const newTabEnabled = document.getElementById('new-tab-enabled');
const defaultProtocol = document.getElementById('default-protocol');
const notificationsEnabled = document.getElementById('notifications-enabled');
const clearDataBtn = document.getElementById('clear-data-btn');
const saveBtn = document.getElementById('save-btn');
const statusDiv = document.getElementById('status');

// Load settings on page load
document.addEventListener('DOMContentLoaded', async () => {
  const stored = await chrome.storage.local.get([
    'token',
    'settings',
    'protocols',
    'userEmail'
  ]);
  
  // Load settings
  if (stored.settings) {
    floatBtnEnabled.checked = stored.settings.floatBtnEnabled !== false;
    newTabEnabled.checked = stored.settings.newTabEnabled !== false;
    notificationsEnabled.checked = stored.settings.notificationsEnabled || false;
  }
  
  // Check login status
  if (stored.token) {
    showLoggedIn(stored.userEmail || 'User');
    loadProtocols(stored.protocols);
    
    // Set default protocol
    if (stored.settings?.defaultProtocol) {
      defaultProtocol.value = stored.settings.defaultProtocol;
    }
  } else {
    showLoggedOut();
  }
  
  // Event listeners
  loginBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: API_BASE.replace('/api', '') });
  });
  
  logoutBtn.addEventListener('click', logout);
  clearDataBtn.addEventListener('click', clearData);
  saveBtn.addEventListener('click', saveSettings);
});

function showLoggedIn(email) {
  accountEmail.textContent = email;
  accountStatus.textContent = 'Connected to InfoPilot Explorer';
  accountStatus.style.color = '#10b981';
  loginBtn.style.display = 'none';
  logoutBtn.style.display = 'inline-block';
}

function showLoggedOut() {
  accountEmail.textContent = 'Not logged in';
  accountStatus.textContent = 'Connect to InfoPilot Explorer';
  accountStatus.style.color = '#71717a';
  loginBtn.style.display = 'inline-block';
  logoutBtn.style.display = 'none';
}

function loadProtocols(protocols) {
  if (!protocols || protocols.length === 0) return;
  
  protocols.forEach(p => {
    const option = document.createElement('option');
    option.value = p.id;
    option.textContent = p.name;
    defaultProtocol.appendChild(option);
  });
}

async function logout() {
  await chrome.storage.local.remove(['token', 'userEmail', 'protocols', 'stats']);
  showLoggedOut();
  showStatus('Logged out successfully', 'success');
}

async function clearData() {
  if (!confirm('Are you sure you want to clear all local data?')) return;
  
  await chrome.storage.local.clear();
  showStatus('All data cleared', 'success');
  setTimeout(() => location.reload(), 1500);
}

async function saveSettings() {
  const settings = {
    floatBtnEnabled: floatBtnEnabled.checked,
    newTabEnabled: newTabEnabled.checked,
    defaultProtocol: defaultProtocol.value,
    notificationsEnabled: notificationsEnabled.checked
  };
  
  await chrome.storage.local.set({ settings });
  showStatus('Settings saved!', 'success');
}

function showStatus(message, type) {
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  
  setTimeout(() => {
    statusDiv.className = 'status';
  }, 3000);
}
