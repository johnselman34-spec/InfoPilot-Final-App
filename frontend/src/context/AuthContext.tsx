import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../services/api';

interface User {
  id: string;
  email: string;
  username: string;
  is_paid: boolean;
  is_admin: boolean;
  profile_picture?: string;
  ultimate_search_public?: boolean;
  friends_visible?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  googleAuth: (email: string, googleId: string, name: string, picture?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  const loadStoredAuth = async () => {
    try {
      const storedToken = await AsyncStorage.getItem('token');
      const storedUser = await AsyncStorage.getItem('user');
      
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        api.setToken(storedToken);
        
        // Verify token is still valid
        try {
          const response = await api.get('/auth/me');
          setUser(response);
          await AsyncStorage.setItem('user', JSON.stringify(response));
        } catch (error) {
          // Token invalid, clear storage
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
    await AsyncStorage.removeItem('token');
    await AsyncStorage.removeItem('user');
    setToken(null);
    setUser(null);
    api.setToken(null);
  };

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    await saveAuth(response.token, response.user);
  };

  const register = async (email: string, username: string, password: string) => {
    const response = await api.post('/auth/register', { email, username, password });
    await saveAuth(response.token, response.user);
  };

  const googleAuth = async (email: string, googleId: string, name: string, picture?: string) => {
    const response = await api.post('/auth/google', { email, google_id: googleId, name, picture });
    await saveAuth(response.token, response.user);
  };

  const saveAuth = async (newToken: string, newUser: User) => {
    await AsyncStorage.setItem('token', newToken);
    await AsyncStorage.setItem('user', JSON.stringify(newUser));
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
        await AsyncStorage.setItem('user', JSON.stringify(response));
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
