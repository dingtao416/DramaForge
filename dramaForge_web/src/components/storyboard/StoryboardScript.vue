<script setup lang="ts">
import { ref } from 'vue'
import type { Segment } from '@/types/segment'
import type { Shot } from '@/types/shot'

const props = defineProps<{
  segment: Segment | null
  segmentIndex: number
}>()

const emit = defineEmits<{
  editScript: []
  regenerate: []
  selectShot: [shot: Shot, index: number]
}>()

const editing = ref(false)
</script>

<template>
  <div class="flex-1 overflow-y-auto p-6 bg-gray-50">
    <template v-if="segment">
      <!-- Segment header -->
      <div class="flex items-start justify-between mb-4">
        <div>
          <div class="flex items-center gap-3">
            <h2 class="text-[16px] font-semibold text-gray-900">
              片段 {{ segmentIndex + 1 }}
            </h2>
          </div>
          <p class="text-[12px] text-gray-400 mt-1">
            片段时长请限制在4-15s，输入"@"可快速调整镜头时长、引用角色、场景、素材
          </p>
        </div>
        <span class="text-[12px] text-gray-400 whitespace-nowrap shrink-0">
          视频每秒消耗11积分，以实际生成为准
        </span>
      </div>

      <!-- Script card -->
      <div class="bg-white border border-gray-200 rounded-[12px] p-5 mb-4">
        <!-- Style info -->
        <div class="text-[13px] text-gray-500 mb-4 pb-3 border-b border-gray-100">
          画面风格和类型: {{ segment.style || '真人写实, 电视风格, 暖色调' }}
        </div>

        <!-- Shots list -->
        <div class="space-y-5">
          <div
            v-for="(shot, idx) in segment.shots"
            :key="shot.id"
            class="cursor-pointer rounded-lg px-3 py-2 -mx-3 hover:bg-gray-50 transition-colors"
            @click="emit('selectShot', shot, idx)"
          >
            <!-- Shot header -->
            <div class="flex items-center gap-2 mb-1.5">
              <span class="text-[14px] font-medium text-gray-800">分镜{{ idx + 1 }}</span>
              <span class="text-[13px] text-gray-400">⊙ {{ shot.duration }}s</span>
              <span class="text-[13px] text-gray-400">; 时间: {{ shot.time_of_day }}</span>
            </div>

            <!-- Shot content as natural text -->
            <div class="text-[13px] text-gray-600 leading-[1.9]">
              <!-- Scene ref (紫色胶囊) -->
              <span v-if="shot.scene_ref" class="inline-flex items-center gap-1 bg-primary-50 text-primary-600 text-[12px] px-2 py-0.5 rounded-full mr-1">
                🖼 {{ shot.scene_ref }}
              </span>

              <!-- Camera info -->
              <span class="text-gray-500">镜头: {{ shot.camera_type || '中景' }}, </span>

              <!-- Character refs (紫色胶囊) -->
              <template v-if="shot.characters?.length">
                <span
                  v-for="char in shot.characters"
                  :key="char"
                  class="inline-flex items-center gap-1 bg-primary-50 text-primary-600 text-[12px] px-2 py-0.5 rounded-full mr-1"
                >🎭 {{ char }}</span>
              </template>

              <!-- Background/Action -->
              <span v-if="shot.background" class="text-gray-600">{{ shot.background }}</span>

              <!-- Dialogue -->
              <template v-if="shot.dialogue">
                <br />
                <span class="text-gray-500">台词: </span>
                <span class="text-gray-700">「{{ shot.dialogue }}」</span>
              </template>

              <!-- Voice -->
              <template v-if="shot.voice_style">
                <br />
                <span class="text-gray-400 text-[12px]">音色: {{ shot.voice_style }}</span>
              </template>

              <!-- Camera movement -->
              <template v-if="shot.camera_movement">
                <span class="text-gray-400 text-[12px]"> , 运镜: {{ shot.camera_movement }}</span>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-3">
        <button class="btn btn-outline btn-sm text-[13px]" @click="emit('editScript')">
          ✏️ 编辑脚本
        </button>
        <button class="btn btn-ghost btn-sm text-[13px]" @click="emit('regenerate')">
          🔄 再次生成
        </button>
      </div>
    </template>

    <!-- Empty state -->
    <div v-else class="flex flex-col items-center justify-center h-full">
      <div class="text-4xl mb-4">🎬</div>
      <p class="text-[14px] text-gray-500">选择一个片段开始编辑</p>
    </div>
  </div>
</template>
