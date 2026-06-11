import axios from 'axios';

const envApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const isBrowser = typeof window !== 'undefined';
const apiBaseUrl = isBrowser ? '' : (envApiUrl || 'http://localhost:8000');

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

export default api;
