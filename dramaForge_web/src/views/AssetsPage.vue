<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAssetsStore } from '@/stores/assets'
import { assetsApi } from '@/api/assets'
import CharacterCard from '@/components/assets/CharacterCard.vue'
import SceneCard from '@/components/assets/SceneCard.vue'
import CharacterEditModal from '@/components/assets/CharacterEditModal.vue'
import SceneEditModal from '@/components/assets/SceneEditModal.vue'
import GenerateAssetsModal from '@/components/assets/GenerateAssetsModal.vue'
import RegenerateModal from '@/components/assets/RegenerateModal.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { ProjectStep, VideoStyle } from '@/types/enums'
import type { CharacterDetail, CharacterUpdate, RefImage } from '@/types/character'
import type { SceneDetail, SceneUpdate } from '@/types/scene'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const assetsStore = useAssetsStore()

const projectId = Number(route.params.id)
const activeTab = ref<'characters' | 'scenes'>('characters')
const approving = ref(false)

// ── Generate modal state ──
const showGenModal = ref(false)
const isGenerating = ref(false)
const genProgress = ref('')

// ── Regenerate modal state ──
const showRegenModal = ref(false)
const regenType = ref<'character' | 'scene'>('character')
const regenTarget = ref<CharacterDetail | SceneDetail | null>(null)

// ── Edit modal state ──
const editingCharacter = ref<CharacterDetail | null>(null)
const showCharEdit = ref(false)
const editingScene = ref<SceneDetail | null>(null)
const showSceneEdit = ref(false)
const creatingCharacter = ref(false)
const creatingScene = ref(false)

onMounted(async () => {
  await assetsStore.fetchAssets(projectId)
  // Ensure project step is at least ASSETS when on this page
  if (projectStore.currentProject && projectStore.currentProject.status === ProjectStep.SCRIPT) {
    projectStore.currentProject.status = ProjectStep.ASSETS
  }
})

const charCount = computed(() => assetsStore.characters.length)
const sceneCount = computed(() => assetsStore.scenes.length)

// Total images across all visual groups in the open canvas
const totalCanvasImages = computed(() =>
  visualGroups.value.reduce((sum, g) => sum + g.images.length, 0)
)

// ── Generate all assets ──

const genProgressMessages = [
  '正在分析剧本角色特征...',
  '生成角色形象描述...',
  '绘制角色形象图...',
  '分析场景环境要素...',
  '生成场景描述...',
  '绘制场景图...',
  '整理优化中...',
]

async function handleGenerate(options: { style: string; target: string }) {
  isGenerating.value = true
  genProgress.value = genProgressMessages[0]

  // Simulate progress updates
  let msgIdx = 0
  const progressTimer = setInterval(() => {
    msgIdx = Math.min(msgIdx + 1, genProgressMessages.length - 1)
    genProgress.value = genProgressMessages[msgIdx]
  }, 2500)

  try {
    await assetsStore.generateAll(projectId)
  } catch (e: any) {
    console.error('Failed to generate assets:', e)
  } finally {
    clearInterval(progressTimer)
    isGenerating.value = false
    showGenModal.value = false
    genProgress.value = ''
    await assetsStore.fetchAssets(projectId)
  }
}

// ── Canvas workspace state ──
interface VisualGroup {
  id: string
  name: string        // 形象名称
  description: string // 形象描述（AI生成prompt）
  images: RefImage[]
}

const canvasChar = ref<CharacterDetail | null>(null)
const visualGroups = ref<VisualGroup[]>([])
const canvasSaving = ref(false)
const charDescDraft = ref('')  // character-level description

function newGroupId(): string {
  return 'vg_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6)
}

function openImageCanvas(char: CharacterDetail) {
  canvasChar.value = char
  charDescDraft.value = char.description || ''

  // Group images by name into 形象 groups
  const rawImages: RefImage[] = (char.reference_images || []).map(img =>
    typeof img === 'string' ? { url: img, name: '', description: '' } : { ...img }
  )

  const groupMap = new Map<string, RefImage[]>()
  for (const img of rawImages) {
    const key = img.name || '默认形象'
    if (!groupMap.has(key)) groupMap.set(key, [])
    groupMap.get(key)!.push(img)
  }

  const groups: VisualGroup[] = []
  for (const [name, images] of groupMap) {
    // Use first image's description as group description
    const desc = images[0]?.description || ''
    groups.push({ id: newGroupId(), name, description: desc, images })
  }

  // If no images at all, start with one empty default group
  if (!groups.length) {
    groups.push({ id: newGroupId(), name: '默认形象', description: '', images: [] })
  }

  visualGroups.value = groups
  uploadingCharId.value = null
}

