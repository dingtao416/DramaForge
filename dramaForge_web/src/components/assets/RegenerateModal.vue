<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
  type: 'character' | 'scene'
  name: string
  description: string
  loading: boolean
  currentPrompt: string
  /** Visual group description (形象描述) */
  visualDescription?: string
  /** Character-level description for context */
  characterDescription?: string
}>()

const emit = defineEmits<{
  close: []
  confirm: [data: { prompt: string; visualDescription: string; optimizePrompt: boolean }]
}>()

const customPrompt = ref('')
const visualDesc = ref('')
const useOptimize = ref(true)

watch(() => props.visible, (v) => {
  if (v) {
    customPrompt.value = props.currentPrompt || ''
    visualDesc.value = props.visualDescription || ''
    useOptimize.value = true
  }
})

function handleConfirm() {
  emit('confirm', {
    prompt: customPrompt.value.trim(),
    visualDescription: visualDesc.value.trim(),
    optimizePrompt: useOptimize.value,
  })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="reg-overlay" @click.self="!loading && emit('close')">
        <div class="reg-panel">
          <!-- Header -->
          <div class="reg-header">
            <div class="reg-header-icon">
              {{ type === 'character' ? '👤' : '🏠' }}
            </div>
            <div>
              <h3 class="reg-title">
                {{ type === 'character' ? 'AI 生成角色形象' : '重新生成场景图' }}
              </h3>
              <p class="reg-subtitle">{{ name }}</p>
            </div>
            <button v-if="!loading" class="reg-close" @click="emit('close')">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
            </button>
          </div>

          <!-- Body -->
          <div class="reg-body">
            <!-- Visual description -->
            <div class="reg-field">
              <label class="reg-label">形象描述</label>
              <p class="reg-hint">描述当前形象的外观特征，AI 会结合角色背景生成合适的图片</p>
              <textarea
                v-model="visualDesc"
                class="reg-textarea"
                placeholder="例如：正面视角，微笑表情，白色长裙，柔和自然光..."
                rows="2"
                :disabled="loading"
              />
            </div>

            <!-- User extra guidance -->
            <div class="reg-field">
              <label class="reg-label">额外指引（可选）</label>
              <p class="reg-hint">补充其他对生成图片的要求</p>
              <textarea
                v-model="customPrompt"
                class="reg-textarea"
                placeholder="例如：背景是在花园里，画面偏暖色调..."
                rows="2"
                :disabled="loading"
              />
            </div>

            <!-- AI Optimization toggle -->
            <div v-if="type === 'character'" class="reg-optimize">
              <label class="reg-optimize-label" :class="{ disabled: loading }">
                <input
                  v-model="useOptimize"
                  type="checkbox"
                  class="reg-optimize-check"
                  :disabled="loading"
                />
                <span class="reg-optimize-text">
                  <span class="reg-optimize-title">AI 提示词优化</span>
                  <span class="reg-optimize-hint">使用文本 LLM 将角色描述 + 形象描述融合优化为高质量英文图像提示词</span>
                </span>
              </label>
            </div>

            <!-- Character context preview -->
            <div v-if="characterDescription && type === 'character'" class="reg-context">
              <div class="reg-context-label">角色背景参考</div>
              <div class="reg-context-text">{{ characterDescription }}</div>
            </div>
          </div>

          <!-- Progress -->
          <div v-if="loading" class="reg-progress">
            <div class="reg-spinner" />
            <span>{{ useOptimize ? 'AI 正在优化提示词并生成图片...' : '正在生成中，请稍候...' }}</span>
          </div>

          <!-- Footer -->
          <div class="reg-footer">
            <button
              class="btn btn-ghost btn-sm"
              :disabled="loading"
              @click="emit('close')"
            >取消</button>
            <button
              class="btn btn-primary btn-sm"
              :disabled="loading"
              @click="handleConfirm"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1.5 7A5.5 5.5 0 0112.17 5.5M12.5 7A5.5 5.5 0 011.83 8.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M12.17 5.5H9.5M1.83 8.5H4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
              {{ loading ? '生成中...' : '开始生成' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.reg-overlay {
  position: fixed;
  inset: 0;
  z-index: 120;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.reg-panel {
  background: #FDF5D6;
  border-radius: 18px;
  width: 500px;
  max-width: 92vw;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

.reg-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 24px 24px 0;
}
.reg-header-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(232, 163, 23, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.reg-title {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}
.reg-subtitle {
  font-size: 13px;
  color: #9CA3AF;
  margin: 2px 0 0;
}
.reg-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9CA3AF;
  cursor: pointer;
  margin-left: auto;
  flex-shrink: 0;
}
.reg-close:hover {
  background: #F3F4F6;
  color: #374151;
}

.reg-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.reg-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.reg-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}
.reg-hint {
  font-size: 12px;
  color: #9CA3AF;
  margin: 0;
}
.reg-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1.5px solid #E5E7EB;
  border-radius: 10px;
  font-size: 13px;
  color: #374151;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
  font-family: var(--font-sans);
  line-height: 1.6;
  box-sizing: border-box;
  background: #fff;
}
.reg-textarea:focus {
  border-color: #F5C34B;
}
.reg-textarea::placeholder {
  color: #A89870;
}

/* ── AI Optimization toggle ── */
.reg-optimize {
  padding: 12px 14px;
  background: rgba(232, 163, 23, 0.06);
  border: 1.5px solid rgba(232, 163, 23, 0.2);
  border-radius: 10px;
}
.reg-optimize-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
}
.reg-optimize-label.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
.reg-optimize-check {
  margin-top: 2px;
  width: 16px; height: 16px;
  accent-color: #E8A317;
  flex-shrink: 0;
}
.reg-optimize-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.reg-optimize-title {
  font-size: 13px;
  font-weight: 600;
  color: #2D2515;
}
.reg-optimize-hint {
  font-size: 11px;
  color: #8B7A5A;
  line-height: 1.4;
}

/* ── Character context ── */
.reg-context {
  padding: 10px 12px;
  background: #F3F4F6;
  border-radius: 8px;
}
.reg-context-label {
  font-size: 11px;
  font-weight: 600;
  color: #9CA3AF;
  margin-bottom: 4px;
}
.reg-context-text {
  font-size: 12px;
  color: #6B7280;
  line-height: 1.5;
  max-height: 80px;
  overflow-y: auto;
}

.reg-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 24px 16px;
  color: #E8A317;
  font-size: 13px;
  font-weight: 500;
}
.reg-spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid rgba(232, 163, 23, 0.1);
  border-top-color: #E8A317;
  border-radius: 50%;
  animation: regSpin 0.6s linear infinite;
}
@keyframes regSpin {
  to { transform: rotate(360deg); }
}

.reg-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px 18px;
  border-top: 1px solid #F3F4F6;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
