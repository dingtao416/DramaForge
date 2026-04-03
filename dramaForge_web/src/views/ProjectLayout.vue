<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import StepNavigator from '@/components/common/StepNavigator.vue'
import TopbarActions from '@/components/common/TopbarActions.vue'

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
  <div class="min-h-screen flex flex-col bg-white">
    <!-- Top bar -->
    <div class="h-[56px] border-b border-gray-200 bg-white flex items-center px-6 shrink-0">
      <!-- Back -->
      <button
        class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors mr-3 shrink-0"
        @click="router.push('/drama-workbench')"
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

      <!-- Right actions (unified component) -->
      <TopbarActions />
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto">
      <router-view />
    </div>
  </div>
</template>