/**
 * DramaForge — Auth Store (Pinia)
 * User login state management.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, register, logout, getCurrentUser } from '@/api/auth'
import { isAuthenticated, clearTokens } from '@/api/client'
import type { LoginRequest, RegisterRequest, UserInfo } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // ═══════ State ═══════
  const user = ref<UserInfo | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // ═══════ Getters ═══════
  const isLoggedIn = computed(() => !!user.value)
  const displayName = computed(() => {
    if (!user.value) return ''
    if (user.value.nickname) return user.value.nickname
    if (user.value.email) return user.value.email.split('@')[0]
    if (user.value.phone) return '用户' + user.value.phone.slice(-4)
    return '用户' + user.value.id
  })

  // ═══════ Actions ═══════

  /** Login */
  async function doLogin(credentials: LoginRequest): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      await login(credentials)
      await fetchUser()
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '登录失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /** Register */
  async function doRegister(data: RegisterRequest): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      await register(data)
      await fetchUser()
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '注册失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /** Logout */
  async function doLogout(): Promise<void> {
    try {
      await logout()
    } finally {
      user.value = null
    }
  }

  /** Fetch current user from API */
  async function fetchUser(): Promise<void> {
    if (!isAuthenticated()) {
      user.value = null
      return
    }
    isLoading.value = true
    try {
      user.value = await getCurrentUser()
    } catch {
      user.value = null
      clearTokens()
    } finally {
      isLoading.value = false
    }
  }

  /** Initialize — check stored token on app start */
  async function initialize(): Promise<void> {
    if (isAuthenticated()) {
      await fetchUser()
    }
  }

  function clearError(): void {
    error.value = null
  }

  return {
    user,
    isLoading,
    error,
    isLoggedIn,
    displayName,
    doLogin,
    doRegister,
    doLogout,
    fetchUser,
    initialize,
    clearError,
  }
})
