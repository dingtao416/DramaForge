<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useBillingStore } from '@/stores/billing'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits<{
  (e: 'subscribe'): void
  (e: 'feedback'): void
  (e: 'notification'): void
  (e: 'message'): void
  (e: 'imageTasks'): void
}>()

const router = useRouter()
const billingStore = useBillingStore()
const authStore = useAuthStore()
const userMenuOpen = ref(false)
const accountDialogOpen = ref(false)
const loggingOut = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)
const activeAccountAction = ref<'username' | 'email' | 'password' | null>(null)
const accountActionMessage = ref('')
const accountActionError = ref('')
const accountForm = ref({
  username: '',
  email: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const accountStatusLabel = computed(() => {
  const status = authStore.user?.status
  if (!status || status === 'active') return '正常使用中'
  if (status === 'disabled') return '已停用'
  if (status === 'pending') return '待验证'
  return status
})

const accountCreatedAt = computed(() => formatDate(authStore.user?.created_at))

function openAIConfig() {
  router.push('/settings')
}

function handleAvatarClick() {
  if (authStore.isLoggedIn) {
    userMenuOpen.value = !userMenuOpen.value
  } else {
    router.push('/login')
  }
}

function closeUserMenu() {
  userMenuOpen.value = false
}

function closeAccountDialog() {
  accountDialogOpen.value = false
  closeAccountActionDialog()
}

function handleDocumentClick(event: MouseEvent) {
  if (!userMenuRef.value) return
  if (!userMenuRef.value.contains(event.target as Node)) {
    closeUserMenu()
  }
}

function formatDate(value?: string | null) {
  if (!value) return '暂无记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

async function openAccountDialog() {
  closeUserMenu()
  accountDialogOpen.value = true
  activeAccountAction.value = null
  accountActionMessage.value = ''
  accountActionError.value = ''
  await billingStore.fetchBalance()
}

function startAccountAction(action: 'username' | 'email' | 'password') {
  activeAccountAction.value = action
  accountActionMessage.value = ''
  accountActionError.value = ''
  accountForm.value = {
    username: authStore.user?.username || '',
    email: authStore.user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  }
}

function closeAccountActionDialog() {
  activeAccountAction.value = null
  accountActionMessage.value = ''
  accountActionError.value = ''
  accountForm.value.currentPassword = ''
  accountForm.value.newPassword = ''
  accountForm.value.confirmPassword = ''
}

const accountActionTitle = computed(() => {
  if (activeAccountAction.value === 'username') return '修改用户名'
  if (activeAccountAction.value === 'email') return '修改邮箱'
  if (activeAccountAction.value === 'password') return '修改密码'
  return ''
})

const accountActionDescription = computed(() => {
  if (activeAccountAction.value === 'username') return '更新你的公开用户名，系统会立即同步展示。'
  if (activeAccountAction.value === 'email') return '修改接收通知和登录使用的邮箱地址。'
  if (activeAccountAction.value === 'password') return '输入当前密码并设置新的登录密码。'
  return ''
})

async function submitAccountAction() {
  accountActionMessage.value = ''
  accountActionError.value = ''

  let ok = false
  if (activeAccountAction.value === 'username') {
    const username = accountForm.value.username.trim()
    if (!/^[A-Za-z0-9_.-]{3,64}$/.test(username)) {
      accountActionError.value = '用户名需为 3-64 位字母、数字、下划线、点或短横线'
      return
    }
    ok = await authStore.doUpdateUsername(username)
    accountActionMessage.value = ok ? '用户名已更新' : ''
  }

  if (activeAccountAction.value === 'email') {
    const email = accountForm.value.email.trim()
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      accountActionError.value = '请输入有效的邮箱地址'
      return
    }
    ok = await authStore.doUpdateEmail(email)
    accountActionMessage.value = ok ? '邮箱已更新' : ''
  }

  if (activeAccountAction.value === 'password') {
    const { currentPassword, newPassword, confirmPassword } = accountForm.value
    if (currentPassword.length < 8 || newPassword.length < 8) {
      accountActionError.value = '密码长度至少 8 位'
      return
    }
    if (newPassword !== confirmPassword) {
      accountActionError.value = '两次输入的新密码不一致'
      return
    }
    ok = await authStore.doChangePassword(currentPassword, newPassword)
    accountActionMessage.value = ok ? '密码已更新' : ''
  }

  if (!ok) {
    accountActionError.value = authStore.error || '操作失败'
    return
  }

  closeAccountActionDialog()
}

async function handleLogout() {
  if (loggingOut.value) return
  loggingOut.value = true
  try {
    await authStore.doLogout()
    closeAccountDialog()
    closeUserMenu()
    router.push('/login')
  } finally {
    loggingOut.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<template>
  <div class="tba-root">
    <!-- Credits + Subscribe (Mario red capsule) -->
    <div class="tba-credits-group" @click="$emit('subscribe')">
      <span class="tba-credits-icon">✦</span>
      <span class="tba-credits-num">{{ billingStore.credits }}</span>
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M3 4L5 6L7 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <div class="tba-divider" />
      <span class="tba-subscribe-label">订阅</span>
    </div>

    <!-- Feedback -->
    <button class="tba-icon-btn" title="反馈" @click="$emit('feedback')">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 5.5A1.5 1.5 0 015.5 4h9A1.5 1.5 0 0116 5.5v7a1.5 1.5 0 01-1.5 1.5H8.5L6 16v-3H5.5A1.5 1.5 0 014 11.5v-6z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M7.5 8h5M7.5 10.5h3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
    </button>

    <!-- Notification -->
    <button class="tba-icon-btn" title="通知" @click="$emit('notification')">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 3a4 4 0 00-4 4v3c0 .9-.4 1.75-1.1 2.35l-.4.3a.75.75 0 00.5 1.35h10a.75.75 0 00.5-1.35l-.4-.3A3.5 3.5 0 0114 10V7a4 4 0 00-4-4z" stroke="currentColor" stroke-width="1.4"/><path d="M8 14s.5 2 2 2 2-2 2-2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
    </button>

    <!-- Image tasks -->
    <button class="tba-icon-btn" title="图片任务" @click="$emit('imageTasks')">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="3.5" y="4" width="13" height="12" rx="1.6" stroke="currentColor" stroke-width="1.4"/>
        <circle cx="7.5" cy="8" r="1.4" stroke="currentColor" stroke-width="1.2"/>
        <path d="M4 14l3.2-3.4 2.1 2.1 2.8-3.1L16 14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <!-- Messages -->
    <button class="tba-icon-btn" title="消息" @click="$emit('message')">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="4.5" width="14" height="10" rx="1.5" stroke="currentColor" stroke-width="1.4"/><path d="M3 6l7 4.5L17 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>

    <button class="tba-ai-config" title="AI Config" @click="openAIConfig">
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
        <path d="M8 2.25l1.05 2.68 2.7 1.07-2.7 1.07L8 9.75 6.95 7.07 4.25 6l2.7-1.07L8 2.25z" stroke="currentColor" stroke-width="1.35" stroke-linejoin="round"/>
        <path d="M12.25 9.25l.55 1.4 1.45.6-1.45.6-.55 1.4-.55-1.4-1.45-.6 1.45-.6.55-1.4z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
      </svg>
      <span>AI 配置</span>
    </button>

    <div ref="userMenuRef" class="tba-user-menu">
      <button
        class="tba-avatar"
        type="button"
        :title="authStore.isLoggedIn ? authStore.displayName : '未登录'"
        @click="handleAvatarClick"
      >
        {{ authStore.isLoggedIn ? authStore.displayName.charAt(0).toUpperCase() : 'U' }}
      </button>

      <Transition name="user-menu">
        <div v-if="authStore.isLoggedIn && userMenuOpen" class="tba-user-popover">
          <div class="tba-user-summary">
            <span class="tba-user-name">{{ authStore.displayName }}</span>
            <span class="tba-user-email">{{ authStore.user?.email || '已登录账号' }}</span>
          </div>
          <button type="button" class="tba-menu-item" @click="openAccountDialog">
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
              <path d="M8 3.25a2.25 2.25 0 110 4.5 2.25 2.25 0 010-4.5z" stroke="currentColor" stroke-width="1.35"/>
              <path d="M3.75 13c.55-2.05 2.1-3.2 4.25-3.2s3.7 1.15 4.25 3.2" stroke="currentColor" stroke-width="1.35" stroke-linecap="round"/>
            </svg>
            账号设置
          </button>
          <button type="button" class="tba-menu-item tba-menu-item--danger" :disabled="loggingOut" @click="handleLogout">
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
              <path d="M6.25 3H4.5A1.5 1.5 0 003 4.5v7A1.5 1.5 0 004.5 13h1.75" stroke="currentColor" stroke-width="1.35" stroke-linecap="round"/>
              <path d="M9 5l3 3-3 3M12 8H6.5" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ loggingOut ? '退出中...' : '退出登录' }}
          </button>
        </div>
      </Transition>
    </div>

    <Teleport to="body">
      <Transition name="account-dialog">
        <div v-if="accountDialogOpen" class="account-overlay" @click.self="closeAccountDialog">
          <section class="account-dialog" aria-label="用户信息">
            <header class="account-header">
              <div>
                <span class="account-kicker">USER PROFILE</span>
                <h2>用户信息</h2>
              </div>
              <button class="account-close" type="button" title="关闭" @click="closeAccountDialog">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M5 5l8 8M13 5l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </button>
            </header>

            <div class="account-hero">
              <div class="account-avatar">
                {{ authStore.displayName.charAt(0).toUpperCase() }}
              </div>
              <div class="account-identity">
                <strong>{{ authStore.displayName }}</strong>
                <span>{{ authStore.user?.email || '未绑定邮箱' }}</span>
              </div>
              <span class="account-status">{{ accountStatusLabel }}</span>
            </div>

            <div class="account-grid">
              <article class="account-panel">
                <span class="panel-label">账号资料</span>
                <dl class="account-list">
                  <div>
                    <dt>用户名</dt>
                    <dd>{{ authStore.user?.username || '未设置' }}</dd>
                  </div>
                  <div>
                    <dt>邮箱</dt>
                    <dd>{{ authStore.user?.email || '未绑定' }}</dd>
                  </div>
                  <div>
                    <dt>账号 ID</dt>
                    <dd>#{{ authStore.user?.id }}</dd>
                  </div>
                  <div>
                    <dt>创建时间</dt>
                    <dd>{{ accountCreatedAt }}</dd>
                  </div>
                </dl>
              </article>

              <article class="account-panel">
                <span class="panel-label">账户操作</span>
                <div class="account-actions">
                  <div class="account-action-list">
                    <button
                      class="account-secondary"
                      type="button"
                      @click="startAccountAction('username')"
                    >
                      修改用户名
                    </button>
                    <button
                      class="account-secondary"
                      type="button"
                      @click="startAccountAction('email')"
                    >
                      修改邮箱
                    </button>
                    <button
                      class="account-secondary"
                      type="button"
                      @click="startAccountAction('password')"
                    >
                      修改密码
                    </button>
                  </div>
                  <p v-if="accountActionMessage" class="account-action-success">{{ accountActionMessage }}</p>

                  <button class="account-danger" type="button" :disabled="loggingOut" @click="handleLogout">
                    {{ loggingOut ? '退出中...' : '退出登录' }}
                  </button>
                </div>
              </article>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="action-dialog">
        <div v-if="activeAccountAction" class="action-overlay" @click.self="closeAccountActionDialog">
          <section class="action-dialog" :aria-label="accountActionTitle">
            <header class="action-header">
              <div>
                <span class="action-kicker">ACCOUNT ACTION</span>
                <h3>{{ accountActionTitle }}</h3>
                <p>{{ accountActionDescription }}</p>
              </div>
              <button class="action-close" type="button" title="关闭" @click="closeAccountActionDialog">
                <svg width="16" height="16" viewBox="0 0 18 18" fill="none">
                  <path d="M5 5l8 8M13 5l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </button>
            </header>

            <form class="account-edit-form" @submit.prevent="submitAccountAction">
              <label v-if="activeAccountAction === 'username'">
                <span>新用户名</span>
                <input
                  v-model="accountForm.username"
                  type="text"
                  autocomplete="username"
                  placeholder="3-64 位字母、数字或符号"
                >
              </label>

              <label v-if="activeAccountAction === 'email'">
                <span>新邮箱</span>
                <input
                  v-model="accountForm.email"
                  type="email"
                  autocomplete="email"
                  placeholder="name@example.com"
                >
              </label>

              <template v-if="activeAccountAction === 'password'">
                <label>
                  <span>当前密码</span>
                  <input
                    v-model="accountForm.currentPassword"
                    type="password"
                    autocomplete="current-password"
                    placeholder="请输入当前密码"
                  >
                </label>
                <label>
                  <span>新密码</span>
                  <input
                    v-model="accountForm.newPassword"
                    type="password"
                    autocomplete="new-password"
                    placeholder="至少 8 位"
                  >
                </label>
                <label>
                  <span>确认新密码</span>
                  <input
                    v-model="accountForm.confirmPassword"
                    type="password"
                    autocomplete="new-password"
                    placeholder="再次输入新密码"
                  >
                </label>
              </template>

              <p v-if="accountActionError" class="account-action-error">{{ accountActionError }}</p>

              <div class="account-form-actions">
                <button class="account-secondary compact" type="button" @click="closeAccountActionDialog">
                  取消
                </button>
                <button class="account-primary" type="submit" :disabled="authStore.isLoading">
                  {{ authStore.isLoading ? '保存中...' : '保存修改' }}
                </button>
              </div>
            </form>
          </section>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.tba-root {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ── Credits + Subscribe red capsule ── */
.tba-credits-group {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border-radius: 2px;
  background: rgba(232, 163, 23, 0.15);
  cursor: pointer;
  transition: all 0.15s;
  border: 2px solid rgba(232, 163, 23, 0.2);
}
.tba-credits-group:hover {
  background: rgba(232, 163, 23, 0.25);
}

.tba-credits-icon {
  color: #E8A317;
  font-size: 15px;
}

.tba-credits-num {
  font-weight: 600;
  font-size: 14px;
  color: #E8A317;
}

.tba-credits-group svg {
  color: #E8A317;
  opacity: 0.6;
}

.tba-divider {
  width: 1px;
  height: 16px;
  background: rgba(232, 163, 23, 0.3);
  margin: 0 4px;
}

.tba-subscribe-label {
  font-size: 13px;
  font-weight: 600;
  color: #E8A317;
}

/* ── Icon buttons ── */
.tba-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6B5D40;
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.tba-icon-btn:hover {
  background: rgba(0,0,0,0.04);
  color: #111111;
}

/* ── Avatar ── */
.tba-user-menu {
  position: relative;
}

.tba-avatar {
  width: 32px;
  height: 32px;
  border-radius: 2px;
  background: #E8A317;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  margin-left: 2px;
  border: none;
}
.tba-avatar:hover {
  background: #C88A0C;
}

.tba-user-popover {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 80;
  width: 210px;
  padding: 8px;
  border: 1px solid #D4C898;
  border-radius: 8px;
  background: #FEF9E7;
  box-shadow: 0 14px 40px rgba(45, 37, 21, 0.18);
}

.tba-user-summary {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 8px 9px 10px;
  border-bottom: 1px solid rgba(212, 200, 152, 0.75);
  margin-bottom: 6px;
}

.tba-user-name {
  font-size: 13px;
  font-weight: 700;
  color: #2D2515;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tba-user-email {
  font-size: 11px;
  color: #8a7d62;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tba-menu-item {
  width: 100%;
  height: 34px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 9px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #6B5D40;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.tba-menu-item:hover:not(:disabled) {
  background: rgba(232, 163, 23, 0.1);
  color: #2D2515;
}

.tba-menu-item--danger {
  color: #b91c1c;
}

.tba-menu-item--danger:hover:not(:disabled) {
  background: rgba(220, 38, 38, 0.08);
  color: #991b1b;
}

.tba-menu-item:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.user-menu-enter-active,
.user-menu-leave-active {
  transition: opacity 0.14s ease, transform 0.14s ease;
}

.user-menu-enter-from,
.user-menu-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.tba-ai-config {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 34px;
  padding: 0 12px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: transparent;
  color: #6B5D40;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.tba-ai-config:hover {
  border-color: #F5C34B;
  background: rgba(245, 195, 75, 0.08);
  color: #F5C34B;
}

.tba-ai-config svg {
  color: currentColor;
}

.account-overlay {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(20, 16, 8, 0.34);
  backdrop-filter: blur(3px);
}

.account-dialog {
  width: min(920px, 100%);
  max-height: min(820px, calc(100vh - 48px));
  overflow: auto;
  border: 2px solid #D4C898;
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 252, 238, 0.96), rgba(253, 246, 218, 0.98)),
    #FEF9E7;
  box-shadow: 12px 12px 0 rgba(45, 37, 21, 0.28), 0 24px 70px rgba(45, 37, 21, 0.24);
}

.account-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 24px 16px;
  border-bottom: 1px solid rgba(212, 200, 152, 0.8);
}

