<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { ProjectList } from '@/types/project'

const props = defineProps<{
  projects: ProjectList[]
}>()

const router = useRouter()
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between px-5 mb-3">
      <span class="text-[12px] text-gray-400 font-medium">历史记录</span>
      <span
        class="text-[12px] text-gray-400 cursor-pointer hover:text-primary-600 transition-colors"
        @click="router.push('/projects')"
      >全部</span>
    </div>

    <!-- Project list -->
    <div class="flex-1 overflow-y-auto px-3">
      <template v-if="projects.length">
        <div class="text-[11px] text-gray-400 px-3 mb-2">更早</div>
        <div
          v-for="p in projects"
          :key="p.id"
          class="flex items-center gap-3 px-3 py-3 rounded-[10px] hover:bg-gray-50 cursor-pointer transition-colors"
          @click="router.push(`/projects/${p.id}`)"
        >
          <div class="w-9 h-9 rounded-full bg-gradient-to-br from-purple-100 to-purple-200 flex items-center justify-center text-[13px] text-primary-600 font-medium shrink-0">
            {{ p.title.charAt(0) }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="text-[13px] text-gray-800 truncate leading-tight">{{ p.title }}</div>
            <div class="text-[11px] text-gray-400 truncate mt-0.5">全能创作Agent</div>
          </div>
        </div>
      </template>
      <div v-else class="text-center text-[13px] text-gray-400 py-10">暂无项目</div>
    </div>
  </div>
</template>