function closeImageCanvas() {
  canvasChar.value = null
  visualGroups.value = []
  charDescDraft.value = ''
}

// ── Flatten groups to reference_images and save ──
async function canvasSave() {
  if (!canvasChar.value) return
  canvasSaving.value = true
  try {
    // Save character-level description
    const updateData: CharacterUpdate = {}
    if (charDescDraft.value !== (canvasChar.value.description || '')) {
      updateData.description = charDescDraft.value
    }

    // Flatten all group images into reference_images
    const allImages: RefImage[] = []
    for (const g of visualGroups.value) {
      for (const img of g.images) {
        allImages.push({
          ...img,
          name: g.name,
          description: g.description,
        })
      }
    }

    if (allImages.length > 0 || Object.keys(updateData).length > 0) {
      updateData.reference_images = allImages
      await assetsApi.updateCharacter(projectId, canvasChar.value.id, updateData)
      // Refresh local char reference
      canvasChar.value = { ...canvasChar.value, ...updateData, reference_images: allImages }
      await assetsStore.fetchAssets(projectId)
    }
  } finally { canvasSaving.value = false }
}

// ── Character description ──
function saveCharDesc() {
  canvasSave()
}

// ── Visual group operations ──
function addVisualGroup() {
  visualGroups.value.push({
    id: newGroupId(),
    name: `形象${visualGroups.value.length + 1}`,
    description: '',
    images: [],
  })
}

function removeVisualGroup(groupId: string) {
  visualGroups.value = visualGroups.value.filter(g => g.id !== groupId)
  canvasSave()
}

function updateGroupName(groupId: string, name: string) {
  const g = visualGroups.value.find(v => v.id === groupId)
  if (g) g.name = name
}

function updateGroupDesc(groupId: string, desc: string) {
  const g = visualGroups.value.find(v => v.id === groupId)
  if (g) g.description = desc
}

// ── Image operations within a group ──
function setPrimaryImage(groupId: string, imgIdx: number) {
  // Unset primary on all images across all groups
  for (const g of visualGroups.value) {
    for (const img of g.images) {
      img.is_primary = false
    }
  }
  const g = visualGroups.value.find(v => v.id === groupId)
  if (g && g.images[imgIdx]) {
    g.images[imgIdx].is_primary = true
  }
  canvasSave()
}

async function deleteImageFromGroup(groupId: string, imgIdx: number) {
  const g = visualGroups.value.find(v => v.id === groupId)
  if (!g) return
  g.images = g.images.filter((_, i) => i !== imgIdx)
  await canvasSave()
}

function updateImageNameInGroup(groupId: string, imgIdx: number, name: string) {
  const g = visualGroups.value.find(v => v.id === groupId)
  if (g && g.images[imgIdx]) {
    g.images[imgIdx] = { ...g.images[imgIdx], name }
  }
}

// ── Upload & AI Generate scoped to a visual group ──
const activeGroupId = ref<string | null>(null)

async function uploadToGroup(groupId: string, file: File) {
  uploadingCharId.value = canvasChar.value?.id || null
  activeGroupId.value = groupId
  try {
    const fd = new FormData(); fd.append('file', file)
    const { data } = await assetsApi.uploadAsset(projectId, fd, false)
    if (data?.url) {
      const g = visualGroups.value.find(v => v.id === groupId)
      if (g) {
        g.images.push({ url: data.url, name: file.name.replace(/\.[^.]+$/, ''), description: g.description })
      }
      await canvasSave()
    }
  } catch (err) { console.error('Upload failed', err) }
  finally {
    uploadingCharId.value = null
    activeGroupId.value = null
    if (charFileInput.value) charFileInput.value.value = ''
  }
}

function triggerGroupUpload(groupId: string) {
  activeGroupId.value = groupId
  charFileInput.value?.click()
}

async function handleGroupFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file || !activeGroupId.value) {
    if (charFileInput.value) charFileInput.value.value = ''
    return
  }
  await uploadToGroup(activeGroupId.value, file)
}

// Trigger AI generate for a specific 形象 group's description
function openRegenForGroup(groupId: string) {
  if (!canvasChar.value) return
  const g = visualGroups.value.find(v => v.id === groupId)
  regenType.value = 'character'
  regenTarget.value = canvasChar.value
  regenPresetPrompt.value = g?.description || ''
  regenVisualName.value = g?.name || ''
  regenTargetGroupId.value = groupId
  showRegenModal.value = true
}

const regenPresetPrompt = ref('')
const regenTargetGroupId = ref<string | null>(null)
const regenVisualName = ref('')

