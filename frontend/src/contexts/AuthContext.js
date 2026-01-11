import React, { useState, useEffect, createContext, useContext } from 'react';
import { API } from '../utils/api';

// ==================== AUTH CONTEXT ====================
const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
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
    
    // Read response text first to avoid "body stream already read" error
    const responseText = await res.text();
    let data;
    try {
      data = responseText ? JSON.parse(responseText) : {};
    } catch (e) {
      throw new Error('Server returned invalid response');
    }
    
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
    
    // Read response text first to avoid "body stream already read" error
    const responseText = await res.text();
    let data;
    try {
      data = responseText ? JSON.parse(responseText) : {};
    } catch (e) {
      throw new Error('Server returned invalid response');
    }
    
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
    
    // Read response text first to avoid "body stream already read" error
    const responseText = await res.text();
    let data;
    try {
      data = responseText ? JSON.parse(responseText) : {};
    } catch (e) {
      throw new Error('Server returned invalid response');
    }
    
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

export default AuthContext;
