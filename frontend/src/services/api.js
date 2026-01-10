import axios from 'axios';

const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('token');
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  async get(endpoint, params) {
    const response = await axios.get(`${BASE_URL}/api${endpoint}`, {
      headers: this.getHeaders(),
      params,
    });
    return response.data;
  }

  async post(endpoint, data) {
    const response = await axios.post(`${BASE_URL}/api${endpoint}`, data, {
      headers: this.getHeaders(),
    });
    return response.data;
  }

  async put(endpoint, data) {
    const response = await axios.put(`${BASE_URL}/api${endpoint}`, data, {
      headers: this.getHeaders(),
    });
    return response.data;
  }

  async delete(endpoint) {
    const response = await axios.delete(`${BASE_URL}/api${endpoint}`, {
      headers: this.getHeaders(),
    });
    return response.data;
  }
}

export const api = new ApiService();
