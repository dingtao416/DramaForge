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
  <div class="max-w-[1100px] mx-auto px-8 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-2">
      <h1 class="text-[18px] font-bold text-gray-900">共 {{ episodes.length }} 集</h1>
      <button class="btn btn-outline btn-sm">多选</button>
    </div>
    <p class="text-[13px] text-gray-400 mb-8">分镜脚本生成100字符消耗2积分，以实际生成为准</p>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <EmptyState v-else-if="!episodes.length" title="暂无分集" icon="📺" />

    <!-- Episode grid — 2列 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div
        v-for="ep in episodes"
        :key="ep.id"
        class="bg-white border border-gray-200 rounded-[14px] p-5 flex gap-5 hover:shadow-md transition-shadow cursor-pointer"
        @click="router.push(`/projects/${projectId}/episodes/${ep.id}/storyboard`)"
      >
        <!-- Number -->
        <div class="text-[28px] font-light text-gray-200 w-10 flex items-start justify-center pt-1 shrink-0">
          {{ ep.number }}
        </div>

        <!-- Thumbnail -->
        <div class="w-[100px] h-[130px] bg-gray-100 rounded-[10px] shrink-0 relative overflow-hidden">
          <div class="w-full h-full flex items-center justify-center text-3xl text-gray-300">🎬</div>
          <!-- Duration badge -->
          <span
            v-if="ep.total_duration"
            class="absolute bottom-1.5 left-1.5 bg-black/70 text-white text-[11px] px-2 py-0.5 rounded-md"
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
            <div class="flex items-center gap-4 text-[13px] text-gray-400 mt-2">
              <span>👥 {{ ep.character_count }} 角色</span>
              <span>🏠 {{ ep.scene_count }} 场景</span>
              <span>🎬 {{ ep.segment_count }} 分镜</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 mt-4">
            <button
              class="h-[32px] px-3.5 rounded-lg text-[13px] text-gray-600 border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors bg-white"
              @click.stop
            >
              ▶ 预览
            </button>
            <button
              class="h-[32px] px-3.5 rounded-lg text-[13px] text-gray-600 border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors bg-white"
              @click.stop="router.push(`/projects/${projectId}/episodes/${ep.id}/storyboard`)"
            >
              ✏️ 编辑
            </button>
            <button
              class="h-[32px] px-3.5 rounded-lg text-[13px] text-white bg-gray-900 hover:bg-black cursor-pointer transition-colors"
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
  <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-8 py-4 flex items-center z-40">
    <div class="flex items-center gap-3 text-[14px] text-gray-500">
      <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 text-[12px]">🤖</div>
      <span>点击进入分镜编辑器，可以细调每个分镜的画面和台词</span>
    </div>
    <div class="flex-1" />
    <div class="flex items-center gap-3">
      <button class="btn btn-outline" @click="router.push(`/projects/${projectId}/assets`)">
        ← 上一步
      </button>
    </div>
  </div>
</template>