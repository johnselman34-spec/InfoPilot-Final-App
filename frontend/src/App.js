import React, { useState, useEffect, createContext, useContext, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

// Fix Leaflet default marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ==================== HASHTAG EXTRACTION ====================
// Extract 4-6 relevant hashtags from article content
const extractHashtags = (title, snippet, articleType) => {
  const text = `${title || ''} ${snippet || ''}`.toLowerCase();
  const words = text.match(/\b[a-z]{4,15}\b/g) || [];
  
  // Common words to exclude
  const stopWords = new Set([
    'this', 'that', 'with', 'from', 'have', 'been', 'were', 'they', 'their',
    'what', 'when', 'where', 'which', 'while', 'about', 'would', 'could',
    'should', 'there', 'these', 'those', 'being', 'other', 'some', 'such',
    'into', 'over', 'after', 'before', 'under', 'between', 'through', 'during',
    'without', 'again', 'further', 'then', 'once', 'here', 'there', 'more',
    'most', 'very', 'just', 'only', 'also', 'back', 'well', 'even', 'still',
    'will', 'each', 'make', 'like', 'time', 'take', 'come', 'made', 'find'
  ]);
  
  // Count word frequency
  const wordCount = {};
  words.forEach(word => {
    if (!stopWords.has(word) && word.length > 3) {
      wordCount[word] = (wordCount[word] || 0) + 1;
    }
  });
  
  // Sort by frequency and take top words
  const sortedWords = Object.entries(wordCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([word]) => word);
  
  // Add article type as a hashtag
  const typeTag = articleType?.toLowerCase().replace(/\s+/g, '') || 'article';
  
  // Combine and format as hashtags (4-6 total)
  const hashtags = [typeTag, ...sortedWords].slice(0, 6);
  return hashtags.map(tag => `#${tag.charAt(0).toUpperCase() + tag.slice(1)}`);
};

// Hashtag component for displaying clickable hashtags
const HashtagDisplay = ({ hashtags, small = false }) => (
  <div style={{ 
    display: 'flex', 
    flexWrap: 'wrap', 
    gap: small ? 4 : 6, 
    marginTop: small ? 6 : 10 
  }}>
    {hashtags.map((tag, idx) => (
      <span
        key={idx}
        style={{
          background: 'rgba(124, 58, 237, 0.2)',
          color: '#a78bfa',
          padding: small ? '2px 6px' : '3px 8px',
          borderRadius: 12,
          fontSize: small ? '0.65rem' : '0.7rem',
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'all 0.2s',
          border: '1px solid rgba(124, 58, 237, 0.3)'
        }}
        onMouseEnter={(e) => {
          e.target.style.background = 'rgba(124, 58, 237, 0.4)';
          e.target.style.color = '#c4b5fd';
        }}
        onMouseLeave={(e) => {
          e.target.style.background = 'rgba(124, 58, 237, 0.2)';
          e.target.style.color = '#a78bfa';
        }}
      >
        {tag}
      </span>
    ))}
  </div>
);

// ==================== AUTH CONTEXT ====================
const AuthContext = createContext(null);

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('token');
      
      // Sync token state with localStorage
      if (storedToken !== token) {
        setToken(storedToken);
      }
      
      if (storedToken) {
        try {
          const res = await fetch(`${API}/auth/me`, {
            headers: { 'Authorization': `Bearer ${storedToken}` }
          });
          if (res.ok) {
            const data = await res.json();
            setUser(data);
          } else {
            // Token is invalid or expired
            console.warn('Token validation failed, clearing auth');
            localStorage.removeItem('token');
            setToken(null);
            setUser(null);
          }
        } catch (e) {
          console.error('Auth check network error:', e);
          // Network error - don't clear token, might be temporary
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, [token]);

  const login = async (email, password) => {
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    localStorage.setItem('token', data.token);
    setToken(data.token);
    setUser(data.user);
    return data;
  };

  const register = async (email, username, password) => {
    const res = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');
    localStorage.setItem('token', data.token);
    setToken(data.token);
    setUser(data.user);
    return data;
  };

  // Google OAuth login using Emergent Auth
  const loginWithGoogle = async (googleUserData) => {
    const res = await fetch(`${API}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: googleUserData.email,
        google_id: googleUserData.id,
        name: googleUserData.name,
        picture: googleUserData.picture
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Google login failed');
    localStorage.setItem('token', data.token);
    setToken(data.token);
    setUser(data.user);
    return data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    if (token) {
      const res = await fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      }
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, loginWithGoogle, logout, refreshUser, setUser, setToken, setLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

// ==================== TOAST NOTIFICATION ====================
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`toast toast-${type}`}>
      {message}
    </div>
  );
};

// ==================== ICONS ====================
const Icons = {
  Search: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>,
  Home: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9,22 9,12 15,12 15,22"/></svg>,
  Users: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  Map: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="1,6 1,22 8,18 16,22 23,18 23,2 16,6 8,2 1,6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>,
  Message: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
  Settings: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  LogOut: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16,17 21,12 16,7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>,
  Plus: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
  ChevronRight: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9,18 15,12 9,6"/></svg>,
  Star: () => <svg viewBox="0 0 24 24" fill="currentColor"><polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/></svg>,
  Heart: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>,
  Globe: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>,
  Book: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>,
  Shield: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
  Trash: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3,6 5,6 21,6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>,
  Edit: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>,
  Send: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22,2 15,22 11,13 2,9"/></svg>,
};

// ==================== LOGIN PAGE ====================
const LoginPage = ({ onSwitch }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>InfoPilot</h1>
          <p>World Wide Web Information Exchange</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div style={{ color: '#ef4444', textAlign: 'center', fontSize: '0.9rem' }}>{error}</div>}
          <input
            className="input-field"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="input-field"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div className="auth-divider"><span>or</span></div>
        <button className="google-btn" onClick={handleGoogleLogin}>
          <img src="https://www.google.com/favicon.ico" alt="Google" style={{ width: 20 }} />
          Continue with Google
        </button>
        <div className="auth-footer">
          Don't have an account? <a href="#" onClick={(e) => { e.preventDefault(); onSwitch(); }}>Sign Up</a>
        </div>
      </div>
    </div>
  );
};

// ==================== REGISTER PAGE ====================
const RegisterPage = ({ onSwitch }) => {
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(email, username, password);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>InfoPilot</h1>
          <p>Your 3D View of the Internet</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div style={{ color: '#ef4444', textAlign: 'center', fontSize: '0.9rem' }}>{error}</div>}
          <input
            className="input-field"
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            className="input-field"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="input-field"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
        <div className="auth-divider"><span>or</span></div>
        <button className="google-btn" onClick={handleGoogleLogin}>
          <img src="https://www.google.com/favicon.ico" alt="Google" style={{ width: 20 }} />
          Continue with Google
        </button>
        <div className="auth-footer">
          Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); onSwitch(); }}>Sign In</a>
        </div>
      </div>
    </div>
  );
};

// ==================== AUTH CALLBACK (Google OAuth) ====================
const AuthCallback = () => {
  const [status, setStatus] = useState('processing'); // 'processing', 'error', 'success'
  const [errorMsg, setErrorMsg] = useState('');
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const doAuth = async () => {
      try {
        // Get session_id from URL hash
        const hashParts = window.location.hash.split('session_id=');
        if (hashParts.length < 2) {
          setErrorMsg('No session ID found');
          setStatus('error');
          return;
        }
        
        const sessionId = hashParts[1].split('&')[0];
        console.log('Processing session ID:', sessionId);
        
        // Call our backend proxy to get session data (avoids CORS issues)
        const sessionResponse = await fetch(`${API}/auth/google/session-data?session_id=${encodeURIComponent(sessionId)}`);
        
        if (!sessionResponse.ok) {
          const errorData = await sessionResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to verify Google session');
        }
        
        const userData = await sessionResponse.json();
        console.log('Got user data:', userData);
        
        // Validate we have required fields
        if (!userData.email || !userData.id) {
          throw new Error('Invalid user data received');
        }
        
        // Now authenticate with our backend
        const authResponse = await fetch(`${API}/auth/google`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: userData.email,
            google_id: userData.id,
            name: userData.name,
            picture: userData.picture || null
          })
        });
        
        if (!authResponse.ok) {
          const errorData = await authResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Login failed');
        }
        
        const authData = await authResponse.json();
        localStorage.setItem('token', authData.token);
        
        // Clear hash and redirect to clean URL
        window.location.href = window.location.origin + window.location.pathname;
        
      } catch (err) {
        console.error('Auth error:', err);
        setErrorMsg(err.message || 'Authentication failed');
        setStatus('error');
      }
    };

    doAuth();
  }, []);

  // Redirect back to login after error
  useEffect(() => {
    if (status === 'error') {
      const timer = setTimeout(() => {
        window.location.href = window.location.origin + window.location.pathname;
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [status]);

  if (status === 'error') {
    return (
      <div className="auth-container">
        <div className="auth-card" style={{ textAlign: 'center' }}>
          <h2 style={{ color: '#ef4444', marginBottom: 15 }}>Authentication Error</h2>
          <p style={{ color: '#a1a1aa' }}>{errorMsg}</p>
          <p style={{ color: '#a1a1aa', marginTop: 10 }}>Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card" style={{ textAlign: 'center' }}>
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
        <p style={{ marginTop: 20, color: '#a1a1aa' }}>Completing sign in...</p>
      </div>
    </div>
  );
};

// ==================== SIDEBAR ====================
const Sidebar = ({ currentPage, setCurrentPage }) => {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'search', label: 'Ultimate Search', icon: Icons.Search },
    { id: 'social', label: 'Social', icon: Icons.Users },
    { id: 'map', label: 'Map View', icon: Icons.Map },
    { id: 'messages', label: 'Messages', icon: Icons.Message },
    { id: 'settings', label: 'Settings', icon: Icons.Settings },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <h1>InfoPilot</h1>
        <p>Information Exchange Network</p>
      </div>
      
      <div className="sidebar-user">
        <div className="sidebar-user-avatar">
          {user?.username?.[0]?.toUpperCase() || 'U'}
        </div>
        <div className="sidebar-user-info">
          <h3>
            {user?.username}
            {user?.is_admin && <span className="admin-badge">ADMIN</span>}
            {!user?.is_admin && user?.is_paid && <span className="full-access-badge">FULL ACCESS</span>}
          </h3>
          <p>{user?.email}</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {/* ADMIN CONTROL - Bright Sticker - Only for Admin */}
        {user?.is_admin && (
          <div
            className={`sidebar-nav-item admin-control-link ${currentPage === 'admin' ? 'active' : ''}`}
            onClick={() => setCurrentPage('admin')}
          >
            Admin Control
          </div>
        )}

        {navItems.map(item => (
          <div
            key={item.id}
            className={`sidebar-nav-item ${currentPage === item.id ? 'active' : ''}`}
            onClick={() => setCurrentPage(item.id)}
          >
            <item.icon />
            {item.label}
          </div>
        ))}

        <div className="sidebar-nav-item" onClick={logout} style={{ marginTop: 'auto' }}>
          <Icons.LogOut />
          Logout
        </div>
      </nav>

      {/* Book Promo - Enhanced */}
      <div style={{ marginTop: 20, padding: 15, background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.25), rgba(124, 58, 237, 0.25))', borderRadius: 12, border: '2px solid rgba(236, 72, 153, 0.5)' }}>
        <div style={{ fontSize: '0.85rem', color: '#fbbf24', fontWeight: 800, marginBottom: 8, textAlign: 'center' }}>
          🎬 OPTIONED FOR FILM! 🎬
        </div>
        <div style={{ fontSize: '0.9rem', color: '#f472b6', marginBottom: 6, textAlign: 'center', fontWeight: 700 }}>
          "Letters to Evelyn"
        </div>
        <div style={{ fontSize: '0.7rem', color: '#a78bfa', marginBottom: 8, fontStyle: 'italic', textAlign: 'center' }}>
          Supernatural Thriller Comedy
        </div>
        <div style={{ fontSize: '0.65rem', color: '#10b981', marginBottom: 6, textAlign: 'center', fontWeight: 600 }}>
          ⭐ 19 Five-Star Professional Reviews
        </div>
        <div style={{ fontSize: '0.6rem', color: '#a1a1aa', marginBottom: 10, fontStyle: 'italic', textAlign: 'center', lineHeight: 1.3 }}>
          "Comedy that creeps into your mind!"
        </div>
        <a 
          href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191" 
          target="_blank" 
          rel="noopener noreferrer"
          className="btn btn-primary"
          style={{ fontSize: '0.8rem', padding: '10px 12px', display: 'block', textAlign: 'center', textDecoration: 'none', background: 'linear-gradient(135deg, #ec4899, #f97316)', boxShadow: '0 0 15px rgba(236, 72, 153, 0.5)' }}
        >
          🛒 GET IT - Only $2.99!
        </a>
      </div>
    </div>
  );
};

// ==================== ADMIN CONTROL PANEL ====================
const AdminPanel = ({ showToast }) => {
  const { token } = useAuth();
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('general');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API}/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
    } catch (e) {
      console.error('Failed to fetch settings:', e);
    }
    setLoading(false);
  };

  const updateSetting = async (key, value) => {
    try {
      await fetch(`${API}/admin/settings/${key}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(value)
      });
      showToast('Setting updated!', 'success');
      fetchSettings();
    } catch (e) {
      showToast('Failed to update setting', 'error');
    }
  };

  const getSetting = (key) => settings.find(s => s.key === key)?.value || '';

  // Newsletter state
  const [newsletterPreview, setNewsletterPreview] = useState(null);
  const [newsletterLoading, setNewsletterLoading] = useState(false);
  const [newsletterHistory, setNewsletterHistory] = useState([]);
  const [newsletterSchedule, setNewsletterSchedule] = useState({
    enabled: false,
    day_of_week: 'monday',
    hour: 9,
    last_scheduled_send: null
  });
  const [testEmail, setTestEmail] = useState('');

  const generateNewsletter = async () => {
    setNewsletterLoading(true);
    try {
      const res = await fetch(`${API}/newsletter/generate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNewsletterPreview(data.content);
        showToast('Newsletter generated!', 'success');
        fetchNewsletterHistory();
      } else {
        showToast('Failed to generate newsletter', 'error');
      }
    } catch (e) {
      showToast('Error generating newsletter', 'error');
    }
    setNewsletterLoading(false);
  };

  const sendNewsletter = async () => {
    if (!window.confirm('Send newsletter to all subscribed users?')) return;
    setNewsletterLoading(true);
    try {
      const res = await fetch(`${API}/newsletter/send`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`Newsletter sent to ${data.sent_count} users!`, 'success');
        fetchNewsletterHistory();
      } else {
        showToast('Failed to send newsletter', 'error');
      }
    } catch (e) {
      showToast('Error sending newsletter', 'error');
    }
    setNewsletterLoading(false);
  };

  const sendTestNewsletter = async () => {
    if (!testEmail) {
      showToast('Please enter an email address', 'error');
      return;
    }
    setNewsletterLoading(true);
    try {
      const res = await fetch(`${API}/newsletter/test-email`, {
        method: 'POST',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: testEmail })
      });
      if (res.ok) {
        showToast(`Test newsletter sent to ${testEmail}!`, 'success');
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to send test', 'error');
      }
    } catch (e) {
      showToast('Error sending test newsletter', 'error');
    }
    setNewsletterLoading(false);
  };

  const fetchNewsletterHistory = async () => {
    try {
      const res = await fetch(`${API}/newsletter/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNewsletterHistory(data);
      }
    } catch (e) {
      console.error('Failed to fetch newsletter history');
    }
  };

  const fetchNewsletterSchedule = async () => {
    try {
      const res = await fetch(`${API}/newsletter/schedule`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNewsletterSchedule(data);
      }
    } catch (e) {
      console.error('Failed to fetch newsletter schedule');
    }
  };

  const saveNewsletterSchedule = async () => {
    try {
      const res = await fetch(`${API}/newsletter/schedule`, {
        method: 'POST',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newsletterSchedule)
      });
      if (res.ok) {
        showToast(newsletterSchedule.enabled 
          ? `Newsletter scheduled for ${newsletterSchedule.day_of_week}s at ${newsletterSchedule.hour}:00 UTC`
          : 'Newsletter schedule disabled', 
          'success'
        );
      } else {
        showToast('Failed to save schedule', 'error');
      }
    } catch (e) {
      showToast('Error saving schedule', 'error');
    }
  };

  useEffect(() => {
    if (activeTab === 'newsletter') {
      fetchNewsletterHistory();
      fetchNewsletterSchedule();
    }
  }, [activeTab]);

  if (loading) {
    return <div className="loading-spinner"><div className="spinner"></div></div>;
  }

  return (
    <div className="admin-panel">
      <div className="admin-panel-header">
        ⚙️ Admin Control Panel
      </div>
      <div className="admin-panel-content">
        <div className="tabs">
          {['general', 'search', 'pricing', 'newsletter', 'users', 'content'].map(tab => (
            <div
              key={tab}
              className={`tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </div>
          ))}
        </div>

        {activeTab === 'general' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>General Settings</h3>
            <div className="admin-setting">
              <label>Daily Collate Limit</label>
              <input
                type="number"
                defaultValue={getSetting('daily_collate_limit') || 10}
                onBlur={(e) => updateSetting('daily_collate_limit', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Max Category Levels</label>
              <input
                type="number"
                defaultValue={getSetting('max_category_levels') || 100}
                onBlur={(e) => updateSetting('max_category_levels', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Tutorial Video URL</label>
              <input
                type="text"
                defaultValue={getSetting('tutorial_video_url') || ''}
                onBlur={(e) => updateSetting('tutorial_video_url', e.target.value)}
                style={{ width: 250 }}
              />
            </div>
          </div>
        )}

        {activeTab === 'search' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>Search Settings</h3>
            <div className="admin-setting">
              <label>Results Per Page</label>
              <input
                type="number"
                defaultValue={getSetting('results_per_page') || 20}
                onBlur={(e) => updateSetting('results_per_page', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Max Search Pages (Admin/Paid)</label>
              <input
                type="number"
                min="1"
                max="99"
                defaultValue={getSetting('max_search_pages') || 99}
                onBlur={(e) => updateSetting('max_search_pages', Math.min(99, Math.max(1, parseInt(e.target.value))))}
              />
              <small style={{ color: '#a1a1aa', display: 'block', marginTop: 5 }}>
                Maximum pages to fetch during Search & Collate (1-99)
              </small>
            </div>
            <div className="admin-setting">
              <label>Unpaid User Max Pages</label>
              <input
                type="number"
                defaultValue={getSetting('unpaid_max_pages') || 3}
                onBlur={(e) => updateSetting('unpaid_max_pages', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Ph.D. Min Words</label>
              <input
                type="number"
                defaultValue={getSetting('phd_min_words') || 1500}
                onBlur={(e) => updateSetting('phd_min_words', parseInt(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>Ph.D. Keyword Count</label>
              <input
                type="number"
                defaultValue={getSetting('phd_keyword_count') || 3}
                onBlur={(e) => updateSetting('phd_keyword_count', parseInt(e.target.value))}
              />
            </div>
          </div>
        )}

        {activeTab === 'pricing' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>Pricing & Subscription</h3>
            <div className="admin-setting">
              <label>Subscription Price ($)</label>
              <input
                type="number"
                step="0.01"
                defaultValue={getSetting('subscription_price') || 0.99}
                onBlur={(e) => updateSetting('subscription_price', parseFloat(e.target.value))}
              />
            </div>
            <div className="admin-setting">
              <label>PayPal Business Email</label>
              <input
                type="email"
                defaultValue={getSetting('paypal_email') || 'JJSpilot24@gmail.com'}
                onBlur={(e) => updateSetting('paypal_email', e.target.value)}
                style={{ width: 300 }}
                placeholder="your-business@email.com"
              />
            </div>
            <div className="admin-setting">
              <label>PayPal Payment Link (fallback)</label>
              <input
                type="text"
                defaultValue={getSetting('paypal_link') || ''}
                onBlur={(e) => updateSetting('paypal_link', e.target.value)}
                style={{ width: 300 }}
              />
            </div>
            <div style={{ marginTop: 20, padding: 15, background: 'rgba(16, 185, 129, 0.1)', borderRadius: 10, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              <p style={{ fontSize: '0.85rem', color: '#10b981' }}>
                💡 Tips:<br/>
                • Enter your PayPal business email to accept "Pay What You Want" payments<br/>
                • Set "Unpaid User Max Pages" to more than 40 to make the app FREE
              </p>
            </div>
          </div>
        )}

        {activeTab === 'newsletter' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>📧 Weekly Newsletter</h3>
            <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
              Generate and send AI-powered funny newsletters to promote your book and app!
            </p>
            
            {/* Manual Send Controls */}
            <div style={{ display: 'flex', gap: 15, marginBottom: 25, flexWrap: 'wrap' }}>
              <button 
                className="btn btn-primary" 
                onClick={generateNewsletter}
                disabled={newsletterLoading}
              >
                {newsletterLoading ? '🤖 Generating...' : '🎨 Generate New Newsletter'}
              </button>
              <button 
                className="btn btn-success" 
                onClick={sendNewsletter}
                disabled={newsletterLoading}
              >
                📤 Send to All Users
              </button>
            </div>

            {/* Test Email */}
            <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: 20, borderRadius: 12, marginBottom: 25, border: '1px solid rgba(59, 130, 246, 0.3)' }}>
              <h4 style={{ color: '#3b82f6', marginBottom: 15 }}>🧪 Send Test Email</h4>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <input 
                  type="email" 
                  placeholder="your@email.com"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  style={{ flex: 1, minWidth: 200 }}
                />
                <button 
                  className="btn btn-secondary"
                  onClick={sendTestNewsletter}
                  disabled={newsletterLoading}
                >
                  📧 Send Test
                </button>
              </div>
            </div>

            {/* Automated Schedule */}
            <div style={{ background: 'rgba(124, 58, 237, 0.1)', padding: 20, borderRadius: 12, marginBottom: 25, border: '2px solid rgba(124, 58, 237, 0.3)' }}>
              <h4 style={{ color: '#a78bfa', marginBottom: 15 }}>⏰ Automated Weekly Schedule</h4>
              <div style={{ display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap', marginBottom: 15 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                  <input 
                    type="checkbox"
                    checked={newsletterSchedule.enabled}
                    onChange={(e) => setNewsletterSchedule({...newsletterSchedule, enabled: e.target.checked})}
                    style={{ width: 20, height: 20, accentColor: '#7c3aed' }}
                  />
                  <span style={{ color: newsletterSchedule.enabled ? '#10b981' : '#a1a1aa', fontWeight: 600 }}>
                    {newsletterSchedule.enabled ? '✅ Enabled' : '⏸️ Disabled'}
                  </span>
                </label>
                
                <select 
                  value={newsletterSchedule.day_of_week}
                  onChange={(e) => setNewsletterSchedule({...newsletterSchedule, day_of_week: e.target.value})}
                  style={{ padding: '8px 15px', borderRadius: 8, background: 'rgba(30, 20, 50, 0.8)', color: 'white', border: '1px solid rgba(124, 58, 237, 0.5)' }}
                >
                  <option value="monday">Monday</option>
                  <option value="tuesday">Tuesday</option>
                  <option value="wednesday">Wednesday</option>
                  <option value="thursday">Thursday</option>
                  <option value="friday">Friday</option>
                  <option value="saturday">Saturday</option>
                  <option value="sunday">Sunday</option>
                </select>
                
                <span style={{ color: '#a1a1aa' }}>at</span>
                
                <select 
                  value={newsletterSchedule.hour}
                  onChange={(e) => setNewsletterSchedule({...newsletterSchedule, hour: parseInt(e.target.value)})}
                  style={{ padding: '8px 15px', borderRadius: 8, background: 'rgba(30, 20, 50, 0.8)', color: 'white', border: '1px solid rgba(124, 58, 237, 0.5)' }}
                >
                  {[...Array(24)].map((_, i) => (
                    <option key={i} value={i}>{i.toString().padStart(2, '0')}:00 UTC</option>
                  ))}
                </select>
                
                <button 
                  className="btn btn-primary"
                  onClick={saveNewsletterSchedule}
                  style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)' }}
                >
                  💾 Save Schedule
                </button>
              </div>
              
              {newsletterSchedule.last_scheduled_send && (
                <p style={{ color: '#a78bfa', fontSize: '0.85rem' }}>
                  Last automated send: {new Date(newsletterSchedule.last_scheduled_send).toLocaleString()}
                </p>
              )}
              
              <p style={{ color: '#a1a1aa', fontSize: '0.8rem', marginTop: 10 }}>
                ℹ️ When enabled, newsletters are automatically generated with AI and sent every week at the scheduled time.
              </p>
            </div>

            {/* Newsletter Preview */}
            {newsletterPreview && (
              <div style={{ marginBottom: 25 }}>
                <h4 style={{ color: '#f472b6', marginBottom: 10 }}>Preview:</h4>
                <div 
                  style={{ 
                    background: '#fff', 
                    borderRadius: 12, 
                    padding: 20, 
                    maxHeight: 500, 
                    overflow: 'auto',
                    border: '2px solid rgba(236, 72, 153, 0.3)'
                  }}
                  dangerouslySetInnerHTML={{ __html: newsletterPreview }}
                />
              </div>
            )}

            {/* Newsletter History */}
            <div>
              <h4 style={{ color: '#f472b6', marginBottom: 15 }}>📜 Newsletter History</h4>
              {newsletterHistory.length === 0 ? (
                <p style={{ color: '#a1a1aa' }}>No newsletters sent yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {newsletterHistory.map((n, i) => (
                    <div key={n.id} style={{ 
                      padding: 15, 
                      background: 'rgba(30, 20, 50, 0.5)', 
                      borderRadius: 10,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: 10
                    }}>
                      <div>
                        <span style={{ color: n.ai_generated ? '#10b981' : '#f472b6' }}>
                          {n.ai_generated ? '🤖 AI Generated' : '📝 Template'}
                        </span>
                        <span style={{ color: '#a1a1aa', marginLeft: 15 }}>
                          {new Date(n.generated_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div>
                        {n.sent ? (
                          <span style={{ color: '#10b981' }}>
                            ✅ Sent to {n.sent_count} users {n.failed_count > 0 && `(${n.failed_count} failed)`}
                          </span>
                        ) : (
                          <span style={{ color: '#fbbf24' }}>⏳ Not sent</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ marginTop: 25, padding: 15, background: 'rgba(236, 72, 153, 0.1)', borderRadius: 10, border: '1px solid rgba(236, 72, 153, 0.3)' }}>
              <p style={{ fontSize: '0.85rem', color: '#f472b6' }}>
                💡 Newsletter promotes:<br/>
                • "Letters to Evelyn" by John Selman - $2.99 on Amazon (19 Five-Star Reviews!)<br/>
                • InfoPilot Premium subscriptions - Pay what you want!<br/>
                • Uses AI to create funny, engaging content with your book's actual reviews!<br/>
                • Includes your book advertisement images with rotating selection!
              </p>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>User Management</h3>
            <p style={{ color: '#a1a1aa', marginBottom: 20 }}>
              Ban users or manage user accounts from here.
            </p>
            <div className="admin-setting">
              <label>Ban User by ID</label>
              <div style={{ display: 'flex', gap: 10 }}>
                <input type="text" placeholder="User ID" id="ban-user-id" />
                <button 
                  className="btn btn-danger"
                  onClick={async () => {
                    const userId = document.getElementById('ban-user-id').value;
                    if (userId) {
                      try {
                        await fetch(`${API}/admin/ban-user/${userId}`, {
                          method: 'POST',
                          headers: { Authorization: `Bearer ${token}` }
                        });
                        showToast('User banned!', 'success');
                      } catch (e) {
                        showToast('Failed to ban user', 'error');
                      }
                    }
                  }}
                >
                  Ban
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'content' && (
          <div>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>Content Moderation</h3>
            <div className="admin-setting">
              <label>Add Blocked Word</label>
              <div style={{ display: 'flex', gap: 10 }}>
                <input type="text" placeholder="Word to block" id="block-word" />
                <button 
                  className="btn btn-danger"
                  onClick={async () => {
                    const word = document.getElementById('block-word').value;
                    if (word) {
                      try {
                        await fetch(`${API}/admin/ban-word`, {
                          method: 'POST',
                          headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${token}`
                          },
                          body: JSON.stringify(word)
                        });
                        showToast('Word blocked!', 'success');
                        document.getElementById('block-word').value = '';
                      } catch (e) {
                        showToast('Failed to block word', 'error');
                      }
                    }
                  }}
                >
                  Block
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== ULTIMATE SEARCH PAGE ====================
const UltimateSearchPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [categories, setCategories] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [aggregation, setAggregation] = useState('and_or');
  const [loading, setLoading] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [newCategory, setNewCategory] = useState({ name: '', protocol: '', parent_id: null, is_public: false });

  const fetchCategories = useCallback(async () => {
    if (!token) {
      console.warn('No token available for fetchCategories');
      return;
    }
    try {
      const res = await fetch(`${API}/categories`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data);
      } else if (res.status === 401) {
        console.error('Token expired or invalid');
      }
    } catch (e) {
      console.error('Failed to fetch categories:', e);
    }
  }, [token]);

  const fetchSearchResults = useCallback(async () => {
    try {
      const params = new URLSearchParams({
        aggregation,
        page: 1
      });
      if (selectedCategories.length > 0) {
        params.append('category_ids', selectedCategories.join(','));
      }
      
      const res = await fetch(`${API}/ultimate-search?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
      }
    } catch (e) {
      console.error('Failed to fetch results:', e);
    }
  }, [token, selectedCategories, aggregation]);

  useEffect(() => {
    fetchCategories();
    fetchSearchResults();
  }, [fetchCategories, fetchSearchResults]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      // First search
      const searchRes = await fetch(`${API}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ query: searchQuery })
      });
      
      if (searchRes.ok) {
        const searchData = await searchRes.json();
        
        // Then collate
        const collateRes = await fetch(`${API}/collate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ search_results: searchData.results })
        });
        
        if (collateRes.ok) {
          const collateData = await collateRes.json();
          showToast(`Collated ${collateData.collated_count} results!`, 'success');
          fetchSearchResults();
        }
      }
    } catch (e) {
      showToast('Search failed', 'error');
    }
    setLoading(false);
  };

  const createCategory = async () => {
    if (!newCategory.name || !newCategory.protocol) {
      showToast('Name and protocol are required', 'error');
      return;
    }
    
    // Check if token exists
    if (!token) {
      showToast('Session expired. Please log in again.', 'error');
      return;
    }
    
    // Show loading state
    showToast('Creating category...', 'success');
    
    try {
      const requestBody = {
        name: newCategory.name,
        protocol: newCategory.protocol,
        parent_id: newCategory.parent_id || null,
        is_public: newCategory.is_public || false
      };
      
      const res = await fetch(`${API}/categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });
      
      // Clone response before reading to avoid "body stream already read" error
      const resClone = res.clone();
      
      let data;
      try {
        data = await res.json();
      } catch (jsonError) {
        // If JSON parsing fails, try to get text from cloned response
        const text = await resClone.text();
        console.error('Response parsing error:', text);
        throw new Error(`Server returned invalid response: ${res.status}`);
      }
      
      if (res.ok) {
        showToast(`Category "${newCategory.name}" created successfully!`, 'success');
        setShowCategoryModal(false);
        setNewCategory({ name: '', protocol: '', parent_id: null, is_public: false });
        fetchCategories();
      } else {
        const errorMsg = data.detail || data.message || 'Failed to create category. Please try again.';
        showToast(errorMsg, 'error');
      }
    } catch (e) {
      console.error('Category creation error:', e);
      if (e.message.includes('Failed to fetch')) {
        showToast('Network error. Please check your connection.', 'error');
      } else {
        showToast(e.message || 'Failed to create category', 'error');
      }
    }
  };

  const toggleCategorySelection = (catId) => {
    setSelectedCategories(prev => 
      prev.includes(catId) 
        ? prev.filter(id => id !== catId)
        : [...prev, catId]
    );
  };

  const addReaction = async (resultId, reactionType) => {
    try {
      await fetch(`${API}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ search_result_id: resultId, reaction_type: reactionType })
      });
      fetchSearchResults();
    } catch (e) {
      console.error('Failed to add reaction:', e);
    }
  };

  const buildCategoryTree = (cats, parentId = null, level = 0) => {
    return cats
      .filter(c => c.parent_id === parentId)
      .map(cat => (
        <div key={cat.id}>
          <div 
            className={`category-item category-item-level-${level} ${selectedCategories.includes(cat.id) ? 'selected' : ''}`}
            onClick={() => toggleCategorySelection(cat.id)}
          >
            <span>{cat.name}</span>
            {cat.is_public && <span style={{ fontSize: '0.7rem', color: '#10b981' }}>Public</span>}
          </div>
          {buildCategoryTree(cats, cat.id, level + 1)}
        </div>
      ));
  };

  return (
    <div>
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <h2>{user?.username}'s Ultimate Search Page</h2>
          <button className="btn btn-primary" onClick={() => setShowCategoryModal(true)}>
            <Icons.Plus /> New Category
          </button>
        </div>

        {/* Search Box */}
        <div className="search-box">
          <input
            className="input-field"
            placeholder="Enter search query and click 'Search & Collate'"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
            {loading ? 'Searching...' : 'Search & Collate'}
          </button>
        </div>

        {/* Aggregation Options */}
        <div style={{ display: 'flex', gap: 20, marginBottom: 20, alignItems: 'center' }}>
          <span style={{ color: '#a1a1aa' }}>Search Aggregation:</span>
          {['and_or', 'and', 'or'].map(agg => (
            <label key={agg} style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer' }}>
              <input
                type="radio"
                name="aggregation"
                checked={aggregation === agg}
                onChange={() => setAggregation(agg)}
              />
              {agg.toUpperCase().replace('_', '/')}
            </label>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20 }}>
        {/* Categories Sidebar */}
        <div className="card">
          <h3 style={{ marginBottom: 15, color: '#f472b6' }}>Categories</h3>
          <div className="categories-tree">
            {categories.length === 0 ? (
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
                No categories yet. Create one to start organizing your searches!
              </p>
            ) : (
              buildCategoryTree(categories)
            )}
          </div>
          {selectedCategories.length > 0 && (
            <button 
              className="btn btn-secondary" 
              style={{ marginTop: 15, width: '100%' }}
              onClick={() => setSelectedCategories([])}
            >
              Clear Selection ({selectedCategories.length})
            </button>
          )}
        </div>

        {/* Search Results */}
        <div className="card">
          <h3 style={{ marginBottom: 15, color: '#f472b6' }}>
            Search Results ({searchResults.length})
          </h3>
          <div className="results-grid">
            {searchResults.length === 0 ? (
              <p style={{ color: '#a1a1aa' }}>
                No results yet. Use "Search & Collate" to find and categorize web content!
              </p>
            ) : (
              searchResults.map(result => (
                <div key={result.id} className="result-card">
                  <h3>
                    <a href={result.url} target="_blank" rel="noopener noreferrer">
                      {result.title}
                    </a>
                  </h3>
                  <p>{result.snippet}</p>
                  <div className="result-card-meta">
                    <span className="result-tag">{result.article_type}</span>
                    <span className="result-tag">{result.root_domain}</span>
                    {result.categories?.map((cat, i) => (
                      <span key={i} className="result-tag" style={{ background: 'rgba(236, 72, 153, 0.2)', color: '#f472b6' }}>
                        {cat}
                      </span>
                    ))}
                  </div>
                  {/* Hashtags */}
                  <HashtagDisplay hashtags={extractHashtags(result.title, result.snippet, result.article_type)} />
                  <div className="reactions-bar">
                    {['Like', 'Love', 'Funny', 'Sad', 'Best'].map(reaction => (
                      <button
                        key={reaction}
                        className="reaction-btn"
                        onClick={() => addReaction(result.id, reaction)}
                      >
                        {reaction === 'Like' && '👍'}
                        {reaction === 'Love' && '❤️'}
                        {reaction === 'Funny' && '😂'}
                        {reaction === 'Sad' && '😢'}
                        {reaction === 'Best' && '⭐'}
                        {reaction}
                      </button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Create Category Modal */}
      {showCategoryModal && (
        <div className="modal-overlay" onClick={() => setShowCategoryModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create Category</h2>
              <button className="modal-close" onClick={() => setShowCategoryModal(false)}>×</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 15 }}>
              <input
                className="input-field"
                placeholder="Category Name"
                value={newCategory.name}
                onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
              />
              <textarea
                className="input-field"
                placeholder="Protocol (e.g., (word1 or word2) & (word3)+ )"
                rows={4}
                value={newCategory.protocol}
                onChange={(e) => setNewCategory({ ...newCategory, protocol: e.target.value })}
                style={{ resize: 'vertical' }}
              />
              <select
                className="input-field"
                value={newCategory.parent_id || ''}
                onChange={(e) => setNewCategory({ ...newCategory, parent_id: e.target.value || null })}
              >
                <option value="">No Parent (Top Level)</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <input
                  type="checkbox"
                  checked={newCategory.is_public}
                  onChange={(e) => setNewCategory({ ...newCategory, is_public: e.target.checked })}
                />
                Make this category public
              </label>
              <p style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>
                💡 Protocols are case-insensitive. Use (word1 or word2) for OR logic, 
                & for AND, + for INCLUDE ALL, ^ for EXCLUDE ALL
              </p>
              <button className="btn btn-primary" onClick={createCategory}>
                Create Category
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== SOCIAL PAGE ====================
const SocialPage = ({ showToast }) => {
  const { token, user } = useAuth();
  const [activeTab, setActiveTab] = useState('feed');
  const [friends, setFriends] = useState([]);
  const [groups, setGroups] = useState([]);
  const [pages, setPages] = useState([]);
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    if (activeTab === 'friends') fetchFriends();
  }, [activeTab]);

  const fetchFriends = async () => {
    try {
      const res = await fetch(`${API}/friends`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFriends(data.friends || []);
      }
    } catch (e) {
      console.error('Failed to fetch friends:', e);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Social Network</h2>
      </div>

      <div className="tabs">
        {['feed', 'friends', 'groups', 'pages'].map(tab => (
          <div
            key={tab}
            className={`tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </div>
        ))}
      </div>

      {activeTab === 'feed' && (
        <div>
          <div style={{ marginBottom: 20 }}>
            <textarea
              className="input-field"
              placeholder="What's on your mind?"
              rows={3}
            />
            <button className="btn btn-primary" style={{ marginTop: 10 }}>Post</button>
          </div>
          <div className="post-card">
            <div className="post-header">
              <div className="post-avatar">J</div>
              <div>
                <strong>john_selman</strong>
                <p style={{ fontSize: '0.75rem', color: '#a1a1aa' }}>Admin</p>
              </div>
            </div>
            <div className="post-content">
              Welcome to InfoPilot! Start exploring the world wide web with our powerful search and categorization tools. Don't forget to check out "Letters to Evelyn" - available on Amazon!
            </div>
            <div className="post-actions">
              <button className="reaction-btn">👍 Like</button>
              <button className="reaction-btn">❤️ Love</button>
              <button className="reaction-btn">💬 Comment</button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'friends' && (
        <div>
          <div style={{ marginBottom: 20 }}>
            <input className="input-field" placeholder="Search for users..." />
          </div>
          {friends.length === 0 ? (
            <p style={{ color: '#a1a1aa' }}>No friends yet. Start connecting with other users!</p>
          ) : (
            friends.map(friend => (
              <div key={friend.id} className="conversation-item">
                <div className="post-avatar">{friend.username?.[0]?.toUpperCase()}</div>
                <div>
                  <strong>{friend.username}</strong>
                </div>
                <button className="btn btn-secondary" style={{ marginLeft: 'auto', padding: '6px 12px', fontSize: '0.8rem' }}>
                  View Profile
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'groups' && (
        <GroupsSection showToast={showToast} token={token} />
      )}

      {activeTab === 'pages' && (
        <PagesSection showToast={showToast} token={token} />
      )}
    </div>
  );
};

// ==================== GROUPS SECTION ====================
const GroupsSection = ({ showToast, token }) => {
  const [groups, setGroups] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newGroup, setNewGroup] = useState({ name: '', description: '', is_public: true });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API}/groups`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setGroups(data);
      }
    } catch (e) {
      console.error('Failed to fetch groups');
    }
    setLoading(false);
  };

  const createGroup = async () => {
    if (!newGroup.name) {
      showToast('Group name is required', 'error');
      return;
    }
    try {
      const res = await fetch(`${API}/groups`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newGroup)
      });
      if (res.ok) {
        showToast('Group created!', 'success');
        setShowCreateModal(false);
        setNewGroup({ name: '', description: '', is_public: true });
        fetchGroups();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to create group', 'error');
      }
    } catch (e) {
      showToast('Failed to create group', 'error');
    }
  };

  if (loading) {
    return <div className="loading-spinner"><div className="spinner"></div></div>;
  }

  return (
    <div>
      <button 
        className="btn btn-primary" 
        style={{ marginBottom: 20 }}
        onClick={() => setShowCreateModal(true)}
      >
        <Icons.Plus /> Create Group
      </button>

      {groups.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: '3rem', marginBottom: 15 }}>👥</div>
          <p style={{ color: '#a1a1aa' }}>No groups yet. Create one to start collaborating!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {groups.map(group => (
            <div 
              key={group.id} 
              style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(124, 58, 237, 0.3)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 10 }}>
                <h3 style={{ color: '#f472b6', margin: 0 }}>{group.name}</h3>
                <span style={{ 
                  fontSize: '0.7rem', 
                  padding: '3px 8px', 
                  borderRadius: 10,
                  background: group.is_public ? 'rgba(16, 185, 129, 0.2)' : 'rgba(124, 58, 237, 0.2)',
                  color: group.is_public ? '#10b981' : '#a78bfa'
                }}>
                  {group.is_public ? '🌐 Public' : '🔒 Private'}
                </span>
              </div>
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 15 }}>
                {group.description || 'No description'}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>
                  👤 {group.member_count || 1} members
                </span>
                <button className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
                  View Group
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Group Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: 20, color: '#f472b6' }}>Create New Group</h3>
            <input
              type="text"
              placeholder="Group Name"
              className="input-field"
              value={newGroup.name}
              onChange={e => setNewGroup({...newGroup, name: e.target.value})}
              style={{ marginBottom: 15 }}
            />
            <textarea
              placeholder="Description (optional)"
              className="input-field"
              value={newGroup.description}
              onChange={e => setNewGroup({...newGroup, description: e.target.value})}
              rows={3}
              style={{ marginBottom: 15 }}
            />
            <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, color: '#a1a1aa' }}>
              <input
                type="checkbox"
                checked={newGroup.is_public}
                onChange={e => setNewGroup({...newGroup, is_public: e.target.checked})}
              />
              Public group (anyone can join)
            </label>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={createGroup}>Create Group</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== PAGES SECTION ====================
const PagesSection = ({ showToast, token }) => {
  const [pages, setPages] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPage, setNewPage] = useState({ name: '', description: '', category: 'General' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      const res = await fetch(`${API}/pages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPages(data);
      }
    } catch (e) {
      console.error('Failed to fetch pages');
    }
    setLoading(false);
  };

  const createPage = async () => {
    if (!newPage.name) {
      showToast('Page name is required', 'error');
      return;
    }
    try {
      const res = await fetch(`${API}/pages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(newPage)
      });
      if (res.ok) {
        showToast('Page created!', 'success');
        setShowCreateModal(false);
        setNewPage({ name: '', description: '', category: 'General' });
        fetchPages();
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to create page', 'error');
      }
    } catch (e) {
      showToast('Failed to create page', 'error');
    }
  };

  if (loading) {
    return <div className="loading-spinner"><div className="spinner"></div></div>;
  }

  const categories = ['General', 'Technology', 'Science', 'History', 'Entertainment', 'Sports', 'News', 'Other'];

  return (
    <div>
      <button 
        className="btn btn-primary" 
        style={{ marginBottom: 20 }}
        onClick={() => setShowCreateModal(true)}
      >
        <Icons.Plus /> Create Page
      </button>

      {pages.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: '3rem', marginBottom: 15 }}>📄</div>
          <p style={{ color: '#a1a1aa' }}>No pages yet. Create one to share your content!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
          {pages.map(page => (
            <div 
              key={page.id} 
              style={{
                padding: 20,
                background: 'rgba(30, 20, 50, 0.5)',
                borderRadius: 12,
                border: '1px solid rgba(236, 72, 153, 0.3)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 10 }}>
                <h3 style={{ color: '#ec4899', margin: 0 }}>{page.name}</h3>
                <span style={{ 
                  fontSize: '0.7rem', 
                  padding: '3px 8px', 
                  borderRadius: 10,
                  background: 'rgba(59, 130, 246, 0.2)',
                  color: '#3b82f6'
                }}>
                  {page.category}
                </span>
              </div>
              <p style={{ color: '#a1a1aa', fontSize: '0.9rem', marginBottom: 15 }}>
                {page.description || 'No description'}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>
                  ❤️ {page.likes || 0} likes
                </span>
                <button className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
                  View Page
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Page Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: 20, color: '#ec4899' }}>Create New Page</h3>
            <input
              type="text"
              placeholder="Page Name"
              className="input-field"
              value={newPage.name}
              onChange={e => setNewPage({...newPage, name: e.target.value})}
              style={{ marginBottom: 15 }}
            />
            <textarea
              placeholder="Description (optional)"
              className="input-field"
              value={newPage.description}
              onChange={e => setNewPage({...newPage, description: e.target.value})}
              rows={3}
              style={{ marginBottom: 15 }}
            />
            <select
              className="input-field"
              value={newPage.category}
              onChange={e => setNewPage({...newPage, category: e.target.value})}
              style={{ marginBottom: 20 }}
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={createPage}>Create Page</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== MAP PAGE ====================
const MapPage = ({ showToast, setCurrentPage }) => {
  const { user, token } = useAuth();
  const [mapResults, setMapResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hoveredResult, setHoveredResult] = useState(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  const mapContainerRef = useRef(null);

  // Known locations for context-based geocoding
  const KNOWN_LOCATIONS = {
    'texas': { lat: 31.9686, lng: -99.9018 },
    'california': { lat: 36.7783, lng: -119.4179 },
    'new york': { lat: 40.7128, lng: -74.0060 },
    'florida': { lat: 27.6648, lng: -81.5158 },
    'washington': { lat: 47.7511, lng: -120.7401 },
    'washington dc': { lat: 38.9072, lng: -77.0369 },
    'virginia': { lat: 37.4316, lng: -78.6569 },
    'houston': { lat: 29.7604, lng: -95.3698 },
    'midland': { lat: 31.9973, lng: -102.0779 },
    'new haven': { lat: 41.3083, lng: -72.9279 },
    'yale': { lat: 41.3163, lng: -72.9223 },
    'gettysburg': { lat: 39.8309, lng: -77.2311 },
    'united states': { lat: 39.8283, lng: -98.5795 },
    'usa': { lat: 39.8283, lng: -98.5795 },
    'america': { lat: 39.8283, lng: -98.5795 },
    'england': { lat: 51.5074, lng: -0.1278 },
    'france': { lat: 46.2276, lng: 2.2137 },
    'germany': { lat: 51.1657, lng: 10.4515 },
    'air force': { lat: 38.8719, lng: -77.0563 },
    'pentagon': { lat: 38.8719, lng: -77.0563 },
    'white house': { lat: 38.8977, lng: -77.0365 },
  };

  const extractLocation = (text, title) => {
    if (!text && !title) return null;
    const combined = `${title || ''} ${text || ''}`.toLowerCase();
    for (const [place, coords] of Object.entries(KNOWN_LOCATIONS)) {
      if (combined.includes(place)) {
        return {
          lat: coords.lat + (Math.random() - 0.5) * 1.5,
          lng: coords.lng + (Math.random() - 0.5) * 1.5,
          place: place
        };
      }
    }
    return null;
  };

  useEffect(() => {
    fetchMapResults();
  }, []);

  const fetchMapResults = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/ultimate-search?limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const resultsWithLocation = data.results
          .map((r, idx) => {
            if (r.latitude && r.longitude && 
                r.latitude >= -90 && r.latitude <= 90 &&
                r.longitude >= -180 && r.longitude <= 180) {
              return { ...r, hasRealLocation: true, hashtags: extractHashtags(r.title, r.snippet, r.article_type) };
            }
            const extracted = extractLocation(r.content || r.snippet, r.title);
            if (extracted) {
              return { 
                ...r, 
                latitude: extracted.lat, 
                longitude: extracted.lng, 
                extractedPlace: extracted.place,
                hashtags: extractHashtags(r.title, r.snippet, r.article_type)
              };
            }
            return null;
          })
          .filter(r => r !== null);
        setMapResults(resultsWithLocation);
      }
    } catch (e) {
      console.error('Failed to fetch map results:', e);
    }
    setLoading(false);
  };

  const getMarkerColor = (articleType) => {
    const colors = {
      'News Article': '#ef4444',
      'Blog Post': '#f97316',
      'Academic Paper': '#3b82f6',
      'Wiki': '#10b981',
      'Forum': '#8b5cf6',
      'Government': '#06b6d4',
      'Video': '#ec4899',
      'Unknown': '#6b7280'
    };
    return colors[articleType] || colors['Unknown'];
  };

  // Create custom colored marker icon
  const createCustomIcon = (color) => {
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        width: 24px;
        height: 24px;
        background: ${color};
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 0 10px ${color}, 0 2px 6px rgba(0,0,0,0.4);
        cursor: pointer;
      "></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
      popupAnchor: [0, -12]
    });
  };

  // Handle marker click - open URL in new tab
  const handleMarkerClick = (result) => {
    if (result.url) {
      window.open(result.url, '_blank', 'noopener,noreferrer');
    }
  };

  // Handle marker hover
  const handleMarkerHover = (result, event) => {
    if (mapContainerRef.current) {
      const rect = mapContainerRef.current.getBoundingClientRect();
      const x = event.originalEvent.clientX - rect.left;
      const y = event.originalEvent.clientY - rect.top;
      setHoverPosition({ x, y });
    }
    setHoveredResult(result);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>🗺️ Interactive World Map</h2>
        <span style={{ color: '#10b981', fontSize: '0.9rem' }}>
          {mapResults.length} results mapped • Click markers to open articles
        </span>
      </div>

      {/* Legend */}
      <div style={{ 
        display: 'flex', gap: 15, flexWrap: 'wrap', marginBottom: 15,
        padding: 10, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10
      }}>
        {[
          { type: 'News Article', color: '#ef4444' },
          { type: 'Blog Post', color: '#f97316' },
          { type: 'Academic Paper', color: '#3b82f6' },
          { type: 'Wiki', color: '#10b981' },
          { type: 'Forum', color: '#8b5cf6' },
          { type: 'Government', color: '#06b6d4' }
        ].map(({ type, color }) => (
          <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: color, boxShadow: `0 0 5px ${color}` }} />
            <span style={{ fontSize: '0.75rem', color: '#a1a1aa' }}>{type}</span>
          </div>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <div className="loading-spinner"><div className="spinner"></div></div>
          <p style={{ color: '#a1a1aa', marginTop: 15 }}>Loading map data...</p>
        </div>
      ) : mapResults.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <p style={{ color: '#a1a1aa', fontSize: '1.1rem' }}>
            No mapped results yet. Search and collate content to see results on the map!
          </p>
          <button className="btn btn-primary" style={{ marginTop: 15 }} onClick={() => setCurrentPage('search')}>
            Go to Ultimate Search
          </button>
        </div>
      ) : (
        <>
          {/* React-Leaflet Map with hover popups */}
          <div 
            ref={mapContainerRef}
            style={{ 
              height: 450, borderRadius: 12, overflow: 'hidden',
              border: '2px solid rgba(124, 58, 237, 0.3)',
              position: 'relative'
            }}
          >
            <MapContainer
              center={[39.8283, -98.5795]}
              zoom={4}
              style={{ height: '100%', width: '100%' }}
              scrollWheelZoom={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mapResults.slice(0, 50).map((result, idx) => (
                <Marker
                  key={result.id || `marker-${idx}`}
                  position={[result.latitude, result.longitude]}
                  icon={createCustomIcon(getMarkerColor(result.article_type))}
                  eventHandlers={{
                    click: () => handleMarkerClick(result),
                    mouseover: (e) => handleMarkerHover(result, e),
                    mouseout: () => setHoveredResult(null)
                  }}
                />
              ))}
            </MapContainer>

            {/* Hover Popup Window */}
            {hoveredResult && (
              <div 
                style={{
                  position: 'absolute',
                  left: Math.min(hoverPosition.x + 15, mapContainerRef.current?.clientWidth - 320 || 0),
                  top: Math.max(hoverPosition.y - 150, 10),
                  width: 300,
                  background: 'rgba(15, 10, 35, 0.98)',
                  borderRadius: 12,
                  border: `2px solid ${getMarkerColor(hoveredResult.article_type)}`,
                  boxShadow: `0 8px 32px rgba(0,0,0,0.6), 0 0 20px ${getMarkerColor(hoveredResult.article_type)}40`,
                  zIndex: 1000,
                  pointerEvents: 'auto',
                  overflow: 'hidden'
                }}
              >
                {/* Header */}
                <div style={{
                  padding: '10px 12px',
                  background: `linear-gradient(135deg, ${getMarkerColor(hoveredResult.article_type)}30, transparent)`,
                  borderBottom: '1px solid rgba(255,255,255,0.1)'
                }}>
                  <span style={{
                    background: getMarkerColor(hoveredResult.article_type),
                    padding: '3px 8px', borderRadius: 10,
                    fontSize: '0.65rem', fontWeight: 600, color: '#fff'
                  }}>
                    {hoveredResult.article_type}
                  </span>
                  {hoveredResult.extractedPlace && (
                    <span style={{ color: '#10b981', fontSize: '0.7rem', marginLeft: 8 }}>
                      📍 {hoveredResult.extractedPlace.charAt(0).toUpperCase() + hoveredResult.extractedPlace.slice(1)}
                    </span>
                  )}
                </div>
                
                {/* Content */}
                <div style={{ padding: 12 }}>
                  <h4 style={{ color: '#fff', margin: '0 0 8px 0', fontSize: '0.85rem', lineHeight: 1.3 }}>
                    {hoveredResult.title?.substring(0, 70) || 'Untitled'}...
                  </h4>
                  <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: '0 0 8px 0', lineHeight: 1.4 }}>
                    {hoveredResult.snippet?.substring(0, 120) || 'No description'}...
                  </p>
                  
                  {/* Hashtags */}
                  {hoveredResult.hashtags && (
                    <HashtagDisplay hashtags={hoveredResult.hashtags} small={true} />
                  )}
                  
                  {/* Click instruction */}
                  <div style={{ 
                    marginTop: 10, padding: '6px 10px', 
                    background: `${getMarkerColor(hoveredResult.article_type)}30`,
                    borderRadius: 6, textAlign: 'center'
                  }}>
                    <span style={{ color: '#fff', fontSize: '0.7rem', fontWeight: 600 }}>
                      🖱️ Click marker to open article
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results list with hashtags */}
          <div style={{ marginTop: 20 }}>
            <h3 style={{ color: '#f472b6', marginBottom: 15 }}>📍 Mapped Results ({mapResults.length})</h3>
            <div style={{ 
              display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: 12, maxHeight: 400, overflowY: 'auto'
            }}>
              {mapResults.slice(0, 20).map((result, idx) => (
                <div 
                  key={result.id || `result-${idx}`}
                  data-testid={`map-result-${idx}`}
                  style={{
                    padding: 12,
                    background: 'rgba(30, 20, 50, 0.5)',
                    borderRadius: 10,
                    border: '1px solid rgba(124, 58, 237, 0.2)',
                    cursor: 'pointer', transition: 'all 0.2s'
                  }}
                  onClick={() => window.open(result.url, '_blank', 'noopener,noreferrer')}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = getMarkerColor(result.article_type)}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = 'rgba(124, 58, 237, 0.2)'}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <div style={{
                      width: 10, height: 10, borderRadius: '50%',
                      background: getMarkerColor(result.article_type),
                      boxShadow: `0 0 6px ${getMarkerColor(result.article_type)}`
                    }} />
                    <span style={{ color: getMarkerColor(result.article_type), fontSize: '0.7rem', fontWeight: 600 }}>
                      {result.article_type}
                    </span>
                    {result.extractedPlace && (
                      <span style={{ color: '#10b981', fontSize: '0.65rem', marginLeft: 'auto' }}>
                        📍 {result.extractedPlace.charAt(0).toUpperCase() + result.extractedPlace.slice(1)}
                      </span>
                    )}
                  </div>
                  <div style={{ color: '#fff', fontWeight: 600, fontSize: '0.85rem', marginBottom: 5, lineHeight: 1.3 }}>
                    {result.title?.substring(0, 60) || 'Untitled'}...
                  </div>
                  <p style={{ color: '#a1a1aa', fontSize: '0.75rem', margin: '0 0 8px 0', lineHeight: 1.4 }}>
                    {result.snippet?.substring(0, 80) || ''}...
                  </p>
                  {/* Hashtags */}
                  {result.hashtags && <HashtagDisplay hashtags={result.hashtags} small={true} />}
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      <p style={{ marginTop: 20, color: '#a1a1aa', fontSize: '0.85rem', textAlign: 'center' }}>
        💡 Hover over markers to preview details. Click any marker to open the article in a new tab!
      </p>
    </div>
  );
};

// ==================== MESSAGES PAGE ====================
const MessagesPage = ({ showToast }) => {
  const { token } = useAuth();
  const [friends, setFriends] = useState([]);
  const [selectedFriend, setSelectedFriend] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');

  useEffect(() => {
    fetchFriends();
  }, []);

  const fetchFriends = async () => {
    try {
      const res = await fetch(`${API}/friends`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFriends(data.friends || []);
      }
    } catch (e) {
      console.error('Failed to fetch friends:', e);
    }
  };

  const fetchMessages = async (friendId) => {
    try {
      const res = await fetch(`${API}/messages/${friendId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (e) {
      console.error('Failed to fetch messages:', e);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedFriend) return;
    try {
      await fetch(`${API}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          recipient_id: selectedFriend.id,
          content: newMessage
        })
      });
      setNewMessage('');
      fetchMessages(selectedFriend.id);
    } catch (e) {
      showToast('Failed to send message', 'error');
    }
  };

  return (
    <div className="messages-container">
      <div className="conversations-list">
        <h3 style={{ marginBottom: 15, color: '#f472b6' }}>Conversations</h3>
        {friends.length === 0 ? (
          <p style={{ color: '#a1a1aa', fontSize: '0.9rem' }}>
            Add friends to start messaging!
          </p>
        ) : (
          friends.map(friend => (
            <div
              key={friend.id}
              className={`conversation-item ${selectedFriend?.id === friend.id ? 'active' : ''}`}
              onClick={() => {
                setSelectedFriend(friend);
                fetchMessages(friend.id);
              }}
            >
              <div className="post-avatar">{friend.username?.[0]?.toUpperCase()}</div>
              <div>
                <strong>{friend.username}</strong>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="chat-area">
        {selectedFriend ? (
          <>
            <div style={{ padding: 15, borderBottom: '1px solid rgba(124, 58, 237, 0.2)' }}>
              <strong>{selectedFriend.username}</strong>
            </div>
            <div className="chat-messages">
              {messages.map(msg => (
                <div key={msg.id} className={`chat-message ${msg.is_mine ? 'sent' : 'received'}`}>
                  {msg.content}
                </div>
              ))}
            </div>
            <div className="chat-input">
              <input
                className="input-field"
                placeholder="Type a message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              />
              <button className="btn btn-primary" onClick={sendMessage}>
                <Icons.Send />
              </button>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#a1a1aa' }}>
            Select a conversation to start messaging
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== SETTINGS PAGE ====================
const SettingsPage = ({ showToast, setCurrentPage }) => {
  const { token, user, refreshUser } = useAuth();
  const [settings, setSettings] = useState({
    ultimate_search_public: user?.ultimate_search_public || false,
    friends_visible: user?.friends_visible || false
  });

  const updateSettings = async () => {
    try {
      const params = new URLSearchParams();
      params.append('ultimate_search_public', settings.ultimate_search_public);
      params.append('friends_visible', settings.friends_visible);
      
      await fetch(`${API}/users/settings?${params}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      });
      showToast('Settings saved!', 'success');
      refreshUser();
    } catch (e) {
      showToast('Failed to save settings', 'error');
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>User Settings</h2>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div style={{ padding: 15, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.ultimate_search_public}
              onChange={(e) => setSettings({ ...settings, ultimate_search_public: e.target.checked })}
            />
            <div>
              <strong>Make Ultimate Search Page Public</strong>
              <p style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 4 }}>
                Allow other users to view your Ultimate Search page and public categories
              </p>
            </div>
          </label>
        </div>

        <div style={{ padding: 15, background: 'rgba(30, 20, 50, 0.5)', borderRadius: 10 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.friends_visible}
              onChange={(e) => setSettings({ ...settings, friends_visible: e.target.checked })}
            />
            <div>
              <strong>Show Friends List to Others</strong>
              <p style={{ fontSize: '0.8rem', color: '#a1a1aa', marginTop: 4 }}>
                Allow other users to see your friends list
              </p>
            </div>
          </label>
        </div>

        <button className="btn btn-primary" onClick={updateSettings}>
          Save Settings
        </button>

        {/* Account Info */}
        <div style={{ marginTop: 20, padding: 20, background: 'rgba(124, 58, 237, 0.1)', borderRadius: 10 }}>
          <h3 style={{ marginBottom: 15, color: '#f472b6' }}>Account Information</h3>
          <p><strong>Username:</strong> {user?.username}</p>
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>Status:</strong> {user?.is_admin ? 'Admin' : (user?.is_paid ? 'Premium' : 'Free')}</p>
        </div>

        {/* Subscription */}
        {!user?.is_paid && !user?.is_admin && (
          <div style={{ padding: 20, background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(124, 58, 237, 0.2))', borderRadius: 10, border: '1px solid rgba(236, 72, 153, 0.3)' }}>
            <h3 style={{ marginBottom: 10, color: '#f472b6' }}>Upgrade to Premium</h3>
            <p style={{ fontSize: '0.9rem', color: '#a1a1aa', marginBottom: 15 }}>
              Get unlimited search results, access to the interactive map, and more!
            </p>
            <button className="btn btn-primary" onClick={() => setCurrentPage('subscribe')}>Subscribe - Pay What You Want</button>
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== SUBSCRIBE PAGE ====================
const SubscribePage = ({ showToast, onBack }) => {
  const { token, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [paymentClicked, setPaymentClicked] = useState(false);
  const [selectedAmount, setSelectedAmount] = useState(null);
  const [customAmount, setCustomAmount] = useState('');
  const [settings, setSettings] = useState({
    subscription_price: 0.99,
    paypal_email: 'JJSpilot24@gmail.com',
    paypal_link: 'https://py.pl/vdf9TkEwfV1ngxIsu9JzlQ'
  });

  useEffect(() => {
    // Fetch subscription settings from admin
    const fetchSettings = async () => {
      try {
        const res = await fetch(`${API}/subscription-info`);
        if (res.ok) {
          const data = await res.json();
          setSettings(data);
        }
      } catch (e) {
        console.log('Using default settings');
      }
    };
    fetchSettings();
  }, []);

  const handlePayPalClick = (amount) => {
    // Create PayPal payment URL with specific amount
    // Using PayPal's standard payment link format
    const paypalEmail = settings.paypal_email || 'JJSpilot24@gmail.com';
    const paymentUrl = `https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=${encodeURIComponent(paypalEmail)}&amount=${amount.toFixed(2)}&currency_code=USD&item_name=${encodeURIComponent('InfoPilot Premium Subscription (1 Year)')}&no_shipping=1&no_note=1`;
    
    window.open(paymentUrl, '_blank');
    setSelectedAmount(amount);
    setPaymentClicked(true);
  };

  const handleCustomPayment = () => {
    const amount = parseFloat(customAmount);
    if (isNaN(amount) || amount < 0.01) {
      showToast('Please enter a valid amount', 'error');
      return;
    }
    handlePayPalClick(amount);
  };

  const handleActivateSubscription = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/subscriptions/activate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        }
      });
      
      if (res.ok) {
        showToast('Subscription activated! Thank you!', 'success');
        await refreshUser();
        onBack();
      } else {
        const data = await res.json();
        showToast(data.detail || 'Activation failed', 'error');
      }
    } catch (e) {
      showToast('Failed to activate subscription', 'error');
    }
    setLoading(false);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>🎉 InfoPilot is FREE!</h2>
        <button className="btn btn-secondary" onClick={onBack}>← Back</button>
      </div>

      <div style={{ maxWidth: 700, margin: '0 auto' }}>
        {/* FREE Announcement */}
        <div style={{ 
          marginBottom: 30, 
          padding: 25, 
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(59, 130, 246, 0.2))', 
          borderRadius: 16,
          border: '3px solid rgba(16, 185, 129, 0.5)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🎊</div>
          <h3 style={{ color: '#10b981', marginBottom: 15, fontSize: '1.8rem' }}>Good News!</h3>
          <p style={{ color: '#fff', fontSize: '1.2rem', marginBottom: 10 }}>
            InfoPilot is <span style={{ color: '#10b981', fontWeight: 800, fontSize: '1.5rem' }}>100% FREE</span> for everyone!
          </p>
          <p style={{ color: '#a1a1aa', fontSize: '0.95rem' }}>
            Enjoy all premium features at no cost. If you love InfoPilot, please support us by checking out our amazing book below! 📚
          </p>
        </div>

        {/* Premium Benefits - Now FREE */}
        <div style={{ marginBottom: 30, padding: 20, background: 'rgba(124, 58, 237, 0.1)', borderRadius: 12 }}>
          <h3 style={{ color: '#f472b6', marginBottom: 15 }}>✅ All Features Included FREE</h3>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {[
              '✨ Unlimited search results',
              '🗺️ Access to interactive world map',
              '📊 Advanced statistics and analytics',
              '🚀 Priority support',
              '💾 Unlimited categories and protocols',
              '🤖 AI-powered collation'
            ].map((benefit, i) => (
              <li key={i} style={{ padding: '8px 0', borderBottom: '1px solid rgba(124, 58, 237, 0.2)', color: '#10b981' }}>
                {benefit}
              </li>
            ))}
          </ul>
        </div>

        {/* HUGE Book Promotion */}
        <div style={{ 
          padding: 30, 
          background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.3), rgba(124, 58, 237, 0.3))',
          borderRadius: 20,
          border: '3px solid rgba(236, 72, 153, 0.6)',
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Film Badge */}
          <div style={{
            position: 'absolute',
            top: 15,
            right: -35,
            background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
            color: '#000',
            padding: '8px 50px',
            fontWeight: 800,
            fontSize: '0.75rem',
            transform: 'rotate(45deg)',
            boxShadow: '0 4px 15px rgba(251, 191, 36, 0.5)'
          }}>
            OPTIONED FOR FILM!
          </div>
          
          <h3 style={{ color: '#f472b6', marginBottom: 20, fontSize: '1.5rem' }}>
            💝 Want to Support the Developer?
          </h3>
          
          {/* Book Images Grid */}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
            <img 
              src="https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/024v1r34_Letters%20to%20Evelyn%20advertisement%201.jpg"
              alt="Letters to Evelyn"
              style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.4)' }}
            />
            <img 
              src="https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/e90a1rlq_Letters%20to%20Evelyn%20advertisement%202.jpg"
              alt="Letters to Evelyn"
              style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.4)' }}
            />
            <img 
              src="https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/ccdegcr8_Letters%20to%20Evelyn%20advertisement%203.jpg"
              alt="Letters to Evelyn"
              style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.4)' }}
            />
            <img 
              src="https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/3gqu0i0v_Letters%20to%20Evelyn%20advertisement%204.jpg"
              alt="Letters to Evelyn"
              style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 12, boxShadow: '0 10px 30px rgba(0,0,0,0.4)' }}
            />
          </div>
          
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fce7f3', marginBottom: 10 }}>
            "Letters to Evelyn"
          </div>
          <div style={{ color: '#a78bfa', marginBottom: 8, fontWeight: 600 }}>
            A Supernatural Thriller Comedy Memoir by John Selman
          </div>
          <div style={{ color: '#fbbf24', marginBottom: 8, fontWeight: 700 }}>
            By World Record Aviation Holder & Navy Pilot
          </div>
          
          {/* Key Points */}
          <div style={{ marginBottom: 15, color: '#a1a1aa', fontSize: '0.9rem' }}>
            ✈️ Navy pilot flew 10 aircraft types • 👽 Extraterrestrial encounters • 😂 "Exceedingly brilliant comedy"
          </div>
          
          <div style={{ 
            background: 'rgba(16, 185, 129, 0.2)', 
            padding: 15, 
            borderRadius: 12, 
            marginBottom: 20,
            borderLeft: '4px solid #10b981'
          }}>
            <div style={{ color: '#10b981', fontStyle: 'italic', marginBottom: 8 }}>
              "A true story that defies belief... readers keep asking: 'WOW, is it all true?'"
            </div>
            <div style={{ color: '#34d399', fontSize: '0.85rem', fontWeight: 600 }}>
              — Readers' Favorite ★★★★★ (19 Five-Star Reviews)
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: 15, justifyContent: 'center', flexWrap: 'wrap' }}>
            <a 
              href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                background: 'linear-gradient(135deg, #ec4899, #f97316)',
                color: 'white',
                padding: '18px 40px',
                borderRadius: 30,
                fontWeight: 800,
                fontSize: '1.2rem',
                textDecoration: 'none',
                boxShadow: '0 10px 40px rgba(236, 72, 153, 0.5)',
                border: '2px solid rgba(255,255,255,0.3)'
              }}
            >
              🛒 BUY NOW - Only $2.99!
            </a>
            <a 
              href="https://letters-to-evelyn.sintra.site"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                background: 'rgba(124, 58, 237, 0.3)',
                color: '#a78bfa',
                padding: '18px 30px',
                borderRadius: 30,
                fontWeight: 700,
                fontSize: '1rem',
                textDecoration: 'none',
                border: '2px solid rgba(124, 58, 237, 0.5)'
              }}
            >
              🌐 Official Website
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==================== BOOK PROMOTION BANNER (Enhanced with Funny Images) ====================
const BOOK_IMAGES = [
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/024v1r34_Letters%20to%20Evelyn%20advertisement%201.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/e90a1rlq_Letters%20to%20Evelyn%20advertisement%202.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/ccdegcr8_Letters%20to%20Evelyn%20advertisement%203.jpg",
  "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/3gqu0i0v_Letters%20to%20Evelyn%20advertisement%204.jpg"
];

