<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import StepNavigator from '@/components/common/StepNavigator.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const authStore = useAuthStore()

const projectId = Number(route.params.id)

onMounted(() => {
  projectStore.fetchProject(projectId)
})

onUnmounted(() => {
  projectStore.clear()
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-white">
    <!-- Top bar -->
    <div class="h-[56px] border-b border-gray-200 bg-white flex items-center px-6 shrink-0">
      <!-- Back -->
      <button
        class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors mr-3 shrink-0"
        @click="router.push('/projects')"
      >
        <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <!-- Title -->
      <span class="text-[15px] font-semibold text-gray-900 truncate max-w-[260px]">
        {{ projectStore.currentProject?.title || '加载中...' }}
      </span>

      <!-- Step Navigator (centered) -->
      <div class="flex-1 flex justify-center">
        <StepNavigator
          v-if="projectStore.currentProject"
          :current-step="projectStore.currentStep"
        />
      </div>

      <!-- Right actions -->
      <div class="flex items-center gap-3 shrink-0 ml-6">
        <button class="h-[34px] px-3.5 rounded-full border border-gray-200 flex items-center gap-1.5 text-[13px] text-gray-500 hover:bg-gray-50 cursor-pointer transition-colors bg-white">
          <span class="text-primary-500 text-[14px]">✦</span>
          <span>0</span>
        </button>
        <button class="w-[34px] h-[34px] rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 cursor-pointer transition-colors">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2a2.5 2.5 0 0 0-2.5 2.5v1.25a.5.5 0 0 1-.12.33l-.7.8A2 2 0 0 0 6 8.5V10c0 1.1-.4 2.1-1.07 2.9l-.43.5a1 1 0 0 0 .76 1.6h9.48a1 1 0 0 0 .76-1.6l-.43-.5A4.5 4.5 0 0 1 14 10V8.5a2 2 0 0 0-.68-1.5l-.7-.82a.5.5 0 0 1-.12-.33V4.5A2.5 2.5 0 0 0 10 2z" stroke="currentColor" stroke-width="1.3"/><path d="M8.5 15.5s.5 1.5 1.5 1.5 1.5-1.5 1.5-1.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
        </button>
        <div
          class="w-[34px] h-[34px] rounded-full bg-gray-800 flex items-center justify-center text-white text-[12px] font-medium cursor-pointer hover:bg-gray-900 transition-colors"
          :title="authStore.isLoggedIn ? authStore.displayName : '未登录'"
          @click="authStore.isLoggedIn ? undefined : router.push('/login')"
        >{{ authStore.isLoggedIn ? authStore.displayName.charAt(0).toUpperCase() : 'U' }}</div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto">
      <router-view />
    </div>
  </div>
</template>