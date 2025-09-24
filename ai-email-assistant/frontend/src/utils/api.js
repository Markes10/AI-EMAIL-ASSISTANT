import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

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

export default api;
