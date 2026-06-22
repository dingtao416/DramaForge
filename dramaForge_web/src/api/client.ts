/**
 * DramaForge v2.0 — API Client
 * Axios instance with JWT token management & auto-refresh.
 * Pattern adapted from IAA project.
 */
import axios from 'axios'
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

// ═══════════════════════════════════════════════════════════════════
// Token Management (localStorage)
// ═══════════════════════════════════════════════════════════════════

const TOKEN_KEY = 'df_access_token'
const REFRESH_TOKEN_KEY = 'df_refresh_token'
const REMEMBER_LOGIN_KEY = 'df_remember_login'

function tokenStorage(): Storage {
  return localStorage.getItem(REMEMBER_LOGIN_KEY) === 'true' ? localStorage : sessionStorage
}

function storageWithToken(key: string): Storage | null {
  if (localStorage.getItem(key)) return localStorage
  if (sessionStorage.getItem(key)) return sessionStorage
  return null
}

function writeToken(key: string, value: string, remember = isRememberLoginEnabled()): void {
  const target = remember ? localStorage : sessionStorage
  const stale = remember ? sessionStorage : localStorage
  stale.removeItem(key)
  target.setItem(key, value)
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string, remember = isRememberLoginEnabled()): void {
  writeToken(TOKEN_KEY, token, remember)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY) || sessionStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token: string, remember = isRememberLoginEnabled()): void {
  writeToken(REFRESH_TOKEN_KEY, token, remember)
}

export function setRememberLogin(remember: boolean): void {
  localStorage.setItem(REMEMBER_LOGIN_KEY, remember ? 'true' : 'false')
}

export function isRememberLoginEnabled(): boolean {
  return localStorage.getItem(REMEMBER_LOGIN_KEY) === 'true'
}

export function setAuthTokens(accessToken: string, refreshToken: string, remember: boolean): void {
  setRememberLogin(remember)
  setToken(accessToken, remember)
  setRefreshToken(refreshToken, remember)
}

export function getTokenStorageRemembered(): boolean {
  return storageWithToken(REFRESH_TOKEN_KEY) === localStorage || tokenStorage() === localStorage
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function isAuthenticated(): boolean {
  return !!getToken()
}

// ═══════════════════════════════════════════════════════════════════
// Axios Instance
// ═══════════════════════════════════════════════════════════════════

const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 120_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request interceptor: auto-attach Bearer token ──
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor: 401 auto-refresh ──
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError<{ detail?: string }>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // 401 and not already retried → try refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = getRefreshToken()
      if (refreshToken) {
        try {
          // Use raw axios to avoid interceptor loop
          const refreshUrl = `${import.meta.env.VITE_API_BASE_URL}/user/refresh`
          const response = await axios.post(refreshUrl, {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token: newRefresh } = response.data
          const remember = getTokenStorageRemembered()
          setToken(access_token, remember)
          setRefreshToken(newRefresh, remember)

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return apiClient(originalRequest)
        } catch {
          // Refresh failed → clear tokens and redirect to login
          clearTokens()
          window.location.href = '/login'
        }
      } else {
        clearTokens()
        window.location.href = '/login'
      }
    }

    const msg = error.response?.data?.detail || error.message || '请求失败'
    console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}: ${msg}`)
    return Promise.reject(error)
  }
)

export default apiClient
