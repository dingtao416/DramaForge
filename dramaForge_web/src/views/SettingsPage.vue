<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

function handleLogout() {
  authStore.doLogout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-white">
    <!-- Top bar -->
    <div class="h-[56px] border-b border-gray-200 bg-white flex items-center px-8 shrink-0">
      <button
        class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors mr-3"
        @click="router.push('/')"
      >
        <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <h1 class="text-[16px] font-bold text-gray-900">设置</h1>
    </div>

    <div class="page-container" style="max-width: 640px;">
      <!-- Profile section -->
      <div class="mb-8">
        <h2 class="text-[15px] font-semibold text-gray-900 mb-4">账户信息</h2>
        <div class="card p-6">
          <div class="flex items-center gap-4 mb-6">
            <div class="w-14 h-14 rounded-full bg-gray-800 flex items-center justify-center text-white text-[20px] font-semibold">
              {{ authStore.isLoggedIn ? authStore.displayName.charAt(0).toUpperCase() : 'U' }}
            </div>
            <div>
              <div class="text-[15px] font-semibold text-gray-900">
                {{ authStore.isLoggedIn ? authStore.displayName : '未登录' }}
              </div>
              <div class="text-[13px] text-gray-400 mt-0.5">
                {{ authStore.user?.email || authStore.user?.phone || '—' }}
              </div>
            </div>
          </div>
          <div class="space-y-4">
            <div class="flex items-center justify-between py-3 border-b border-gray-100">
              <span class="text-[14px] text-gray-600">昵称</span>
              <span class="text-[14px] text-gray-900">{{ authStore.user?.nickname || '未设置' }}</span>
            </div>
            <div class="flex items-center justify-between py-3 border-b border-gray-100">
              <span class="text-[14px] text-gray-600">账号状态</span>
              <span class="badge badge-success">{{ authStore.user?.status || '—' }}</span>
            </div>
            <div class="flex items-center justify-between py-3">
              <span class="text-[14px] text-gray-600">注册时间</span>
              <span class="text-[14px] text-gray-400">{{ authStore.user?.created_at ? new Date(authStore.user.created_at).toLocaleDateString('zh-CN') : '—' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Preferences -->
      <div class="mb-8">
        <h2 class="text-[15px] font-semibold text-gray-900 mb-4">偏好设置</h2>
        <div class="card p-6">
          <div class="space-y-4">
            <div class="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <div class="text-[14px] text-gray-800">默认视频风格</div>
                <div class="text-[12px] text-gray-400 mt-0.5">新建项目时的默认风格</div>
              </div>
              <span class="text-[14px] text-gray-500">写实</span>
            </div>
            <div class="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <div class="text-[14px] text-gray-800">默认画面比例</div>
                <div class="text-[12px] text-gray-400 mt-0.5">新建项目时的默认比例</div>
              </div>
              <span class="text-[14px] text-gray-500">9:16</span>
            </div>
            <div class="flex items-center justify-between py-3">
              <div>
                <div class="text-[14px] text-gray-800">AI 模型偏好</div>
                <div class="text-[12px] text-gray-400 mt-0.5">生成内容时优先使用的模型</div>
              </div>
              <span class="text-[14px] text-gray-500">自动</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Danger zone -->
      <div>
        <h2 class="text-[15px] font-semibold text-gray-900 mb-4">其他</h2>
        <div class="card p-6">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-[14px] text-gray-800">退出登录</div>
              <div class="text-[12px] text-gray-400 mt-0.5">退出当前账号</div>
            </div>
            <button class="btn btn-outline btn-sm text-red-500 border-red-200 hover:bg-red-50" @click="handleLogout">
              退出登录
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>