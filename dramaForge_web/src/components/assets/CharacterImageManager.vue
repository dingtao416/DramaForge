<script setup lang="ts">
import { ref, watch } from 'vue'
import { assetsApi } from '@/api/assets'
import type { CharacterDetail, RefImage } from '@/types/character'
import { CharacterAppearanceType, CharacterAppearanceTypeLabel, TURNAROUND_TYPES, STAGE_TYPES } from '@/types/character'

const props = defineProps<{
  visible: boolean
  character: CharacterDetail | null
}>()

const emit = defineEmits<{
  close: []
  updated: []
}>()

// ── Local editable image list ──
const images = ref<RefImage[]>([])
const saving = ref(false)
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

watch([() => props.visible, () => props.character], ([visible, character]) => {
  if (visible && character) {
    images.value = (character.reference_images || []).map(img => {
      if (typeof img === 'string') return { url: img, name: '', appearance_type: CharacterAppearanceType.STANDARD }
      return { ...img, appearance_type: img.appearance_type || CharacterAppearanceType.STANDARD }
    })
  }
}, { immediate: true })

// ── Normalize for display name ──
function displayName(img: RefImage, idx: number): string {
  const label = img.appearance_type ? CharacterAppearanceTypeLabel[img.appearance_type] : ''
  return img.name || label || `形象图 ${idx + 1}`
}

// ── Rename ──
function updateName(idx: number, name: string) {
  images.value[idx] = { ...images.value[idx], name }
  autoSave()
}

// ── Set appearance type ──
function setAppearanceType(idx: number, appearanceType: string) {
  images.value[idx] = { ...images.value[idx], appearance_type: appearanceType }
  autoSave()
}

// ── Upload ──
function triggerUpload() {
  fileInput.value?.click()
}

async function handleFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file || !props.character) return
  uploading.value = true
  try {
    const fd = new FormData(); fd.append('file', file)
    const { data } = await assetsApi.uploadAsset(props.character.project_id, fd)
    if (data?.url) {
      images.value = [...images.value, { url: data.url, name: file.name.replace(/\.[^.]+$/, ''), appearance_type: CharacterAppearanceType.STANDARD }]
      await saveToBackend()
    }
  } catch (err) { console.error('Upload failed', err) }
  finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

// ── Delete ──
async function removeImage(idx: number) {
  images.value = images.value.filter((_, i) => i !== idx)
  await saveToBackend()
}

// ── Save ──
async function saveToBackend() {
  if (!props.character) return
  saving.value = true
  try {
    await assetsApi.updateCharacter(
      (props.character as any).project_id,
      props.character.id,
      { reference_images: images.value },
    )
  } catch (err) { console.error('Save failed', err) }
  finally { saving.value = false }
}

async function autoSave() {
  await saveToBackend()
}

function handleClose() {
  emit('updated')
  emit('close')
}

// ── Appearance type badge color ──
function typeBadgeClass(appearanceType: string | undefined): string {
  if (!appearanceType || appearanceType === CharacterAppearanceType.STANDARD) return 'badge-standard'
  if (TURNAROUND_TYPES.includes(appearanceType as any)) return 'badge-turnaround'
  if (STAGE_TYPES.includes(appearanceType as any)) return 'badge-stage'
  return 'badge-standard'
}
</script>

<template>
  <Transition name="fade">
    <div
      v-if="visible && character"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-[2px]"
      @click.self="handleClose"
    >
      <div class="gallery-panel w-[720px] max-w-[92vw] max-h-[85vh] overflow-y-auto">
        <!-- Header -->
        <div class="gallery-header">
          <div class="flex items-center gap-3">
            <span class="text-2xl">🖼️</span>
            <div>
              <h3 class="gallery-title">形象图管理</h3>
              <p class="gallery-subtitle">{{ character.name }} · {{ images.length }} 张形象图</p>
            </div>
          </div>
          <button class="gallery-close" @click="handleClose">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 3L13 13M13 3L3 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
        </div>

        <!-- Grid -->
        <div class="gallery-body">
          <!-- Empty state -->
          <div v-if="!images.length" class="gallery-empty">
            <span class="text-5xl mb-4">🖼️</span>
            <p class="text-gray-600 mb-2">暂无形象图</p>
            <p class="text-gray-500 text-[13px]">上传或生成角色的形象图</p>
          </div>

          <!-- Image grid -->
          <div v-else class="gallery-grid">
            <div
              v-for="(img, idx) in images"
              :key="idx"
              class="image-card group"
            >
              <!-- Image -->
              <div class="image-card-pic">
                <img :src="img.url" :alt="displayName(img, idx)" class="w-full h-full object-cover" />
                <!-- Appearance type badge -->
                <span
                  v-if="img.appearance_type && img.appearance_type !== 'standard'"
                  class="type-badge"
                  :class="typeBadgeClass(img.appearance_type)"
                >
                  {{ CharacterAppearanceTypeLabel[img.appearance_type] || img.appearance_type }}
                </span>
                <!-- Delete overlay -->
                <button
                  class="image-delete-btn"
                  title="删除此图"
                  @click="removeImage(idx)"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M2.5 4h9M5 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M10.5 4v6a2 2 0 01-2 2h-3a2 2 0 01-2-2V4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
              <!-- Name (editable) -->
              <div class="image-card-name">
                <input
                  :value="displayName(img, idx)"
                  class="image-name-input"
                  placeholder="输入形象图名称"
                  @input="updateName(idx, ($event.target as HTMLInputElement).value)"
                />
              </div>
              <!-- Appearance type selector -->
              <div class="image-card-type">
                <select
                  :value="img.appearance_type || CharacterAppearanceType.STANDARD"
                  class="type-select"
                  @change="setAppearanceType(idx, ($event.target as HTMLSelectElement).value)"
                >
                  <option value="standard">标准形象</option>
                  <optgroup label="三视图">
                    <option value="turnaround_front">正面</option>
                    <option value="turnaround_side">侧面</option>
                    <option value="turnaround_back">背面</option>
                  </optgroup>
                  <optgroup label="阶段形象">
                    <option value="stage_early">前期形象</option>
                    <option value="stage_mid">转折后</option>
                    <option value="stage_late">结局形象</option>
                  </optgroup>
                </select>
              </div>
            </div>

            <!-- Add button -->
            <button
              class="image-card image-card-add"
              :disabled="uploading"
              @click="triggerUpload"
            >
              <div class="image-card-pic image-add-pic">
                <svg v-if="uploading" class="animate-spin" width="32" height="32" viewBox="0 0 32 32" fill="none">
                  <circle cx="16" cy="16" r="13" stroke="currentColor" stroke-width="2.5" stroke-dasharray="50 16" stroke-linecap="round"/>
                </svg>
                <template v-else>
                  <svg width="32" height="32" viewBox="0 0 32 32" fill="none"><line x1="16" y1="8" x2="16" y2="24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><line x1="8" y1="16" x2="24" y2="16" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>
                  <span class="text-[13px] mt-2 font-semibold">{{ uploading ? '上传中' : '添加形象图' }}</span>
                </template>
              </div>
            </button>
          </div>

          <!-- Hidden file input -->
          <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFile" />
        </div>

        <!-- Footer -->
        <div class="gallery-footer">
          <span class="text-[12px] text-gray-500">修改名称后自动保存 · 点击图片上传区域添加新图</span>
          <button class="btn btn-primary" @click="handleClose">完成</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* ── Panel ── */
