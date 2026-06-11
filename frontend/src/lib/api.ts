import axios from 'axios';

const envApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const defaultApiUrl = 'http://localhost:8000';

const apiBaseUrl = envApiUrl || defaultApiUrl;

const api = axios.create({
  baseURL: apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

export default api;