.account-kicker {
  display: block;
  margin-bottom: 7px;
  color: #C88A0C;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.account-header h2 {
  margin: 0;
  color: #16130d;
  font-size: 24px;
  font-weight: 900;
  letter-spacing: 0;
  text-shadow: 2px 2px 0 rgba(232, 163, 23, 0.22);
}

.account-close {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.38);
  color: #6B5D40;
  cursor: pointer;
}

.account-close:hover {
  border-color: #E8A317;
  color: #16130d;
}

.account-hero {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(212, 200, 152, 0.55);
}

.account-avatar {
  width: 54px;
  height: 54px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #9b7419;
  border-radius: 4px;
  background: #E8A317;
  color: #fff;
  font-size: 20px;
  font-weight: 900;
  box-shadow: 4px 4px 0 rgba(45, 37, 21, 0.16);
}

.account-identity {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.account-identity strong {
  color: #1f1a11;
  font-size: 18px;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-identity span {
  color: #75684c;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-status {
  padding: 7px 10px;
  border: 1px solid rgba(35, 121, 78, 0.28);
  border-radius: 999px;
  background: rgba(53, 169, 111, 0.1);
  color: #23794e;
  font-size: 12px;
  font-weight: 800;
}

.account-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 16px 24px 24px;
}

.account-panel {
  min-width: 0;
  padding: 15px;
  border: 1px solid #D4C898;
  border-radius: 6px;
  background: rgba(255, 252, 238, 0.72);
}

.panel-label {
  display: block;
  margin-bottom: 12px;
  color: #C88A0C;
  font-size: 12px;
  font-weight: 900;
}

.account-list {
  display: grid;
  gap: 10px;
  margin: 0;
}

.account-list div {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 14px;
}

.account-list dt {
  flex: 0 0 auto;
  color: #8a7d62;
  font-size: 12px;
}

.account-list dd {
  min-width: 0;
  margin: 0;
  color: #2D2515;
  font-size: 13px;
  font-weight: 800;
  overflow: hidden;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-list.compact {
  margin-top: 12px;
}

.account-actions {
  display: grid;
  gap: 10px;
}

.account-action-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.account-action-list .account-secondary {
  width: 100%;
  min-width: 0;
  height: 40px;
  justify-self: stretch;
}

.account-secondary,
.account-primary,
.account-danger {
  width: 100%;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  box-sizing: border-box;
  line-height: 1;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  vertical-align: top;
}

.account-secondary {
  border: 2px solid #D4C898;
  background: rgba(255, 255, 255, 0.34);
  color: #5f5237;
}

.account-secondary:hover {
  border-color: #E8A317;
  color: #16130d;
}

.account-secondary.compact {
  height: 44px;
  padding: 0 16px;
}

.account-primary {
  height: 44px;
  padding: 0 18px;
  border: 2px solid #111;
  background: #111;
  color: #fff7d7;
}

.account-primary:hover:not(:disabled) {
  background: #2D2515;
}

.account-primary:disabled {
  opacity: 0.58;
  cursor: not-allowed;
}

.account-edit-form {
  display: grid;
  gap: 10px;
  padding: 12px 0 0;
}

.account-edit-form label {
  display: grid;
  gap: 6px;
}

.account-edit-form label span {
  color: #8a7d62;
  font-size: 12px;
  font-weight: 800;
}

.account-edit-form input {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 1px solid #D4C898;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.58);
  color: #2D2515;
  font-size: 13px;
  font-weight: 700;
  outline: none;
}

.account-edit-form input:focus {
  border-color: #E8A317;
  box-shadow: 0 0 0 2px rgba(232, 163, 23, 0.12);
}

.account-form-actions {
  display: flex;
  align-items: stretch;
  gap: 10px;
  margin-top: 4px;
}

.account-form-actions > * {
  flex: 1 1 0;
  align-self: stretch;
}

.account-form-actions > .account-primary {
  flex: 1.35 1 0;
}

.action-overlay {
  position: fixed;
  inset: 0;
  z-index: 130;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(20, 16, 8, 0.16);
}

.action-dialog {
  width: min(460px, 100%);
  border: 2px solid #D4C898;
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 252, 238, 0.98), rgba(253, 246, 218, 0.98)),
    #FEF9E7;
  box-shadow: 10px 10px 0 rgba(45, 37, 21, 0.22), 0 16px 50px rgba(45, 37, 21, 0.18);
}

