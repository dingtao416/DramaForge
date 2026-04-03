<script setup lang="ts">
/**
 * ModalOverlay — 全屏覆盖式弹窗
 * 从中间淡入，背景深色遮罩
 */
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
      <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
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
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.modal-panel {
  width: 90%;
  max-height: 90vh;
  background: #fff;
  border-radius: 20px;
  overflow-y: auto;
  position: relative;
  padding: 40px 36px 36px;
}

.modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
  z-index: 2;
}

.modal-close:hover {
  background: #f5f5f5;
  color: #333;
}

.modal-header {
  text-align: center;
  margin-bottom: 32px;
}

.modal-title {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 6px;
  letter-spacing: -0.3px;
}

.modal-subtitle {
  font-size: 14px;
  color: #999;
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
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-panel {
  transform: scale(0.95);
  opacity: 0;
}

.modal-leave-to .modal-panel {
  transform: scale(0.95);
  opacity: 0;
}
</style>
