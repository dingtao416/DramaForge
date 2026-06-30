<script setup lang="ts">
import type { Shot } from '@/types/shot'
import { ref } from 'vue'

const props = defineProps<{
  shot: Shot
  index: number
  active?: boolean
}>()

const emit = defineEmits<{
  select: []
  regenerate: []
}>()

const imgError = ref(false)

const hasImage = () => !!(props.shot as any).image_url && !imgError.value
const isFailed = () => (props.shot as any).shot_status === 'failed'
const isGenerating = () => (props.shot as any).shot_status === 'generating'
</script>

<template>
  <div
    class="bg-[#FEF9E7] border rounded-[2px] p-4 cursor-pointer transition-all"
    :class="active ? 'border-primary-400 border-2 border-[#D4C898] !shadow-pixel' : isFailed() ? 'border-red-300 border-2' : 'border-[#D4C898] hover:border-[#D4C898] hover:shadow-[2px_2px_0_0_rgba(0,0,0,0.1)]'"
    @click="emit('select')"
  >
    <!-- Thumbnail Preview (if image exists) -->
    <div v-if="hasImage()" class="shot-thumb mb-3 rounded overflow-hidden border border-[#D4C898]">
      <img
        :src="(shot as any).image_url"
        :alt="`分镜 ${index + 1}`"
        class="w-full object-cover aspect-video"
        @error="imgError = true"
      />
    </div>

    <!-- Generating progress -->
    <div v-if="isGenerating()" class="shot-generating mb-3">
      <div class="flex items-center gap-2 text-[12px] text-amber-600 mb-2">
        <div class="w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
        <span>生成中...</span>
      </div>
      <div class="h-1.5 bg-amber-100 rounded-full overflow-hidden">
        <div class="h-full bg-amber-400 rounded-full animate-pulse" style="width: 60%" />
      </div>
    </div>

    <!-- Failed state + retry -->
    <div v-if="isFailed()" class="shot-failed mb-3 p-2 rounded bg-red-50 border border-red-200">
      <div class="flex items-center gap-2 text-[12px] text-red-600">
        <span>❌ 生成失败</span>
      </div>
      <p v-if="(shot as any).error_message" class="text-[11px] text-red-400 mt-1 truncate">{{ (shot as any).error_message }}</p>
      <button
        class="shot-retry-btn"
        @click.stop="emit('regenerate')"
      >🔄 重新生成</button>
    </div>

    <!-- Header -->
    <div class="flex items-center gap-2 mb-2">
      <span class="text-[14px] font-medium text-gray-800">分镜 {{ index + 1 }}</span>
      <span class="text-[12px] text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">⊙ {{ shot.duration }}s</span>
      <span v-if="hasImage()" class="text-[12px] text-green-600 bg-green-50 px-2 py-0.5 rounded-full">✓ 已生成</span>
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
            v-for="(char, idx) in shot.characters"
            :key="`${char.char_id}-${char.appearance_idx}-${idx}`"
            class="inline-flex items-center gap-1 bg-primary-50 text-primary-600 text-[12px] px-2 py-0.5 rounded-full"
          >🎭 {{ char }}</span>
        </div>
      </div>
      <div v-if="shot.dialogue" class="flex items-start gap-2">
        <span class="text-gray-400 w-10 shrink-0 pt-0.5">台词</span>
        <span class="text-gray-700 leading-relaxed">「{{ shot.dialogue }}」</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shot-thumb img {
  max-height: 140px;
}
.shot-retry-btn {
  margin-top: 6px;
  padding: 3px 10px;
  border: 1px solid #ef4444;
  border-radius: 4px;
  background: #fff;
  color: #ef4444;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.shot-retry-btn:hover {
  background: #fef2f2;
}
</style>
