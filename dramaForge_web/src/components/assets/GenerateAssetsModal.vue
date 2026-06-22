<script setup lang="ts">
import { ref, computed } from 'vue'
import { VideoStyle, VideoStyleLabel } from '@/types/enums'

const props = defineProps<{
  visible: boolean
  generating: boolean
  progress: string
  charCount: number
  sceneCount: number
}>()

const emit = defineEmits<{
  close: []
  generate: [options: { style: string; target: 'all' | 'characters' | 'scenes' }]
}>()

const selectedStyle = ref<VideoStyle>(VideoStyle.REALISTIC)
const selectedTarget = ref<'all' | 'characters' | 'scenes'>('all')

const styleOptions = Object.entries(VideoStyleLabel) as [VideoStyle, string][]

const styleEmoji: Record<VideoStyle, string> = {
  [VideoStyle.REALISTIC]: '📸',
  [VideoStyle.ANIME]: '🎌',
  [VideoStyle.CARTOON]: '🎮',
  [VideoStyle.CINEMATIC]: '🎬',
  [VideoStyle.WATERCOLOR]: '🎨',
  [VideoStyle.INK_WASH]: '🖌',
}

const targetLabel = computed(() => {
  switch (selectedTarget.value) {
    case 'all': return `全部（${props.charCount} 角色 + ${props.sceneCount} 场景）`
    case 'characters': return `仅角色（${props.charCount} 个）`
    case 'scenes': return `仅场景（${props.sceneCount} 个）`
  }
})

function handleGenerate() {
  emit('generate', {
    style: selectedStyle.value,
    target: selectedTarget.value,
  })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="gen-overlay">
        <div class="gen-panel">
          <!-- Header -->
          <div class="gen-header">
            <div>
              <h3 class="gen-title">生成角色 & 场景</h3>
              <p class="gen-subtitle">基于剧本内容，AI 自动生成角色形象和场景图</p>
            </div>
            <button v-if="!generating" class="gen-close" @click="emit('close')">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
            </button>
          </div>

          <!-- Body — config or progress -->
          <div v-if="!generating" class="gen-body">
            <!-- Visual style -->
            <div class="gen-section">
              <label class="gen-label">视觉风格</label>
              <div class="gen-style-grid">
                <button
                  v-for="[key, label] in styleOptions"
                  :key="key"
                  class="gen-style-card"
                  :class="{ active: selectedStyle === key }"
                  @click="selectedStyle = key"
                >
                  <span class="gen-style-icon">
                    {{ styleEmoji[key] || '🎨' }}
                  </span>
                  <span class="gen-style-label">{{ label }}</span>
                </button>
              </div>
            </div>

            <!-- Target -->
            <div class="gen-section">
              <label class="gen-label">生成范围</label>
              <div class="gen-target-row">
                <button
                  v-for="opt in [
                    { key: 'all' as const, label: '全部' },
                    { key: 'characters' as const, label: '仅角色' },
                    { key: 'scenes' as const, label: '仅场景' },
                  ]"
                  :key="opt.key"
                  class="gen-target-btn"
                  :class="{ active: selectedTarget === opt.key }"
                  @click="selectedTarget = opt.key"
                >{{ opt.label }}</button>
              </div>
              <p class="gen-target-hint">{{ targetLabel }}</p>
            </div>
          </div>

          <!-- Progress -->
          <div v-else class="gen-progress">
            <div class="gen-progress-icon">🤖</div>
            <div class="gen-progress-spinner" />
            <p class="gen-progress-text">{{ progress || '正在生成中...' }}</p>
            <div class="gen-progress-bar">
              <div class="gen-progress-fill" />
            </div>
          </div>

          <!-- Footer -->
          <div class="gen-footer">
            <button
              v-if="!generating"
              class="btn btn-ghost"
              @click="emit('close')"
            >取消</button>
            <button
              v-if="!generating"
              class="btn btn-primary"
              style="min-width: 140px;"
              @click="handleGenerate"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M13.5 2.5l-4 4M8.5 2.5h5v5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 3H3.5a1 1 0 00-1 1v8.5a1 1 0 001 1H12a1 1 0 001-1V10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
              开始生成
            </button>
            <p v-if="!generating" class="gen-footer-hint">将消耗图片生成额度</p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ── Overlay ── */
