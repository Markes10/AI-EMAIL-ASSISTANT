import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const auth = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  register: (userData) => api.post('/api/auth/register', userData),
};

// Email endpoints
export const emails = {
  generate: (data) => api.post('/api/email/generate', data),
  send: (data) => api.post('/api/email/send', data),
  getHistory: () => api.get('/api/history'),
  exportPDF: (emailId) => api.get(`/api/history/export/${emailId}`, {
    responseType: 'blob'
  }),
};

// Resume endpoints
export const resumes = {
  upload: (formData) => api.post('/api/resume/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  match: (jobDescription) => api.post('/api/resume/match', { jobDescription }),
  list: () => api.get('/api/resume/list'),
};

// Reply endpoints
export const reply = {
  generate: (data) => api.post('/api/reply/generate', data),
};

// Tone endpoints
export const tone = {
  adjust: (data) => api.post('/api/tone/adjust', data),
};

// Gmail / OAuth endpoints
export const gmail = {
  start: () => api.get('/api/gmail/start'),
  status: () => api.get('/api/gmail/status'),
  disconnect: () => api.post('/api/gmail/disconnect'),
  send: (payload) => api.post('/api/gmail/send', payload),
};

// Model registry / intent endpoints
export const models = {
  list: () => api.get('/api/intent/models'),
  retrain: (samples) => api.post('/api/intent/retrain', samples),
};

export default api;
