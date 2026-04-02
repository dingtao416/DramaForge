<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import StepNavigator from '@/components/common/StepNavigator.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = Number(route.params.id)

onMounted(() => {
  projectStore.fetchProject(projectId)
})

onUnmounted(() => {
  projectStore.clear()
})
</script>

<template>
  <div class="min-h-[calc(100vh-56px)] flex flex-col">
    <!-- Top bar: back + title + step navigator + actions -->
    <div class="h-[56px] border-b border-gray-200 bg-white flex items-center px-6 shrink-0">
      <!-- Back + Title -->
      <button
        class="flex items-center gap-2 text-gray-600 hover:text-gray-900 cursor-pointer transition-colors mr-4 shrink-0"
        @click="router.push('/projects')"
      >
        <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <span class="text-[15px] font-semibold text-gray-900 truncate max-w-[280px] mr-6">
        {{ projectStore.currentProject?.title || '加载中...' }}
      </span>

      <!-- Step Navigator (centered) -->
      <div class="flex-1 flex justify-center">
        <StepNavigator
          v-if="projectStore.currentProject"
          :current-step="projectStore.currentStep"
        />
      </div>

      <!-- Right actions placeholder — same as AppHeader right side -->
      <div class="flex items-center gap-4 shrink-0 ml-6">
        <button class="h-[34px] px-3.5 rounded-full border border-gray-200 flex items-center gap-1.5 text-[13px] text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors">
          <span class="text-primary-500">⚡</span>
          <span>0</span>
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none" class="text-gray-400"><path d="M3 4L5 6L7 4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button class="text-[13px] text-primary-600 font-semibold hover:text-primary-700 cursor-pointer">订阅</button>
        <button class="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 cursor-pointer transition-colors">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M14 11C14 11.4 13.8 11.7 13.5 12L11.5 14C11.2 14.3 10.8 14.3 10.5 14L8.5 12H4C3.2 12 2.5 11.3 2.5 10.5V4C2.5 3.2 3.2 2.5 4 2.5H13C13.8 2.5 14.5 3.2 14.5 4V11Z" stroke="currentColor" stroke-width="1.3"/></svg>
        </button>
        <button class="w-8 h-8 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 cursor-pointer transition-colors">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M14 12.5s-1.2-1.2-1.2-3V7a4.3 4.3 0 0 0-8.6 0v2.5c0 1.8-1.2 3-1.2 3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M7 14.5s.4.6 1.5.6 1.5-.6 1.5-.6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
        </button>
        <div class="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-white text-[12px] font-medium cursor-pointer">U</div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1">
      <router-view />
    </div>
  </div>
</template>