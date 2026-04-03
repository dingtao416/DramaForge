<script setup lang="ts">
/**
 * DramaForge — Login Page
 * Split layout: left showcase + right auth form.
 * Design reference: 小云雀 login page.
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

/* ─── Auth state ─── */
const isRegister = ref(false)
const email = ref('')
const phone = ref('')
const password = ref('')
const nickname = ref('')
const agreeTerms = ref(false)
const loginMethod = ref<'email' | 'phone'>('email')  // 切换邮箱/手机登录

async function handleSubmit() {
  if (!agreeTerms.value) {
    authStore.error = '请先阅读并同意相关协议'
    return
  }

  const identifier = loginMethod.value === 'email' ? email.value : phone.value
  if (!identifier || !password.value) return

  let ok: boolean
  if (isRegister.value) {
    ok = await authStore.doRegister({
      email: loginMethod.value === 'email' ? email.value : undefined,
      phone: loginMethod.value === 'phone' ? phone.value : undefined,
      password: password.value,
      nickname: nickname.value || undefined,
    })
  } else {
    ok = await authStore.doLogin({
      email: loginMethod.value === 'email' ? email.value : undefined,
      phone: loginMethod.value === 'phone' ? phone.value : undefined,
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

/* ─── Left showcase carousel ─── */
const showcaseItems = [
  {
    title: '短剧创作',
    desc: 'AI 一键生成专业短剧剧本，从创意到分镜全流程覆盖',
    icon: '🎬',
  },
  {
    title: '智能分镜',
    desc: '自动拆解场景、角色、镜头语言，可视化分镜编辑',
    icon: '🎞️',
  },
  {
    title: '角色设计',
    desc: 'AI 智能生成角色形象，保持一致性的多场景角色',
    icon: '👤',
  },
  {
    title: '一键成片',
    desc: '从剧本到成片全自动化，多风格视频输出',
    icon: '🎥',
  },
]

const currentShowcase = ref(0)
let showcaseTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  showcaseTimer = setInterval(() => {
    currentShowcase.value = (currentShowcase.value + 1) % showcaseItems.length
  }, 4000)
})

onUnmounted(() => {
  if (showcaseTimer) clearInterval(showcaseTimer)
})

const isFormValid = computed(() => {
  const identifier = loginMethod.value === 'email' ? email.value : phone.value
  return identifier && password.value && password.value.length >= 6
})
</script>

<template>
  <div class="login-page">
    <!-- ═══════════════════════════════════════════════ -->
    <!-- LEFT: Showcase Panel                            -->
    <!-- ═══════════════════════════════════════════════ -->
    <div class="showcase-panel">
      <!-- Gradient overlay -->
      <div class="showcase-overlay" />

      <!-- Top feature pills -->
      <div class="showcase-top-pills">
        <span
          v-for="(item, idx) in showcaseItems"
          :key="idx"
          class="pill"
          :class="currentShowcase === idx ? 'pill-active' : ''"
          @click="currentShowcase = idx"
        >
          <span class="pill-icon">{{ item.icon }}</span>
          <span class="pill-label">{{ item.title }}</span>
        </span>
      </div>

      <!-- Center visual -->
      <div class="showcase-center">
        <div class="showcase-logo-large">D</div>
        <transition name="showcase-fade" mode="out-in">
          <div :key="currentShowcase" class="showcase-text">
            <h2 class="showcase-title">{{ showcaseItems[currentShowcase].title }}</h2>
            <p class="showcase-desc">{{ showcaseItems[currentShowcase].desc }}</p>
          </div>
        </transition>
      </div>

      <!-- Bottom caption -->
      <div class="showcase-bottom">
        <div class="showcase-bottom-icon">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.2"/>
            <path d="M6 8l1.5 1.5L10 6.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <span>{{ showcaseItems[currentShowcase].icon }} {{ showcaseItems[currentShowcase].title }} · {{ showcaseItems[currentShowcase].desc }}</span>
      </div>

      <!-- Carousel dots -->
      <div class="showcase-dots">
        <span
          v-for="(_, idx) in showcaseItems"
          :key="idx"
          class="dot"
          :class="currentShowcase === idx ? 'dot-active' : ''"
          @click="currentShowcase = idx"
        />
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════ -->
    <!-- RIGHT: Auth Form                                -->
    <!-- ═══════════════════════════════════════════════ -->
    <div class="auth-panel">
      <div class="auth-container">
        <!-- Logo -->
        <div class="auth-logo-row">
          <div class="auth-logo">D</div>
        </div>

        <!-- Welcome text -->
        <h1 class="auth-title">欢迎使用 DramaForge</h1>
        <p class="auth-subtitle">
          {{ isRegister ? '创建账号，开启 AI 短剧创作之旅' : '支持邮箱或手机号登录，探索 AI 短剧创作' }}
        </p>

        <!-- Login method toggle -->
        <div class="method-tabs">
          <button
            class="method-tab"
            :class="loginMethod === 'email' ? 'method-tab-active' : ''"
            @click="loginMethod = 'email'"
          >邮箱登录</button>
          <button
            class="method-tab"
            :class="loginMethod === 'phone' ? 'method-tab-active' : ''"
            @click="loginMethod = 'phone'"
          >手机号登录</button>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="auth-form">
          <!-- Email input -->
          <div v-if="loginMethod === 'email'" class="form-group">
            <input
              v-model="email"
              type="email"
              class="form-input"
              placeholder="请输入邮箱地址"
              required
            />
          </div>

          <!-- Phone input -->
          <div v-else class="form-group">
            <input
              v-model="phone"
              type="tel"
              class="form-input"
              placeholder="请输入手机号"
              required
            />
          </div>

          <!-- Nickname (register only) -->
          <div v-if="isRegister" class="form-group">
            <input
              v-model="nickname"
              type="text"
              class="form-input"
              placeholder="请输入昵称（可选）"
            />
          </div>

          <!-- Password -->
          <div class="form-group">
            <input
              v-model="password"
              type="password"
              class="form-input"
              placeholder="请输入密码"
              minlength="6"
              required
            />
          </div>

          <!-- Error -->
          <div v-if="authStore.error" class="error-msg">
            {{ authStore.error }}
          </div>

          <!-- Submit -->
          <button
            type="submit"
            class="submit-btn"
            :disabled="authStore.isLoading || !isFormValid"
          >
            <span v-if="authStore.isLoading" class="spinner" />
            <span v-else>{{ isRegister ? '注册' : '登录' }}</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="divider-row">
          <span class="divider-line" />
          <span class="divider-text">或</span>
          <span class="divider-line" />
        </div>

        <!-- Toggle login/register -->
        <button class="alt-btn" @click="toggleMode">
          {{ isRegister ? '已有账号？直接登录' : '没有账号？立即注册' }}
        </button>

        <!-- Agreement -->
        <div class="agreement-row">
          <label class="agreement-checkbox">
            <input type="checkbox" v-model="agreeTerms" />
            <span class="checkmark" />
          </label>
          <span class="agreement-text">
            已阅读并同意
            <a href="javascript:void(0)" class="agreement-link">《用户服务协议》</a>、
            <a href="javascript:void(0)" class="agreement-link">《隐私政策》</a>
            和
            <a href="javascript:void(0)" class="agreement-link">《AI功能使用规范》</a>
          </span>
        </div>
      </div>

      <!-- Footer -->
      <div class="auth-footer">
        <span>DramaForge © 2025 — AI 短剧创作平台</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════
   Page layout: left showcase + right form
   ═══════════════════════════════════════════════ */
.login-page {
  display: flex;
  min-height: 100vh;
  background: #fff;
}

/* ─── Left Showcase Panel ─── */
.showcase-panel {
  width: 50%;
  min-height: 100vh;
  background: #0a0a0a;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.showcase-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 60%, rgba(124, 58, 237, 0.15) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 30%, rgba(99, 102, 241, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

/* Top pills */
.showcase-top-pills {
  position: absolute;
  top: 28px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 2;
}

.pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  backdrop-filter: blur(8px);
}

.pill:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.pill-active {
  background: rgba(124, 58, 237, 0.25);
  border-color: rgba(124, 58, 237, 0.4);
  color: #fff;
}

.pill-icon {
  font-size: 14px;
}

.pill-label {
  font-weight: 500;
}

/* Center showcase */
.showcase-center {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 32px;
}

.showcase-logo-large {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
  color: #fff;
  font-size: 36px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 40px rgba(124, 58, 237, 0.35);
}

.showcase-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.showcase-title {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.5px;
}

.showcase-desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.55);
  max-width: 360px;
  line-height: 1.6;
}

