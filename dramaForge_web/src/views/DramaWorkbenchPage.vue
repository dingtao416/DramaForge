<!--
  DramaForge — DramaWorkbenchPage.vue
  ======================================
  短剧 Agent 创作工作台
  - 上传剧本 / AI 生成剧本 (tab 切换)
  - 我的项目 (网格卡片)
-->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api/projects'
import type { ProjectList } from '@/types/project'
import TopbarActions from '@/components/common/TopbarActions.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useBillingStore } from '@/stores/billing'

const router = useRouter()
const billingStore = useBillingStore()

// ── Tab state ──
const activeTab = ref<'upload' | 'ai'>('upload')

// ── Upload state ──
const isDragging = ref(false)
const uploadFile = ref<File | null>(null)
const uploading = ref(false)
const uploadError = ref('')

// ── AI generate state ──
const aiPrompt = ref('')
const aiGenre = ref('都市')
const aiEpisodes = ref(5)
const generating = ref(false)
const genreOptions = ['都市', '古装', '仙侠', '悬疑', '甜宠', '末世', '穿越', '逆袭', '复仇', '豪门']

// ── Projects ──
const projects = ref<ProjectList[]>([])
const loadingProjects = ref(false)

// ── Subscription modal ──
const showSubscribeSheet = ref(false)

onMounted(async () => {
  billingStore.fetchBalance()
  await loadProjects()
})

async function loadProjects() {
  loadingProjects.value = true
  try {
    const { data } = await projectsApi.list()
    projects.value = data
  } finally {
    loadingProjects.value = false
  }
}

const seedingExamples = ref(false)

async function seedExamples() {
  seedingExamples.value = true
  try {
    await projectsApi.seedExamples()
    await loadProjects()
  } catch (e: any) {
    console.error('seed examples failed:', e)
  } finally {
    seedingExamples.value = false
  }
}

// ── Upload handlers ──
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}
function handleDragLeave() {
  isDragging.value = false
}
function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) validateAndSetFile(file)
}
function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) validateAndSetFile(file)
  input.value = ''
}
function validateAndSetFile(file: File) {
  uploadError.value = ''
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['docx', 'doc', 'txt'].includes(ext || '')) {
    uploadError.value = '仅支持 .docx / .doc / .txt 格式'
    return
  }
  if (file.size > 20 * 1024 * 1024) {
    uploadError.value = '文件大小不能超过 20MB'
    return
  }
  uploadFile.value = file
}
function clearFile() {
  uploadFile.value = null
  uploadError.value = ''
}

async function handleUpload() {
  if (!uploadFile.value) return
  uploading.value = true
  try {
    // TODO: call upload API → creates project → navigate
    // const { data } = await projectsApi.uploadScript(uploadFile.value)
    // router.push(`/projects/${data.id}/script`)
    await new Promise(r => setTimeout(r, 1500)) // Simulate
    alert('剧本上传成功！(接口对接中)')
  } catch (e: any) {
    uploadError.value = e.message || '上传失败'
  } finally {
    uploading.value = false
  }
}

// ── AI Generate ──
async function handleGenerate() {
  if (!aiPrompt.value.trim()) return
  generating.value = true
  try {
    // TODO: call AI script gen API → creates project → navigate
    // const { data } = await projectsApi.generateScript({ prompt, genre, episodes })
    // router.push(`/projects/${data.id}/script`)
    await new Promise(r => setTimeout(r, 2000))
    alert('剧本生成成功！(接口对接中)')
  } catch (e: any) {
    uploadError.value = e.message || '生成失败'
  } finally {
    generating.value = false
  }
}

// ── Helpers ──
function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function getStepLabel(status: string) {
  const map: Record<string, string> = {
    script: '剧本',
    assets: '角色',
    storyboard: '分镜',
    completed: '完成',
  }
  return map[status] || '示例'
}


