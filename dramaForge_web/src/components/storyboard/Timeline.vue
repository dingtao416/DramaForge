<script setup lang="ts">
import type { Segment } from '@/types/segment'
import TimelineItem from './TimelineItem.vue'

defineProps<{
  segments: Segment[]
  currentIndex: number
  totalDuration: number
}>()

const emit = defineEmits<{
  select: [index: number]
  multiSelect: []
}>()

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
</script>

<template>
  <div class="h-[130px] border-t border-gray-200 bg-white shrink-0 px-4 py-2 flex flex-col">
    <!-- Playback bar -->
    <div class="flex items-center gap-3 mb-2">
      <button class="text-[18px] text-gray-700 cursor-pointer hover:text-gray-900 transition-colors">▶</button>
      <span class="text-[13px] text-gray-500">00:00 / {{ formatDuration(totalDuration) }}</span>
      <div class="flex-1" />
      <button
        class="h-[28px] px-3 rounded-[6px] text-[12px] text-gray-500 hover:bg-gray-100 cursor-pointer transition-colors flex items-center gap-1"
        @click="emit('multiSelect')"
      >
        🔀 多选
      </button>
    </div>

    <!-- Segments horizontal scroll -->
    <div class="flex-1 flex gap-2 overflow-x-auto pb-1 scrollbar-thin">
      <TimelineItem
        v-for="(seg, idx) in segments"
        :key="seg.id"
        :segment="seg"
        :index="idx"
        :active="idx === currentIndex"
        @click="emit('select', idx)"
      />
    </div>
  </div>
</template>

<style scoped>
.scrollbar-thin::-webkit-scrollbar { height: 4px; }
.scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
.scrollbar-thin::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 2px; }
</style>
