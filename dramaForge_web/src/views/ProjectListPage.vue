<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api/projects'
import { VideoStyleLabel, DramaGenreLabel, ProjectStepLabel } from '@/types/enums'
import type { ProjectList } from '@/types/project'
import EmptyState from '@/components/common/EmptyState.vue'

const router = useRouter()
const projects = ref<ProjectList[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await projectsApi.list()
    projects.value = data
  } finally {
    loading.value = false
  }
})

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-semibold text-gray-900">我的项目</h1>
      <button class="btn btn-primary" @click="router.push('/')">
        + 新建项目
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="!projects.length"
      title="还没有项目"
      description="点击上方按钮创建你的第一个短剧项目"
      icon="🎬"
    />

    <!-- Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="p in projects"
        :key="p.id"
        class="card p-4 cursor-pointer hover:shadow-md transition-all group"
        @click="router.push(`/projects/${p.id}`)"
      >
        <!-- Thumbnail placeholder -->
        <div class="h-32 bg-gray-100 rounded-lg mb-3 flex items-center justify-center text-3xl group-hover:bg-gray-200 transition-colors">
          🎬
        </div>

        <h3 class="text-sm font-medium text-gray-900 truncate">{{ p.title }}</h3>

        <div class="flex items-center gap-2 mt-2">
          <span class="badge badge-primary">{{ VideoStyleLabel[p.style] }}</span>
          <span class="badge" style="background:#f0f0f0;color:#666">{{ DramaGenreLabel[p.genre] }}</span>
        </div>

        <div class="flex items-center justify-between mt-3 text-xs text-gray-400">
          <span>{{ ProjectStepLabel[p.status] }}</span>
          <span>{{ formatDate(p.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>