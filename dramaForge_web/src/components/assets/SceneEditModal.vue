<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { SceneDetail } from '@/types/scene'

const props = defineProps<{
  visible: boolean
  scene: SceneDetail | null
  createMode?: boolean
}>()

const emit = defineEmits<{
  close: []
  save: [data: Partial<SceneDetail>]
}>()

const form = ref({
  name: '',
  description: '',
  time_of_day: 'day',
  interior: true,
})

watch(() => props.visible, (v) => {
  if (v) {
    if (props.createMode || !props.scene) {
      form.value = { name: '', description: '', time_of_day: 'day', interior: true }
    } else {
      form.value = {
        name: props.scene.name,
        description: props.scene.description || '',
        time_of_day: props.scene.time_of_day || 'day',
        interior: props.scene.interior !== undefined ? props.scene.interior : true,
      }
    }
  }
})

function handleSave() {
  emit('save', { ...form.value })
}

const isCreate = computed(() => props.createMode || !props.scene)
</script>

<template>
  <Transition name="fade">
    <div
      v-if="visible"
      class="fixed inset-0 z-[90] flex items-center justify-center bg-black/30 backdrop-blur-[2px]"
      @click.self="emit('close')"
    >
      <div class="modal-panel w-[520px] max-w-[90vw] max-h-[85vh] overflow-y-auto">
        <div class="modal-header-bar">
          <div class="flex items-center gap-3">
            <span class="text-2xl">🏠</span>
            <h3 class="modal-title-text">{{ isCreate ? '新建场景' : '编辑场景' }}</h3>
          </div>
          <button class="modal-close-btn" @click="emit('close')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 3L13 13M13 3L3 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
        </div>

        <div v-if="!isCreate && scene" class="px-6 pb-2">
          <span class="character-chip">{{ scene.name }}</span>
        </div>

        <div class="modal-body-content">
          <div class="field-group">
            <label class="field-label">场景名</label>
            <input v-model="form.name" class="field-input" placeholder="输入场景名" />
          </div>
          <div class="field-group">
            <label class="field-label">场景描述</label>
            <textarea v-model="form.description" rows="3" class="field-textarea"
              placeholder="描述场景的环境、氛围、光线等..." />
          </div>
          <div class="flex gap-4">
            <div class="field-group flex-1">
              <label class="field-label">时段</label>
              <select v-model="form.time_of_day" class="field-input">
                <option value="day">☀️ 日景</option>
                <option value="night">🌙 夜景</option>
                <option value="dawn">🌅 黎明</option>
                <option value="dusk">🌆 黄昏</option>
              </select>
            </div>
            <div class="field-group flex-1">
              <label class="field-label">类型</label>
              <select v-model="form.interior" class="field-input">
                <option :value="true">室内</option>
                <option :value="false">室外</option>
              </select>
            </div>
          </div>
        </div>

        <div class="modal-footer-bar">
          <button class="btn btn-outline" @click="emit('close')">取消</button>
          <button class="btn btn-primary" @click="handleSave">{{ isCreate ? '创建' : '保存' }}</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-panel {
  background: #FEF9E7;
  border: 3px solid #D4C898;
  border-radius: 2px;
  box-shadow: 8px 8px 0 0 rgba(0, 0, 0, 0.18);
}
.modal-header-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px 0;
}
.modal-title-text {
  font-family: 'Press Start 2P', monospace;
  font-size: 14px; color: #2D2515; letter-spacing: 2px;
}
.modal-close-btn {
  width: 32px; height: 32px; border-radius: 2px;
  border: 2px solid #D4C898; background: transparent;
  display: flex; align-items: center; justify-content: center;
  color: #8B7A5A; cursor: pointer; transition: all 0.15s;
}
.modal-close-btn:hover {
  background: rgba(232, 163, 23, 0.08); color: #E8A317; border-color: #E8A317;
}
.character-chip {
  display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 2px;
  background: rgba(232, 163, 23, 0.1); border: 2px solid #D4C898;
  color: #E8A317; font-family: 'Press Start 2P', monospace; font-size: 10px; letter-spacing: 1px;
}
.modal-body-content {
  padding: 16px 24px; display: flex; flex-direction: column; gap: 20px;
}
.field-group { display: flex; flex-direction: column; gap: 6px; }
.field-label {
  font-family: 'Press Start 2P', monospace; font-size: 10px; color: #6B5D40; letter-spacing: 1px;
}
.field-input {
  height: 40px; padding: 0 14px; border: 2px solid #D4C898; border-radius: 2px;
  font-size: 14px; color: #2D2515; background: #FDF5D6; outline: none;
  transition: border-color 0.15s;
}
.field-input:focus { border-color: #E8A317; box-shadow: 0 0 0 3px rgba(232, 163, 23, 0.15); }
.field-textarea {
  padding: 10px 14px; border: 2px solid #D4C898; border-radius: 2px;
  font-size: 14px; color: #2D2515; background: #FDF5D6; outline: none;
  resize: vertical; line-height: 1.7; transition: border-color 0.15s;
}
.field-textarea:focus { border-color: #E8A317; box-shadow: 0 0 0 3px rgba(232, 163, 23, 0.15); }
.modal-footer-bar {
  display: flex; align-items: center; justify-content: flex-end; gap: 12px;
  padding: 16px 24px; border-top: 2px solid #D4C898; background: #FDF5D6;
}
</style>
