<script setup lang="ts">
import type { EpisodeOverview } from '@/types/episode'

const props = defineProps<{
  episode: EpisodeOverview
}>()

const emit = defineEmits<{
  preview: []
  edit: []
  export: []
}>()

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-[12px] p-4 flex gap-4 hover:shadow-[0_2px_8px_rgba(0,0,0,0.06)] transition-shadow">
    <!-- 大号序号 -->
    <div class="text-[24px] font-light text-gray-300 w-8 flex items-start justify-center pt-1 shrink-0">
      {{ episode.number }}
    </div>

    <!-- 缩略图 -->
    <div class="w-[100px] h-[130px] bg-gray-100 rounded-[8px] shrink-0 relative overflow-hidden">
      <div class="w-full h-full flex items-center justify-center text-2xl text-gray-300">🎬</div>
      <!-- 时长标签 -->
      <span
        v-if="episode.total_duration"
        class="absolute bottom-1 left-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded"
      >
        {{ formatDuration(episode.total_duration) }}
      </span>
    </div>

    <!-- 信息区 -->
    <div class="flex-1 flex flex-col justify-between min-w-0">
      <div>
        <h3 class="text-[14px] font-medium text-gray-900 truncate">
          第 {{ episode.number }} 集：{{ episode.title || '无标题' }}
        </h3>
        <div class="flex items-center gap-3 text-[12px] text-gray-400 mt-1.5">
          <span>👥 {{ episode.character_count }} 角色</span>
          <span>🏠 {{ episode.scene_count }} 场景</span>
          <span>🎬 {{ episode.segment_count }} 分镜</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex items-center gap-2 mt-3">
        <button class="btn btn-outline btn-sm text-[12px]" @click="emit('preview')">▶ 预览</button>
        <button class="btn btn-outline btn-sm text-[12px]" @click="emit('edit')">✏️ 编辑</button>
        <button class="btn btn-primary btn-sm text-[12px]" @click="emit('export')">⬇ 导出</button>
      </div>
    </div>
  </div>
</template>
