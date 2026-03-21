import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance with credentials
const apiClient = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper to get CSRF token from cookies
const getCsrfToken = () => {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
};

// Add CSRF token to requests that need it
apiClient.interceptors.request.use((config) => {
  if (['post', 'put', 'delete', 'patch'].includes(config.method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers['x-csrf-token'] = csrfToken;
    }
  }
  return config;
});

// Auth API
export const authAPI = {
  login: (email, password) => apiClient.post('/auth/login', { email, password }),
  register: (email, password) => apiClient.post('/auth/register', { email, password }),
  getMe: () => apiClient.get('/auth/me'),
  logout: () => apiClient.post('/auth/logout'),
  logoutAll: () => apiClient.post('/auth/logout-all'),
  refresh: () => apiClient.post('/auth/refresh'),
  telegramCallback: (initData) => apiClient.get(`/auth/telegram/callback?${initData}`),
};

// Modules API
export const modulesAPI = {
  getAll: () => apiClient.get('/modules'),
  getOne: (moduleId) => apiClient.get(`/modules/${moduleId}`),
};

// Lessons API
export const lessonsAPI = {
  getOne: (lessonId) => apiClient.get(`/lessons/${lessonId}`),
  getContent: (lessonId) => apiClient.get(`/lessons/${lessonId}/content`),
};

// Progress API
export const progressAPI = {
  get: () => apiClient.get('/progress'),
  getStats: () => apiClient.get('/progress/stats'),
  completeLesson: (lessonId) => apiClient.post(`/progress/lessons/${lessonId}/complete`),
};

// Chat API (non-streaming)
export const chatAPI = {
  lecture: (lessonId, message, messageId, sessionId = null) =>
    apiClient.post('/chat/lecture', { lesson_id: lessonId, message, message_id: messageId, session_id: sessionId }),
  examStart: (lessonId) => apiClient.post('/chat/exam/start', { lesson_id: lessonId }),
  examFinish: (sessionId, answers) => apiClient.post('/chat/exam/finish', { session_id: sessionId, answers }),
  consultant: (message, messageId, sessionId = null) =>
    apiClient.post('/chat/consultant', { message, message_id: messageId, session_id: sessionId }),
  getSessions: () => apiClient.get('/chat/sessions'),
  getSession: (sessionId) => apiClient.get(`/chat/sessions/${sessionId}`),
};

export default apiClient;
