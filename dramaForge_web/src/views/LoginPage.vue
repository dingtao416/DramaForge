<script setup lang="ts">
/**
 * DramaForge — Login / Register Page
 * Minimal, beautiful auth page with tab switch.
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const email = ref('')
const password = ref('')
const nickname = ref('')

async function handleSubmit() {
  if (!email.value || !password.value) return

  let ok: boolean
  if (isRegister.value) {
    ok = await authStore.doRegister({
      email: email.value,
      password: password.value,
      nickname: nickname.value || undefined,
    })
  } else {
    ok = await authStore.doLogin({
      email: email.value,
      password: password.value,
    })
  }

  if (ok) {
    router.replace('/')
  }
}

function toggleMode() {
  isRegister.value = !isRegister.value
  authStore.clearError()
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <div class="logo-box">
        <div class="logo">D</div>
        <h1 class="logo-title">DramaForge</h1>
        <p class="logo-subtitle">AI 短剧创作平台</p>
      </div>

      <!-- Tab switch -->
      <div class="tab-row">
        <button
          class="tab-btn"
          :class="!isRegister ? 'tab-active' : ''"
          @click="isRegister = false; authStore.clearError()"
        >登录</button>
        <button
          class="tab-btn"
          :class="isRegister ? 'tab-active' : ''"
          @click="isRegister = true; authStore.clearError()"
        >注册</button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label class="form-label">邮箱</label>
          <input
            v-model="email"
            type="email"
            class="form-input"
            placeholder="your@email.com"
            required
          />
        </div>

        <div v-if="isRegister" class="form-group">
          <label class="form-label">昵称 <span class="optional">(可选)</span></label>
          <input
            v-model="nickname"
            type="text"
            class="form-input"
            placeholder="你的昵称"
          />
        </div>

        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            placeholder="至少 6 位"
            minlength="6"
            required
          />
        </div>

        <!-- Error -->
        <div v-if="authStore.error" class="error-msg">
          {{ authStore.error }}
        </div>

        <button
          type="submit"
          class="submit-btn"
          :disabled="authStore.isLoading || !email || !password"
        >
          <span v-if="authStore.isLoading" class="spinner" />
          <span v-else>{{ isRegister ? '注册并登录' : '登录' }}</span>
        </button>
      </form>

      <!-- Toggle -->
      <p class="toggle-text">
        {{ isRegister ? '已有账号？' : '没有账号？' }}
        <span class="toggle-link" @click="toggleMode">
          {{ isRegister ? '去登录' : '立即注册' }}
        </span>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8f7ff 0%, #f0ebff 50%, #e8e0ff 100%);
}

.login-card {
  width: 400px;
  background: white;
  border-radius: 20px;
  padding: 40px 36px;
  box-shadow: 0 8px 40px rgba(124, 58, 237, 0.08), 0 2px 12px rgba(0, 0, 0, 0.04);
}

.logo-box {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  border-radius: 14px;
  color: white;
  font-size: 22px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  box-shadow: 0 4px 16px rgba(124, 58, 237, 0.2);
}

.logo-title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
}

.logo-subtitle {
  font-size: 13px;
  color: #999;
  margin: 4px 0 0;
}

.tab-row {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  background: #f5f3ff;
  border-radius: 12px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  height: 38px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #888;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-active {
  background: white;
  color: #7c3aed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #555;
}

.optional {
  color: #bbb;
  font-weight: 400;
}

.form-input {
  height: 44px;
  padding: 0 14px;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  font-size: 14px;
  color: #1a1a1a;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  border-color: #c4b5fd;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.06);
}

.form-input::placeholder {
  color: #ccc;
}

.error-msg {
  font-size: 13px;
  color: #ef4444;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  padding: 10px 14px;
}

.submit-btn {
  height: 46px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 4px;
}

.submit-btn:hover:not(:disabled) {
  opacity: 0.92;
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.toggle-text {
  text-align: center;
  font-size: 13px;
  color: #888;
  margin-top: 20px;
}

.toggle-link {
  color: #7c3aed;
  font-weight: 500;
  cursor: pointer;
}

.toggle-link:hover {
  text-decoration: underline;
}
</style>
