<script setup lang="ts">
import type { Segment } from '@/types/segment'

const props = defineProps<{
  segment: Segment
  index: number
  active: boolean
}>()

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
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
    </div>

    <!-- Duration -->
    <div class="text-center text-[11px] text-gray-500 py-1 bg-white">
      {{ segment.duration ? formatDuration(segment.duration) : '--:--' }}
    </div>
  </div>
</template>