.action-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 18px 14px;
  border-bottom: 1px solid rgba(212, 200, 152, 0.8);
}

.action-kicker {
  display: block;
  margin-bottom: 6px;
  color: #C88A0C;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.action-header h3 {
  margin: 0;
  color: #16130d;
  font-size: 20px;
  font-weight: 900;
}

.action-header p {
  margin: 6px 0 0;
  color: #75684c;
  font-size: 12px;
  line-height: 1.5;
}

.action-close {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #D4C898;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.34);
  color: #6B5D40;
  cursor: pointer;
}

.action-close:hover {
  border-color: #E8A317;
  color: #16130d;
}

.action-dialog .account-edit-form {
  padding: 16px 18px 18px;
}

.action-dialog .account-secondary {
  margin-top: 0;
}

.account-action-error,
.account-action-success {
  margin: 0;
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.45;
}

.account-action-error {
  border: 1px solid rgba(220, 38, 38, 0.18);
  background: rgba(220, 38, 38, 0.08);
  color: #b91c1c;
}

.account-action-success {
  border: 1px solid rgba(35, 121, 78, 0.22);
  background: rgba(53, 169, 111, 0.1);
  color: #23794e;
}

.account-danger {
  border: 2px solid rgba(185, 28, 28, 0.24);
  background: rgba(220, 38, 38, 0.08);
  color: #b91c1c;
}

