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
import type { CharacterDetail, CharacterUpdate } from '@/types/character'
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
const regenLoading = ref(false)

// ── Edit modal state ──
const editingCharacter = ref<CharacterDetail | null>(null)
const showCharEdit = ref(false)
const editingScene = ref<SceneDetail | null>(null)
const showSceneEdit = ref(false)

onMounted(async () => {
  await assetsStore.fetchAssets(projectId)
  // Ensure project step is at least ASSETS when on this page
  if (projectStore.currentProject && projectStore.currentProject.status === ProjectStep.SCRIPT) {
    projectStore.currentProject.status = ProjectStep.ASSETS
  }
})

const charCount = computed(() => assetsStore.characters.length)
const sceneCount = computed(() => assetsStore.scenes.length)

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

// ── Character actions ──

function openCharEdit(char: CharacterDetail) {
  editingCharacter.value = char
  showCharEdit.value = true
}

async function saveCharEdit(data: Partial<CharacterDetail>) {
  if (!editingCharacter.value) return
  try {
    await assetsApi.updateCharacter(projectId, editingCharacter.value.id, data as CharacterUpdate)
    showCharEdit.value = false
    await assetsStore.fetchAssets(projectId)
  } catch (e: any) {
    console.error('Failed to update character:', e)
  }
}

// ── Regenerate (opens modal) ──
function openRegenCharacter(char: CharacterDetail) {
  regenType.value = 'character'
  regenTarget.value = char
  showRegenModal.value = true
}
function openRegenScene(scene: SceneDetail) {
  regenType.value = 'scene'
  regenTarget.value = scene
  showRegenModal.value = true
}

async function confirmRegenerate(prompt: string) {
  if (!regenTarget.value) return
  regenLoading.value = true
  try {
    if (regenType.value === 'character') {
      const char = regenTarget.value as CharacterDetail
      await assetsApi.regenerateCharacter(projectId, char.id, prompt || undefined)
    } else {
      const scene = regenTarget.value as SceneDetail
      await assetsApi.regenerateScene(projectId, scene.id, prompt || undefined)
    }
    showRegenModal.value = false
    await assetsStore.fetchAssets(projectId)
  } catch (e: any) {
    console.error('Regenerate failed:', e)
    // Keep modal open on error so user can retry
  } finally {
    regenLoading.value = false
  }
}

// ── Scene actions ──

function openSceneEdit(scene: SceneDetail) {
  editingScene.value = scene
  showSceneEdit.value = true
}

async function saveSceneEdit(data: Partial<SceneDetail>) {
  if (!editingScene.value) return
  try {
    await assetsApi.updateScene(projectId, editingScene.value.id, data as SceneUpdate)
    showSceneEdit.value = false
    await assetsStore.fetchAssets(projectId)
  } catch (e: any) {
    console.error('Failed to update scene:', e)
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

    <!-- Characters grid -->
    <div v-if="activeTab === 'characters'">
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
          :regenerating="false"
          @edit="openCharEdit"
          @regenerate="openRegenCharacter"
        />
      </div>
    </div>

    <!-- Scenes grid -->
    <div v-if="activeTab === 'scenes'">
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
          :regenerating="false"
          @edit="openSceneEdit"
          @regenerate="openRegenScene"
        />
      </div>
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
    :description="(regenTarget as any)?.description || ''"
    :loading="regenLoading"
    :current-prompt="(regenTarget as any)?.description || ''"
    @close="showRegenModal = false"
    @confirm="confirmRegenerate"
  />

  <!-- ── Edit Modals ── -->
  <CharacterEditModal
    :visible="showCharEdit"
    :character="editingCharacter"
    @close="showCharEdit = false"
    @save="saveCharEdit"
  />
  <SceneEditModal
    :visible="showSceneEdit"
    :scene="editingScene"
    @close="showSceneEdit = false"
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
</style>
