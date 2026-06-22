<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const email = ref('')
const code = ref('')
const nickname = ref('')
const agreeTerms = ref(false)
const rememberMe = ref(true)
const countdown = ref(0)
const sendMessage = ref('')
let countdownTimer: ReturnType<typeof setInterval> | null = null
const REMEMBER_EMAIL_KEY = 'df_remember_email'
const REMEMBER_LOGIN_KEY = 'df_remember_login'

const showcaseItems = [
  {
    title: '短剧创作',
    desc: '从创意到分镜，完整管理短剧生产流程。',
    label: 'SCRIPT',
  },
  {
    title: '智能分镜',
    desc: '自动拆解场景、角色和镜头语言，保持创作节奏。',
    label: 'SHOT',
  },
  {
    title: '角色资产',
    desc: '沉淀角色和场景设定，让后续生成保持一致。',
    label: 'CAST',
  },
  {
    title: '视频成片',
    desc: '串联画面、配音和镜头，推进到可交付短片。',
    label: 'FILM',
  },
]

const currentShowcase = ref(0)
let showcaseTimer: ReturnType<typeof setInterval> | null = null

const normalizedEmail = computed(() => email.value.trim())
const isEmailValid = computed(() => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(normalizedEmail.value))
const isCodeValid = computed(() => /^\d{4,10}$/.test(code.value.trim()))
const canSendCode = computed(() => isEmailValid.value && countdown.value === 0 && !authStore.isSendingCode)
const isFormValid = computed(() => isEmailValid.value && isCodeValid.value)

