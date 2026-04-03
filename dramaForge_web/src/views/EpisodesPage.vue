<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { episodesApi } from '@/api/episodes'
import type { EpisodeOverview } from '@/types/episode'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const projectId = Number(route.params.id)

const episodes = ref<EpisodeOverview[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await episodesApi.list(projectId)
    episodes.value = data
  } finally {
    loading.value = false
  }
})

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
</script>

<template>
  <div class="page-container">
    <!-- Header -->
    <div class="flex items-center justify-between mb-2">
      <h1 class="page-title">共 {{ episodes.length }} 集</h1>
      <button class="btn btn-outline btn-sm">多选</button>
    </div>
    <p class="page-subtitle mb-8">分镜脚本生成100字符消耗2积分，以实际生成为准</p>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-24">
      <div class="w-8 h-8 border-[3px] border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <EmptyState v-else-if="!episodes.length" title="暂无分集" icon="📺" />

    <!-- Episode grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div
        v-for="ep in episodes"
        :key="ep.id"
        class="card p-5 flex gap-5 hover:shadow-[0_4px_16px_rgba(0,0,0,0.06)] cursor-pointer group transition-all"
        @click="router.push(`/projects/${projectId}/episodes/${ep.id}/storyboard`)"
      >
        <!-- Number -->
        <div class="text-[28px] font-light text-gray-200 w-10 flex items-start justify-center pt-1 shrink-0 group-hover:text-primary-300 transition-colors">
          {{ ep.number }}
        </div>

        <!-- Thumbnail -->
        <div class="w-[100px] h-[130px] bg-gradient-to-br from-gray-50 to-gray-100 rounded-[12px] shrink-0 relative overflow-hidden group-hover:from-purple-50 group-hover:to-purple-100 transition-colors">
          <div class="w-full h-full flex items-center justify-center text-3xl text-gray-300">🎬</div>
          <span
            v-if="ep.total_duration"
            class="absolute bottom-2 left-2 bg-black/70 text-white text-[11px] px-2 py-0.5 rounded-md"
          >
            {{ formatDuration(ep.total_duration) }}
          </span>
        </div>

        <!-- Info -->
        <div class="flex-1 flex flex-col justify-between min-w-0">
          <div>
            <h3 class="text-[15px] font-semibold text-gray-900 truncate">
              第 {{ ep.number }} 集：{{ ep.title || '无标题' }}
            </h3>
            <div class="flex items-center gap-4 text-[13px] text-gray-400 mt-2.5">
              <span class="flex items-center gap-1">
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="5" r="3" stroke="currentColor" stroke-width="1.2"/><path d="M2 13c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="currentColor" stroke-width="1.2"/></svg>
                {{ ep.character_count }}
              </span>
              <span class="flex items-center gap-1">
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><rect x="2" y="3" width="10" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M5 3V2M9 3V2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
                {{ ep.scene_count }}
              </span>
              <span class="flex items-center gap-1">
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><rect x="1" y="3" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M5 3l2-2 2 2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                {{ ep.segment_count }}
              </span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 mt-4">
            <button
              class="btn btn-outline btn-sm"
              @click.stop
            >
              ▶ 预览
            </button>
            <button
              class="btn btn-outline btn-sm"
              @click.stop="router.push(`/projects/${projectId}/episodes/${ep.id}/storyboard`)"
            >
              ✏️ 编辑
            </button>
            <button
              class="btn btn-primary btn-sm"
              @click.stop
            >
              ⬇ 导出
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Bottom bar -->
  <div class="bottom-action-bar">
    <div class="bar-hint">
      <div class="bar-icon">🤖</div>
      <span>点击进入分镜编辑器，可以细调每个分镜的画面和台词</span>
    </div>
    <div class="bar-actions">
      <button class="btn btn-outline btn-sm" @click="router.push(`/projects/${projectId}/assets`)">
        ← 上一步
      </button>
    </div>
  </div>
</template>