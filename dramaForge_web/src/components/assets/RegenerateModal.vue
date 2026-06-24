<script setup lang="ts">
import { ref, watch } from 'vue'
import { assetsApi } from '@/api/assets'

const props = defineProps<{
  visible: boolean
  type: 'character' | 'scene'
  name: string
  projectId: number
  charId?: number
  sceneId?: number
  visualDescription?: string
  visualName?: string
}>()

const emit = defineEmits<{
  close: []
  generated: []
}>()

// ── State ──
const visualDesc = ref('')
const extraGuidance = ref('')
const optimizing = ref(false)
const generating = ref(false)
const optimizedPrompt = ref('')
const editedPrompt = ref('')
const errorMsg = ref('')
const successMsg = ref('')

watch(() => props.visible, (v) => {
  if (v) {
    visualDesc.value = props.visualDescription || ''
    extraGuidance.value = ''
    optimizedPrompt.value = ''
    editedPrompt.value = ''
    optimizing.value = false
    generating.value = false
    errorMsg.value = ''
    successMsg.value = ''
  }
})

const busy = ref(false) // combined loading state

// ── Optimize ──
async function handleOptimize() {
  if (!props.charId || !props.projectId) return
  optimizing.value = true
  errorMsg.value = ''
  try {
    const { data } = await assetsApi.optimizeCharacterPrompt(
      props.projectId, props.charId,
      { visual_name: props.visualName || '默认形象', visual_description: visualDesc.value, extra_guidance: extraGuidance.value },
    )
    optimizedPrompt.value = data.optimized_prompt
    editedPrompt.value = data.optimized_prompt
  } catch (e: any) {
    errorMsg.value = '提示词优化失败：' + (e.response?.data?.detail || e.message)
  } finally {
    optimizing.value = false
  }
}

// ── Generate (called by both optimized and direct paths) ──
async function doGenerate(prompt: string) {
  generating.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    if (props.type === 'character' && props.charId) {
      await assetsApi.regenerateCharacter(props.projectId, props.charId, prompt || undefined, visualDesc.value || undefined, false)
    } else if (props.sceneId) {
      await assetsApi.regenerateScene(props.projectId, props.sceneId, prompt || undefined)
    }
    successMsg.value = '生成完成！'
    emit('generated')
    // Auto close after short delay
    setTimeout(() => emit('close'), 1200)
  } catch (e: any) {
    errorMsg.value = '生成失败：' + (e.response?.data?.detail || e.message)
  } finally {
    generating.value = false
  }
}

function handleGenerate() {
  doGenerate(editedPrompt.value.trim() || optimizedPrompt.value.trim())
}