.account-danger:hover:not(:disabled) {
  border-color: rgba(185, 28, 28, 0.42);
  background: rgba(220, 38, 38, 0.12);
}

.account-danger:disabled {
  opacity: 0.62;
  cursor: not-allowed;
}

.account-dialog-enter-active,
.account-dialog-leave-active {
  transition: opacity 0.16s ease;
}

.account-dialog-enter-active .account-dialog,
.account-dialog-leave-active .account-dialog {
  transition: transform 0.16s ease;
}

.account-dialog-enter-from,
.account-dialog-leave-to {
  opacity: 0;
}

.account-dialog-enter-from .account-dialog,
.account-dialog-leave-to .account-dialog {
  transform: translateY(8px) scale(0.98);
}

.action-dialog-enter-active,
.action-dialog-leave-active {
  transition: opacity 0.14s ease;
}

.action-dialog-enter-active .action-dialog,
.action-dialog-leave-active .action-dialog {
  transition: transform 0.14s ease;
}

.action-dialog-enter-from,
.action-dialog-leave-to {
  opacity: 0;
}

.action-dialog-enter-from .action-dialog,
.action-dialog-leave-to .action-dialog {
  transform: translateY(6px) scale(0.985);
}

@media (max-width: 720px) {
  .tba-ai-config {
    width: 36px;
    padding: 0;
  }

  .tba-ai-config span {
    display: none;
  }

  .account-overlay {
    align-items: flex-end;
    padding: 12px;
  }

  .account-dialog {
    max-height: calc(100vh - 24px);
  }

  .account-hero {
    grid-template-columns: 46px minmax(0, 1fr);
  }

  .account-avatar {
    width: 46px;
    height: 46px;
  }

  .account-status {
    grid-column: 1 / -1;
    width: max-content;
  }

  .account-grid {
    grid-template-columns: 1fr;
    padding: 14px;
  }

  .action-overlay {
    align-items: flex-end;
    padding: 12px;
  }

  .action-dialog {
    width: 100%;
  }
}
</style>
