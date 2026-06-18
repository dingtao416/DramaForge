<script setup lang="ts">
import { computed } from 'vue'
import { DEFAULT_SCENE_IMAGE } from '@/constants/defaultAssets'
import type { SceneDetail } from '@/types/scene'

const props = defineProps<{
  scene: SceneDetail
  regenerating?: boolean
}>()

const emit = defineEmits<{
  edit: [SceneDetail]
  regenerate: [SceneDetail]
}>()

const mainImage = computed(() => props.scene.reference_images?.[0])
</script>

<template>
  <div class="scene-card group">
    <!-- Image -->
    <div class="scene-card-img">
      <img
        v-if="mainImage"
        :src="mainImage"
        :alt="scene.name"
        class="w-full h-full object-cover transition-transform duration-400 group-hover:scale-105"
      />
      <img
        v-else
        :src="DEFAULT_SCENE_IMAGE"
        :alt="`${scene.name} 默认场景图`"
        class="w-full h-full object-cover transition-transform duration-400 group-hover:scale-105"
      />

      <!-- Action buttons -->
      <div class="scene-card-actions">
        <button
          class="scene-action-btn"
          title="编辑场景"
          @click.stop="emit('edit', scene)"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M10 2.5l1.5 1.5L4.5 11H3V9.5L10 2.5z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button
          class="scene-action-btn"
          :class="{ 'scene-action-spin': regenerating }"
          title="重新生成场景"
          :disabled="regenerating"
          @click.stop="emit('regenerate', scene)"
        >
          <svg v-if="!regenerating" width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1.5 7A5.5 5.5 0 0112.17 5.5M12.5 7A5.5 5.5 0 011.83 8.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M12.17 5.5H9.5M1.83 8.5H4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
          <svg v-else class="animate-spin" width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.4" stroke-dasharray="24 8" stroke-linecap="round"/></svg>
        </button>
      </div>
    </div>

    <!-- Info -->
    <div class="scene-card-info">
      <div class="scene-card-name">{{ scene.name }}</div>
      <div class="scene-card-meta">
        {{ scene.time_of_day === 'night' ? '🌙 夜景' : scene.time_of_day === 'dawn' ? '🌅 黎明' : scene.time_of_day === 'dusk' ? '🌆 黄昏' : '☀️ 日景' }}
        · {{ scene.interior ? '室内' : '室外' }}
        · {{ scene.reference_images?.length || 0 }} 图
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

.scene-card-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: #D1D5DB;
}

/* Action buttons */
.scene-card-actions {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%) translateY(6px);
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.2s, transform 0.2s;
}
.scene-card:hover .scene-card-actions {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
.scene-card-actions:focus-within {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.scene-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  color: #4B5563;
  cursor: pointer;
  transition: all 0.15s;
  backdrop-filter: blur(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.scene-action-btn:hover {
  background: #fff;
  color: #7C3AED;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.2);
}
.scene-action-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.scene-action-spin {
  color: #7C3AED !important;
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