function getGenreLabel(genre: string) {
  const map: Record<string, string> = {
    romance: '甜宠', suspense: '悬疑', comedy: '搞笑',
    fantasy: '奇幻', urban: '都市', historical: '古装',
    revenge: '复仇', thriller: '惊悚', other: '其他',
  }
  return map[genre] || '短剧'
}
</script>

<template>
  <div class="workbench-page">
    <!-- ══════ Top Bar ══════ -->
    <header class="wb-topbar">
      <div class="wb-topbar-left">
        <button class="wb-back-btn" @click="router.push('/')" title="返回首页">
          <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>
      <TopbarActions @subscribe="showSubscribeSheet = true" />
    </header>

    <!-- ══════ Main Content ══════ -->
    <main class="wb-main">
      <!-- Hero section -->
      <div class="wb-hero">
        <!-- Decorative arc -->
        <div class="wb-hero-arc">
          <svg viewBox="0 0 800 60" fill="none" preserveAspectRatio="none">
            <path d="M0 60 Q400 0 800 60" fill="none" stroke="#e8e0f5" stroke-width="1.5"/>
          </svg>
        </div>
        <h1 class="wb-hero-title">短剧 Agent</h1>
        <p class="wb-hero-subtitle">全面应用 ✦ Seedance 2.0 模型，一键直出整部剧！</p>
      </div>

      <!-- ═══ Upload / AI Tabs ═══ -->
      <div class="wb-card-area">
        <div class="wb-tabs">
          <button
            class="wb-tab"
            :class="{ active: activeTab === 'upload' }"
            @click="activeTab = 'upload'"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2v8M5 5l3-3 3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 10v3a1 1 0 001 1h10a1 1 0 001-1v-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
            上传我的剧本
          </button>
          <button
            class="wb-tab"
            :class="{ active: activeTab === 'ai' }"
            @click="activeTab = 'ai'"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/><path d="M5 6h6M5 8.5h4M5 11h2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
            AI 生成剧本
            <span class="wb-tab-badge">剧本限免1次</span>
          </button>
        </div>

        <!-- Upload Panel -->
        <div v-if="activeTab === 'upload'" class="wb-panel">
          <div
            class="wb-upload-zone"
            :class="{ dragging: isDragging, 'has-file': uploadFile }"
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
            @drop="handleDrop"
          >
            <template v-if="!uploadFile">
              <p class="wb-upload-hint">支持 docx 格式，剧本字数不超过 10 万字，可拖拽至此处上传</p>
              <label class="wb-upload-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2v8M5 5l3-3 3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 10v3a1 1 0 001 1h10a1 1 0 001-1v-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
                上传
                <input type="file" accept=".docx,.doc,.txt" hidden @change="handleFileSelect" />
              </label>
            </template>
            <template v-else>
              <div class="wb-file-info">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="4" y="2" width="16" height="20" rx="2" stroke="#7c3aed" stroke-width="1.5"/><path d="M8 7h8M8 11h6M8 15h4" stroke="#7c3aed" stroke-width="1.3" stroke-linecap="round"/></svg>
                <div class="wb-file-detail">
                  <span class="wb-file-name">{{ uploadFile.name }}</span>
                  <span class="wb-file-size">{{ (uploadFile.size / 1024).toFixed(1) }} KB</span>
                </div>
                <button class="wb-file-remove" @click="clearFile">✕</button>
              </div>
              <button
                class="wb-submit-btn"
                :disabled="uploading"
                @click="handleUpload"
              >
                <template v-if="uploading">
                  <div class="wb-spinner" />
                  上传中...
                </template>
                <template v-else>开始创作</template>
              </button>
            </template>
          </div>
          <p v-if="uploadError" class="wb-error">{{ uploadError }}</p>
        </div>

        <!-- AI Generate Panel -->
        <div v-if="activeTab === 'ai'" class="wb-panel">
          <div class="wb-ai-form">
            <div class="wb-form-group">
              <label class="wb-label">故事题材</label>
              <div class="wb-genre-grid">
                <button
                  v-for="g in genreOptions"
                  :key="g"
                  class="wb-genre-tag"
                  :class="{ active: aiGenre === g }"
                  @click="aiGenre = g"
                >{{ g }}</button>
              </div>
            </div>

            <div class="wb-form-group">
              <label class="wb-label">集数</label>
              <div class="wb-episode-row">
                <button
                  v-for="n in [3, 5, 8, 10, 15, 20]"
                  :key="n"
                  class="wb-episode-tag"
                  :class="{ active: aiEpisodes === n }"
                  @click="aiEpisodes = n"
                >{{ n }} 集</button>
              </div>
            </div>

            <div class="wb-form-group">
              <label class="wb-label">故事描述 / 关键词</label>
              <textarea
                v-model="aiPrompt"
                class="wb-textarea"
                placeholder="例如：霸道总裁与灰姑娘的虐恋故事，要有反转和高潮..."
                rows="4"
              />
            </div>

            <button
              class="wb-submit-btn full"
              :disabled="generating || !aiPrompt.trim()"
              @click="handleGenerate"
            >
              <template v-if="generating">
                <div class="wb-spinner" />
                AI 正在创作...
              </template>
              <template v-else>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M13.5 2.5l-5 5M8.5 2.5h5v5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 3H3.5a1 1 0 00-1 1v8.5a1 1 0 001 1H12a1 1 0 001-1V10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                AI 一键生成剧本
              </template>
            </button>
          </div>
        </div>

        <!-- Credit note -->
        <p class="wb-credit-note">
          请确认上传的剧本有合法版权。剧本每100字符消耗5积分，实际消耗与最终上传的剧本字符相关
        </p>
      </div>

      <!-- ═══ My Projects ═══ -->
      <div class="wb-projects-section">
        <div class="wb-projects-header">
          <h2 class="wb-section-title">我的项目</h2>
          <div class="wb-header-actions">
            <button
              v-if="!projects.length && !loadingProjects"
              class="wb-seed-btn"
              :disabled="seedingExamples"
              @click="seedExamples"
            >
              {{ seedingExamples ? '创建中...' : '✨ 创建示例项目' }}
            </button>
            <button class="wb-manage-btn" @click="router.push('/projects')">管理</button>
          </div>
        </div>

        <div v-if="loadingProjects" class="wb-loading">
          <div class="wb-spinner-lg" />
        </div>

        <div v-else-if="!projects.length" class="wb-empty">
          <div class="wb-empty-icon">🎬</div>
          <div class="wb-empty-title">还没有项目</div>
          <div class="wb-empty-desc">上传剧本或使用 AI 生成，开始你的第一部短剧</div>
          <button class="wb-seed-btn-lg" :disabled="seedingExamples" @click="seedExamples">
            {{ seedingExamples ? '创建中...' : '✨ 一键创建示例项目' }}
          </button>
        </div>

        <div v-else class="wb-project-grid">
          <div
            v-for="p in projects"
            :key="p.id"
            class="wb-project-card"
            @click="router.push(`/projects/${p.id}/assets`)"
          >
            <!-- Thumbnail row (character placeholders) -->
            <div class="wb-project-thumb">
              <span class="wb-project-badge">{{ getStepLabel(p.status) }}</span>
              <div class="wb-thumb-images">
                <div v-for="i in 4" :key="i" class="wb-thumb-img-slot">
                  <svg width="28" height="28" viewBox="0 0 28 28" fill="none"><circle cx="14" cy="10" r="5" stroke="#d4d4d8" stroke-width="1.2"/><path d="M4 26c0-5.5 4.5-9 10-9s10 3.5 10 9" stroke="#d4d4d8" stroke-width="1.2" stroke-linecap="round"/></svg>
                </div>
              </div>
            </div>
            <!-- Info -->
            <div class="wb-project-info">
              <div class="wb-project-name">{{ p.title }}</div>
              <div class="wb-project-meta">
                <span class="wb-project-genre">{{ getGenreLabel(p.genre) }}</span>
                <span class="wb-meta-sep">｜</span>
                {{ formatDate(p.created_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ══════════════════════════════════════════════════════
   Page Layout
   ══════════════════════════════════════════════════════ */
.workbench-page {
  min-height: 100vh;
  background: #fff;
}

/* ── Top Bar ── */
.wb-topbar {
  height: 56px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: #fff;
  position: sticky;
  top: 0;
  z-index: 50;
}
.wb-topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.wb-back-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-back-btn:hover { background: #f5f5f5; color: #333; }

/* ── Main ── */
.wb-main {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 24px 80px;
}

/* ══════════════════════════════════════════════════════
   Hero
   ══════════════════════════════════════════════════════ */
.wb-hero {
  text-align: center;
  padding: 56px 0 36px;
  position: relative;
}
.wb-hero-arc {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  opacity: 0.6;
  pointer-events: none;
}
.wb-hero-title {
  font-size: 34px;
  font-weight: 800;
  color: #1a1a1a;
  letter-spacing: -0.5px;
  margin: 0 0 10px;
}
.wb-hero-subtitle {
  font-size: 15px;
  color: #999;
  margin: 0;
}

/* ══════════════════════════════════════════════════════
   Card Area (Tabs + Upload/AI)
   ══════════════════════════════════════════════════════ */
.wb-card-area {
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 16px;
}

/* ── Tabs ── */
.wb-tabs {
  display: flex;
  border-bottom: 1px solid #e5e5e5;
}
.wb-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 0;
  background: #fafafa;
  border: none;
  font-size: 14px;
  font-weight: 600;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.wb-tab.active {
  background: #fff;
  color: #1a1a1a;
}
.wb-tab:not(:last-child) {
  border-right: 1px solid #e5e5e5;
}
.wb-tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 20%;
  right: 20%;
  height: 2px;
  background: #1a1a1a;
  border-radius: 1px;
}
.wb-tab-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #FEF2F2;
  color: #ef4444;
  font-weight: 600;
  letter-spacing: 0.2px;
}

/* ── Panel ── */
.wb-panel {
  padding: 32px 40px;
}

/* ── Upload Zone ── */
.wb-upload-zone {
  border: 1.5px dashed #d4d4d8;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  transition: all 0.2s;
  background: #fafafa;
}
.wb-upload-zone.dragging {
  border-color: #7c3aed;
  background: #F9F5FF;
}
.wb-upload-zone.has-file {
  border-style: solid;
  border-color: #7c3aed;
  background: #FDFBFF;
}
.wb-upload-hint {
  font-size: 14px;
  color: #999;
  margin: 0 0 20px;
}
.wb-upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 28px;
  border: 1.5px solid #1a1a1a;
  border-radius: 24px;
  background: #fff;
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-upload-btn:hover {
  background: #1a1a1a;
  color: #fff;
}

/* ── File Info ── */
.wb-file-info {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
  justify-content: center;
}
.wb-file-detail {
  display: flex;
  flex-direction: column;
  text-align: left;
}
.wb-file-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.wb-file-size {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.wb-file-remove {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: #f5f5f5;
  color: #999;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.wb-file-remove:hover { background: #FEE2E2; color: #ef4444; }

/* ── Submit Button ── */
.wb-submit-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 36px;
  border: none;
  border-radius: 12px;
  background: #1a1a1a;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-submit-btn:hover { background: #333; }
.wb-submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.wb-submit-btn.full { width: 100%; }

/* ── Error ── */
.wb-error {
  text-align: center;
  font-size: 13px;
  color: #ef4444;
  margin: 12px 0 0;
}

/* ── Credit note ── */
.wb-credit-note {
  text-align: center;
  font-size: 12px;
  color: #ccc;
  padding: 16px 0;
  margin: 0;
}

/* ══════════════════════════════════════════════════════
   AI Form
   ══════════════════════════════════════════════════════ */
.wb-ai-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.wb-form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.wb-label {
  font-size: 13px;
  font-weight: 600;
  color: #666;
}
.wb-genre-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.wb-genre-tag, .wb-episode-tag {
  padding: 6px 16px;
  border: 1.5px solid #e5e5e5;
  border-radius: 20px;
  background: #fff;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-genre-tag.active, .wb-episode-tag.active {
  border-color: #7c3aed;
  background: #F9F5FF;
  color: #7c3aed;
  font-weight: 600;
}
.wb-genre-tag:hover:not(.active), .wb-episode-tag:hover:not(.active) {
  border-color: #ccc;
}
.wb-episode-row {
  display: flex;
  gap: 8px;
}
.wb-textarea {
  width: 100%;
  padding: 14px 16px;
  border: 1.5px solid #e5e5e5;
  border-radius: 12px;
  font-size: 14px;
  color: #333;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
  font-family: inherit;
  line-height: 1.6;
}
.wb-textarea::placeholder { color: #ccc; }
.wb-textarea:focus { border-color: #7c3aed; }

/* ══════════════════════════════════════════════════════
   My Projects
   ══════════════════════════════════════════════════════ */
.wb-projects-section {
  margin-top: 48px;
}
.wb-projects-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.wb-section-title {
  font-size: 20px;
  font-weight: 800;
  color: #1a1a1a;
  margin: 0;
}
.wb-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.wb-manage-btn {
  padding: 6px 18px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  background: #fff;
  font-size: 13px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-manage-btn:hover { border-color: #ccc; background: #fafafa; }

.wb-seed-btn {
  padding: 6px 16px;
  border: 1px solid #7c3aed;
  border-radius: 8px;
  background: #F9F5FF;
  color: #7c3aed;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-seed-btn:hover { background: #EDE9FE; }
.wb-seed-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Empty state */
.wb-empty {
  text-align: center;
  padding: 48px 0;
}
.wb-empty-icon { font-size: 40px; margin-bottom: 12px; }
.wb-empty-title { font-size: 16px; font-weight: 700; color: #333; margin-bottom: 6px; }
.wb-empty-desc { font-size: 13px; color: #999; margin-bottom: 20px; }
.wb-seed-btn-lg {
  padding: 10px 28px;
  border: none;
  border-radius: 12px;
  background: #7c3aed;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-seed-btn-lg:hover { background: #6d28d9; }
.wb-seed-btn-lg:disabled { opacity: 0.5; cursor: not-allowed; }

.wb-project-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
@media (max-width: 768px) {
  .wb-project-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 520px) {
  .wb-project-grid { grid-template-columns: 1fr; }
}

.wb-project-card {
  border: 1px solid #ececec;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}
.wb-project-card:hover {
  border-color: #ddd;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

.wb-project-thumb {
  position: relative;
  height: 160px;
  background: #f9f9f9;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.wb-project-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 3px 10px;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  z-index: 2;
}
.wb-thumb-images {
  display: flex;
  gap: 6px;
  padding: 0 16px;
}
.wb-thumb-img-slot {
  width: 72px;
  height: 120px;
  border-radius: 8px;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #d4d4d8;
  overflow: hidden;
}
.wb-thumb-img-slot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.wb-project-info {
  padding: 14px 16px;
}
.wb-project-name {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}
.wb-project-meta {
  font-size: 12px;
  color: #bbb;
  display: flex;
  align-items: center;
  gap: 0;
}
.wb-project-genre {
  color: #7c3aed;
  font-weight: 500;
}
.wb-meta-sep {
  margin: 0 2px;
  color: #ddd;
}

/* ── Loading / Spinner ── */
.wb-loading {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}
.wb-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: wbspin 0.6s linear infinite;
}
.wb-spinner-lg {
  width: 32px;
  height: 32px;
  border: 3px solid #7c3aed;
  border-top-color: transparent;
  border-radius: 50%;
  animation: wbspin 0.7s linear infinite;
}
@keyframes wbspin {
  to { transform: rotate(360deg); }
}
</style>