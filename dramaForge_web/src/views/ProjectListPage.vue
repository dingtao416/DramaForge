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
const duplicatingId = ref<number | null>(null)

async function refreshList() {
  const { data } = await projectsApi.list()
  projects.value = data
}

onMounted(async () => {
  loading.value = true
  try {
    await refreshList()
  } finally {
    loading.value = false
  }
})

async function handleDuplicate(id: number) {
  duplicatingId.value = id
  try {
    await projectsApi.duplicate(id)
    await refreshList()
  } catch (e: any) {
    alert('复制失败')
  } finally {
    duplicatingId.value = null
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="page-container-wide">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="page-title">我的项目</h1>
        <p class="page-subtitle">管理你的短剧创作项目</p>
      </div>
      <button class="btn btn-primary" @click="router.push('/')">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><line x1="7" y1="2" x2="7" y2="12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="2" y1="7" x2="12" y2="7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        新建项目
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-24">
      <div class="w-8 h-8 border-[3px] border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="!projects.length"
      title="还没有项目"
      description="点击上方按钮创建你的第一个短剧项目"
      icon="🎬"
    />

    <!-- Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div
        v-for="p in projects"
        :key="p.id"
        class="card overflow-hidden cursor-pointer group hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] transition-all"
        @click="router.push(`/projects/${p.id}`)"
      >
        <!-- Thumbnail -->
        <div class="h-[140px] bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center text-4xl group-hover:from-purple-50 group-hover:to-purple-100 transition-colors">
          🎬
        </div>

        <div class="p-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-[14px] font-semibold text-gray-900 truncate">{{ p.title }}</h3>
            <button
              class="duplicate-btn"
              :disabled="duplicatingId === p.id"
              title="复制项目"
              @click.stop="handleDuplicate(p.id)"
            >
              <svg v-if="duplicatingId === p.id" class="animate-spin" width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
                <path d="M7 1.5a5.5 5.5 0 015.1 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="4" y="4" width="8" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
                <path d="M2 10V2.5A.5.5 0 012.5 2H10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="flex items-center gap-2 mb-3">
            <span class="badge badge-primary">{{ VideoStyleLabel[p.style] }}</span>
            <span class="badge" style="background:#f5f5f5;color:#666">{{ DramaGenreLabel[p.genre] }}</span>
          </div>

          <div class="flex items-center justify-between text-[12px] text-gray-400">
            <span class="flex items-center gap-1">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1"/><path d="M6 3v3l2 1" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>
              {{ formatDate(p.created_at) }}
            </span>
            <span class="px-2 py-0.5 rounded bg-gray-50 text-gray-500 text-[11px]">{{ ProjectStepLabel[p.status] }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.duplicate-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: 6px;
  color: #ccc;
  transition: all 0.15s;
  flex-shrink: 0;
  opacity: 0;
}
.group:hover .duplicate-btn,
.duplicate-btn:hover {
  opacity: 1;
}
.duplicate-btn:hover {
  background: #f5f5f5;
  color: #666;
}
.duplicate-btn:disabled {
  opacity: 1;
  cursor: not-allowed;
}
</style>