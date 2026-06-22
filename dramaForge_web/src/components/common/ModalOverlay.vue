<script setup lang="ts">
import { watch } from 'vue'

const props = defineProps<{
  visible: boolean
  title?: string
  subtitle?: string
  width?: string
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
    <Transition name="modal">
      <div v-if="visible" class="modal-overlay" >
        <div class="modal-panel" :style="{ maxWidth: width || '960px' }">
          <!-- Close button (top-right) -->
          <button class="modal-close" @click="emit('close')">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M5 5l10 10M15 5L5 15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          </button>
          <!-- Header -->
          <div v-if="title || subtitle" class="modal-header">
            <slot name="icon" />
            <h2 v-if="title" class="modal-title">{{ title }}</h2>
            <p v-if="subtitle" class="modal-subtitle">{{ subtitle }}</p>
          </div>
          <!-- Content -->
          <div class="modal-body">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.modal-panel {
  width: 90%;
  max-height: 90vh;
  background: #FDF5D6;
  border: 3px solid #F5C34B;
  border-radius: 2px;
  overflow-y: auto;
  position: relative;
  padding: 40px 36px 36px;
  box-shadow: 8px 8px 0 0 rgba(0, 0, 0, 0.5);
}

.modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6B5D40;
  cursor: pointer;
  transition: all 0.15s;
  z-index: 2;
}

.modal-close:hover {
  background: rgba(0,0,0,0.04);
  color: #F5C34B;
  border-color: #F5C34B;
}

.modal-header {
  text-align: center;
  margin-bottom: 32px;
}

.modal-title {
  font-size: 20px;
  font-family: 'Press Start 2P', monospace;
  color: #111111;
  margin: 0 0 6px;
  letter-spacing: 2px;
}

.modal-subtitle {
  font-size: 14px;
  color: #6B5D40;
  margin: 0;
}

.modal-body {
  /* content fills here */
}

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-active .modal-panel,
.modal-leave-active .modal-panel {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-panel {
  transform: scale(0.9);
  opacity: 0;
}

.modal-leave-to .modal-panel {
  transform: scale(0.9);
  opacity: 0;
}
</style>
