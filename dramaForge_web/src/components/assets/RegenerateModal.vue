<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
  type: 'character' | 'scene'
  name: string
  description: string
  loading: boolean
  currentPrompt: string
}>()

const emit = defineEmits<{
  close: []
  confirm: [prompt: string]
}>()

const customPrompt = ref('')

watch(() => props.visible, (v) => {
  if (v) {
    customPrompt.value = props.currentPrompt || ''
  }
})

function handleConfirm() {
  emit('confirm', customPrompt.value.trim() || '')
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
                {{ type === 'character' ? '重新生成角色形象' : '重新生成场景图' }}
              </h3>
              <p class="reg-subtitle">{{ name }}</p>
            </div>
            <button v-if="!loading" class="reg-close" @click="emit('close')">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
            </button>
          </div>

          <!-- Body -->
          <div class="reg-body">
            <div class="reg-field">
              <label class="reg-label">
                {{ type === 'character' ? '形象描述（可选）' : '场景描述（可选）' }}
              </label>
              <p class="reg-hint">留空则使用原始描述自动生成。修改描述可调整生成效果。</p>
              <textarea
                v-model="customPrompt"
                class="reg-textarea"
                :placeholder="type === 'character'
                  ? '例如：25岁女性，长发及腰，气质优雅，穿着白色连衣裙，站在樱花树下...'
                  : '例如：现代都市写字楼大厅，玻璃幕墙，极简风格，阳光透过落地窗洒入...'"
                rows="4"
                :disabled="loading"
              />
            </div>
          </div>

          <!-- Progress -->
          <div v-if="loading" class="reg-progress">
            <div class="reg-spinner" />
            <span>正在生成中，请稍候...</span>
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
              {{ loading ? '生成中...' : '重新生成' }}
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
  background: #fff;
  border-radius: 18px;
  width: 460px;
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
  background: #F5F3FF;
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
  padding: 12px 14px;
  border: 1.5px solid #E5E7EB;
  border-radius: 10px;
  font-size: 14px;
  color: #374151;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
  font-family: inherit;
  line-height: 1.7;
  box-sizing: border-box;
}
.reg-textarea:focus {
  border-color: #A78BFA;
}
.reg-textarea::placeholder {
  color: #D1D5DB;
}

.reg-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 24px 16px;
  color: #7C3AED;
  font-size: 13px;
  font-weight: 500;
}
.reg-spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid #EDE9FE;
  border-top-color: #7C3AED;
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
