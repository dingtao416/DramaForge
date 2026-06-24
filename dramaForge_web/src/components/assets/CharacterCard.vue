<script setup lang="ts">
import { computed } from 'vue'
import { CharacterRoleLabel, CharacterRole } from '@/types/enums'
import type { CharacterDetail } from '@/types/character'

const props = defineProps<{
  character: CharacterDetail
}>()

const emit = defineEmits<{
  openGallery: [CharacterDetail]
}>()

const mainImage = computed(() => {
  const imgs = props.character.reference_images || []
  if (!imgs.length) return null
  const primary = imgs.find(img => img.is_primary)
  return primary?.url || imgs[0]?.url
})
const imageCount = computed(() => props.character.reference_images?.length || 0)
</script>

<template>
  <div class="char-card group">
    <!-- Image area — click to open gallery -->
    <div class="char-card-img" @click.stop="emit('openGallery', character)">
      <!-- Hover hint -->
      <div class="char-img-hover-hint">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="11" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="3" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="11" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/></svg>
        <span class="text-[11px] mt-1">查看全部</span>
      </div>
      <img
        v-if="mainImage"
        :src="mainImage"
        :alt="character.name"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-400"
      />
      <div v-else class="char-card-placeholder">👤</div>

      <!-- Role badge -->
      <span
        v-if="character.role === CharacterRole.PROTAGONIST"
        class="char-role-badge"
      >主角</span>

      <!-- Image count badge -->
      <span v-if="imageCount > 0" class="char-img-count">{{ imageCount }}图</span>
    </div>

    <!-- Info -->
    <div class="char-card-info">
      <div class="char-card-name">{{ character.name }}</div>
      <div class="char-card-meta">
        {{ CharacterRoleLabel[character.role] || '配角' }} · {{ imageCount }} 形象
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
  background: #FDF4D8;
  border-radius: 2px;
  border: 2px solid #D4C898;
  position: relative;
  overflow: hidden;
  box-shadow: 3px 3px 0 0 rgba(0,0,0,0.08);
  cursor: pointer;
}

/* Hover hint over image */
.char-img-hover-hint {
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
.char-card-img:hover .char-img-hover-hint {
  opacity: 1;
}

.char-card-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: #A89870;
}

.char-role-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 3px 10px;
  border-radius: 2px;
  background: #E8A317;
  color: #1A1508;
  font-family: 'Press Start 2P', monospace;
  font-size: 9px;
  letter-spacing: 1px;
  border: 2px solid #C88A0C;
}

.char-img-count {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 2px;
  background: rgba(0,0,0,0.55);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

/* Info */
.char-card-info {
  margin-top: 10px;
  padding: 0 2px;
}
.char-card-name {
  font-size: 14px;
  font-weight: 600;
  color: #2D2515;
  line-height: 1.3;
}
.char-card-meta {
  font-size: 12px;
  color: #8B7A5A;
  margin-top: 2px;
}
</style>
