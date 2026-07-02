/**
 * DramaForge Auth Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  login,
  register,
  logout,
  getCurrentUser,
  sendLoginCode,
  updateUsername,
  updateEmail,
  changePassword,
} from '@/api/auth'
import { isAuthenticated, clearTokens } from '@/api/client'
import type { LoginRequest, RegisterRequest, UserInfo } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const isLoading = ref(false)
  const isSendingCode = ref(false)
  const error = ref<string | null>(null)

  const isLoggedIn = computed(() => !!user.value)
  const displayName = computed(() => {
    if (!user.value) return ''
    if (user.value.username) return user.value.username
    if (user.value.nickname) return user.value.nickname
    if (user.value.email) return user.value.email.split('@')[0]
    if (user.value.phone) return `用户${user.value.phone.slice(-4)}`
    return `用户${user.value.id}`
  })

  async function requestLoginCode(email: string): Promise<number | null> {
    isSendingCode.value = true
    error.value = null
    try {
      const result = await sendLoginCode({ email })
      return result.resend_after
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '验证码发送失败'
      return null
    } finally {
      isSendingCode.value = false
    }
  }

  async function doLogin(credentials: LoginRequest, remember = true): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      await login(credentials, remember)
      await fetchUser()
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '登录失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function doRegister(data: RegisterRequest, remember = true): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      await register(data, remember)
      await fetchUser()
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '注册失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function doLogout(): Promise<void> {
    try {
      await logout()
    } finally {
      user.value = null
    }
  }

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

  async function doUpdateUsername(username: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      user.value = await updateUsername({ username })
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '用户名修改失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function doUpdateEmail(email: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      user.value = await updateEmail({ email })
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '邮箱修改失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function doChangePassword(currentPassword: string, newPassword: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '密码修改失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

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
    isSendingCode,
    error,
    isLoggedIn,
    displayName,
    requestLoginCode,
    doLogin,
    doRegister,
    doLogout,
    fetchUser,
    doUpdateUsername,
    doUpdateEmail,
    doChangePassword,
    initialize,
    clearError,
  }
})
