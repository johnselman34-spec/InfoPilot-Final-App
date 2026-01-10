import axios from 'axios';

const BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

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

  async get(endpoint: string, params?: Record<string, any>) {
    const response = await axios.get(`${BASE_URL}/api${endpoint}`, {
      headers: this.getHeaders(),
      params,
    });
    return response.data;
  }

  async post(endpoint: string, data: any) {
    const response = await axios.post(`${BASE_URL}/api${endpoint}`, data, {
      headers: this.getHeaders(),
    });
    return response.data;
  }

  async put(endpoint: string, data: any) {
    const response = await axios.put(`${BASE_URL}/api${endpoint}`, data, {
      headers: this.getHeaders(),
    });
    return response.data;
  }

  async delete(endpoint: string) {
    const response = await axios.delete(`${BASE_URL}/api${endpoint}`, {
      headers: this.getHeaders(),
    });
    return response.data;
  }
}

export const api = new ApiService();