.gen-overlay {
  position: fixed;
  inset: 0;
  z-index: 110;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── Panel ── */
.gen-panel {
  background: #FDF5D6;
  border-radius: 20px;
  width: 520px;
  max-width: 92vw;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

/* ── Header ── */
.gen-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 28px 28px 0;
}
.gen-title {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}
.gen-subtitle {
  font-size: 13px;
  color: #9CA3AF;
  margin: 4px 0 0;
}
.gen-close {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9CA3AF;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}
.gen-close:hover {
  background: #F3F4F6;
  color: #374151;
}

/* ── Body ── */
.gen-body {
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.gen-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.gen-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

/* Style grid */
.gen-style-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.gen-style-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 8px;
  border-radius: 12px;
  border: 2px solid #E5E7EB;
  background: #FDF5D6;
  cursor: pointer;
  transition: all 0.2s;
}
.gen-style-card:hover {
  border-color: #A89870;
  background: #F9FAFB;
}
.gen-style-card.active {
  border-color: #E8A317;
  background: rgba(232, 163, 23, 0.08);
}
.gen-style-icon {
  font-size: 24px;
  line-height: 1;
}
.gen-style-label {
  font-size: 12px;
  font-weight: 600;
  color: #6B7280;
}
.gen-style-card.active .gen-style-label {
  color: #E8A317;
}

/* Target */
.gen-target-row {
  display: flex;
  gap: 8px;
}
.gen-target-btn {
  flex: 1;
  padding: 10px 0;
  border-radius: 10px;
  border: 2px solid #E5E7EB;
  background: #FDF5D6;
  font-size: 14px;
  font-weight: 600;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.2s;
}
.gen-target-btn:hover {
  border-color: #A89870;
}
.gen-target-btn.active {
  border-color: #E8A317;
  background: rgba(232, 163, 23, 0.08);
  color: #E8A317;
}
.gen-target-hint {
  font-size: 12px;
  color: #9CA3AF;
  margin: 0;
}

/* ── Progress ── */
.gen-progress {
  padding: 40px 28px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.gen-progress-icon {
  font-size: 48px;
}
.gen-progress-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid rgba(232, 163, 23, 0.1);
  border-top-color: #E8A317;
  border-radius: 50%;
  animation: genSpin 0.7s linear infinite;
}
@keyframes genSpin {
  to { transform: rotate(360deg); }
}
.gen-progress-text {
  font-size: 14px;
  font-weight: 600;
  color: #E8A317;
  margin: 0;
  text-align: center;
}
.gen-progress-bar {
  width: 100%;
  height: 4px;
  background: #F3F4F6;
  border-radius: 2px;
  overflow: hidden;
}
.gen-progress-fill {
  height: 100%;
  width: 60%;
  background: linear-gradient(90deg, #F5C34B, #E8A317);
  border-radius: 2px;
  animation: genBarPulse 1.2s ease-in-out infinite;
}
@keyframes genBarPulse {
  0%, 100% { width: 20%; }
  50% { width: 85%; }
}

/* ── Footer ── */
.gen-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 28px 20px;
  border-top: 1px solid #F3F4F6;
}
.gen-footer-hint {
  font-size: 12px;
  color: #9CA3AF;
  margin: 0;
  margin-right: auto;
}

/* ── Modal transition ── */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}
.modal-enter-active .gen-panel,
.modal-leave-active .gen-panel {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .gen-panel {
  transform: scale(0.95) translateY(8px);
  opacity: 0;
}
.modal-leave-to .gen-panel {
  transform: scale(0.95) translateY(8px);
  opacity: 0;
}
</style>
