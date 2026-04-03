/**
 * DramaForge Auth API
 * ====================
 * Registration, login, logout, and user profile functions.
 */
import apiClient, { setToken, setRefreshToken, clearTokens } from './client'

// ═══════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════

export interface RegisterRequest {
  email?: string
  phone?: string
  password: string
  nickname?: string
}

export interface LoginRequest {
  email?: string
  phone?: string
  password: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserInfo {
  id: number
  email: string | null
  phone: string | null
  nickname: string | null
  avatar_url: string | null
  status: string
  created_at: string
}

// ═══════════════════════════════════════════════════════════════════
// API Functions
// ═══════════════════════════════════════════════════════════════════

/** Register a new user and store tokens */
export async function register(data: RegisterRequest): Promise<AuthTokens> {
  const response = await apiClient.post<AuthTokens>('/user/register', data)
  const tokens = response.data
  setToken(tokens.access_token)
  setRefreshToken(tokens.refresh_token)
  return tokens
}

/** Login with email/phone + password and store tokens */
export async function login(data: LoginRequest): Promise<AuthTokens> {
  const response = await apiClient.post<AuthTokens>('/user/login', data)
  const tokens = response.data
  setToken(tokens.access_token)
  setRefreshToken(tokens.refresh_token)
  return tokens
}

/** Logout and clear tokens */
export async function logout(): Promise<void> {
  try {
    await apiClient.post('/user/logout')
  } finally {
    clearTokens()
  }
}

/** Get current user profile */
export async function getCurrentUser(): Promise<UserInfo> {
  const response = await apiClient.get<UserInfo>('/user/me')
  return response.data
}
