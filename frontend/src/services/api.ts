import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';
const API_URL = `${BASE_URL}/api`;

class ApiService {
  private token: string | null = null;

  private getHeaders() {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  async loadTokenFromStorage() {
    try {
      const storedToken = await AsyncStorage.getItem('auth_token');
      if (storedToken) {
        this.token = storedToken;
      }
    } catch (error) {
      console.error('Error loading token:', error);
    }
  }

  async get(endpoint: string, params?: Record<string, any>) {
    await this.loadTokenFromStorage();
    const response = await axios.get(`${API_URL}${endpoint}`, {
      headers: this.getHeaders(),
      params,
    });
    return response.data;
  }

  async post(endpoint: string, data: any) {
    await this.loadTokenFromStorage();
    const response = await axios.post(`${API_URL}${endpoint}`, data, {
      headers: this.getHeaders(),
    });
    return response.data;
  }

  async put(endpoint: string, data: any) {
    await this.loadTokenFromStorage();
    const response = await axios.put(`${API_URL}${endpoint}`, data, {
      headers: this.getHeaders(),
    });
    return response.data;
  }

  async delete(endpoint: string) {
    await this.loadTokenFromStorage();
    const response = await axios.delete(`${API_URL}${endpoint}`, {
      headers: this.getHeaders(),
    });
    return response.data;
  }

  // Search endpoints
  async googleSearch(query: string, num: number = 10) {
    return this.get('/search/google', { q: query, num });
  }

  async collateResults(query: string, results: any[], selectedCategoryIds?: string[]) {
    return this.post('/search/collate', {
      query,
      results,
      category_ids: selectedCategoryIds,
    });
  }
}

export const api = new ApiService();

// Legacy axios-based API for backward compatibility
const legacyApi = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
legacyApi.interceptors.request.use(
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
    legacyApi.post('/auth/register', data),
  login: (data: { username: string; password: string }) =>
    legacyApi.post('/auth/login', data),
  getMe: () => legacyApi.get('/auth/me'),
};

// Category APIs
export const categoryAPI = {
  create: (data: { name: string; protocol: string; parent_id?: string; is_public: boolean }) =>
    legacyApi.post('/categories', data),
  getAll: () => legacyApi.get('/categories'),
  getPublic: (username: string) => legacyApi.get(`/categories/user/${username}`),
  update: (id: string, data: any) => legacyApi.put(`/categories/${id}`, data),
  delete: (id: string) => legacyApi.delete(`/categories/${id}`),
};

// Search APIs
export const searchAPI = {
  collate: (data: { category_id: string; search_query: string }) =>
    legacyApi.post('/search/collate', data),
  getResults: (params: any) => legacyApi.get('/search/results', { params }),
  react: (resultId: string, reactionType: string) =>
    legacyApi.post(`/search/results/${resultId}/react`, { reaction_type: reactionType }),
  deleteResults: (categoryId: string) =>
    legacyApi.delete('/search/results/bulk', { params: { category_id: categoryId } }),
};

// User APIs
export const userAPI = {
  updateProfile: (data: any) => legacyApi.put('/users/profile', data),
  subscribe: () => legacyApi.post('/users/subscribe'),
};

// Admin APIs
export const adminAPI = {
  getSettings: () => legacyApi.get('/admin/settings'),
};

// Marketplace APIs
export const marketplaceAPI = {
  getProtocols: (params?: { sort?: string; min_price?: number; max_price?: number }) =>
    legacyApi.get('/marketplace/protocols', { params }),
  sellProtocol: (data: { category_id: string; price: number; description?: string }) =>
    legacyApi.post('/marketplace/sell', data),
  purchaseProtocol: (data: { protocol_id: string }) =>
    legacyApi.post('/marketplace/purchase', data),
  getPayoutInfo: () => legacyApi.get('/marketplace/payout'),
  requestPayout: () => legacyApi.post('/marketplace/payout'),
};

export default legacyApi;
