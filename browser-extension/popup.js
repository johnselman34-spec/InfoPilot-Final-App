// InfoPilot Explorer - Browser Extension Popup Script

const APP_URL = 'https://search-pilot.preview.emergentagent.com';
const API_URL = `${APP_URL}/api`;

// DOM Elements
const searchInput = document.getElementById('searchInput');
const engineSelect = document.getElementById('engineSelect');
const searchBtn = document.getElementById('searchBtn');
const voiceBtn = document.getElementById('voiceBtn');
const statusEl = document.getElementById('status');

// Quick Links
document.getElementById('openSearch').addEventListener('click', (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: `${APP_URL}/search` });
});

document.getElementById('openMarket').addEventListener('click', (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: `${APP_URL}/marketplace` });
});

document.getElementById('openChat').addEventListener('click', (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: `${APP_URL}/chat` });
});

document.getElementById('openDashboard').addEventListener('click', (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: `${APP_URL}/stats` });
});

document.getElementById('openApp').addEventListener('click', (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: APP_URL });
});

// Search functionality
searchBtn.addEventListener('click', performSearch);
searchInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') performSearch();
});

async function performSearch() {
  const query = searchInput.value.trim();
  if (!query) {
    showStatus('Please enter a search query', 'error');
    return;
  }

  const engine = engineSelect.value;
  searchBtn.disabled = true;
  searchBtn.textContent = '⏳ Searching...';
  showStatus('Searching...', '');

  try {
    // Get auth token from storage
    const { authToken } = await chrome.storage.local.get('authToken');
    
    if (!authToken) {
      // No token - redirect to login
      showStatus('Please log in to InfoPilot first', 'error');
      setTimeout(() => {
        chrome.tabs.create({ url: `${APP_URL}/login` });
      }, 1500);
      return;
    }

    // Open search page with query
    const searchUrl = `${APP_URL}/search?q=${encodeURIComponent(query)}&engine=${engine}`;
    chrome.tabs.create({ url: searchUrl });
    
    showStatus('Opening search...', 'success');
    window.close();
  } catch (error) {
    console.error('Search error:', error);
    showStatus('Search failed. Please try again.', 'error');
  } finally {
    searchBtn.disabled = false;
    searchBtn.textContent = '🔍 Search & Collate';
  }
}

function showStatus(message, type) {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
}

// Voice Search
let recognition = null;
let isListening = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map(result => result[0].transcript)
      .join('');
    searchInput.value = transcript;
    
    if (event.results[0].isFinal) {
      stopListening();
      showStatus(`Voice input: "${transcript}"`, 'success');
    }
  };

  recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    stopListening();
    if (event.error === 'not-allowed') {
      showStatus('Microphone access denied', 'error');
    } else {
      showStatus(`Voice error: ${event.error}`, 'error');
    }
  };

  recognition.onend = () => {
    stopListening();
  };

  voiceBtn.addEventListener('click', () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  });
} else {
  voiceBtn.style.display = 'none';
}

function startListening() {
  if (recognition && !isListening) {
    try {
      recognition.start();
      isListening = true;
      voiceBtn.classList.add('listening');
      showStatus('Listening...', '');
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
    }
  }
}

function stopListening() {
  if (recognition && isListening) {
    recognition.stop();
    isListening = false;
    voiceBtn.classList.remove('listening');
  }
}

// Load saved preferences
chrome.storage.local.get(['lastEngine', 'lastQuery'], (result) => {
  if (result.lastEngine) {
    engineSelect.value = result.lastEngine;
  }
});

// Save preferences on change
engineSelect.addEventListener('change', () => {
  chrome.storage.local.set({ lastEngine: engineSelect.value });
});

// Focus search input on open
searchInput.focus();
