<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const account = ref('')
const username = ref('')
const email = ref('')
const password = ref('')
const code = ref('')
const agreeTerms = ref(false)
const rememberMe = ref(true)
const countdown = ref(0)
const sendMessage = ref('')
let countdownTimer: ReturnType<typeof setInterval> | null = null
const REMEMBER_ACCOUNT_KEY = 'df_remember_account'
const REMEMBER_LOGIN_KEY = 'df_remember_login'

const showcaseItems = [
  {
    title: '筑梦成片',
    desc: '用 AI 将创意、角色与镜头节奏生成可预演的影像。',
  },
  {
    title: '光影显影',
    desc: '让故事从暗场里慢慢成形，进入可控的视频生成流程。',
  },
  {
    title: '镜头预演',
    desc: '在生成前看见叙事重心、运动轨迹与画面情绪。',
  },
]

const currentShowcase = ref(0)
const showcasePanelRef = ref<HTMLElement | null>(null)
let showcaseTimer: ReturnType<typeof setInterval> | null = null
let dreamMotionContext: ReturnType<typeof gsap.context> | null = null

const normalizedAccount = computed(() => account.value.trim())
const normalizedUsername = computed(() => username.value.trim())
const normalizedEmail = computed(() => email.value.trim())
const isAccountValid = computed(() => normalizedAccount.value.length >= 3)
const isUsernameValid = computed(() => /^[A-Za-z0-9_.-]{3,64}$/.test(normalizedUsername.value))
const isEmailValid = computed(() => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(normalizedEmail.value))
const isPasswordValid = computed(() => password.value.length >= 8 && password.value.length <= 128)
const isCodeValid = computed(() => /^\d{4,10}$/.test(code.value.trim()))
const canSendCode = computed(() => isEmailValid.value && countdown.value === 0 && !authStore.isSendingCode)
const hasSubmitInput = computed(() => {
  if (isRegister.value) {
    return Boolean(normalizedUsername.value || normalizedEmail.value || password.value || code.value.trim())
  }
  return Boolean(normalizedAccount.value || password.value)
})
const isFormValid = computed(() => {
  if (isRegister.value) {
    return isUsernameValid.value && isEmailValid.value && isPasswordValid.value && isCodeValid.value
  }
  return isAccountValid.value && isPasswordValid.value
})

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

  if (isRegister.value) {
    if (!isUsernameValid.value) {
      authStore.error = '用户名需为 3-64 位字母、数字、下划线、点或短横线'
      return
    }
    if (!isEmailValid.value) {
      authStore.error = '请输入有效的邮箱地址'
      return
    }
    if (!isPasswordValid.value) {
      authStore.error = '密码需为 8-128 位'
      return
    }
    if (!isCodeValid.value) {
      authStore.error = '请输入 4-10 位数字验证码'
      return
    }
  } else {
    if (!isAccountValid.value) {
      authStore.error = '请输入至少 3 位用户名或邮箱'
      return
    }
    if (!isPasswordValid.value) {
      authStore.error = '密码需为 8-128 位'
      return
    }
  }

  const ok = isRegister.value
    ? await authStore.doRegister({
        username: normalizedUsername.value,
        email: normalizedEmail.value,
        password: password.value,
        code: code.value.trim(),
      }, rememberMe.value)
    : await authStore.doLogin({
        account: normalizedAccount.value,
        password: password.value,
      }, rememberMe.value)

  if (ok) {
    if (rememberMe.value) {
      const rememberedAccount = isRegister.value ? normalizedUsername.value : normalizedAccount.value
      localStorage.setItem(REMEMBER_ACCOUNT_KEY, rememberedAccount)
    } else {
      localStorage.removeItem(REMEMBER_ACCOUNT_KEY)
    }
    const redirect = typeof router.currentRoute.value.query.redirect === 'string'
      ? router.currentRoute.value.query.redirect
      : '/'
    router.replace(redirect)
  }
}

