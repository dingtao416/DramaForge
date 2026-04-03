<!--
  DramaForge — TopbarActions.vue
  ================================
  Shared right-side topbar actions used across all pages:
  积分+订阅 badge, feedback, notification, messages, avatar.

  Usage:
    <TopbarActions />
    <TopbarActions @subscribe="handleSubscribe" />
-->
<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useBillingStore } from '@/stores/billing'
import { useAuthStore } from '@/stores/auth'

const emit = defineEmits<{
  (e: 'subscribe'): void
  (e: 'feedback'): void
  (e: 'notification'): void
  (e: 'message'): void
}>()

const router = useRouter()
const billingStore = useBillingStore()
const authStore = useAuthStore()

function handleAvatarClick() {
  if (authStore.isLoggedIn) {
    // Could open a dropdown in the future
    router.push('/settings')
  } else {
    router.push('/login')
  }
}
</script>

<template>
  <div class="tba-root">
    <!-- Credits + Subscribe (purple capsule) -->
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

    <!-- Messages -->
    <button class="tba-icon-btn" title="消息" @click="$emit('message')">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="4.5" width="14" height="10" rx="1.5" stroke="currentColor" stroke-width="1.4"/><path d="M3 6l7 4.5L17 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>

    <!-- Avatar -->
    <div
      class="tba-avatar"
      :title="authStore.isLoggedIn ? authStore.displayName : '未登录'"
      @click="handleAvatarClick"
    >
      {{ authStore.isLoggedIn ? authStore.displayName.charAt(0).toUpperCase() : 'U' }}
    </div>
  </div>
</template>

<style scoped>
.tba-root {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ── Credits + Subscribe purple capsule ── */
.tba-credits-group {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border-radius: 20px;
  background: #f3f0ff;
  cursor: pointer;
  transition: all 0.15s;
}
.tba-credits-group:hover {
  background: #ede9fe;
}

.tba-credits-icon {
  color: #7c3aed;
  font-size: 15px;
}

.tba-credits-num {
  font-weight: 600;
  font-size: 14px;
  color: #7c3aed;
}

.tba-credits-group svg {
  color: #7c3aed;
  opacity: 0.6;
}

.tba-divider {
  width: 1px;
  height: 16px;
  background: #d8ccf5;
  margin: 0 4px;
}

.tba-subscribe-label {
  font-size: 13px;
  font-weight: 600;
  color: #7c3aed;
}

/* ── Icon buttons ── */
.tba-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1a1a1a;
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.tba-icon-btn:hover {
  background: #f5f5f5;
  color: #000;
}

/* ── Avatar ── */
.tba-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #1a1a1a;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  margin-left: 2px;
}
.tba-avatar:hover {
  background: #333;
}
</style>