const FUNNY_TAGLINES = [
  { image: 0, text: "WROTE A BOOK. UNIVERSE FACT-CHECKED IT. IT PASSED.", subtext: "Now it's YOUR turn to verify!" },
  { image: 1, text: "THERAPIST: THIS IS A LOT TO UNPACK.", subtext: "Bring snacks. Possibly a helmet." },
  { image: 2, text: "I FLEW JETS. THEN REALITY BROKE.", subtext: "Navy pilot meets cosmic chaos." },
  { image: 3, text: "TERROR OF THE COSMIC GULPER", subtext: "A comedy of galactic proportions!" }
];

const BookPromoBanner = () => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % BOOK_IMAGES.length);
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  const currentTagline = FUNNY_TAGLINES[currentImageIndex];

  return (
    <div data-testid="book-promo-banner" style={{
      background: 'linear-gradient(135deg, rgba(20, 10, 40, 0.98), rgba(80, 20, 100, 0.95))',
      borderRadius: 20,
      padding: 0,
      marginBottom: 25,
      border: '3px solid rgba(236, 72, 153, 0.7)',
      overflow: 'hidden',
      boxShadow: '0 25px 80px rgba(124, 58, 237, 0.5)'
    }}>
      {/* Animated Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #7c3aed, #ec4899, #f97316)',
        padding: '18px 25px',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Shimmer effect */}
        <div style={{
          position: 'absolute',
          top: 0, left: '-100%', right: 0, bottom: 0,
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
          animation: 'shimmer 3s infinite'
        }} />
        
        <div style={{
          position: 'absolute',
          top: 8,
          right: 15,
          background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
          color: '#000',
          padding: '6px 18px',
          borderRadius: 20,
          fontWeight: 800,
          fontSize: '0.8rem',
          boxShadow: '0 4px 20px rgba(251, 191, 36, 0.6)',
          animation: 'pulse 2s infinite'
        }}>
          🎬 OPTIONED FOR FILM!
        </div>
        
        <div style={{
          fontSize: '1.6rem',
          fontWeight: 900,
          color: '#fff',
          textShadow: '2px 2px 8px rgba(0,0,0,0.4)',
          letterSpacing: '1px',
          transition: 'all 0.5s'
        }}>
          {currentTagline.text}
        </div>
        <div style={{
          fontSize: '1rem',
          color: 'rgba(255,255,255,0.95)',
          marginTop: 5,
          fontWeight: 600,
          fontStyle: 'italic'
        }}>
          {currentTagline.subtext}
        </div>
      </div>

      {/* Main Content */}
      <div style={{
        display: 'flex',
        gap: 30,
        padding: 25,
        flexWrap: 'wrap',
        alignItems: 'flex-start'
      }}>
        {/* Book Image with Gallery */}
        <div style={{ flex: '0 0 auto', position: 'relative' }}>
          <div style={{
            width: 250,
            height: 320,
            borderRadius: 15,
            overflow: 'hidden',
            boxShadow: '0 20px 60px rgba(236, 72, 153, 0.6)',
            border: '4px solid rgba(255, 255, 255, 0.25)',
            transition: 'transform 0.3s',
            cursor: 'pointer'
          }}>
            <img 
              src={BOOK_IMAGES[currentImageIndex]} 
              alt="Letters to Evelyn - Funny Promo"
              style={{ width: '100%', height: '100%', objectFit: 'cover', transition: 'all 0.5s' }}
            />
          </div>
          {/* Thumbnail Gallery */}
          <div style={{ 
            display: 'flex', 
            gap: 10, 
            marginTop: 15,
            justifyContent: 'center'
          }}>
            {BOOK_IMAGES.map((img, idx) => (
              <div 
                key={idx}
                onClick={() => setCurrentImageIndex(idx)}
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 10,
                  overflow: 'hidden',
                  cursor: 'pointer',
                  border: idx === currentImageIndex ? '3px solid #ec4899' : '2px solid rgba(255,255,255,0.3)',
                  opacity: idx === currentImageIndex ? 1 : 0.7,
                  transition: 'all 0.3s',
                  boxShadow: idx === currentImageIndex ? '0 0 15px rgba(236, 72, 153, 0.5)' : 'none'
                }}
              >
                <img src={img} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
            ))}
          </div>
        </div>

        {/* Book Details */}
        <div style={{ flex: 1, minWidth: 300 }}>
          <h2 style={{
            fontSize: '2.2rem',
            fontWeight: 900,
            background: 'linear-gradient(135deg, #f472b6, #ec4899, #fbbf24)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: 10,
            letterSpacing: '1px'
          }}>
            LETTERS TO EVELYN
          </h2>
          
          <div style={{ 
            color: '#a78bfa', 
            fontSize: '1.1rem', 
            marginBottom: 8,
            fontWeight: 600
          }}>
            A Supernatural Thriller Comedy Memoir
          </div>
          
          <div style={{ 
            color: '#fbbf24', 
            fontSize: '1rem', 
            marginBottom: 12,
            fontWeight: 700
          }}>
            By World Record Aviation Holder <span style={{ color: '#fff' }}>John Selman</span>
          </div>

          {/* Star Rating */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 15 }}>
            <span style={{ color: '#fbbf24', fontSize: '1.4rem' }}>★★★★★</span>
            <span style={{ color: '#fbbf24', fontWeight: 800, fontSize: '1rem' }}>19 Five-Star Reviews</span>
            <span style={{ 
              background: 'rgba(16, 185, 129, 0.2)', 
              color: '#10b981', 
              padding: '4px 12px', 
              borderRadius: 15,
              fontSize: '0.8rem',
              fontWeight: 700
            }}>
              Readers' Favorite
            </span>
          </div>

          {/* Key Selling Points */}
          <div style={{ marginBottom: 18 }}>
            <div style={{ color: '#f472b6', fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              ✈️ <span>Written by a Navy pilot who flew 10 aircraft types</span>
            </div>
            <div style={{ color: '#a78bfa', fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              👽 <span>Extraterrestrial encounters & cosmic visions</span>
            </div>
            <div style={{ color: '#fbbf24', fontSize: '0.95rem', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              😂 <span>"Comedy that creeps into your mind and causes abrupt laughter"</span>
            </div>
          </div>

          {/* Review Quote */}
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            padding: 15,
            borderRadius: 12,
            marginBottom: 20,
            borderLeft: '4px solid #10b981'
          }}>
            <div style={{ color: '#10b981', fontStyle: 'italic', fontSize: '0.95rem', lineHeight: 1.5 }}>
              "The comical side is exceedingly brilliant... imagination off the charts. A true story that defies belief!"
            </div>
            <div style={{ 
              color: '#34d399', 
              fontSize: '0.85rem', 
              marginTop: 8, 
              fontWeight: 600
            }}>
              — Professional Review, Readers' Favorite ★★★★★
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 15 }}>
            <a 
              href="https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191"
              target="_blank"
              rel="noopener noreferrer"
              data-testid="book-buy-amazon"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'linear-gradient(135deg, #ec4899, #f97316)',
                color: 'white',
                padding: '14px 28px',
                borderRadius: 30,
                fontWeight: 800,
                fontSize: '1rem',
                textDecoration: 'none',
                boxShadow: '0 8px 30px rgba(236, 72, 153, 0.5)',
                border: '2px solid rgba(255,255,255,0.2)',
                transition: 'transform 0.2s'
              }}
            >
              🛒 BUY NOW - $2.99
            </a>
            <a 
              href="https://letters-to-evelyn.sintra.site"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(124, 58, 237, 0.3)',
                color: '#a78bfa',
                padding: '14px 24px',
                borderRadius: 30,
                fontWeight: 700,
                fontSize: '1rem',
                textDecoration: 'none',
                border: '2px solid rgba(124, 58, 237, 0.5)'
              }}
            >
              🌐 OFFICIAL SITE
            </a>
            <a 
              href="https://readersfavorite.com/book-review/letters-to-evelyn"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(16, 185, 129, 0.2)',
                color: '#10b981',
                padding: '14px 24px',
                borderRadius: 30,
                fontWeight: 700,
                fontSize: '1rem',
                textDecoration: 'none',
                border: '2px solid rgba(16, 185, 129, 0.5)'
              }}
            >
              ⭐ READ REVIEWS
            </a>
          </div>

          {/* Film Badge */}
          <div style={{
            display: 'inline-block',
            background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.3))',
            padding: '12px 20px',
            borderRadius: 25,
            border: '2px solid rgba(251, 191, 36, 0.6)'
          }}>
            <span style={{ color: '#fbbf24', fontWeight: 800, fontSize: '0.9rem' }}>
              🎬 Hollywood couldn't resist - OPTIONED FOR FILM!
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==================== MAIN APP ====================
const MainApp = () => {
  const { user } = useAuth();
  const [currentPage, setCurrentPage] = useState('search');
  const [toast, setToast] = useState(null);

  const showToast = (message, type) => {
    setToast({ message, type });
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'admin':
        return user?.is_admin ? <AdminPanel showToast={showToast} /> : <UltimateSearchPage showToast={showToast} />;
      case 'search':
        return <UltimateSearchPage showToast={showToast} />;
      case 'social':
        return <SocialPage showToast={showToast} />;
      case 'map':
        return <MapPage showToast={showToast} setCurrentPage={setCurrentPage} />;
      case 'messages':
        return <MessagesPage showToast={showToast} />;
      case 'settings':
        return <SettingsPage showToast={showToast} setCurrentPage={setCurrentPage} />;
      case 'subscribe':
        return <SubscribePage showToast={showToast} onBack={() => setCurrentPage('settings')} />;
      default:
        return <UltimateSearchPage showToast={showToast} />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <main className="main-content">
        {/* Book Promotion Banner - Always visible */}
        <BookPromoBanner />
        {renderPage()}
      </main>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

// ==================== APP ROOT ====================
function App() {
  const [authMode, setAuthMode] = useState('login');

  return (
    <AuthProvider>
      <AppContent authMode={authMode} setAuthMode={setAuthMode} />
    </AuthProvider>
  );
}

const AppContent = ({ authMode, setAuthMode }) => {
  const { user, loading } = useAuth();

  // Check for session_id in URL hash (Google OAuth callback)
  // REMINDER: This check must happen synchronously during render, NOT in useEffect
  if (window.location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  if (loading) {
    return (
      <div className="auth-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return authMode === 'login' 
      ? <LoginPage onSwitch={() => setAuthMode('register')} />
      : <RegisterPage onSwitch={() => setAuthMode('login')} />;
  }

  return <MainApp />;
};

export default App;
