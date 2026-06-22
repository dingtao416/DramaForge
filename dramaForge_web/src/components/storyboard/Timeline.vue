<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import type { Segment } from '@/types/segment'
import TimelineItem from './TimelineItem.vue'

const props = defineProps<{
  segments: Segment[]
  currentIndex: number
  totalDuration: number
}>()

const emit = defineEmits<{
  select: [index: number]
  multiSelect: []
}>()

const isPlaying = ref(false)
const playTime = ref(0)
let playTimer: ReturnType<typeof setInterval> | null = null

watch(() => props.currentIndex, () => {
  playTime.value = 0
})

onBeforeUnmount(() => {
  stopPlayback()
})

function togglePlay() {
  if (isPlaying.value) {
    stopPlayback()
  } else {
    startPlayback()
  }
}

function startPlayback() {
  stopTimerOnly()
  isPlaying.value = true
  playTimer = setInterval(() => {
    playTime.value += 1
    const seg = props.segments[props.currentIndex]
    if (!seg) return

    const duration = seg.duration || 5
    if (playTime.value >= duration) {
      playTime.value = 0
      const next = props.currentIndex + 1
      if (next >= props.segments.length) {
        stopPlayback()
        return
      }
      emit('select', next)
    }
  }, 1000)
}

function stopTimerOnly() {
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
}

function stopPlayback() {
  isPlaying.value = false
  playTime.value = 0
  stopTimerOnly()
}

function formatDuration(seconds: number) {
  const safe = Number.isFinite(seconds) ? seconds : 0
  const m = Math.floor(safe / 60)
  const s = Math.floor(safe % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
</script>

<template>
  <div class="timeline-root">
    <div class="timeline-toolbar">
      <button class="timeline-play" type="button" title="播放片段序列" @click="togglePlay">
        <svg v-if="isPlaying" width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
          <path d="M6.5 4v10M11.5 4v10" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/>
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
          <path d="M6.5 4.5v9l7-4.5-7-4.5z" fill="currentColor"/>
        </svg>
      </button>

      <div class="timeline-progress">
        <span>{{ formatDuration(playTime) }}</span>
        <div class="timeline-line">
          <span :style="{ width: `${totalDuration ? Math.min(100, (playTime / totalDuration) * 100) : 0}%` }" />
        </div>
        <span>{{ formatDuration(totalDuration) }}</span>
      </div>

      <button class="timeline-multi" type="button" @click="emit('multiSelect')">多选</button>
    </div>

    <div class="timeline-strip">
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
.timeline-root {
  height: 120px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-top: 1px solid #e5e7eb;
  background: #FDF5D6;
  padding: 10px 22px 12px;
  border-top-left-radius: 22px;
}

.timeline-toolbar {
  height: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.timeline-play {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: #111827;
  cursor: pointer;
}

.timeline-play:hover {
  background: #f1f5f9;
}

.timeline-progress {
  flex: 1;
  min-width: 120px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 11px;
}

.timeline-line {
  height: 2px;
  flex: 1;
  border-radius: 2px;
  background: #cbd5e1;
  overflow: hidden;
}

.timeline-line span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #111827;
}

.timeline-multi {
  height: 26px;
  padding: 0 12px;
  border: 0;
  border-radius: 2px;
  background: #f1f5f9;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.timeline-multi:hover {
  color: #111827;
  background: #e5e7eb;
}

.timeline-strip {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 10px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 4px;
}

.timeline-strip::-webkit-scrollbar {
  height: 4px;
}

.timeline-strip::-webkit-scrollbar-track {
  background: transparent;
}

.timeline-strip::-webkit-scrollbar-thumb {
  background: #A89870;
  border-radius: 2px;
}
</style>