.gallery-panel {
  background: #FEF9E7;
  border: 3px solid #D4C898;
  border-radius: 2px;
  box-shadow: 8px 8px 0 0 rgba(0,0,0,0.18);
  display: flex;
  flex-direction: column;
}

/* ── Header ── */
.gallery-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px 12px;
  border-bottom: 2px solid #D4C898;
  background: #FDF5D6;
}
.gallery-title {
  font-family: 'Press Start 2P', monospace;
  font-size: 14px;
  color: #2D2515;
  letter-spacing: 2px;
  margin: 0;
}
.gallery-subtitle {
  font-size: 12px;
  color: #8B7A5A;
  margin-top: 4px;
}
.gallery-close {
  width: 32px; height: 32px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  background: transparent;
  display: flex; align-items: center; justify-content: center;
  color: #8B7A5A;
  cursor: pointer;
  flex-shrink: 0;
}
.gallery-close:hover {
  background: rgba(232,163,23,0.08);
  color: #E8A317;
  border-color: #E8A317;
}

/* ── Body ── */
.gallery-body {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
}
.gallery-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

/* ── Image card ── */
.image-card {
  display: flex;
  flex-direction: column;
  border-radius: 2px;
  overflow: hidden;
  border: 2px solid #D4C898;
  background: #FDF5D6;
  box-shadow: 3px 3px 0 0 rgba(0,0,0,0.08);
  transition: box-shadow 0.15s, transform 0.15s;
}
.image-card:hover {
  box-shadow: 2px 2px 0 0 rgba(0,0,0,0.08);
  transform: translate(1px, 1px);
}
.image-card-pic {
  aspect-ratio: 1;
  position: relative;
  overflow: hidden;
  background: #FDF4D8;
}

/* Delete button overlay */
.image-delete-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 28px; height: 28px;
  border-radius: 2px;
  background: rgba(231, 76, 60, 0.85);
  color: #fff;
  border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.group:hover .image-delete-btn { opacity: 1; }
.image-delete-btn:hover { background: #E74C3C; }

/* Name input */
.image-card-name {
  padding: 8px 10px;
}
.image-name-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-family: 'Press Start 2P', monospace;
  font-size: 9px;
  color: #4A3F28;
  letter-spacing: 1px;
  text-align: center;
}
.image-name-input::placeholder {
  color: #A89870;
  font-size: 8px;
}

/* Add button */
.image-card-add {
  cursor: pointer;
  border-style: dashed;
}
.image-card-add:hover {
  border-color: #E8A317;
  background: rgba(232,163,23,0.05);
}
.image-card-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.image-add-pic {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #A89870;
}

/* ── Footer ── */
.gallery-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  border-top: 2px solid #D4C898;
  background: #FDF5D6;
}

/* ── Appearance Type Badge ── */
.type-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  padding: 2px 7px;
  border-radius: 2px;
  font-family: 'Press Start 2P', monospace;
  font-size: 7px;
  letter-spacing: 0.5px;
  color: #fff;
  line-height: 1.6;
  z-index: 2;
  pointer-events: none;
}
.badge-standard { display: none; }
.badge-turnaround { background: rgba(79, 70, 229, 0.85); }
.badge-stage { background: rgba(6, 182, 212, 0.85); }

/* ── Appearance Type Selector ── */
.image-card-type {
  padding: 4px 8px 8px;
  border-top: 1px solid rgba(212, 200, 152, 0.3);
}
.type-select {
  width: 100%;
  border: 1px solid #D4C898;
  border-radius: 4px;
  background: #FEF9E7;
  font-size: 10px;
  color: #4A3F28;
  padding: 3px 4px;
  outline: none;
  cursor: pointer;
  font-family: inherit;
}
.type-select:focus {
  border-color: #E8A317;
}
</style>