async function onRegenComplete() {
  await assetsStore.fetchAssets(projectId)
  if (canvasChar.value) {
    const updated = assetsStore.characters.find(c => c.id === canvasChar.value!.id)
    if (updated) openImageCanvas(updated)
  }
  if (canvasScene.value) {
    const updated = assetsStore.scenes.find(s => s.id === canvasScene.value!.id)
    if (updated) openSceneCanvas(updated)
  }
}

// ── Scene canvas workspace state ──
const canvasScene = ref<SceneDetail | null>(null)
const sceneImages = ref<any[]>([])
const sceneDescDraft = ref('')
const sceneTimeOfDay = ref('day')
const sceneInterior = ref(true)
const sceneSaving = ref(false)

function openSceneCanvas(scene: SceneDetail) {
  canvasScene.value = scene
  sceneDescDraft.value = scene.description || ''
  sceneTimeOfDay.value = scene.time_of_day || 'day'
  sceneInterior.value = scene.interior !== undefined ? scene.interior : true
  sceneImages.value = (scene.reference_images || []).map((img: any) =>
    typeof img === 'string' ? { url: img, name: scene.name, description: '' } : { ...img }
  )
}

function closeSceneCanvas() {
  canvasScene.value = null
  sceneImages.value = []
}

async function sceneCanvasSave() {
  if (!canvasScene.value) return
  sceneSaving.value = true
  try {
    await assetsApi.updateScene(projectId, canvasScene.value.id, {
      description: sceneDescDraft.value,
      time_of_day: sceneTimeOfDay.value,
      interior: sceneInterior.value,
      reference_images: sceneImages.value,
    } as SceneUpdate)
    await assetsStore.fetchAssets(projectId)
    const updated = assetsStore.scenes.find(s => s.id === canvasScene.value!.id)
    if (updated) canvasScene.value = updated
  } catch (e: any) { console.error('Save scene failed', e) }
  finally { sceneSaving.value = false }
}

function sceneSetPrimary(idx: number) {
  sceneImages.value = sceneImages.value.map((img: any, i: number) => ({ ...img, is_primary: i === idx }))
  sceneCanvasSave()
}

async function sceneDeleteImage(idx: number) {
  sceneImages.value = sceneImages.value.filter((_: any, i: number) => i !== idx)
  await sceneCanvasSave()
}

function sceneUpdateImageName(idx: number, name: string) {
  sceneImages.value[idx] = { ...sceneImages.value[idx], name }
}

const uploadingSceneId = ref<number | null>(null)
const sceneFileInput = ref<HTMLInputElement | null>(null)

function triggerSceneUpload() {
  sceneFileInput.value?.click()
}

async function handleSceneFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploadingSceneId.value = canvasScene.value?.id || null
  try {
    const fd = new FormData(); fd.append('file', file)
    const { data } = await assetsApi.uploadAsset(projectId, fd, false)
    if (data?.url) {
      sceneImages.value = [...sceneImages.value, {
        url: data.url,
        name: canvasScene.value?.name || '场景图',
        description: '',
      }]
      await sceneCanvasSave()
    }
  } catch (err) { console.error('Scene upload failed', err) }
  finally {
    uploadingSceneId.value = null
    if (sceneFileInput.value) sceneFileInput.value.value = ''
  }
}

// Trigger AI generate for a scene
function openRegenScene(scene: SceneDetail) {
  regenType.value = 'scene'
  regenTarget.value = scene
  regenPresetPrompt.value = scene.description || ''
  regenVisualName.value = scene.name || ''
  showRegenModal.value = true
}

// ── Character edit (for canvas) ──
const uploadingCharId = ref<number | null>(null)
const charFileInput = ref<HTMLInputElement | null>(null)

function openCharEdit(char: CharacterDetail) {
  editingCharacter.value = char
  showCharEdit.value = true
}

async function saveCharEdit(data: Partial<CharacterDetail>) {
  try {
    if (creatingCharacter.value) {
      await assetsApi.createCharacter(projectId, {
        name: data.name || '',
        role: data.role,
        description: data.description,
        voice_desc: data.voice_desc,
      })
      creatingCharacter.value = false
    } else if (editingCharacter.value) {
      await assetsApi.updateCharacter(projectId, editingCharacter.value.id, data as CharacterUpdate)
    }
    showCharEdit.value = false
    await assetsStore.fetchAssets(projectId)
  } catch (e: any) {
    console.error('Failed to save character:', e)
  }
}

// ── Scene actions ──

function openSceneEdit(scene: SceneDetail) {
  editingScene.value = scene
  showSceneEdit.value = true
}

