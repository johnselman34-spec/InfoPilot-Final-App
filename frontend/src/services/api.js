/**
 * API service for making HTTP requests
 */
import axios from 'axios';
import { API } from './constants';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// Auth API
export const authAPI = {
  login: (email, password) => apiClient.post('/auth/login', { email, password }),
  register: (username, email, password) => apiClient.post('/auth/register', { username, email, password }),
  googleAuth: (credential) => apiClient.post('/auth/google', { credential }),
  getMe: () => apiClient.get('/auth/me')
};

// Categories API
export const categoriesAPI = {
  getAll: () => apiClient.get('/categories'),
  getTree: () => apiClient.get('/categories/tree'),
  getWithCounts: () => apiClient.get('/categories/with-counts'),
  create: (data) => apiClient.post('/categories', data),
  update: (id, data) => apiClient.put(`/categories/${id}`, data),
  delete: (id) => apiClient.delete(`/categories/${id}`),
  copy: (id) => apiClient.post(`/categories/${id}/copy`),
  createSubcategory: (parentId, data) => apiClient.post(`/categories/${parentId}/subcategory`, data)
};

// Search API
export const searchAPI = {
  collate: (data) => apiClient.post('/search/collate', data),
  ultimateSearch: (data) => apiClient.post('/ultimate-search', data),
  aiSearch: (data) => apiClient.post('/ultimate-search/ai', data),
  getFilters: () => apiClient.get('/ultimate-search/filters'),
  getMapData: () => apiClient.get('/ultimate-search/map-data'),
  getSessions: () => apiClient.get('/ultimate-search/sessions'),
  deleteResult: (id) => apiClient.delete(`/results/${id}`),
  deleteResults: (ids) => apiClient.delete('/results/batch', { data: { result_ids: ids } }),
  clearAll: () => apiClient.delete('/ultimate-search/clear-all'),
  clearCategory: (categoryId) => apiClient.delete(`/ultimate-search/category/${categoryId}/clear`),
  deleteSession: (timestamp) => apiClient.delete(`/ultimate-search/session/${timestamp}`),
  getUserStats: () => apiClient.get('/ultimate-search/user-stats'),
  getCategoryResults: (categoryId) => apiClient.get(`/ultimate-search/category/${categoryId}/results`)
};

// Social API
export const socialAPI = {
  // Friends
  getFriends: () => apiClient.get('/friends'),
  sendFriendRequest: (friendId) => apiClient.post('/friends/request', { friend_id: friendId }),
  getFriendRequests: () => apiClient.get('/friends/requests'),
  acceptFriendRequest: (requestId) => apiClient.post(`/friends/accept/${requestId}`),
  rejectFriendRequest: (requestId) => apiClient.post(`/friends/reject/${requestId}`),
  removeFriend: (friendId) => apiClient.delete(`/friends/${friendId}`),
  
  // Groups
  getGroups: () => apiClient.get('/groups'),
  createGroup: (data) => apiClient.post('/groups', data),
  getGroup: (id) => apiClient.get(`/groups/${id}`),
  updateGroup: (id, data) => apiClient.put(`/groups/${id}`, data),
  deleteGroup: (id) => apiClient.delete(`/groups/${id}`),
  joinGroup: (id) => apiClient.post(`/groups/${id}/join`),
  leaveGroup: (id) => apiClient.post(`/groups/${id}/leave`),
  createGroupPost: (groupId, data) => apiClient.post(`/groups/${groupId}/posts`, data),
  
  // Pages
  getPages: () => apiClient.get('/pages'),
  createPage: (data) => apiClient.post('/pages', data),
  getPage: (id) => apiClient.get(`/pages/${id}`),
  updatePage: (id, data) => apiClient.put(`/pages/${id}`, data),
  deletePage: (id) => apiClient.delete(`/pages/${id}`),
  followPage: (id) => apiClient.post(`/pages/${id}/follow`),
  unfollowPage: (id) => apiClient.post(`/pages/${id}/unfollow`),
  createPagePost: (pageId, data) => apiClient.post(`/pages/${pageId}/posts`, data)
};

// Messages API
export const messagesAPI = {
  getConversations: () => apiClient.get('/messages/conversations'),
  getConversation: (userId) => apiClient.get(`/messages/conversation/${userId}`),
  sendMessage: (data) => apiClient.post('/messages/send', data),
  getUnreadCount: () => apiClient.get('/messages/unread-count'),
  markRead: (conversationId) => apiClient.put(`/messages/mark-read/${conversationId}`),
  deleteMessage: (messageId) => apiClient.delete(`/messages/${messageId}`)
};

// Admin API
export const adminAPI = {
  getSettings: () => apiClient.get('/admin/settings'),
  updateSettings: (data) => apiClient.put('/admin/settings', data),
  getUsers: () => apiClient.get('/admin/users'),
  banUser: (userId) => apiClient.post(`/admin/ban-user/${userId}`),
  makeAdmin: (userId) => apiClient.post(`/admin/make-admin/${userId}`),
  setPaid: (userId) => apiClient.post(`/admin/set-paid/${userId}`),
  getDatabaseLimits: () => apiClient.get('/admin/database-limits'),
  updateDatabaseLimits: (data) => apiClient.put('/admin/database-limits', data),
  getSearchPagesConfig: () => apiClient.get('/admin/search-pages-config'),
  updateSearchPagesConfig: (data) => apiClient.put('/admin/search-pages-config', data),
  getSubscriptions: () => apiClient.get('/admin/subscriptions'),
  updateSubscriptionConfig: (data) => apiClient.put('/admin/subscription/config', data)
};

// Badges API
export const badgesAPI = {
  getMyBadges: () => apiClient.get('/badges/my-badges'),
  checkNew: () => apiClient.post('/badges/check-new'),
  getProtocolBadges: (categoryId) => apiClient.get(`/badges/protocol/${categoryId}`),
  getLeaderboard: () => apiClient.get('/badges/leaderboard')
};

// Statistics API
export const statisticsAPI = {
  get: () => apiClient.get('/statistics'),
  getPopularProtocols: () => apiClient.get('/statistics/popular-protocols'),
  getGlobal: () => apiClient.get('/statistics/global')
};

// Marketplace API
export const marketplaceAPI = {
  getProtocols: () => apiClient.get('/marketplace/protocols'),
  purchaseProtocol: (categoryId) => apiClient.post(`/marketplace/protocols/${categoryId}/purchase`),
  getMyPurchases: () => apiClient.get('/marketplace/my-purchases'),
  getMySales: () => apiClient.get('/marketplace/my-sales'),
  updateSaleSettings: (categoryId, data) => apiClient.put(`/categories/${categoryId}/sale-settings`, data)
};

// Posts/Reactions/Comments API
export const postsAPI = {
  addReaction: (postType, postId, data) => apiClient.post(`/posts/${postType}/${postId}/reactions`, data),
  removeReaction: (postType, postId) => apiClient.delete(`/posts/${postType}/${postId}/reactions`),
  getReactions: (postType, postId) => apiClient.get(`/posts/${postType}/${postId}/reactions`),
  addComment: (postType, postId, data) => apiClient.post(`/posts/${postType}/${postId}/comments`, data),
  getComments: (postType, postId) => apiClient.get(`/posts/${postType}/${postId}/comments`),
  deleteComment: (commentId) => apiClient.delete(`/comments/${commentId}`),
  reactToComment: (commentId, data) => apiClient.post(`/comments/${commentId}/reactions`, data)
};
