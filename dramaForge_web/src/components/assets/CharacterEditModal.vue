<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { CharacterRole, CharacterRoleLabel } from '@/types/enums'
import type { CharacterDetail } from '@/types/character'

const props = defineProps<{
  visible: boolean
  character: CharacterDetail | null
  /** When true, operates in create mode */
  createMode?: boolean
}>()

const emit = defineEmits<{
  close: []
  save: [data: Partial<CharacterDetail>]
}>()

const form = ref({
  name: '',
  role: CharacterRole.SUPPORTING as CharacterRole,
  description: '',
  voice_desc: '',
})

watch(() => props.visible, (v) => {
  if (v) {
    if (props.createMode || !props.character) {
      form.value = { name: '', role: CharacterRole.SUPPORTING, description: '', voice_desc: '' }
    } else {
      form.value = {
        name: props.character.name,
        role: props.character.role,
        description: props.character.description || '',
        voice_desc: props.character.voice_desc || '',
      }
    }
  }
})

function handleSave() {
  emit('save', { ...form.value })
}

const isCreate = computed(() => props.createMode || !props.character)

const roleOptions = Object.entries(CharacterRoleLabel) as [CharacterRole, string][]
</script>

<template>
  <Transition name="fade">
    <div
      v-if="visible"
      class="fixed inset-0 z-[90] flex items-center justify-center bg-black/50 backdrop-blur-[2px]"
      @click.self="emit('close')"
    >
      <div class="modal-panel w-[520px] max-w-[90vw] max-h-[85vh] overflow-y-auto">
        <!-- Header -->
        <div class="modal-header-bar">
          <div class="flex items-center gap-3">
            <span class="text-2xl">🎭</span>
            <h3 class="modal-title-text">
              {{ isCreate ? '新建角色' : '编辑角色' }}
            </h3>
          </div>
          <button class="modal-close-btn" @click="emit('close')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 3L13 13M13 3L3 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
        </div>

        <!-- Character name chip (edit mode only) -->
        <div v-if="!isCreate && character" class="px-6 pb-2">
          <span class="character-chip">{{ character.name }}</span>
        </div>

        <!-- Body -->
        <div class="modal-body-content">
          <!-- 角色名 -->
          <div class="field-group">
            <label class="field-label">角色名</label>
            <input
              v-model="form.name"
              class="field-input"
              placeholder="输入角色名"
            />
          </div>

          <!-- 角色类型 -->
          <div class="field-group">
            <label class="field-label">角色类型</label>
            <select
              v-model="form.role"
              class="field-input"
            >
              <option v-for="[key, label] in roleOptions" :key="key" :value="key">{{ label }}</option>
            </select>
          </div>

          <!-- 外貌描述 -->
          <div class="field-group">
            <label class="field-label">外貌描述</label>
            <textarea
              v-model="form.description"
              rows="3"
              class="field-textarea"
              placeholder="25岁，长发及腰，气质优雅，常穿白色..."
            />
          </div>

          <!-- 音色描述 -->
          <div class="field-group">
            <label class="field-label">音色描述</label>
            <textarea
              v-model="form.voice_desc"
              rows="2"
              class="field-textarea"
              placeholder="女声，温柔成熟，音调中偏低，语速适中..."
            />
          </div>
        </div>

        <!-- Footer -->
        <div class="modal-footer-bar">
          <button class="btn btn-outline" @click="emit('close')">取消</button>
          <button class="btn btn-primary" @click="handleSave">{{ isCreate ? '创建' : '保存' }}</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* ── Modal Panel ── */
.modal-panel {
  background: #FEF9E7;
  border: 3px solid #D4C898;
  border-radius: 2px;
  box-shadow: 8px 8px 0 0 rgba(0, 0, 0, 0.18);
}

/* ── Header ── */
.modal-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px 0;
}

.modal-title-text {
  font-family: 'Press Start 2P', monospace;
  font-size: 14px;
  color: #2D2515;
  letter-spacing: 2px;
}

.modal-close-btn {
  width: 32px;
  height: 32px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8B7A5A;
  cursor: pointer;
  transition: all 0.15s;
}
.modal-close-btn:hover {
  background: rgba(232, 163, 23, 0.08);
  color: #E8A317;
  border-color: #E8A317;
}

/* ── Character chip ── */
.character-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 2px;
  background: rgba(232, 163, 23, 0.1);
  border: 2px solid #D4C898;
  color: #E8A317;
  font-family: 'Press Start 2P', monospace;
  font-size: 10px;
  letter-spacing: 1px;
}

/* ── Body ── */
.modal-body-content {
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Fields ── */
.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-family: 'Press Start 2P', monospace;
  font-size: 10px;
  color: #6B5D40;
  letter-spacing: 1px;
}

.field-input {
  height: 40px;
  padding: 0 14px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  font-size: 14px;
  color: #2D2515;
  background: #FDF5D6;
  outline: none;
  transition: border-color 0.15s;
}
.field-input:focus {
  border-color: #E8A317;
  box-shadow: 0 0 0 3px rgba(232, 163, 23, 0.15);
}

.field-textarea {
  padding: 10px 14px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  font-size: 14px;
  color: #2D2515;
  background: #FDF5D6;
  outline: none;
  resize: vertical;
  line-height: 1.7;
  transition: border-color 0.15s;
}
.field-textarea:focus {
  border-color: #E8A317;
  box-shadow: 0 0 0 3px rgba(232, 163, 23, 0.15);
}

/* ── Footer ── */
.modal-footer-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 2px solid #D4C898;
  background: #FDF5D6;
}
</style>
