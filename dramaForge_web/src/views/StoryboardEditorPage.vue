<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStoryboardStore } from '@/stores/storyboard'
import { useAssetsStore } from '@/stores/assets'
import { storyboardApi } from '@/api/storyboard'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

const route = useRoute()
const router = useRouter()
const sbStore = useStoryboardStore()
const assetsStore = useAssetsStore()

const projectId = Number(route.params.id)
const episodeId = Number(route.params.epId)

onMounted(async () => {
  await Promise.all([
    sbStore.fetchStoryboard(projectId, episodeId),
    assetsStore.fetchAssets(projectId),
  ])
})

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const totalDuration = computed(() => sbStore.storyboard?.total_duration || 0)
</script>

<template>
  <LoadingOverlay :visible="sbStore.loading" message="正在加载分镜..." />

  <div class="h-[calc(100vh-56px)] flex flex-col">
    <!-- Top bar -->
    <div class="h-[48px] border-b border-gray-200 bg-white flex items-center px-5 shrink-0">
      <button
        class="flex items-center gap-1.5 text-[13px] text-gray-500 hover:text-gray-800 cursor-pointer transition-colors"
        @click="router.back()"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span>返回</span>
      </button>
      <div class="w-px h-5 bg-gray-200 mx-4" />
      <span class="text-[14px] font-semibold text-gray-900">
        {{ sbStore.storyboard?.episode_title || '分镜编辑器' }}
      </span>
      <div class="flex-1" />
      <div class="flex items-center gap-3">
        <select class="h-[34px] text-[13px] border border-gray-200 rounded-lg px-3 bg-white outline-none text-gray-700 cursor-pointer">
          <option>Seedance 2.0 · Fast</option>
          <option>veo-3.1-fast</option>
          <option>veo3</option>
        </select>
        <button class="btn btn-outline btn-sm">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 10l3 3h7V4L9 1H2v9z" stroke="currentColor" stroke-width="1.3"/><path d="M7 1v3h3" stroke="currentColor" stroke-width="1.3"/></svg>
          导出
        </button>
        <button class="btn btn-primary btn-sm">合成全集</button>
      </div>
    </div>

    <!-- Three-column layout + timeline -->
    <div class="flex-1 flex overflow-hidden">
      <!-- LEFT: Asset Panel -->
      <aside class="w-[220px] border-r border-gray-200 bg-white overflow-y-auto shrink-0">
        <div class="flex items-center justify-between px-4 py-3.5 border-b border-gray-100">
          <span class="text-[14px] font-semibold text-gray-900">资产库</span>
          <button class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 cursor-pointer transition-colors">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><line x1="8" y1="3" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="3" y1="8" x2="13" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
        </div>

        <div class="p-4">
          <!-- Characters -->
          <div class="mb-5">
            <div class="text-[12px] text-gray-400 font-medium mb-3 flex items-center gap-1.5">
              <span>👤</span> 角色 ({{ assetsStore.characters.length }})
            </div>
            <div class="grid grid-cols-2 gap-2.5">
              <div
                v-for="char in assetsStore.characters"
                :key="char.id"
                class="text-center cursor-pointer group"
              >
                <div class="w-full aspect-square bg-gray-100 rounded-[10px] overflow-hidden mb-1.5">
                  <img
                    v-if="char.reference_images?.[0]"
                    :src="char.reference_images[0]"
                    :alt="char.name"
                    class="w-full h-full object-cover transition-transform group-hover:scale-105"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center text-xl text-gray-300">👤</div>
                </div>
                <div class="text-[11px] text-gray-600 truncate px-0.5">{{ char.name }}</div>
              </div>
            </div>
          </div>

          <!-- Scenes -->
          <div>
            <div class="text-[12px] text-gray-400 font-medium mb-3 flex items-center gap-1.5">
              <span>🏠</span> 场景 ({{ assetsStore.scenes.length }})
            </div>
            <div class="space-y-2.5">
              <div
                v-for="scene in assetsStore.scenes"
                :key="scene.id"
                class="cursor-pointer group"
              >
                <div class="w-full aspect-[16/10] bg-gray-100 rounded-[10px] overflow-hidden mb-1.5">
                  <img
                    v-if="scene.reference_images?.[0]"
                    :src="scene.reference_images[0]"
                    :alt="scene.name"
                    class="w-full h-full object-cover transition-transform group-hover:scale-105"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center text-xl text-gray-300">🏠</div>
                </div>
                <div class="text-[11px] text-gray-600 truncate px-0.5">{{ scene.name }}</div>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- CENTER: Storyboard Script -->
      <div class="flex-1 overflow-y-auto bg-gray-50">
        <template v-if="sbStore.storyboard && sbStore.storyboard.segments.length">
          <div class="max-w-[720px] mx-auto px-6 py-6">
            <!-- Segment header -->
            <div class="flex items-center gap-3 mb-5">
              <h2 class="text-[16px] font-bold text-gray-900">
                片段 {{ sbStore.currentSegmentIndex + 1 }}
              </h2>
              <span class="text-[12px] text-gray-400 leading-relaxed">
                片段时长请限制在4-15s，输入"@"可快速调整镜头时长、引用角色、场景、素材
              </span>
            </div>

            <!-- Segment script area -->
            <div class="bg-white border border-gray-200 rounded-[14px] p-6 mb-5">
              <template v-if="sbStore.currentSegment">
                <div v-for="(shot, idx) in sbStore.currentSegment.shots" :key="shot.id" class="mb-7 last:mb-0">
                  <div class="flex items-center gap-2.5 mb-2.5">
                    <span class="text-[14px] font-semibold text-gray-800">分镜{{ idx + 1 }}</span>
                    <span class="text-[12px] text-gray-400 flex items-center gap-1">
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.2"/><path d="M6 3.5V6.5L8 8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
                      {{ shot.duration }}s
                    </span>
                    <span class="text-[12px] text-gray-400">时间：{{ shot.time_of_day }}</span>
                    <span class="text-[12px] text-gray-400">场景图片：{{ shot.scene_ref || '无' }}</span>
                  </div>

                  <div class="text-[14px] text-gray-600 leading-[1.9] pl-5 border-l-2 border-primary-200 ml-0.5">
                    <p v-if="shot.background" class="mb-1.5">{{ shot.background }}</p>
                    <p v-if="shot.dialogue" class="mb-1.5">
                      <span class="text-gray-400">台词：</span>
                      <span class="text-gray-700">「{{ shot.dialogue }}」</span>
                    </p>
                    <p v-if="shot.voice_style" class="text-[12px] text-gray-400">
                      音色：{{ shot.voice_style }}
                    </p>
                  </div>
                </div>
              </template>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-3">
              <button class="btn btn-outline btn-sm">✏️ 编辑脚本</button>
              <button class="btn btn-primary btn-sm">🔄 再次生成</button>
            </div>
          </div>
        </template>

        <!-- Empty state for no storyboard -->
        <div v-else-if="!sbStore.loading" class="flex flex-col items-center justify-center h-full">
          <div class="text-5xl mb-5">🎬</div>
          <p class="text-[15px] text-gray-500 mb-5">尚未生成分镜脚本</p>
          <button class="btn btn-primary" @click="sbStore.generateStoryboard(projectId, episodeId)">
            生成分镜脚本
          </button>
        </div>
      </div>

      <!-- RIGHT: Preview Panel -->
      <aside class="w-[340px] border-l border-gray-200 bg-white overflow-y-auto shrink-0">
        <!-- Video player area -->
        <div class="aspect-[9/16] bg-black relative">
          <div v-if="sbStore.currentShot?.video_url">
            <video
              :src="sbStore.currentShot.video_url"
              controls
              class="w-full h-full object-contain"
            />
          </div>
          <div v-else-if="sbStore.currentShot?.image_url">
            <img :src="sbStore.currentShot.image_url" class="w-full h-full object-contain" />
          </div>
          <div v-else class="w-full h-full flex items-center justify-center text-gray-500 text-[14px]">
            暂无预览
          </div>

          <!-- Playback controls -->
          <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 p-4">
            <div class="flex items-center gap-2.5 text-white text-[13px]">
              <button class="cursor-pointer hover:text-primary-300 transition-colors">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M4 2.5L13 8L4 13.5V2.5Z"/></svg>
              </button>
              <span>00:00</span>
              <div class="flex-1 h-1 bg-white/30 rounded-full overflow-hidden">
                <div class="h-full bg-white rounded-full" style="width: 0%" />
              </div>
              <span>00:15</span>
            </div>
          </div>
        </div>

        <!-- Shot detail -->
        <div v-if="sbStore.currentShot" class="p-5">
          <h3 class="text-[14px] font-semibold text-gray-900 mb-4">分镜详情</h3>
          <div class="space-y-3.5">
            <div class="flex justify-between items-center">
              <span class="text-[13px] text-gray-400">镜头</span>
              <span class="text-[13px] text-gray-700 font-medium">{{ sbStore.currentShot.camera_type }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[13px] text-gray-400">运镜</span>
              <span class="text-[13px] text-gray-700 font-medium">{{ sbStore.currentShot.camera_movement }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[13px] text-gray-400">时长</span>
              <span class="text-[13px] text-gray-700 font-medium">{{ sbStore.currentShot.duration }}s</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-[13px] text-gray-400">过渡</span>
              <span class="text-[13px] text-gray-700 font-medium">{{ sbStore.currentShot.transition }}</span>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- BOTTOM: Timeline -->
    <div class="h-[140px] border-t border-gray-200 bg-white shrink-0 px-5 py-3 flex flex-col">
      <!-- Playback bar -->
      <div class="flex items-center gap-3 mb-2.5">
        <button class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200 cursor-pointer transition-colors">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><path d="M3.5 2L11.5 7L3.5 12V2Z"/></svg>
        </button>
        <span class="text-[13px] text-gray-500 tabular-nums">00:00 / {{ formatDuration(totalDuration) }}</span>
        <div class="flex-1" />
        <button class="h-[30px] px-3 rounded-lg text-[12px] text-gray-500 border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors bg-white flex items-center gap-1.5">
          🔀 多选
        </button>
      </div>

      <!-- Segments horizontal scroll -->
      <div class="flex-1 flex gap-2.5 overflow-x-auto pb-1">
        <div
          v-for="(seg, idx) in sbStore.storyboard?.segments || []"
          :key="seg.id"
          class="shrink-0 w-[120px] rounded-[10px] overflow-hidden border-2 cursor-pointer transition-all"
          :class="idx === sbStore.currentSegmentIndex
            ? 'border-primary-500 shadow-[0_0_0_1px_rgba(124,58,237,0.2)]'
            : 'border-transparent hover:border-gray-300'"
          @click="sbStore.selectSegment(idx)"
        >
          <!-- Thumbnail -->
          <div class="h-[68px] bg-gray-100 relative flex items-center justify-center text-[12px] text-gray-400">
            <img
              v-if="seg.thumbnail_url"
              :src="seg.thumbnail_url"
              class="w-full h-full object-cover"
            />
            <span v-else>片段{{ idx + 1 }}</span>

            <!-- Segment number badge -->
            <span class="absolute top-1.5 left-1.5 bg-primary-500 text-white text-[10px] px-1.5 py-0.5 rounded-md font-medium">
              {{ idx + 1 }}
            </span>
          </div>

          <!-- Duration -->
          <div class="text-center text-[11px] text-gray-500 py-1.5 bg-white">
            {{ seg.duration ? formatDuration(seg.duration) : '--:--' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>