async function saveSceneEdit(data: Partial<SceneDetail>) {
  try {
    if (creatingScene.value) {
      await assetsApi.createScene(projectId, {
        name: data.name || '',
        description: data.description,
        time_of_day: data.time_of_day,
        interior: data.interior,
      })
      creatingScene.value = false
    } else if (editingScene.value) {
      await assetsApi.updateScene(projectId, editingScene.value.id, data as SceneUpdate)
    }
    showSceneEdit.value = false
    await assetsStore.fetchAssets(projectId)
  } catch (e: any) {
    console.error('Failed to save scene:', e)
  }
}

// ── Navigation ──

function goBackToScript() {
  if (projectStore.currentProject) {
    projectStore.currentProject.status = ProjectStep.SCRIPT
  }
  router.push(`/projects/${projectId}/script`)
}

// ── Approve ──

async function handleApprove() {
  approving.value = true
  try {
    await assetsApi.approve(projectId)
    // Force-update store so StepNavigator reflects the change immediately
    if (projectStore.currentProject) {
      projectStore.currentProject.status = ProjectStep.STORYBOARD
    }
    router.push(`/projects/${projectId}/episodes`)
  } finally {
    approving.value = false
  }
}
</script>

<template>
  <LoadingOverlay :visible="assetsStore.loading" message="正在加载资产..." />

  <div class="page-container-wide">
    <!-- ═══ Header with nav ═══ -->
    <div class="assets-header">
      <div class="assets-header-left">
        <h1 class="assets-title">角色 & 场景资产</h1>
        <p class="assets-subtitle">管理剧中角色和场景的视觉设定</p>
      </div>
      <div class="assets-header-actions">
        <button class="btn btn-primary btn-sm" @click="showGenModal = true" :disabled="isGenerating">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M13.5 2.5l-4 4M8.5 2.5h5v5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 3H3.5a1 1 0 00-1 1v8.5a1 1 0 001 1H12a1 1 0 001-1V10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
          {{ isGenerating ? '生成中...' : '生成资产' }}
        </button>
        <button class="btn btn-outline btn-sm" @click="goBackToScript">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M9 2L4 7l5 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          返回剧本
        </button>
        <button class="btn btn-outline btn-sm" @click="router.push(`/projects/${projectId}/episodes`)">
          管理剧集
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M5 2l5 5-5 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="assets-tabs">
      <button
        class="assets-tab"
        :class="{ active: activeTab === 'characters' }"
        @click="activeTab = 'characters'"
      >
        全部角色 {{ charCount }}
      </button>
      <button
        class="assets-tab"
        :class="{ active: activeTab === 'scenes' }"
        @click="activeTab = 'scenes'"
      >
        全部场景 {{ sceneCount }}
      </button>
    </div>

    <!-- Characters: canvas workspace or grid -->
    <div v-if="activeTab === 'characters'">
      <!-- ═══ Canvas Workspace (when a character is selected) ═══ -->
      <div v-if="canvasChar" class="canvas-workspace">
        <!-- Canvas header -->
        <div class="canvas-header">
          <button class="canvas-back-btn" @click="closeImageCanvas">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M9 2L4 7l5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span>返回角色列表</span>
          </button>
          <div class="canvas-header-info">
            <span class="canvas-char-name">{{ canvasChar.name }}</span>
            <span class="canvas-char-role">· {{ canvasChar.role }} · {{ totalCanvasImages }} 张形象图</span>
          </div>
        </div>

        <!-- Canvas area -->
        <div class="canvas-area">
          <!-- ═══ Character description ═══ -->
          <div class="char-desc-section">
            <label class="canvas-label">角色描述</label>
            <textarea
              v-model="charDescDraft"
              class="char-desc-textarea"
              rows="2"
              placeholder="描述角色的外貌、性格、气质等，作为AI生成形象的背景参考..."
              @blur="saveCharDesc"
            ></textarea>
          </div>

          <!-- ═══ Visual groups ═══ -->
          <div class="visual-groups">
            <!-- Header -->
            <div class="vg-header">
              <label class="canvas-label">形象管理</label>
              <span class="text-xs text-gray-500">每个形象代表角色的不同状态/角度</span>
            </div>

            <!-- Empty state -->
            <div v-if="!visualGroups.length" class="canvas-empty">
              <span class="text-5xl mb-3">🎭</span>
              <p class="text-gray-600 mb-1">暂无形象</p>
              <p class="text-gray-500 text-sm">点击下方按钮创建第一个形象</p>
            </div>

            <!-- Each visual group -->
            <div
              v-for="group in visualGroups"
              :key="group.id"
              class="vg-card"
            >
              <!-- Group header -->
              <div class="vg-card-header">
                <div class="vg-card-header-left">
                  <input
                    :value="group.name"
                    class="vg-name-input"
                    placeholder="形象名称"
                    @input="updateGroupName(group.id, ($event.target as HTMLInputElement).value)"
                    @blur="canvasSave()"
                  />
                  <span class="vg-img-count">{{ group.images.length }} 张图</span>
                </div>
                <div class="vg-card-header-right">
                  <button class="vg-action-btn vg-gen-btn" title="AI生成此形象图" @click="openRegenForGroup(group.id)">
                    <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><path d="M1.5 7A5.5 5.5 0 0112.17 5.5M12.5 7A5.5 5.5 0 011.83 8.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M12.17 5.5H9.5M1.83 8.5H4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                    <span class="hidden sm:inline">AI生成</span>
                  </button>
                  <button class="vg-action-btn vg-upload-btn" title="上传形象图" @click="triggerGroupUpload(group.id)">
                    <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><path d="M2 7h10M7 2v10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
                    <span class="hidden sm:inline">上传</span>
                  </button>
                  <button class="vg-action-btn vg-delete-btn" title="删除此形象" @click="removeVisualGroup(group.id)">
                    <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><path d="M2.5 4h9M5 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M10.5 4v6a2 2 0 01-2 2h-3a2 2 0 01-2-2V4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </button>
                </div>
              </div>

              <!-- Group description (AI prompt) -->
              <div class="vg-desc-row">
                <input
                  :value="group.description"
                  class="vg-desc-input"
                  placeholder="形象描述（作为AI生成prompt）"
                  @input="updateGroupDesc(group.id, ($event.target as HTMLInputElement).value)"
                  @blur="canvasSave()"
                />
              </div>

              <!-- Group images -->
              <div v-if="group.images.length" class="vg-images">
                <div
                  v-for="(img, idx) in group.images"
                  :key="idx"
                  class="vg-img-card group"
                >
                  <div class="vg-img-pic">
                    <img :src="img.url" :alt="img.name || group.name" class="w-full h-full object-cover" />
                    <span v-if="img.is_primary" class="vg-primary-badge" title="主图">⭐</span>
                    <button
                      v-if="!img.is_primary"
                      class="vg-set-primary-btn"
                      @click="setPrimaryImage(group.id, idx)"
                    >设为主图</button>
                    <button class="vg-img-delete-btn" @click="deleteImageFromGroup(group.id, idx)">
                      <svg width="12" height="12" viewBox="0 0 14 14" fill="none"><path d="M2.5 4h9M5 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M10.5 4v6a2 2 0 01-2 2h-3a2 2 0 01-2-2V4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </button>
                  </div>
                  <input
                    :value="img.name || ''"
                    class="vg-img-name-input"
                    placeholder="图片名"
                    @input="updateImageNameInGroup(group.id, idx, ($event.target as HTMLInputElement).value)"
                    @blur="canvasSave()"
                  />
                </div>
              </div>

              <!-- Group empty hint -->
              <div v-else class="vg-empty-hint">
                点击「AI生成」或「上传」为此形象添加图片
              </div>
            </div>

            <!-- Add new visual group -->
            <button class="vg-add-btn" @click="addVisualGroup">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><line x1="8" y1="2" x2="8" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
              新建形象
            </button>
          </div>
        </div>
      </div>

      <!-- ═══ Character Grid (default view) ═══ -->
      <template v-else>
        <EmptyState
          v-if="!assetsStore.loading && !charCount"
          title="暂无角色"
          description="生成资产后将在这里显示"
          icon="👤"
        />
        <div v-else class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-5">
          <CharacterCard
            v-for="char in assetsStore.characters"
            :key="char.id"
            :character="char"
            @open-gallery="openImageCanvas"
          />
          <!-- Add new character -->
          <button class="add-new-card" @click="creatingCharacter = true; showCharEdit = true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>
            <span class="text-sm font-semibold mt-3">新建角色</span>
          </button>
        </div>
      </template>

      <!-- Hidden file input (for canvas upload) -->
      <input
        ref="charFileInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="handleGroupFile"
      />
    </div>

    <!-- ═══ Scenes: canvas workspace or grid ═══ -->
    <div v-if="activeTab === 'scenes'">
      <!-- Scene Canvas -->
      <div v-if="canvasScene" class="canvas-workspace">
        <div class="canvas-header">
          <button class="canvas-back-btn" @click="closeSceneCanvas">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M9 2L4 7l5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span>返回场景列表</span>
          </button>
          <div class="canvas-header-info">
            <span class="canvas-char-name">{{ canvasScene.name }}</span>
            <span class="canvas-char-role">· {{ sceneImages.length }} 张图</span>
          </div>
          <div class="canvas-header-actions">
            <button class="btn btn-outline btn-sm" @click="openRegenScene(canvasScene!)">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1.5 7A5.5 5.5 0 0112.17 5.5M12.5 7A5.5 5.5 0 011.83 8.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M12.17 5.5H9.5M1.83 8.5H4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
              AI生成场景
            </button>
            <button class="btn btn-primary btn-sm" @click="triggerSceneUpload" :disabled="!!uploadingSceneId">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><line x1="7" y1="2" x2="7" y2="12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="2" y1="7" x2="12" y2="7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
              上传
            </button>
          </div>
        </div>

        <div class="canvas-area">
          <!-- Scene description -->
          <div class="char-desc-section">
            <label class="canvas-label">场景描述</label>
            <textarea v-model="sceneDescDraft" class="char-desc-textarea" rows="2"
              placeholder="描述场景的环境、氛围、光线等，作为AI生成的参考..."
              @blur="sceneCanvasSave" />
          </div>

          <!-- Scene metadata row -->
          <div class="scene-meta-row">
            <div class="scene-meta-field">
              <label class="canvas-label">时段</label>
              <select v-model="sceneTimeOfDay" class="scene-meta-select" @change="sceneCanvasSave">
                <option value="day">☀️ 日景</option>
                <option value="night">🌙 夜景</option>
                <option value="dawn">🌅 黎明</option>
                <option value="dusk">🌆 黄昏</option>
              </select>
            </div>
            <div class="scene-meta-field">
              <label class="canvas-label">类型</label>
              <label class="scene-interior-toggle">
                <input type="checkbox" v-model="sceneInterior" @change="sceneCanvasSave" />
                <span>{{ sceneInterior ? '室内' : '室外' }}</span>
              </label>
            </div>
          </div>

          <!-- Images -->
          <div class="visual-groups">
            <div class="vg-header">
              <label class="canvas-label">场景图</label>
              <span class="text-xs text-gray-500">{{ sceneImages.length }} 张</span>
            </div>

            <div v-if="!sceneImages.length" class="canvas-empty">
              <span class="text-5xl mb-3">🏠</span>
              <p class="text-gray-600 mb-1">暂无场景图</p>
              <p class="text-gray-500 text-sm">使用 AI 生成或上传场景图</p>
            </div>

            <div v-else class="scene-img-grid">
              <div v-for="(img, idx) in sceneImages" :key="idx" class="vg-img-card group">
                <div class="vg-img-pic">
                  <img :src="typeof img === 'string' ? img : img.url" :alt="img.name || '场景图'" class="w-full h-full object-cover" />
                  <span v-if="img.is_primary" class="vg-primary-badge" title="主图">⭐</span>
                  <button v-if="!img.is_primary" class="vg-set-primary-btn" @click="sceneSetPrimary(idx)">设为主图</button>
                  <button class="vg-img-delete-btn" @click="sceneDeleteImage(idx)">
                    <svg width="12" height="12" viewBox="0 0 14 14" fill="none"><path d="M2.5 4h9M5 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M10.5 4v6a2 2 0 01-2 2h-3a2 2 0 01-2-2V4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </button>
                </div>
                <input :value="img.name || ''" class="vg-img-name-input" placeholder="图片名"
                  @input="sceneUpdateImageName(idx, ($event.target as HTMLInputElement).value)"
                  @blur="sceneCanvasSave()" />
              </div>
            </div>
          </div>
        </div>

        <!-- Hidden file input for scene -->
        <input ref="sceneFileInput" type="file" accept="image/*" class="hidden" @change="handleSceneFile" />
      </div>

      <!-- Scene Grid (default view) -->
      <template v-else>
        <EmptyState
          v-if="!assetsStore.loading && !sceneCount"
          title="暂无场景"
          description="生成资产后将在这里显示"
          icon="🏠"
        />
        <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          <SceneCard
            v-for="scene in assetsStore.scenes"
            :key="scene.id"
            :scene="scene"
            @open-gallery="openSceneCanvas"
          />
          <button class="add-new-card scene-add-card" @click="creatingScene = true; showSceneEdit = true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>
            <span class="text-sm font-semibold mt-3">新建场景</span>
          </button>
        </div>
      </template>
    </div>
  </div>

  <!-- ── Generate Modal ── -->
  <GenerateAssetsModal
    :visible="showGenModal"
    :generating="isGenerating"
    :progress="genProgress"
    :char-count="charCount"
    :scene-count="sceneCount"
    @close="showGenModal = false"
    @generate="handleGenerate"
  />

  <!-- ── Regenerate Modal ── -->
  <RegenerateModal
    :visible="showRegenModal"
    :type="regenType"
    :name="(regenTarget as any)?.name || ''"
    :project-id="projectId"
    :char-id="regenType === 'character' ? (regenTarget as any)?.id : undefined"
    :scene-id="regenType === 'scene' ? (regenTarget as any)?.id : undefined"
    :visual-description="regenPresetPrompt"
    :visual-name="regenVisualName"
    @close="showRegenModal = false; regenPresetPrompt = ''; regenTargetGroupId = null; regenVisualName = ''"
    @generated="onRegenComplete"
  />

  <!-- ── Edit Modals ── -->
  <CharacterEditModal
    :visible="showCharEdit"
    :character="editingCharacter"
    :create-mode="creatingCharacter"
    @close="showCharEdit = false; editingCharacter = null; creatingCharacter = false"
    @save="saveCharEdit"
  />
  <SceneEditModal
    :visible="showSceneEdit"
    :scene="editingScene"
    :create-mode="creatingScene"
    @close="showSceneEdit = false; editingScene = null; creatingScene = false"
    @save="saveSceneEdit"
  />

  <!-- Bottom bar -->
  <div class="bottom-action-bar">
    <div class="bar-hint">
      <div class="bar-icon">🤖</div>
      <span>角色和场景设定会应用到整部剧集中，建议调整完毕后再继续</span>
    </div>
    <div class="bar-actions">
      <button class="btn btn-outline btn-sm" @click="goBackToScript">
        ← 上一步
      </button>
      <button class="btn btn-primary btn-sm" @click="handleApprove" :disabled="approving">
        {{ approving ? '确认中...' : '下一步 →' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
/* ── Header ── */
.assets-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}
.assets-header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.assets-title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}
.assets-subtitle {
  font-size: 13px;
  color: #9CA3AF;
  margin: 0;
}
.assets-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.assets-tabs {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 28px;
  border-bottom: 1px solid #FDF4D8;
}

