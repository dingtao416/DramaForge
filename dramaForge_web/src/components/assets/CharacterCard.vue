<script setup lang="ts">
import { computed } from 'vue'
import { CharacterRoleLabel, CharacterRole } from '@/types/enums'
import type { CharacterDetail } from '@/types/character'

const props = defineProps<{
  character: CharacterDetail
  regenerating?: boolean
}>()

const emit = defineEmits<{
  edit: [CharacterDetail]
  regenerate: [CharacterDetail]
}>()

const mainImage = computed(() => props.character.reference_images?.[0])
</script>

<template>
  <div class="char-card group">
    <!-- Image -->
    <div class="char-card-img">
      <img
        v-if="mainImage"
        :src="mainImage"
        :alt="character.name"
        class="w-full h-full object-cover transition-transform duration-400 group-hover:scale-105"
      />
      <div v-else class="char-card-placeholder">👤</div>

      <!-- Role badge -->
      <span
        v-if="character.role === CharacterRole.PROTAGONIST"
        class="char-role-badge"
      >主角</span>

      <!-- Action buttons — visible on hover -->
      <div class="char-card-actions">
        <button
          class="char-action-btn"
          title="编辑角色"
          @click.stop="emit('edit', character)"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M10 2.5l1.5 1.5L4.5 11H3V9.5L10 2.5z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <button
          class="char-action-btn"
          :class="{ 'char-action-spin': regenerating }"
          title="重新生成形象"
          :disabled="regenerating"
          @click.stop="emit('regenerate', character)"
        >
          <svg v-if="!regenerating" width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1.5 7A5.5 5.5 0 0112.17 5.5M12.5 7A5.5 5.5 0 011.83 8.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M12.17 5.5H9.5M1.83 8.5H4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
          <svg v-else class="animate-spin" width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.4" stroke-dasharray="24 8" stroke-linecap="round"/></svg>
        </button>
      </div>
    </div>

    <!-- Info -->
    <div class="char-card-info">
      <div class="char-card-name">{{ character.name }}</div>
      <div class="char-card-meta">
        {{ CharacterRoleLabel[character.role] || '配角' }} · {{ character.reference_images?.length || 0 }} 形象
      </div>
    </div>
  </div>
</template>

<style scoped>
.char-card {
  cursor: pointer;
}

.char-card-img {
  aspect-ratio: 3 / 4;
  background: #F3F4F6;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.char-card-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: #A89870;
}

.char-role-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 3px 10px;
  border-radius: 6px;
  background: #E8A317;
  color: #2D2515;
  font-size: 11px;
  font-weight: 600;
}

/* Action buttons — appear on hover */
.char-card-actions {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.2s, transform 0.2s;
  transform: translateX(-50%) translateY(6px);
}
.char-card:hover .char-card-actions {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
.char-card-actions:focus-within {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.char-action-btn {
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
.char-action-btn:hover {
  background: #FDF5D6;
  color: #E8A317;
  box-shadow: 0 4px 12px rgba(232, 163, 23, 0.2);
}
.char-action-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.char-action-spin {
  color: #E8A317 !important;
}

/* Info */
.char-card-info {
  margin-top: 10px;
  padding: 0 2px;
}
.char-card-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  line-height: 1.3;
}
.char-card-meta {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 2px;
}
</style>
