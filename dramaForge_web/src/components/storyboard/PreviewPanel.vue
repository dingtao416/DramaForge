<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Shot } from '@/types/shot'

const props = defineProps<{
  shot: Shot | null
}>()

const emit = defineEmits<{
  play: []
  download: []
}>()

const isPlaying = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)

function togglePlay() {
  if (!videoRef.value) return
  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

const hasMedia = computed(() => props.shot?.video_url || props.shot?.image_url)
</script>

<template>
  <aside class="w-[380px] border-l border-gray-200 bg-white overflow-y-auto shrink-0 flex flex-col">
    <!-- Video player area -->
    <div class="aspect-[9/16] bg-black relative">
      <!-- Video -->
      <template v-if="shot?.video_url">
        <video
          ref="videoRef"
          :src="shot.video_url"
          class="w-full h-full object-contain"
          @ended="isPlaying = false"
        />
      </template>
      <!-- Static image -->
      <template v-else-if="shot?.image_url">
        <img :src="shot.image_url" class="w-full h-full object-contain" />
      </template>
      <!-- Empty -->
      <div v-else class="w-full h-full flex items-center justify-center text-gray-500 text-[14px]">
        暂无预览
      </div>

      <!-- Playback controls overlay -->
      <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
        <div class="flex items-center gap-3 text-white">
          <button class="text-lg cursor-pointer hover:scale-110 transition-transform" @click="togglePlay">
            {{ isPlaying ? '⏸' : '▶' }}
          </button>
          <span class="text-[12px]">00:00</span>
          <div class="flex-1 h-1 bg-white/30 rounded-full overflow-hidden">
            <div class="h-full bg-white rounded-full transition-all" style="width: 0%" />
          </div>
          <span class="text-[12px]">{{ shot?.duration ? `00:${String(Math.floor(shot.duration)).padStart(2, '0')}` : '00:00' }}</span>
          <button class="text-[14px] cursor-pointer opacity-80 hover:opacity-100">🔈</button>
          <button class="text-[14px] cursor-pointer opacity-80 hover:opacity-100">🔲</button>
          <button class="text-[14px] cursor-pointer opacity-80 hover:opacity-100" @click="emit('download')">⬇</button>
        </div>
      </div>
    </div>

    <!-- Shot detail info -->
    <div v-if="shot" class="p-4 flex-1">
      <h3 class="text-[14px] font-medium text-gray-900 mb-3">分镜详情</h3>
      <div class="space-y-3">
        <div class="flex items-start justify-between text-[13px]">
          <span class="text-gray-400 shrink-0 w-14">镜头</span>
          <span class="text-gray-700 text-right">{{ shot.camera_type || '—' }}</span>
        </div>
        <div class="flex items-start justify-between text-[13px]">
          <span class="text-gray-400 shrink-0 w-14">运镜</span>
          <span class="text-gray-700 text-right">{{ shot.camera_movement || '—' }}</span>
        </div>
        <div class="flex items-start justify-between text-[13px]">
          <span class="text-gray-400 shrink-0 w-14">时长</span>
          <span class="text-gray-700 text-right">{{ shot.duration }}s</span>
        </div>
        <div class="flex items-start justify-between text-[13px]">
          <span class="text-gray-400 shrink-0 w-14">过渡</span>
          <span class="text-gray-700 text-right">{{ shot.transition || '切换' }}</span>
        </div>

        <!-- Media previews -->
        <div v-if="shot.image_url" class="mt-4">
          <div class="text-[12px] text-gray-400 mb-1">图片</div>
          <div class="w-20 h-14 rounded-[6px] overflow-hidden bg-gray-100">
            <img :src="shot.image_url" class="w-full h-full object-cover" />
          </div>
        </div>
      </div>
    </div>

    <!-- Credits hint -->
    <div class="px-4 py-3 text-[12px] text-gray-400 border-t border-gray-100 shrink-0">
      视频每秒消耗11积分，以实际生成为准
    </div>
  </aside>
</template>
