import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  const loadStoredAuth = async () => {
    try {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');

      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        api.setToken(storedToken);

        try {
          const response = await api.get('/auth/me');
          setUser(response);
          localStorage.setItem('user', JSON.stringify(response));
        } catch (error) {
          await clearAuth();
        }
      }
    } catch (error) {
      console.error('Error loading auth:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearAuth = async () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    api.setToken(null);
  };

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    await saveAuth(response.token, response.user);
  };

  const register = async (email, username, password) => {
    const response = await api.post('/auth/register', { email, username, password });
    await saveAuth(response.token, response.user);
  };

  const googleAuth = async (email, googleId, name, picture) => {
    const response = await api.post('/auth/google', { email, google_id: googleId, name, picture });
    await saveAuth(response.token, response.user);
  };

  const saveAuth = async (newToken, newUser) => {
    localStorage.setItem('token', newToken);
    localStorage.setItem('user', JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
    api.setToken(newToken);
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout', {});
    } catch (error) {
      // Ignore logout errors
    }
    await clearAuth();
  };

  const refreshUser = async () => {
    if (token) {
      try {
        const response = await api.get('/auth/me');
        setUser(response);
        localStorage.setItem('user', JSON.stringify(response));
      } catch (error) {
        console.error('Error refreshing user:', error);
      }
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, googleAuth, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