function startCountdown(seconds: number) {
  countdown.value = Math.max(1, seconds)
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0 && countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

async function handleSendCode() {
  authStore.clearError()
  sendMessage.value = ''

  if (!isEmailValid.value) {
    authStore.error = '请输入有效的邮箱地址'
    return
  }

  const resendAfter = await authStore.requestLoginCode(normalizedEmail.value)
  if (resendAfter !== null) {
    sendMessage.value = '验证码已发送，请查看邮箱'
    startCountdown(resendAfter)
  }
}

async function handleSubmit() {
  authStore.clearError()

  if (!agreeTerms.value) {
    authStore.error = '请先阅读并同意相关协议'
    return
  }

  if (!isFormValid.value) return

  const payload = {
    email: normalizedEmail.value,
    code: code.value.trim(),
  }
  const ok = isRegister.value
    ? await authStore.doRegister({ ...payload, nickname: nickname.value.trim() || undefined }, rememberMe.value)
    : await authStore.doLogin(payload, rememberMe.value)

  if (ok) {
    if (rememberMe.value) {
      localStorage.setItem(REMEMBER_EMAIL_KEY, normalizedEmail.value)
    } else {
      localStorage.removeItem(REMEMBER_EMAIL_KEY)
    }
    const redirect = typeof router.currentRoute.value.query.redirect === 'string'
      ? router.currentRoute.value.query.redirect
      : '/'
    router.replace(redirect)
  }
}

function toggleMode() {
  isRegister.value = !isRegister.value
  code.value = ''
  sendMessage.value = ''
  authStore.clearError()
}

onMounted(() => {
  rememberMe.value = localStorage.getItem(REMEMBER_LOGIN_KEY) !== 'false'
  const rememberedEmail = localStorage.getItem(REMEMBER_EMAIL_KEY)
  if (rememberedEmail) email.value = rememberedEmail

  showcaseTimer = setInterval(() => {
    currentShowcase.value = (currentShowcase.value + 1) % showcaseItems.length
  }, 4000)
})

onUnmounted(() => {
  if (showcaseTimer) clearInterval(showcaseTimer)
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<template>
  <div class="login-page">
    <section class="showcase-panel">
      <div class="showcase-grid" />
      <div class="showcase-top-pills">
        <button
          v-for="(item, idx) in showcaseItems"
          :key="item.label"
          class="pill"
          :class="{ 'pill-active': currentShowcase === idx }"
          type="button"
          @click="currentShowcase = idx"
        >
          <span class="pill-code">{{ item.label }}</span>
          <span class="pill-label">{{ item.title }}</span>
        </button>
      </div>

      <div class="showcase-center">
        <div class="showcase-logo-large">D</div>
        <transition name="showcase-fade" mode="out-in">
          <div :key="currentShowcase" class="showcase-text">
            <div class="showcase-kicker">DramaForge</div>
            <h2 class="showcase-title">{{ showcaseItems[currentShowcase].title }}</h2>
            <p class="showcase-desc">{{ showcaseItems[currentShowcase].desc }}</p>
          </div>
        </transition>
      </div>

      <div class="showcase-bottom">
        <span>{{ showcaseItems[currentShowcase].label }}</span>
        <span>{{ showcaseItems[currentShowcase].title }} · {{ showcaseItems[currentShowcase].desc }}</span>
      </div>

      <div class="showcase-dots">
        <button
          v-for="(_, idx) in showcaseItems"
          :key="idx"
          class="dot"
          :class="{ 'dot-active': currentShowcase === idx }"
          type="button"
          @click="currentShowcase = idx"
        />
      </div>
    </section>

    <main class="auth-panel">
      <div class="auth-container">
        <div class="auth-logo-row">
          <div class="auth-logo">D</div>
        </div>

        <h1 class="auth-title">{{ isRegister ? '创建 DramaForge 账号' : '登录 DramaForge' }}</h1>
        <p class="auth-subtitle">
          {{ isRegister ? '使用邮箱验证码创建账号，无需设置密码。' : '输入邮箱验证码即可登录，未注册邮箱会自动创建账号。' }}
        </p>

        <form class="auth-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <input
              v-model="email"
              type="email"
              class="form-input"
              placeholder="请输入邮箱地址"
              autocomplete="email"
              required
            />
          </div>

          <div v-if="isRegister" class="form-group">
            <input
              v-model="nickname"
              type="text"
              class="form-input"
              placeholder="请输入昵称（可选）"
              autocomplete="nickname"
            />
          </div>

          <div class="code-row">
            <input
              v-model="code"
              type="text"
              class="form-input code-input"
              placeholder="请输入验证码"
              inputmode="numeric"
              autocomplete="one-time-code"
              maxlength="10"
              required
            />
            <button
              type="button"
              class="code-btn"
              :disabled="!canSendCode"
              @click="handleSendCode"
            >
              <span v-if="authStore.isSendingCode" class="spinner dark" />
              <span v-else-if="countdown > 0">{{ countdown }}s</span>
              <span v-else>发送验证码</span>
            </button>
          </div>

          <div v-if="sendMessage && !authStore.error" class="success-msg">
            {{ sendMessage }}
          </div>

          <div v-if="authStore.error" class="error-msg">
            {{ authStore.error }}
          </div>

          <div class="login-options-row">
            <label class="remember-option">
              <input v-model="rememberMe" type="checkbox" />
              <span class="remember-check" />
              <span class="remember-text">记住我，下次自动登录</span>
            </label>
          </div>

          <button
            type="submit"
            class="submit-btn"
            :disabled="authStore.isLoading || !isFormValid"
          >
            <span v-if="authStore.isLoading" class="spinner" />
            <span v-else>{{ isRegister ? '注册并登录' : '登录' }}</span>
          </button>
        </form>

        <div class="divider-row">
          <span class="divider-line" />
          <span class="divider-text">或</span>
          <span class="divider-line" />
        </div>

        <button class="alt-btn" type="button" @click="toggleMode">
          {{ isRegister ? '已有账号，直接登录' : '没有账号，立即注册' }}
        </button>

        <div class="agreement-row">
          <label class="agreement-checkbox">
            <input v-model="agreeTerms" type="checkbox" />
            <span class="checkmark" />
          </label>
          <span class="agreement-text">
            已阅读并同意
            <a href="javascript:void(0)" class="agreement-link">《用户服务协议》</a>
            <a href="javascript:void(0)" class="agreement-link">《隐私政策》</a>
            和
            <a href="javascript:void(0)" class="agreement-link">《AI 功能使用规范》</a>
          </span>
        </div>
      </div>

      <div class="auth-footer">
        <span>DramaForge © 2026 AI 短剧创作平台</span>
      </div>
    </main>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: #FDF5D6;
}

.showcase-panel {
  position: relative;
  display: flex;
  width: 50%;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    linear-gradient(140deg, rgba(8, 8, 10, 0.92), rgba(25, 23, 32, 0.96)),
    url('/assets/default-scene.webp');
  background-size: cover;
  color: #2D2515;
}

.showcase-panel::after {
  position: absolute;
  inset: 0;
  content: '';
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.08), rgba(0, 0, 0, 0.35));
  pointer-events: none;
}