.assets-tab {
  position: relative;
  padding: 10px 4px;
  font-size: 15px;
  font-weight: 500;
  color: #999;
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

.assets-tab:hover {
  color: #555;
}

.assets-tab.active {
  color: #2D2515;
  font-weight: 600;
}

.assets-tab.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  background: #2D2515;
  border-radius: 1px;
}

/* ═══ Canvas Workspace ═══ */
.canvas-workspace {
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: #FEF9E7;
  box-shadow: 4px 4px 0 0 rgba(0,0,0,0.08);
  overflow: hidden;
}
.canvas-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 2px solid #D4C898;
  background: #FDF5D6;
}
.canvas-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  background: transparent;
  color: #6B5D40;
  font-size: 12px;
  font-family: 'Press Start 2P', monospace;
  font-size: 9px;
  letter-spacing: 1px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.canvas-back-btn:hover {
  background: rgba(232,163,23,0.08);
  border-color: #E8A317;
  color: #E8A317;
}
.canvas-header-info {
  flex: 1;
  display: flex;
  align-items: baseline;
  gap: 4px;
  min-width: 0;
}
.canvas-char-name {
  font-family: 'Press Start 2P', monospace;
  font-size: 13px;
  color: #2D2515;
  letter-spacing: 2px;
}
.canvas-char-role {
  font-size: 13px;
  color: #8B7A5A;
}
.canvas-header-actions {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
}

