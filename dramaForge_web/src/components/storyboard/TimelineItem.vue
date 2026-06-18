<script setup lang="ts">
import type { SegmentDetail } from '@/types/segment'

const props = defineProps<{
  segment: SegmentDetail
  index: number
  active: boolean
}>()

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const statusConfig: Record<string, { label: string; dot: string }> = {
  PENDING:    { label: '待生成', dot: 'bg-gray-300' },
  GENERATING: { label: '生成中', dot: 'bg-purple-500 animate-pulse' },
  COMPLETED:  { label: '已完成', dot: 'bg-green-500' },
  FAILED:     { label: '失败',   dot: 'bg-red-500' },
}
</script>

<template>
  <div
    class="shrink-0 w-[120px] rounded-[8px] overflow-hidden border-2 cursor-pointer transition-all"
    :class="active
      ? 'border-primary-500 shadow-[0_0_0_1px_rgba(124,58,237,0.3)]'
      : 'border-transparent hover:border-gray-300'"
  >
    <!-- Thumbnail -->
    <div class="h-[64px] bg-gray-100 relative flex items-center justify-center text-[12px] text-gray-400">
      <img
        v-if="segment.thumbnail_url"
        :src="segment.thumbnail_url"
        class="w-full h-full object-cover"
      />
      <span v-else>片段{{ index + 1 }}</span>

      <!-- Number badge -->
      <span class="absolute top-1 left-1 bg-primary-500 text-white text-[9px] px-1.5 py-0.5 rounded-[4px] font-medium min-w-[16px] text-center">
        {{ index + 1 }}
      </span>

      <!-- Status dot -->
      <span
        class="absolute top-1 right-1 w-[8px] h-[8px] rounded-full border border-white"
        :class="statusConfig[segment.status]?.dot || 'bg-gray-300'"
        :title="statusConfig[segment.status]?.label || segment.status"
      />
    </div>

    <!-- Duration + Status -->
    <div class="flex items-center justify-between text-center px-2 py-1 bg-white">
      <span class="text-[10px] text-gray-400">
        {{ statusConfig[segment.status]?.label || segment.status }}
      </span>
      <span class="text-[11px] text-gray-500 font-medium">
        {{ segment.duration ? formatDuration(segment.duration) : '--:--' }}
      </span>
    </div>
  </div>
</template>
