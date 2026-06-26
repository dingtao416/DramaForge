/**
 * DramaForge Auth API
 */
import apiClient, { setAuthTokens, clearTokens } from './client'

export interface SendLoginCodeRequest {
  email: string
}

export interface SendLoginCodeResponse {
  sent: boolean
  expires_in: number
  resend_after: number
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  code: string
}

export interface LoginRequest {
  account: string
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
  username: string | null
  email: string | null
  phone: string | null
  nickname: string | null
  avatar_url: string | null
  status: string
  created_at: string
  credits: number
  plan_code: string
}

export async function sendLoginCode(data: SendLoginCodeRequest): Promise<SendLoginCodeResponse> {
  const response = await apiClient.post<SendLoginCodeResponse>('/user/send-login-code', data)
  return response.data
}

export async function register(data: RegisterRequest, remember = true): Promise<AuthTokens> {
  const response = await apiClient.post<AuthTokens>('/user/register', data)
  const tokens = response.data
  setAuthTokens(tokens.access_token, tokens.refresh_token, remember)
  return tokens
}

export async function login(data: LoginRequest, remember = true): Promise<AuthTokens> {
  const response = await apiClient.post<AuthTokens>('/user/login', data)
  const tokens = response.data
  setAuthTokens(tokens.access_token, tokens.refresh_token, remember)
  return tokens
}

export async function logout(): Promise<void> {
  try {
    await apiClient.post('/user/logout')
  } finally {
    clearTokens()
  }
}

export async function getCurrentUser(): Promise<UserInfo> {
  const response = await apiClient.get<UserInfo>('/user/me')
  return response.data
}
