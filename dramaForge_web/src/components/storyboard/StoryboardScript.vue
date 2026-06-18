<script setup lang="ts">
import { computed } from 'vue'
import type { SegmentDetail } from '@/types/segment'
import type { ShotDetail } from '@/types/shot'

const props = defineProps<{
  segment: SegmentDetail | null
  segmentIndex: number
  generating?: boolean
  addingShot?: boolean
  deletingShotId?: number | null
}>()

const emit = defineEmits<{
  editScript: []
  regenerate: []
  generateSegment: []
  selectShot: [shot: ShotDetail, index: number]
  addShot: []
  deleteShot: [shotId: number]
}>()

const statusConfig: Record<string, { label: string; cls: string; icon: string }> = {
  pending:    { label: '待生成', cls: 'bg-gray-100 text-gray-500',       icon: '○' },
  generating: { label: '生成中', cls: 'bg-purple-50 text-purple-600',    icon: '◌' },
  completed:  { label: '已完成', cls: 'bg-green-50 text-green-600',       icon: '✓' },
  failed:     { label: '生成失败', cls: 'bg-red-50 text-red-600',         icon: '✕' },
}

const status = computed(() => {
  if (!props.segment) return null
  return statusConfig[props.segment.status] || statusConfig.pending
})
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
            <!-- Status badge -->
            <span
              v-if="status"
              class="inline-flex items-center gap-1 text-[12px] font-medium px-2.5 py-1 rounded-full"
              :class="status.cls"
            >
              <span v-if="segment.status === 'generating'" class="inline-block w-3 h-3 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
              <span v-else>{{ status.icon }}</span>
              {{ status.label }}
            </span>
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
          画面风格和类型: {{ (segment as any).style || '真人写实, 电视风格, 暖色调' }}
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
              <!-- Shot has image/video indicator -->
              <span v-if="shot.image_url" class="text-[11px] text-green-500 ml-auto">🖼</span>
              <span v-if="shot.video_url" class="text-[11px] text-green-500">🎬</span>
              <!-- Delete shot button -->
              <button
                class="shot-delete-btn"
                :disabled="deletingShotId === shot.id"
                title="删除此分镜"
                @click.stop="emit('deleteShot', shot.id)"
              >
                <svg v-if="deletingShotId === shot.id" class="animate-spin" width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
                  <path d="M6 1a5 5 0 013 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                <span v-else class="text-[11px] text-gray-300 hover:text-red-400">✕</span>
              </button>
            </div>

            <!-- Shot content as natural text -->
            <div class="text-[13px] text-gray-600 leading-[1.9]">
              <span v-if="shot.scene_ref" class="inline-flex items-center gap-1 bg-primary-50 text-primary-600 text-[12px] px-2 py-0.5 rounded-full mr-1">
                🖼 {{ shot.scene_ref }}
              </span>

              <span class="text-gray-500">镜头: {{ shot.camera_type || '中景' }}, </span>

              <template v-if="shot.characters?.length">
                <span
                  v-for="char in shot.characters"
                  :key="(char as any).char_id || char"
                  class="inline-flex items-center gap-1 bg-primary-50 text-primary-600 text-[12px] px-2 py-0.5 rounded-full mr-1"
                >🎭 {{ (char as any).name || char }}</span>
              </template>

              <span v-if="shot.background" class="text-gray-600">{{ shot.background }}</span>

              <template v-if="shot.dialogue">
                <br />
                <span class="text-gray-500">台词: </span>
                <span class="text-gray-700">「{{ shot.dialogue }}」</span>
              </template>

              <template v-if="shot.voice_style">
                <br />
                <span class="text-gray-400 text-[12px]">音色: {{ shot.voice_style }}</span>
              </template>

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

        <!-- Add shot -->
        <button
          class="btn btn-ghost btn-sm text-[13px]"
          :disabled="addingShot"
          @click="emit('addShot')"
        >
          <span v-if="addingShot" class="inline-block w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin mr-1" />
          <span v-else>➕</span>
          添加分镜
        </button>

        <!-- Generate button (PENDING) -->
        <button
          v-if="segment.status === 'pending'"
          class="btn btn-primary btn-sm text-[13px]"
          :disabled="generating"
          @click="emit('generateSegment')"
        >
          <svg v-if="generating" class="animate-spin" width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
            <path d="M7 1.5a5.5 5.5 0 015.1 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span v-else>🎬</span>
          {{ generating ? '生成中...' : '生成素材' }}
        </button>

        <!-- Regenerate button (COMPLETED or FAILED) -->
        <button
          v-if="segment.status === 'completed' || segment.status === 'failed'"
          class="btn btn-ghost btn-sm text-[13px]"
          @click="emit('regenerate')"
        >
          🔄 重新生成
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

<style scoped>
.shot-delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.15s;
  padding: 0;
  opacity: 0;
  flex-shrink: 0;
}
.cursor-pointer:hover .shot-delete-btn,
.shot-delete-btn:hover {
  opacity: 1;
}
.shot-delete-btn:hover {
  background: #FEE2E2;
}
.shot-delete-btn:disabled {
  opacity: 1;
  cursor: not-allowed;
}
</style>