.showcase-grid {
  position: absolute;
  inset: 0;
  opacity: 0.24;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 56px 56px;
}

.showcase-top-pills {
  position: absolute;
  top: 28px;
  left: 50%;
  z-index: 2;
  display: flex;
  gap: 8px;
  transform: translateX(-50%);
}

.pill {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.62);
  cursor: pointer;
  backdrop-filter: blur(8px);
  transition: all 0.2s ease;
}

.pill:hover,
.pill-active {
  border-color: rgba(255, 255, 255, 0.34);
  background: rgba(255, 255, 255, 0.14);
  color: #2D2515;
}

.pill-code {
  font-size: 10px;
  font-weight: 700;
}

.pill-label {
  font-size: 12px;
  font-weight: 500;
}

.showcase-center {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
  padding: 0 48px;
  text-align: center;
}

.showcase-logo-large {
  display: flex;
  width: 86px;
  height: 86px;
  align-items: center;
  justify-content: center;
  border-radius: 22px;
  background: linear-gradient(135deg, #E8A317, #111827);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.32);
  font-size: 38px;
  font-weight: 800;
}

.showcase-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.showcase-kicker {
  font-size: 12px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.56);
  text-transform: uppercase;
}

.showcase-title {
  margin: 0;
  color: #2D2515;
  font-size: 30px;
  font-weight: 700;
}

.showcase-desc {
  max-width: 360px;
  margin: 0;
  color: rgba(255, 255, 255, 0.64);
  font-size: 15px;
  line-height: 1.7;
}

.showcase-fade-enter-active,
.showcase-fade-leave-active {
  transition: all 0.35s ease;
}

.showcase-fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.showcase-fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

.showcase-bottom {
  position: absolute;
  right: 40px;
  bottom: 48px;
  left: 40px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: rgba(255, 255, 255, 0.54);
  font-size: 13px;
}

.showcase-dots {
  position: absolute;
  bottom: 24px;
  left: 50%;
  z-index: 2;
  display: flex;
  gap: 6px;
  transform: translateX(-50%);
}

.dot {
  width: 7px;
  height: 7px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.24);
  cursor: pointer;
  transition: all 0.2s ease;
}

.dot-active {
  width: 22px;
  background: #FDF5D6;
}

.auth-panel {
  position: relative;
  display: flex;
  width: 50%;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  background: #FDF5D6;
}

.auth-container {
  width: 100%;
  max-width: 400px;
  padding: 0 24px;
}

