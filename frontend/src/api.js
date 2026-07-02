import axios from 'axios'

// All requests go through the Vite dev proxy (/api -> http://localhost:8000).
// In production, set VITE_API_BASE to your hosted API URL.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  headers: {
    Authorization: `Bearer ${import.meta.env.VITE_API_KEY || 'demo-key'}`,
  },
})

export default api
