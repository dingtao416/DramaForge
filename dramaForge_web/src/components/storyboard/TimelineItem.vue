<script setup lang="ts">
import { computed } from 'vue'
import type { SegmentDetail } from '@/types/segment'
import { SegmentStatus, SegmentStatusLabel } from '@/types/enums'

const props = defineProps<{
  segment: SegmentDetail
  index: number
  active: boolean
}>()

const thumbUrl = computed(() =>
  props.segment.thumbnail_url || props.segment.shots?.find(shot => shot.image_url)?.image_url || ''
)

const durationLabel = computed(() => {
  const duration = props.segment.duration
  if (!duration) return '--'
  return `${Math.round(duration)}s`
})

const statusDot: Record<string, string> = {
  [SegmentStatus.PENDING]: 'dot-muted',
  [SegmentStatus.GENERATING]: 'dot-active',
  [SegmentStatus.COMPLETED]: 'dot-done',
  [SegmentStatus.FAILED]: 'dot-error',
}
</script>

<template>
  <button
    class="timeline-item"
    :class="{ active }"
    type="button"
    :aria-label="`选择片段 ${index + 1}`"
  >
    <span class="timeline-thumb">
      <img v-if="thumbUrl" :src="thumbUrl" alt="" loading="lazy" />
      <span v-else class="timeline-fallback">片段 {{ String(index + 1).padStart(2, '0') }}</span>

      <span class="timeline-index">{{ String(index + 1).padStart(2, '0') }}</span>
      <span
        class="timeline-status-dot"
        :class="statusDot[segment.status] || 'dot-muted'"
        :title="SegmentStatusLabel[segment.status] || segment.status"
      />
    </span>

    <span class="timeline-label">
      <span>片段 {{ String(index + 1).padStart(2, '0') }}</span>
      <span>{{ durationLabel }}</span>
    </span>
  </button>
</template>

<style scoped>
.timeline-item {
  width: 112px;
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 4px;
  border: 1px solid transparent;
  border-radius: 2px;
  background: transparent;
  color: inherit;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.timeline-item:hover {
  background: #f8fafc;
  border-color: #A89870;
}

.timeline-item.active {
  background: #FDF5D6;
  border-color: #111827;
  box-shadow: 0 0 0 1px rgba(17, 24, 39, 0.08);
}

.timeline-thumb {
  position: relative;
  height: 52px;
  display: block;
  overflow: hidden;
  border-radius: 2px;
  background: #edf0f4;
}

.timeline-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.timeline-fallback {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 700;
}

.timeline-index {
  position: absolute;
  top: 5px;
  left: 5px;
  min-width: 20px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  background: rgba(17, 24, 39, 0.74);
  color: #2D2515;
  font-size: 10px;
  font-weight: 800;
}

.timeline-status-dot {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 8px;
  height: 8px;
  border: 1px solid #fff;
  border-radius: 50%;
}

.dot-muted {
  background: #cbd5e1;
}

.dot-active {
  background: #E8A317;
  animation: pulse 1.1s ease-in-out infinite;
}

.dot-done {
  background: #22c55e;
}

.dot-error {
  background: #ef4444;
}

.timeline-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  color: #64748b;
  font-size: 11px;
  line-height: 1.2;
  white-space: nowrap;
}

.timeline-item.active .timeline-label {
  color: #111827;
  font-weight: 700;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.35);
    opacity: 0.7;
  }
}
</style>