/* Transition */
.showcase-fade-enter-active,
.showcase-fade-leave-active {
  transition: all 0.4s ease;
}
.showcase-fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.showcase-fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

/* Bottom caption */
.showcase-bottom {
  position: absolute;
  bottom: 48px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  z-index: 2;
  white-space: nowrap;
}

.showcase-bottom-icon {
  display: flex;
  align-items: center;
}

/* Carousel dots */
.showcase-dots {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 6px;
  z-index: 2;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: all 0.3s;
}

.dot-active {
  width: 20px;
  border-radius: 3px;
  background: #7c3aed;
}

/* ─── Right Auth Panel ─── */
.auth-panel {
  width: 50%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fff;
  position: relative;
}

.auth-container {
  width: 100%;
  max-width: 400px;
  padding: 0 24px;
}

/* Logo */
.auth-logo-row {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.auth-logo {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(124, 58, 237, 0.2);
}

.auth-title {
  text-align: center;
  font-size: 24px;
  font-weight: 700;
  color: #0a0a0a;
  margin: 0 0 8px;
  letter-spacing: -0.3px;
}

.auth-subtitle {
  text-align: center;
  font-size: 13px;
  color: #999;
  margin: 0 0 28px;
  line-height: 1.5;
}

/* Method tabs */
.method-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.method-tab {
  flex: 1;
  padding: 10px 0;
  font-size: 14px;
  font-weight: 500;
  color: #999;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.method-tab:hover {
  color: #555;
}

.method-tab-active {
  color: #0a0a0a;
  border-bottom-color: #0a0a0a;
}

/* Form */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group {
  position: relative;
}

.form-input {
  width: 100%;
  height: 52px;
  padding: 0 16px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  font-size: 15px;
  color: #0a0a0a;
  background: #f8f8f8;
  outline: none;
  transition: all 0.2s;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: #c4b5fd;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.06);
}

.form-input::placeholder {
  color: #bbb;
  font-size: 14px;
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
  width: 100%;
  height: 52px;
  border: none;
  border-radius: 12px;
  background: #0a0a0a;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 4px;
}

.submit-btn:hover:not(:disabled) {
  background: #1a1a1a;
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Divider */
.divider-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 24px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: #f0f0f0;
}

.divider-text {
  font-size: 13px;
  color: #bbb;
}

/* Alt button */
.alt-btn {
  width: 100%;
  height: 50px;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  background: #fff;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.alt-btn:hover {
  border-color: #ccc;
  background: #fafafa;
}

/* Agreement */
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
  cursor: pointer;
  margin-top: 1px;
}

.agreement-checkbox input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkmark {
  width: 16px;
  height: 16px;
  border: 1.5px solid #d0d0d0;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.agreement-checkbox input:checked + .checkmark {
  background: #7c3aed;
  border-color: #7c3aed;
}

.agreement-checkbox input:checked + .checkmark::after {
  content: '';
  width: 4px;
  height: 7px;
  border: solid #fff;
  border-width: 0 1.5px 1.5px 0;
  transform: rotate(45deg);
  margin-top: -1px;
}

.agreement-text {
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

.agreement-link {
  color: #7c3aed;
  text-decoration: none;
}

.agreement-link:hover {
  text-decoration: underline;
}

/* Footer */
.auth-footer {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  color: #ccc;
  white-space: nowrap;
}

/* ─── Responsive ─── */
@media (max-width: 900px) {
  .showcase-panel {
    display: none;
  }
  .auth-panel {
    width: 100%;
  }
}
</style>
