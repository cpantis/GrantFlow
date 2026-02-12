import axios from 'axios';

// Prefer the new env var name; keep the old one as fallback for backward compatibility.
const API_URL = process.env.REACT_APP_API_BASE_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const api = axios.create({ baseURL: `${API_URL}/api` });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('grantflow_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('grantflow_token');
      localStorage.removeItem('grantflow_user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;