/* Canvas area */
.canvas-area {
  padding: 20px;
  min-height: 400px;
  background:
    linear-gradient(45deg, #FDF4D8 25%, transparent 25%),
    linear-gradient(-45deg, #FDF4D8 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #FDF4D8 75%),
    linear-gradient(-45deg, transparent 75%, #FDF4D8 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0;
}

/* ── Character description ── */
.char-desc-section {
  margin-bottom: 24px;
  padding: 14px 16px;
  background: #fff;
  border: 2px solid #D4C898;
  border-radius: 2px;
}
.canvas-label {
  display: block;
  font-family: 'Press Start 2P', monospace;
  font-size: 10px;
  color: #6B5D40;
  letter-spacing: 1px;
  margin-bottom: 8px;
}
.char-desc-textarea {
  width: 100%;
  border: 2px solid #E5D9A8;
  border-radius: 2px;
  padding: 10px 12px;
  font-size: 13px;
  color: #4A3F28;
  background: #FEF9E7;
  resize: vertical;
  outline: none;
  font-family: inherit;
  transition: border-color 0.15s;
}
.char-desc-textarea:focus {
  border-color: #E8A317;
}
.char-desc-textarea::placeholder {
  color: #A89870;
}

/* ── Visual groups ── */
.visual-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.vg-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 4px;
}

/* Visual group card */
.vg-card {
  background: #fff;
  border: 2px solid #D4C898;
  border-radius: 2px;
  overflow: hidden;
}
.vg-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #EDE3C8;
  background: #FDF5D6;
  gap: 8px;
}
.vg-card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.vg-name-input {
  border: none;
  outline: none;
  background: transparent;
  font-family: 'Press Start 2P', monospace;
  font-size: 10px;
  color: #2D2515;
  letter-spacing: 1px;
  min-width: 0;
  flex: 1;
  padding: 2px 0;
  border-bottom: 2px solid transparent;
  transition: border-color 0.15s;
}
.vg-name-input:focus {
  border-bottom-color: #E8A317;
}
.vg-img-count {
  font-size: 11px;
  color: #8B7A5A;
  white-space: nowrap;
}
.vg-card-header-right {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

/* Action buttons in group header */
.vg-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  background: #FEF9E7;
  color: #6B5D40;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.vg-action-btn:hover {
  transform: translate(1px, 1px);
}
.vg-gen-btn:hover {
  background: #E8A317;
  border-color: #C88A0C;
  color: #fff;
}
.vg-upload-btn:hover {
  background: #4A90D9;
  border-color: #3570B0;
  color: #fff;
}
.vg-delete-btn:hover {
  background: #E74C3C;
  border-color: #C0392B;
  color: #fff;
}

/* Group description */
.vg-desc-row {
  padding: 8px 14px;
  border-bottom: 1px solid #EDE3C8;
}
.vg-desc-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 12px;
  color: #6B5D40;
  padding: 4px 0;
  font-family: inherit;
}
.vg-desc-input::placeholder {
  color: #A89870;
  font-style: italic;
}

