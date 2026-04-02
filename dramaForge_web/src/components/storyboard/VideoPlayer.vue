<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  src?: string
  poster?: string
}>()

const emit = defineEmits<{
  play: []
  pause: []
  ended: []
}>()

const videoRef = ref<HTMLVideoElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(1)

function togglePlay() {
  if (!videoRef.value) return
  if (isPlaying.value) {
    videoRef.value.pause()
    emit('pause')
  } else {
    videoRef.value.play()
    emit('play')
  }
}

function onTimeUpdate() {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
  }
}

function onLoadedMetadata() {
  if (videoRef.value) {
    duration.value = videoRef.value.duration
  }
}

function onEnded() {
  isPlaying.value = false
  emit('ended')
}

function seek(e: MouseEvent) {
  if (!videoRef.value) return
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  videoRef.value.currentTime = ratio * duration.value
}

function toggleFullscreen() {
  videoRef.value?.requestFullscreen?.()
}

function formatTime(s: number) {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

const progress = computed(() =>
  duration.value ? (currentTime.value / duration.value) * 100 : 0
)
</script>

<template>
  <div class="relative bg-black rounded-[8px] overflow-hidden">
    <video
      v-if="src"
      ref="videoRef"
      :src="src"
      :poster="poster"
      class="w-full h-full object-contain"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @play="isPlaying = true"
      @pause="isPlaying = false"
      @ended="onEnded"
    />
    <div v-else class="w-full h-full flex items-center justify-center text-gray-500 text-[14px] min-h-[200px]">
      暂无视频
    </div>

    <!-- Controls overlay -->
    <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
      <!-- Progress bar -->
      <div class="h-1 bg-white/30 rounded-full mb-2 cursor-pointer" @click="seek">
        <div class="h-full bg-white rounded-full transition-all" :style="{ width: `${progress}%` }" />
      </div>

      <div class="flex items-center gap-3 text-white">
        <button class="text-[16px] cursor-pointer hover:scale-110 transition-transform" @click="togglePlay">
          {{ isPlaying ? '⏸' : '▶' }}
        </button>
        <span class="text-[12px]">{{ formatTime(currentTime) }}</span>
        <span class="text-[12px] opacity-60">|</span>
        <span class="text-[12px]">{{ formatTime(duration) }}</span>
        <div class="flex-1" />
        <button class="text-[14px] cursor-pointer opacity-80 hover:opacity-100">🔈</button>
        <button class="text-[14px] cursor-pointer opacity-80 hover:opacity-100" @click="toggleFullscreen">🔲</button>
        <button class="text-[14px] cursor-pointer opacity-80 hover:opacity-100">⬇</button>
      </div>
    </div>
  </div>
</template>