function toggleMode() {
  const nextIsRegister = !isRegister.value
  if (nextIsRegister && normalizedAccount.value.includes('@') && !email.value) {
    email.value = normalizedAccount.value
  }
  if (!nextIsRegister && (normalizedUsername.value || normalizedEmail.value)) {
    account.value = normalizedUsername.value || normalizedEmail.value
  }
  isRegister.value = nextIsRegister
  code.value = ''
  password.value = ''
  sendMessage.value = ''
  authStore.clearError()
}

function startDreamMotion() {
  if (!showcasePanelRef.value || dreamMotionContext) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

  dreamMotionContext = gsap.context(() => {
    const particles = gsap.utils.toArray<HTMLElement>('.dream-particle')
    const pixels = gsap.utils.toArray<HTMLElement>('.dream-pixel')

    gsap.fromTo(
      '.dream-canvas',
      { opacity: 0, y: 34, scale: 0.96 },
      { opacity: 1, y: 0, scale: 1, duration: 1.2, ease: 'power3.out' },
    )

    gsap.fromTo(
      '.dream-copy',
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: 0.9, delay: 0.18, ease: 'power3.out' },
    )

    gsap.fromTo(
      '.dream-frame-line',
      { scaleX: 0, scaleY: 0, opacity: 0 },
      {
        scaleX: 1,
        scaleY: 1,
        opacity: 1,
        duration: 0.85,
        delay: 0.35,
        ease: 'power3.out',
        stagger: 0.12,
      },
    )

    gsap.to('.dream-canvas', {
      y: -10,
      duration: 3.6,
      ease: 'sine.inOut',
      repeat: -1,
      yoyo: true,
    })

    gsap.to('.dream-beam', {
      opacity: 0.72,
      scaleX: 1.12,
      duration: 2.4,
      ease: 'sine.inOut',
      repeat: -1,
      yoyo: true,
      stagger: 0.5,
    })

    gsap.to('.dream-core-light', {
      opacity: 0.95,
      scale: 1.18,
      duration: 1.7,
      ease: 'sine.inOut',
      repeat: -1,
      yoyo: true,
    })

    gsap.to('.dream-scan', {
      xPercent: 430,
      duration: 2.8,
      ease: 'power2.inOut',
      repeat: -1,
      repeatDelay: 0.45,
    })

    gsap.to('.dream-track', {
      x: 18,
      opacity: 0.9,
      duration: 2.6,
      ease: 'sine.inOut',
      stagger: 0.22,
      repeat: -1,
      yoyo: true,
    })

    particles.forEach((particle, index) => {
      gsap.set(particle, {
        xPercent: gsap.utils.random(-48, 48),
        yPercent: gsap.utils.random(18, 72),
        scale: gsap.utils.random(0.55, 1.15),
        opacity: gsap.utils.random(0.12, 0.42),
      })

      gsap.to(particle, {
        yPercent: '-=120',
        xPercent: `+=${gsap.utils.random(-12, 12)}`,
        opacity: gsap.utils.random(0.42, 0.82),
        duration: gsap.utils.random(3.2, 5.4),
        delay: index * 0.11,
        ease: 'sine.inOut',
        repeat: -1,
        yoyo: true,
      })
    })

    pixels.forEach((pixel, index) => {
      gsap.set(pixel, {
        opacity: 0,
        scale: 0.7,
      })

      gsap.to(pixel, {
        opacity: gsap.utils.random(0.35, 0.92),
        scale: gsap.utils.random(0.9, 1.3),
        duration: 0.34,
        delay: 0.5 + index * 0.09,
        ease: 'steps(1)',
        repeat: -1,
        yoyo: true,
        repeatDelay: gsap.utils.random(1.1, 2.2),
      })
    })
  }, showcasePanelRef.value)
}

function stopDreamMotion() {
  dreamMotionContext?.revert()
  dreamMotionContext = null
}

onMounted(async () => {
  rememberMe.value = localStorage.getItem(REMEMBER_LOGIN_KEY) !== 'false'
  const rememberedAccount = localStorage.getItem(REMEMBER_ACCOUNT_KEY)
  if (rememberedAccount) account.value = rememberedAccount

  showcaseTimer = setInterval(() => {
    currentShowcase.value = (currentShowcase.value + 1) % showcaseItems.length
  }, 4000)

  await nextTick()
  startDreamMotion()
})