/* Images within group */
.vg-images {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  padding: 14px;
}

.vg-img-card {
  display: flex;
  flex-direction: column;
  border-radius: 2px;
  overflow: hidden;
  border: 2px solid #D4C898;
  background: #FDF5D6;
  box-shadow: 3px 3px 0 0 rgba(0,0,0,0.08);
  transition: box-shadow 0.15s, transform 0.15s;
}
.vg-img-card:hover {
  box-shadow: 2px 2px 0 0 rgba(0,0,0,0.08);
  transform: translate(1px, 1px);
}

.vg-img-pic {
  aspect-ratio: 1;
  position: relative;
  overflow: hidden;
  background: #FDF4D8;
}

.vg-primary-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  font-size: 16px;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3));
  z-index: 2;
}

.vg-set-primary-btn {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  padding: 3px 8px;
  border-radius: 2px;
  border: 2px solid #F5C34B;
  background: rgba(0,0,0,0.6);
  color: #F5C34B;
  font-family: 'Press Start 2P', monospace;
  font-size: 8px;
  letter-spacing: 1px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
  white-space: nowrap;
  z-index: 2;
}
.group:hover .vg-set-primary-btn { opacity: 1; }
.vg-set-primary-btn:hover {
  background: #F5C34B;
  color: #2D2515;
}

