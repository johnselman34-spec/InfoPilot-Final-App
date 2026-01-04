import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  register: (data: { username: string; email?: string; password: string }) =>
    api.post('/auth/register', data),
  login: (data: { username: string; password: string }) =>
    api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

// Category APIs
export const categoryAPI = {
  create: (data: { name: string; protocol: string; parent_id?: string; is_public: boolean }) =>
    api.post('/categories', data),
  getAll: () => api.get('/categories'),
  getPublic: (username: string) => api.get(`/categories/user/${username}`),
  update: (id: string, data: any) => api.put(`/categories/${id}`, data),
  delete: (id: string) => api.delete(`/categories/${id}`),
};

// Search APIs
export const searchAPI = {
  collate: (data: { category_id: string; search_query: string }) =>
    api.post('/search/collate', data),
  getResults: (params: any) => api.get('/search/results', { params }),
  react: (resultId: string, reactionType: string) =>
    api.post(`/search/results/${resultId}/react`, { reaction_type: reactionType }),
  deleteResults: (categoryId: string) =>
    api.delete('/search/results/bulk', { params: { category_id: categoryId } }),
};

// User APIs
export const userAPI = {
  updateProfile: (data: any) => api.put('/users/profile', data),
  subscribe: () => api.post('/users/subscribe'),
};

// Admin APIs
export const adminAPI = {
  getSettings: () => api.get('/admin/settings'),
};

export default api;
