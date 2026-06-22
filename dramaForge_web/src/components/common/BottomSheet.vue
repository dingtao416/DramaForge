<script setup lang="ts">
import { watch } from 'vue'

const props = defineProps<{
  visible: boolean
  title?: string
  height?: string
}>()

const emit = defineEmits<{
  close: []
}>()

watch(() => props.visible, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="visible" class="sheet-overlay" @click.self="emit('close')">
        <div class="sheet-panel" :style="{ maxHeight: height || '80vh' }">
          <!-- Header -->
          <div class="sheet-header">
            <h3 class="sheet-title">{{ title }}</h3>
            <button class="sheet-close" @click="emit('close')">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M5 5l8 8M13 5l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
            </button>
          </div>
          <!-- Content -->
          <div class="sheet-body">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sheet-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  backdrop-filter: blur(2px);
}

.sheet-panel {
  width: 100%;
  max-width: 640px;
  background: #FDF5D6;
  border-top: 3px solid #F5C34B;
  border-radius: 2px 2px 0 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -4px 0 0 rgba(0, 0, 0, 0.3);
}

.sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 12px;
  flex-shrink: 0;
}

.sheet-title {
  font-size: 16px;
  font-family: 'Press Start 2P', monospace;
  color: #111111;
  margin: 0;
}

.sheet-close {
  width: 32px;
  height: 32px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6B5D40;
  cursor: pointer;
  transition: all 0.15s;
}

.sheet-close:hover {
  background: rgba(0,0,0,0.04);
  color: #F5C34B;
  border-color: #F5C34B;
}

.sheet-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
}

/* Transitions */
.sheet-enter-active,
.sheet-leave-active {
  transition: all 0.3s ease;
}

.sheet-enter-active .sheet-panel,
.sheet-leave-active .sheet-panel {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}

.sheet-enter-from .sheet-panel,
.sheet-leave-to .sheet-panel {
  transform: translateY(100%);
}
</style>
