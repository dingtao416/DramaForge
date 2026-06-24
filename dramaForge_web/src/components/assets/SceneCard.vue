<script setup lang="ts">
import { computed } from 'vue'
import { DEFAULT_SCENE_IMAGE } from '@/constants/defaultAssets'
import type { SceneDetail } from '@/types/scene'

const props = defineProps<{
  scene: SceneDetail
}>()

const emit = defineEmits<{
  openGallery: [SceneDetail]
}>()

const mainImage = computed(() => {
  const imgs = props.scene.reference_images || []
  if (!imgs.length) return null
  return typeof imgs[0] === 'string' ? imgs[0] : (imgs[0] as any).url || imgs[0]
})
const imageCount = computed(() => props.scene.reference_images?.length || 0)
</script>

<template>
  <div class="scene-card group" @click="emit('openGallery', scene)">
    <!-- Image -->
    <div class="scene-card-img">
      <div class="scene-img-hover-hint">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="11" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="3" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="11" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/></svg>
        <span class="text-[11px] mt-1">查看全部</span>
      </div>
      <img
        v-if="mainImage"
        :src="mainImage"
        :alt="scene.name"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-400"
      />
      <img
        v-else
        :src="DEFAULT_SCENE_IMAGE"
        :alt="`${scene.name} 默认场景图`"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-400"
      />

      <!-- Image count badge -->
      <span v-if="imageCount > 0" class="scene-img-count">{{ imageCount }}图</span>
    </div>

    <!-- Info -->
    <div class="scene-card-info">
      <div class="scene-card-name">{{ scene.name }}</div>
      <div class="scene-card-meta">
        {{ scene.time_of_day === 'night' ? '🌙 夜景' : scene.time_of_day === 'dawn' ? '🌅 黎明' : scene.time_of_day === 'dusk' ? '🌆 黄昏' : '☀️ 日景' }}
        · {{ scene.interior ? '室内' : '室外' }}
        · {{ imageCount }} 图
      </div>
    </div>
  </div>
</template>

<style scoped>
.scene-card {
  cursor: pointer;
}

.scene-card-img {
  aspect-ratio: 16 / 10;
  background: #F3F4F6;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

/* Hover hint */
.scene-img-hover-hint {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s;
  z-index: 3;
}
.scene-card-img:hover .scene-img-hover-hint {
  opacity: 1;
}

.scene-img-count {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 100px;
  background: rgba(0,0,0,0.55);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

/* Info */
.scene-card-info {
  margin-top: 10px;
  padding: 0 2px;
}
.scene-card-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  line-height: 1.3;
}
.scene-card-meta {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 3px;
}
</style>