.vg-img-delete-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 26px; height: 26px;
  border-radius: 2px;
  background: rgba(231,76,60,0.85);
  color: #fff;
  border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.group:hover .vg-img-delete-btn { opacity: 1; }
.vg-img-delete-btn:hover { background: #E74C3C; }

.vg-img-name-input {
  border: none;
  outline: none;
  background: transparent;
  font-family: 'Press Start 2P', monospace;
  font-size: 8px;
  color: #4A3F28;
  letter-spacing: 1px;
  text-align: center;
  padding: 6px 8px;
  width: 100%;
}
.vg-img-name-input::placeholder {
  color: #A89870;
}

/* Group empty hint */
.vg-empty-hint {
  padding: 24px 14px;
  text-align: center;
  font-size: 12px;
  color: #A89870;
}

/* Add new visual group button */
.vg-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border: 2px dashed #D4C898;
  border-radius: 2px;
  background: transparent;
  color: #8B7A5A;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.vg-add-btn:hover {
  border-color: #E8A317;
  background: rgba(232,163,23,0.05);
  color: #E8A317;
}

.canvas-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

/* ── Scene canvas extras ── */
.scene-meta-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}
.scene-meta-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}
.scene-meta-select {
  padding: 8px 12px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: #fff;
  font-size: 13px;
  color: #4A3F28;
  outline: none;
  cursor: pointer;
}
.scene-interior-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #4A3F28;
}
.scene-interior-toggle input {
  width: 16px; height: 16px;
  accent-color: #E8A317;
}

.scene-img-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.canvas-header-actions {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
}

/* Add new card buttons */
.add-new-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  aspect-ratio: 3 / 4;
  border: 2px dashed #D4C898;
  border-radius: 2px;
  background: transparent;
  color: #A89870;
  cursor: pointer;
  transition: all 0.15s;
}
.add-new-card:hover {
  border-color: #E8A317;
  background: rgba(232, 163, 23, 0.05);
  color: #E8A317;
}
.scene-add-card {
  aspect-ratio: 16 / 10;
  border-radius: 12px;
}
</style>
