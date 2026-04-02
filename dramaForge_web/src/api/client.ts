import axios from 'axios'
import type { AxiosInstance, AxiosError } from 'axios'

const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v2',
  timeout: 120_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request interceptor ──
apiClient.interceptors.request.use(
  (config) => {
    // future: attach auth token here
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor ──
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${msg}`)
    return Promise.reject(error)
  }
)

export default apiClient