.auth-logo-row {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.auth-logo {
  display: flex;
  width: 48px;
  height: 48px;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #0a0a0a;
  color: #FFFFFF;
  font-size: 22px;
  font-weight: 700;
}

.auth-title {
  margin: 0 0 8px;
  color: #0a0a0a;
  font-size: 24px;
  font-weight: 700;
  text-align: center;
}

.auth-subtitle {
  margin: 0 0 28px;
  color: #777;
  font-size: 13px;
  line-height: 1.6;
  text-align: center;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-input {
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 16px;
  border: 1px solid #D4C898;
  border-radius: 8px;
  outline: none;
  background: #f8f8f8;
  color: #0a0a0a;
  font-size: 15px;
  transition: all 0.2s ease;
}

.form-input:focus {
  border-color: #111827;
  background: #FDF5D6;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.06);
}

.form-input::placeholder {
  color: #aaa;
  font-size: 14px;
}

.code-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 116px;
  gap: 10px;
}

.code-btn {
  height: 52px;
  border: 1px solid #0a0a0a;
  border-radius: 8px;
  background: #FDF5D6;
  color: #0a0a0a;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.code-btn:hover:not(:disabled) {
  background: #FDF4D8;
}

.code-btn:disabled {
  border-color: #D4C898;
  color: #aaa;
  cursor: not-allowed;
}

.error-msg,
.success-msg {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.error-msg {
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #dc2626;
}

.success-msg {
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  color: #15803d;
}

.login-options-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 24px;
}

.remember-option {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #555;
  font-size: 13px;
  cursor: pointer;
  user-select: none;
}

.remember-option input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
}

.remember-check {
  display: flex;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: 1.5px solid #d0d0d0;
  border-radius: 4px;
  background: #FDF5D6;
  transition: all 0.2s ease;
}

.remember-option input:checked + .remember-check {
  border-color: #0a0a0a;
  background: #0a0a0a;
}

.remember-option input:checked + .remember-check::after {
  width: 4px;
  height: 7px;
  margin-top: -1px;
  border: solid #fff;
  border-width: 0 1.5px 1.5px 0;
  content: '';
  transform: rotate(45deg);
}

.remember-text {
  line-height: 1.4;
}

.submit-btn {
  display: flex;
  width: 100%;
  height: 52px;
  align-items: center;
  justify-content: center;
  margin-top: 4px;
  border: none;
  border-radius: 8px;
  background: #0a0a0a;
  color: #FFFFFF;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.submit-btn:hover:not(:disabled) {
  background: #2D2515;
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.99);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #2D2515;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.spinner.dark {
  display: inline-block;
  border-color: rgba(0, 0, 0, 0.12);
  border-top-color: #111;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.divider-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 24px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: #FDF4D8;
}

.divider-text {
  color: #bbb;
  font-size: 13px;
}

.alt-btn {
  display: flex;
  width: 100%;
  height: 50px;
  align-items: center;
  justify-content: center;
  border: 1px solid #D4C898;
  border-radius: 8px;
  background: #FDF5D6;
  color: #333;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.alt-btn:hover {
  border-color: #ccc;
  background: #FEF9E7;
}

.agreement-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 24px;
}

.agreement-checkbox {
  position: relative;
  display: flex;
  align-items: center;
  margin-top: 1px;
  cursor: pointer;
}

.agreement-checkbox input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
}

.checkmark {
  display: flex;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: 1.5px solid #d0d0d0;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.agreement-checkbox input:checked + .checkmark {
  border-color: #0a0a0a;
  background: #0a0a0a;
}

.agreement-checkbox input:checked + .checkmark::after {
  width: 4px;
  height: 7px;
  margin-top: -1px;
  border: solid #fff;
  border-width: 0 1.5px 1.5px 0;
  content: '';
  transform: rotate(45deg);
}

.agreement-text {
  color: #888;
  font-size: 12px;
  line-height: 1.6;
}

.agreement-link {
  color: #0a0a0a;
  text-decoration: none;
}

.agreement-link:hover {
  text-decoration: underline;
}

.auth-footer {
  position: absolute;
  bottom: 20px;
  left: 50%;
  color: #bbb;
  font-size: 11px;
  white-space: nowrap;
  transform: translateX(-50%);
}

@media (max-width: 980px) {
  .showcase-panel {
    display: none;
  }

  .auth-panel {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .auth-container {
    padding: 0 20px;
  }

  .code-row {
    grid-template-columns: 1fr;
  }

  .code-btn {
    width: 100%;
  }
}
</style>
