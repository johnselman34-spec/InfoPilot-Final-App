import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  username: string;
  email?: string;
  isPaid: boolean;
  isAdmin: boolean;
  subscriptionStatus?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email?: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  loading: false,

  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),

  login: async (username: string, password: string) => {
    try {
      set({ loading: true });
      const response = await axios.post(`${API_URL}/api/auth/login`, {
        username,
        password,
      });
      
      const { access_token, user } = response.data;
      
      await AsyncStorage.setItem('token', access_token);
      await AsyncStorage.setItem('user', JSON.stringify(user));
      
      set({ token: access_token, user, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  },

  register: async (username: string, password: string, email?: string) => {
    try {
      set({ loading: true });
      const response = await axios.post(`${API_URL}/api/auth/register`, {
        username,
        password,
        email,
      });
      
      const { access_token, user } = response.data;
      
      await AsyncStorage.setItem('token', access_token);
      await AsyncStorage.setItem('user', JSON.stringify(user));
      
      set({ token: access_token, user, loading: false });
    } catch (error: any) {
      set({ loading: false });
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  },

  logout: async () => {
    await AsyncStorage.removeItem('token');
    await AsyncStorage.removeItem('user');
    set({ user: null, token: null });
  },

  checkAuth: async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const userStr = await AsyncStorage.getItem('user');
      
      if (token && userStr) {
        const user = JSON.parse(userStr);
        set({ token, user });
      }
    } catch (error) {
      console.error('Auth check error:', error);
    }
  },
}));