onUnmounted(() => {
  stopDreamMotion()
  if (showcaseTimer) clearInterval(showcaseTimer)
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<template>
  <div class="login-page">
    <section ref="showcasePanelRef" class="showcase-panel" aria-label="DramaForge AI Video">
      <div class="dream-backdrop" aria-hidden="true">
        <span class="dream-vignette" />
        <span class="dream-warmth" />
        <span class="dream-shadow" />
      </div>

      <div class="dream-particles" aria-hidden="true">
        <span v-for="idx in 18" :key="idx" class="dream-particle" />
      </div>

      <div class="dream-canvas" aria-hidden="true">
        <span class="dream-beam beam-left" />
        <span class="dream-beam beam-right" />
        <div class="dream-film">
          <span class="dream-film-glow" />
          <span class="dream-core-light" />
          <span class="dream-scan" />
          <span class="dream-horizon" />
          <span class="dream-track track-one" />
          <span class="dream-track track-two" />
          <span class="dream-track track-three" />
          <span class="dream-track track-four" />
          <span class="dream-frame-line frame-line-top" />
          <span class="dream-frame-line frame-line-bottom" />
          <span class="dream-frame-line frame-line-left" />
          <span class="dream-frame-line frame-line-right" />
          <span v-for="idx in 10" :key="idx" class="dream-pixel" />
        </div>
      </div>

      <div class="dream-copy">
        <div class="dream-kicker">DramaForge AI Video</div>
        <transition name="showcase-fade" mode="out-in">
          <div :key="currentShowcase" class="dream-copy-text">
            <h2 class="dream-title">{{ showcaseItems[currentShowcase].title }}</h2>
            <p class="dream-desc">{{ showcaseItems[currentShowcase].desc }}</p>
          </div>
        </transition>
      </div>

      <div class="dream-dots" aria-label="切换左侧展示文案">
        <button
          v-for="(item, idx) in showcaseItems"
          :key="idx"
          class="dream-dot"
          :class="{ 'dream-dot-active': currentShowcase === idx }"
          type="button"
          :aria-label="`切换到${item.title}`"
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
          {{ isRegister ? '绑定用户名、邮箱和密码，首次创建账号需要邮箱验证码。' : '使用用户名或邮箱加密码登录。未注册账号请先注册。' }}
        </p>

        <form class="auth-form" @submit.prevent="handleSubmit">
          <div v-if="!isRegister" class="form-group">
            <input
              v-model="account"
              type="text"
              class="form-input"
              placeholder="请输入用户名或邮箱"
              autocomplete="username"
              required
            />
          </div>

          <div v-if="isRegister" class="form-group">
            <input
              v-model="username"
              type="text"
              class="form-input"
              placeholder="请输入用户名（3-64 位字母、数字或符号）"
              autocomplete="username"
              required
            />
          </div>

          <div v-if="isRegister" class="form-group">
            <input
              v-model="email"
              type="email"
              class="form-input"
              placeholder="请输入邮箱地址"
              autocomplete="email"
              required
            />
          </div>

          <div class="form-group">
            <input
              v-model="password"
              type="password"
              class="form-input"
              placeholder="请输入密码（至少 8 位）"
              :autocomplete="isRegister ? 'new-password' : 'current-password'"
              required
            />
          </div>

          <div v-if="isRegister" class="code-row">
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
            :disabled="authStore.isLoading || !hasSubmitInput"
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
  isolation: isolate;
  background: #050403;
  color: #F8EED9;
}

.dream-backdrop {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 55% 38%, rgba(184, 138, 70, 0.2), transparent 45%),
    linear-gradient(145deg, #050403 0%, #120d08 46%, #070707 100%);
}

.dream-backdrop::before {
  position: absolute;
  inset: -4%;
  content: '';
  background:
    linear-gradient(90deg, rgba(5, 4, 3, 0.82), rgba(5, 4, 3, 0.3) 45%, rgba(5, 4, 3, 0.88)),
    url('/assets/default-scene.webp');
  background-position: center;
  background-size: cover;
  filter: saturate(0.46) contrast(1.12);
  opacity: 0.34;
  transform: scale(1.04);
  animation: dreamBackdropBreath 18s ease-in-out infinite alternate;
}

.dream-vignette,
.dream-warmth,
.dream-shadow {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.dream-vignette {
  z-index: 2;
  background:
    radial-gradient(ellipse at 50% 42%, transparent 0%, rgba(5, 4, 3, 0.28) 54%, rgba(5, 4, 3, 0.92) 100%),
    linear-gradient(180deg, rgba(5, 4, 3, 0.04), rgba(5, 4, 3, 0.82));
}

.dream-warmth {
  z-index: 1;
  background:
    linear-gradient(112deg, transparent 10%, rgba(208, 164, 88, 0.08) 31%, rgba(236, 205, 142, 0.2) 48%, rgba(208, 164, 88, 0.08) 64%, transparent 86%);
  transform: translateX(-8%);
  animation: dreamWarmthSweep 11s ease-in-out infinite alternate;
}

.dream-shadow {
  z-index: 3;
  opacity: 0.2;
  background-image:
    linear-gradient(rgba(228, 238, 245, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(228, 238, 245, 0.04) 1px, transparent 1px);
  background-size: 58px 58px;
  mask-image: linear-gradient(180deg, transparent, #000 18%, #000 72%, transparent);
  animation: dreamShadowDrift 20s linear infinite;
}

.dream-particles {
  position: absolute;
  inset: 0;
  z-index: 2;
  overflow: hidden;
  pointer-events: none;
}

.dream-particle {
  position: absolute;
  bottom: 16%;
  left: 50%;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(246, 222, 174, 0.86);
  box-shadow: 0 0 12px rgba(246, 222, 174, 0.52);
  opacity: 0;
}

.dream-canvas {
  position: absolute;
  top: 16%;
  left: 50%;
  z-index: 2;
  width: min(540px, 76%);
  aspect-ratio: 16 / 10;
  transform: translateX(-50%);
  animation: dreamCanvasFloat 8s ease-in-out infinite alternate;
}

.dream-beam {
  position: absolute;
  top: 46%;
  z-index: 0;
  width: 52%;
  height: 42%;
  border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(238, 203, 136, 0.26), rgba(238, 203, 136, 0.08) 44%, transparent 72%);
  filter: blur(18px);
  opacity: 0.28;
  pointer-events: none;
  transform-origin: center;
}

.beam-left {
  left: -25%;
  transform: rotate(18deg);
}

.beam-right {
  right: -25%;
  transform: rotate(-18deg);
}

.dream-film {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border: 1px solid rgba(245, 224, 182, 0.18);
  border-radius: 8px;
  background:
    radial-gradient(ellipse at 52% 50%, rgba(223, 178, 95, 0.18), transparent 53%),
    linear-gradient(180deg, rgba(255, 247, 224, 0.08), rgba(255, 247, 224, 0.015)),
    linear-gradient(135deg, rgba(19, 18, 16, 0.45), rgba(5, 4, 3, 0.78));
  box-shadow:
    0 34px 90px rgba(0, 0, 0, 0.5),
    inset 0 0 56px rgba(242, 209, 148, 0.1);
}

.dream-film::before {
  position: absolute;
  inset: 22px 26px;
  border: 1px solid rgba(248, 237, 211, 0.1);
  border-radius: 6px;
  content: '';
}

.dream-film::after {
  position: absolute;
  inset: 0;
  content: '';
  background:
    repeating-linear-gradient(180deg, rgba(248, 237, 211, 0.04) 0, rgba(248, 237, 211, 0.04) 1px, transparent 1px, transparent 7px),
    linear-gradient(90deg, rgba(228, 238, 245, 0.06), transparent 18%, transparent 82%, rgba(228, 238, 245, 0.04));
  opacity: 0.36;
  pointer-events: none;
}

.dream-film-glow {
  position: absolute;
  inset: 20% 18% 24%;
  background: radial-gradient(ellipse at center, rgba(246, 222, 174, 0.24), rgba(246, 222, 174, 0.06) 46%, transparent 72%);
  filter: blur(12px);
  opacity: 0.72;
  animation: dreamFilmGlow 5.8s ease-in-out infinite alternate;
}

.dream-core-light {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 2;
  width: 116px;
  height: 116px;
  border-radius: 50%;
  background:
    radial-gradient(circle at center, rgba(255, 250, 231, 0.82), rgba(239, 201, 132, 0.28) 32%, rgba(239, 201, 132, 0.08) 58%, transparent 72%);
  filter: blur(3px);
  opacity: 0.42;
  transform: translate(-50%, -50%);
  transform-origin: center;
}

.dream-scan {
  position: absolute;
  top: -12%;
  bottom: -12%;
  left: 0;
  z-index: 3;
  width: 34%;
  background: linear-gradient(90deg, transparent, rgba(248, 237, 211, 0.28), rgba(248, 237, 211, 0.08), transparent);
  transform: translateX(-130%) skewX(-9deg);
  animation: dreamScan 4.8s ease-in-out infinite;
}

.dream-horizon {
  position: absolute;
  right: 10%;
  bottom: 34%;
  left: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(247, 223, 178, 0.56), transparent);
  box-shadow: 0 0 24px rgba(247, 223, 178, 0.18);
}

.dream-track {
  position: absolute;
  z-index: 2;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(248, 237, 211, 0.68), transparent);
  opacity: 0.62;
  transform-origin: left center;
  animation: dreamTrackDrift 5.8s ease-in-out infinite alternate;
}

.track-one {
  top: 34%;
  left: 15%;
  width: 62%;
  transform: rotate(-6deg);
}

.track-two {
  top: 48%;
  left: 24%;
  width: 58%;
  animation-delay: -1.2s;
  transform: rotate(3deg);
}

.track-three {
  top: 61%;
  left: 18%;
  width: 68%;
  animation-delay: -2.4s;
  transform: rotate(-2deg);
}

.track-four {
  top: 72%;
  left: 30%;
  width: 46%;
  animation-delay: -3.2s;
  transform: rotate(5deg);
}

.dream-frame-line {
  position: absolute;
  z-index: 4;
  display: block;
  background: linear-gradient(90deg, transparent, rgba(255, 239, 202, 0.82), transparent);
  box-shadow: 0 0 18px rgba(244, 207, 139, 0.26);
  opacity: 0;
}

.frame-line-top,
.frame-line-bottom {
  right: 24px;
  left: 24px;
  height: 1px;
  transform-origin: left center;
}

.frame-line-top {
  top: 22px;
}

.frame-line-bottom {
  bottom: 22px;
}

.frame-line-left,
.frame-line-right {
  top: 22px;
  bottom: 22px;
  width: 1px;
  background: linear-gradient(180deg, transparent, rgba(255, 239, 202, 0.76), transparent);
  transform-origin: top center;
}

.frame-line-left {
  left: 24px;
}

.frame-line-right {
  right: 24px;
}

.dream-pixel {
  position: absolute;
  z-index: 3;
  width: 7px;
  height: 7px;
  border-radius: 2px;
  background: rgba(255, 239, 202, 0.76);
  box-shadow: 0 0 14px rgba(244, 207, 139, 0.32);
  opacity: 0;
}

.dream-pixel:nth-of-type(1) {
  top: 27%;
  left: 21%;
}

.dream-pixel:nth-of-type(2) {
  top: 31%;
  left: 58%;
}

.dream-pixel:nth-of-type(3) {
  top: 39%;
  left: 39%;
}

.dream-pixel:nth-of-type(4) {
  top: 44%;
  left: 72%;
}

.dream-pixel:nth-of-type(5) {
  top: 53%;
  left: 28%;
}

.dream-pixel:nth-of-type(6) {
  top: 59%;
  left: 51%;
}

.dream-pixel:nth-of-type(7) {
  top: 64%;
  left: 78%;
}

.dream-pixel:nth-of-type(8) {
  top: 71%;
  left: 35%;
}

.dream-pixel:nth-of-type(9) {
  top: 76%;
  left: 62%;
}

.dream-pixel:nth-of-type(10) {
  top: 35%;
  left: 83%;
}

.dream-copy {
  position: absolute;
  right: 64px;
  bottom: 108px;
  left: 64px;
  z-index: 3;
  max-width: 430px;
}

.dream-kicker {
  margin-bottom: 14px;
  color: rgba(234, 198, 128, 0.78);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.dream-copy-text {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.dream-title {
  margin: 0;
  color: #FFF4DC;
  font-size: 46px;
  font-weight: 800;
  line-height: 1.08;
  text-shadow: 0 18px 50px rgba(0, 0, 0, 0.46);
}

.dream-desc {
  max-width: 390px;
  margin: 0;
  color: rgba(250, 241, 220, 0.7);
  font-size: 16px;
  line-height: 1.8;
}

.showcase-fade-enter-active,
.showcase-fade-leave-active {
  transition: opacity 0.38s ease, transform 0.38s ease;
}

.showcase-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.showcase-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.dream-dots {
  position: absolute;
  bottom: 56px;
  left: 64px;
  z-index: 3;
  display: flex;
  gap: 8px;
}

.dream-dot {
  width: 26px;
  height: 2px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: rgba(250, 241, 220, 0.22);
  cursor: pointer;
  transition: background 0.24s ease, transform 0.24s ease, width 0.24s ease;
}

.dream-dot:hover,
.dream-dot-active {
  width: 38px;
  background: rgba(234, 198, 128, 0.88);
}

.dream-dot:hover {
  transform: translateY(-1px);
}

@keyframes dreamBackdropBreath {
  from {
    opacity: 0.28;
    transform: scale(1.04) translate3d(-8px, 0, 0);
  }
  to {
    opacity: 0.4;
    transform: scale(1.09) translate3d(8px, -6px, 0);
  }
}

@keyframes dreamWarmthSweep {
  from {
    opacity: 0.52;
    transform: translateX(-10%);
  }
  to {
    opacity: 0.9;
    transform: translateX(8%);
  }
}

@keyframes dreamShadowDrift {
  to {
    background-position: 58px 58px;
  }
}

@keyframes dreamCanvasFloat {
  from {
    transform: translateX(-50%) translateY(0);
  }
  to {
    transform: translateX(-50%) translateY(-10px);
  }
}

@keyframes dreamFilmGlow {
  0%,
  100% {
    opacity: 0.52;
  }
  50% {
    opacity: 0.9;
  }
}

@keyframes dreamScan {
  0% {
    transform: translateX(-130%) skewX(-9deg);
  }
  46%,
  100% {
    transform: translateX(330%) skewX(-9deg);
  }
}

@keyframes dreamTrackDrift {
  0%,
  100% {
    opacity: 0.34;
    translate: 0 0;
  }
  50% {
    opacity: 0.78;
    translate: 10px -4px;
  }
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

@media (max-width: 1180px) {
  .dream-canvas {
    top: 15%;
    width: min(480px, 78%);
  }

  .dream-copy {
    right: 44px;
    bottom: 94px;
    left: 44px;
  }

  .dream-title {
    font-size: 40px;
  }

  .dream-dots {
    left: 44px;
  }
}

@media (max-height: 760px) and (min-width: 981px) {
  .dream-canvas {
    top: 12%;
    width: min(460px, 72%);
  }

  .dream-copy {
    bottom: 78px;
  }

  .dream-title {
    font-size: 38px;
  }

  .dream-desc {
    font-size: 15px;
  }

  .dream-dots {
    bottom: 42px;
  }
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

@media (prefers-reduced-motion: reduce) {
  .dream-backdrop::before,
  .dream-warmth,
  .dream-shadow,
  .dream-canvas,
  .dream-particle,
  .dream-beam,
  .dream-film-glow,
  .dream-core-light,
  .dream-scan,
  .dream-track,
  .dream-frame-line,
  .dream-pixel,
  .spinner {
    animation: none;
  }
}
</style>
