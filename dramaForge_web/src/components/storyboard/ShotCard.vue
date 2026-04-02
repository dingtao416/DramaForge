<script setup lang="ts">
import type { Shot } from '@/types/shot'

defineProps<{
  shot: Shot
  index: number
  active?: boolean
}>()

const emit = defineEmits<{
  select: []
}>()
</script>

<template>
  <div
    class="bg-white border rounded-[12px] p-4 cursor-pointer transition-all"
    :class="active ? 'border-primary-400 ring-2 ring-primary-100 shadow-sm' : 'border-gray-200 hover:border-gray-300 hover:shadow-[0_2px_8px_rgba(0,0,0,0.04)]'"
    @click="emit('select')"
  >
    <!-- Header -->
    <div class="flex items-center gap-2 mb-2">
      <span class="text-[14px] font-medium text-gray-800">分镜 {{ index + 1 }}</span>
      <span class="text-[12px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">⊙ {{ shot.duration }}s</span>
    </div>

    <!-- Content grid -->
    <div class="space-y-1.5 text-[13px]">
      <div class="flex items-center gap-2">
        <span class="text-gray-400 w-10 shrink-0">时间</span>
        <span class="text-gray-700">{{ shot.time_of_day || '日' }}</span>
      </div>
      <div v-if="shot.scene_ref" class="flex items-center gap-2">
        <span class="text-gray-400 w-10 shrink-0">场景</span>
        <span class="inline-flex items-center gap-1 bg-primary-50 text-primary-600 text-[12px] px-2 py-0.5 rounded-full">
          🖼 {{ shot.scene_ref }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-gray-400 w-10 shrink-0">镜头</span>
        <span class="text-gray-700">{{ shot.camera_type || '中景' }}</span>
      </div>
      <div v-if="shot.characters?.length" class="flex items-start gap-2">
        <span class="text-gray-400 w-10 shrink-0 pt-0.5">角色</span>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="char in shot.characters"
            :key="char"
            class="inline-flex items-center gap-1 bg-primary-50 text-primary-600 text-[12px] px-2 py-0.5 rounded-full"
          >🎭 {{ char }}</span>
        </div>
      </div>
      <div v-if="shot.dialogue" class="flex items-start gap-2">
        <span class="text-gray-400 w-10 shrink-0 pt-0.5">台词</span>
        <span class="text-gray-700 leading-relaxed">「{{ shot.dialogue }}」</span>
      </div>
      <div v-if="shot.voice_style" class="flex items-center gap-2">
        <span class="text-gray-400 w-10 shrink-0">音色</span>
        <span class="text-gray-500 text-[12px]">{{ shot.voice_style }}</span>
      </div>
      <div v-if="shot.camera_movement" class="flex items-center gap-2">
        <span class="text-gray-400 w-10 shrink-0">运镜</span>
        <span class="text-gray-700">{{ shot.camera_movement }}</span>
      </div>
    </div>
  </div>
</template>