function handleDirectGenerate() {
  const prompt = [visualDesc.value, extraGuidance.value].filter(Boolean).join('. ')
  doGenerate(prompt)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="reg-overlay" @click.self="!generating && !optimizing && emit('close')">
        <div class="reg-panel">
          <!-- Header -->
          <div class="reg-header">
            <div class="reg-header-icon">{{ type === 'character' ? '👤' : '🏠' }}</div>
            <div>
              <h3 class="reg-title">{{ type === 'character' ? 'AI 生成角色形象' : '重新生成场景图' }}</h3>
              <p class="reg-subtitle">{{ name }}</p>
            </div>
            <button v-if="!generating && !optimizing" class="reg-close" @click="emit('close')">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
            </button>
          </div>

          <div class="reg-body">
            <template v-if="type === 'character'">
              <!-- Visual description -->
              <div class="reg-field">
                <label class="reg-label">形象描述</label>
                <p class="reg-hint">描述当前形象的外观特征</p>
                <textarea v-model="visualDesc" class="reg-textarea" placeholder="例如：正面视角，微笑表情，白色长裙，柔和自然光..." rows="2" :disabled="generating || optimizing" />
              </div>
              <div class="reg-field">
                <label class="reg-label">补充指引（可选）</label>
                <textarea v-model="extraGuidance" class="reg-textarea" placeholder="例如：背景在花园里，画面偏暖色调，柔焦效果..." rows="2" :disabled="generating || optimizing" />
              </div>

              <!-- Buttons (hidden during generation) -->
              <template v-if="!generating">
                <div class="reg-action-row">
                  <button class="reg-optimize-btn" :disabled="optimizing || (!visualDesc && !extraGuidance)" @click="handleOptimize">
                    <svg v-if="optimizing" class="animate-spin" width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.5" stroke-dasharray="24 8" stroke-linecap="round"/></svg>
                    <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1.5 7A5.5 5.5 0 0112.17 5.5M12.5 7A5.5 5.5 0 011.83 8.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M12.17 5.5H9.5M1.83 8.5H4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                    {{ optimizing ? 'AI 正在优化...' : 'AI 优化提示词' }}
                  </button>
                  <button class="reg-direct-btn" :disabled="optimizing || (!visualDesc && !extraGuidance)" @click="handleDirectGenerate">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 2l10 5-10 5 2.5-5-2.5-5z" fill="currentColor"/></svg>
                    直接生成
                  </button>
                </div>

                <!-- Optimized prompt preview -->
                <div v-if="optimizedPrompt" class="reg-result">
                  <div class="reg-result-header">
                    <label class="reg-label">优化后的提示词</label>
                    <span class="reg-result-hint">可编辑后生成</span>
                  </div>
                  <textarea v-model="editedPrompt" class="reg-textarea reg-result-textarea" rows="5" :disabled="generating" />
                </div>

                <button v-if="optimizedPrompt" class="reg-generate-btn" @click="handleGenerate">
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 2l10 5-10 5 2.5-5-2.5-5z" fill="currentColor"/></svg>
                  使用此提示词生成图片
                </button>
              </template>

              <!-- Generating state -->
              <div v-if="generating" class="reg-generating">
                <div class="reg-spinner-lg" />
                <p class="reg-generating-text">AI 正在生成图片，请稍候...</p>
                <p class="reg-generating-hint">这可能需要 10-30 秒</p>
              </div>
            </template>

            <!-- Scene mode -->
            <template v-else>
              <div class="reg-field">
                <label class="reg-label">场景描述</label>
                <textarea v-model="extraGuidance" class="reg-textarea" placeholder="例如：现代都市写字楼大厅，玻璃幕墙，极简风格..." rows="4" :disabled="generating" />
              </div>
              <template v-if="!generating">
                <button class="reg-generate-btn" @click="doGenerate(extraGuidance.trim())">开始生成</button>
              </template>
              <div v-if="generating" class="reg-generating">
                <div class="reg-spinner-lg" />
                <p class="reg-generating-text">AI 正在生成图片，请稍候...</p>
              </div>
            </template>

            <!-- Error / Success -->
            <div v-if="errorMsg" class="reg-error">{{ errorMsg }}</div>
            <div v-if="successMsg" class="reg-success">{{ successMsg }}</div>
          </div>

          <div class="reg-footer">
            <button class="btn btn-ghost btn-sm" :disabled="generating || optimizing" @click="emit('close')">取消</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.reg-overlay {
  position: fixed; inset: 0; z-index: 120;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(3px);
  display: flex; align-items: center; justify-content: center;
}
.reg-panel {
  background: #FDF5D6; border-radius: 18px; width: 520px;
  max-width: 92vw; max-height: 90vh; overflow-y: auto;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.18);
}
.reg-header {
  display: flex; align-items: flex-start; gap: 14px; padding: 24px 24px 0;
}
.reg-header-icon {
  width: 44px; height: 44px; border-radius: 12px;
  background: rgba(232, 163, 23, 0.08);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; flex-shrink: 0;
}
.reg-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0; }
.reg-subtitle { font-size: 13px; color: #9CA3AF; margin: 2px 0 0; }
.reg-close {
  width: 32px; height: 32px; border-radius: 8px; border: none;
  background: transparent; display: flex; align-items: center; justify-content: center;
  color: #9CA3AF; cursor: pointer; margin-left: auto; flex-shrink: 0;
}
.reg-close:hover { background: #F3F4F6; color: #374151; }

.reg-body {
  padding: 20px 24px; display: flex; flex-direction: column; gap: 14px;
}
.reg-field { display: flex; flex-direction: column; gap: 6px; }
.reg-label { font-size: 13px; font-weight: 600; color: #374151; }
.reg-hint { font-size: 12px; color: #9CA3AF; margin: 0; }
.reg-textarea {
  width: 100%; padding: 10px 12px; border: 1.5px solid #E5E7EB;
  border-radius: 10px; font-size: 13px; color: #374151;
  resize: vertical; outline: none; transition: border-color 0.15s;
  font-family: var(--font-sans); line-height: 1.6; box-sizing: border-box; background: #fff;
}
.reg-textarea:focus { border-color: #F5C34B; }
.reg-textarea::placeholder { color: #A89870; }
.reg-textarea:disabled { background: #F3F4F6; color: #9CA3AF; }

.reg-action-row { display: flex; gap: 10px; }

.reg-optimize-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 10px 16px; border-radius: 10px; border: 2px solid #E8A317;
  background: rgba(232, 163, 23, 0.08); color: #C88A0C;
  font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.15s;
}
.reg-optimize-btn:hover:not(:disabled) { background: #E8A317; color: #fff; }
.reg-optimize-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.reg-direct-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 10px 16px; border-radius: 10px; border: 2px solid #D1D5DB;
  background: #F9FAFB; color: #6B7280;
  font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.15s;
}
.reg-direct-btn:hover:not(:disabled) { background: #E5E7EB; color: #374151; border-color: #9CA3AF; }
.reg-direct-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.reg-result {
  border: 2px solid #A8D8A0; border-radius: 10px; overflow: hidden;
}
.reg-result-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; background: rgba(168, 216, 160, 0.15);
  border-bottom: 1px solid rgba(168, 216, 160, 0.3);
}
.reg-result-hint { font-size: 11px; color: #6B9E5F; }
.reg-result-textarea { border: none; border-radius: 0; font-size: 12px; line-height: 1.7; min-height: 120px; }

.reg-generate-btn {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 12px 20px; border-radius: 10px; border: none;
  background: linear-gradient(135deg, #E8A317, #F5C34B);
  color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.15s;
}
.reg-generate-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(232, 163, 23, 0.3); }

/* Generating state */
.reg-generating {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 40px 20px; gap: 12px;
}
.reg-spinner-lg {
  width: 40px; height: 40px;
  border: 3px solid rgba(232, 163, 23, 0.1);
  border-top-color: #E8A317;
  border-radius: 50%;
  animation: regSpin 0.6s linear infinite;
}
@keyframes regSpin { to { transform: rotate(360deg); } }
.reg-generating-text { font-size: 15px; font-weight: 600; color: #2D2515; margin: 0; }
.reg-generating-hint { font-size: 12px; color: #9CA3AF; margin: 0; }

.reg-error {
  padding: 10px 14px; border-radius: 8px;
  background: #FEF2F2; color: #DC2626;
  font-size: 13px; border: 1px solid #FECACA;
}
.reg-success {
  padding: 10px 14px; border-radius: 8px;
  background: #F0FDF4; color: #16A34A;
  font-size: 13px; border: 1px solid #BBF7D0;
  text-align: center; font-weight: 600;
}

.reg-progress {
  display: flex; align-items: center; gap: 10px;
  padding: 0 24px 16px; color: #E8A317; font-size: 13px; font-weight: 500;
}
.reg-spinner {
  width: 18px; height: 18px;
  border: 2.5px solid rgba(232, 163, 23, 0.1);
  border-top-color: #E8A317;
  border-radius: 50%;
  animation: regSpin 0.6s linear infinite;
}

.reg-footer {
  display: flex; align-items: center; justify-content: flex-end; gap: 10px;
  padding: 14px 24px 18px; border-top: 1px solid #F3F4F6;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
