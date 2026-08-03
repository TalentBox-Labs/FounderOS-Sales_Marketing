import axios from 'axios'

// Dev: Vite proxies /api -> http://localhost:8000 (see vite.config.js).
// Production: the FastAPI server hosts the built frontend, so requests go
// to the same origin directly. Override with VITE_API_BASE if the API
// lives elsewhere.
const baseURL = import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? '/api' : '')

const api = axios.create({ baseURL })

export function getApiKey() {
  return localStorage.getItem('crm_api_key') || ''
}

export function setApiKey(key) {
  if (key) localStorage.setItem('crm_api_key', key)
  else localStorage.removeItem('crm_api_key')
}

export function isAuthed() {
  return localStorage.getItem('crm_authed') === '1'
}

export function setAuthed(value) {
  if (value) localStorage.setItem('crm_authed', '1')
  else localStorage.removeItem('crm_authed')
}

export function logout() {
  setApiKey('')
  setAuthed(false)
  window.location.hash = '#/login'
  window.location.reload()
}

api.interceptors.request.use(config => {
  const key = getApiKey()
  if (key) config.headers.Authorization = `Bearer ${key}`
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401 && isAuthed()) {
      // Key was revoked or changed server-side — force re-login.
      logout()
    }
    return Promise.reject(error)
  },
)

export default api
