<!--
  DramaForge — DramaWorkbenchPage.vue
  ======================================
  短剧 Agent 创作工作台
  - 上传剧本 / AI 生成剧本 (tab 切换)
  - 我的项目 (网格卡片)
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api/projects'
import { scriptsApi } from '@/api/scripts'
import type { ScriptParseResult, ScriptGenerateStreamResult } from '@/api/scripts'
import type { ProjectList } from '@/types/project'
import { DramaGenre, VideoStyle } from '@/types/enums'
import TopbarActions from '@/components/common/TopbarActions.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useBillingStore } from '@/stores/billing'
import { useGenerationStore } from '@/stores/generation'

const router = useRouter()
const billingStore = useBillingStore()
const genStore = useGenerationStore()

// ── Tab state ──
const activeTab = ref<'upload' | 'ai'>('upload')

// ── Upload state ──
const isDragging = ref(false)
const uploadFile = ref<File | null>(null)
const uploadError = ref('')

// ── Preview state ──
const parsedResult = ref<ScriptParseResult | null>(null)
const parsing = ref(false)
const creating = ref(false)
const showFullPreview = ref(false)

// ── AI generate state (local UI) ──
const aiPrompt = ref('')
const aiGenre = ref('都市')
const aiEpisodes = ref(5)

// ── Generation progress (global store — survives navigation) ──
const generating = computed(() => genStore.isGenerating)
const genStreamContent = computed(() => genStore.streamContent)

/** Extract human-readable fields from partial streaming JSON */
interface GenPreview {
  protagonist: string
  genre: string
  synopsis: string
  oneLiner: string
  episodeCount: number
  characterCount: number
  sceneCount: number
}
const genPreview = computed<GenPreview>(() => {
  const text = genStreamContent.value
  const extract = (key: string): string => {
    // Match "key": "value" or "key": "value" (partial)
    const re = new RegExp(`"${key}"\\s*:\\s*"([^"]*(?:\\\\.[^"]*)*)"?`, 's')
    const m = text.match(re)
    return m ? m[1].replace(/\\"/g, '"').replace(/\\n/g, '\n') : ''
  }
  const countArray = (key: string): number => {
    // Count opening braces in the array
    const re = new RegExp(`"${key}"\\s*:\\s*\\[`, 's')
    const m = text.match(re)
    if (!m) return 0
    const idx = m.index! + m[0].length
    const slice = text.slice(idx)
    let count = 0; let depth = 1; let i = 0
    while (i < slice.length && depth > 0) {
      if (slice[i] === '{') { depth++; count++ }
      else if (slice[i] === '}') { depth-- }
      i++
    }
    return count
  }
  return {
    protagonist: extract('protagonist'),
    genre: extract('genre'),
    synopsis: extract('synopsis'),
    oneLiner: extract('one_liner'),
    episodeCount: countArray('episodes'),
    characterCount: countArray('characters'),
    sceneCount: countArray('scenes'),
  }
})
const genreOptions = ['都市', '古装', '仙侠', '悬疑', '甜宠', '末世', '穿越', '逆袭', '复仇', '豪门', '其他']
const genreMap: Record<string, DramaGenre> = {
  都市: DramaGenre.URBAN,
  古装: DramaGenre.HISTORICAL,
  仙侠: DramaGenre.FANTASY,
  悬疑: DramaGenre.SUSPENSE,
  甜宠: DramaGenre.ROMANCE,
  末世: DramaGenre.THRILLER,
  穿越: DramaGenre.OTHER,
  逆袭: DramaGenre.REVENGE,
  复仇: DramaGenre.REVENGE,
  豪门: DramaGenre.OTHER,
  其他: DramaGenre.OTHER,
}

// ── Projects ──
const projects = ref<ProjectList[]>([])
const loadingProjects = ref(false)

// ── Subscription modal ──
const showSubscribeSheet = ref(false)

onMounted(async () => {
  billingStore.fetchBalance()
  await loadProjects()

  // If generation is already running (e.g. navigated back mid-generation),
  // watch for completion to auto-navigate to the script page
  if (genStore.isGenerating && genStore.projectId) {
    const genPid = genStore.projectId
    const unwatch = watch(
      () => genStore.status,
      (newStatus) => {
        if (newStatus === 'complete') {
          unwatch()
          router.push(`/projects/${genPid}/script`)
        }
      },
    )
  }
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
  parsedResult.value = null
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
  parsedResult.value = null
}

// ── Parse file (preview) ──
async function handleParse() {
  if (!uploadFile.value) return
  parsing.value = true
  uploadError.value = ''
  try {
    const { data } = await scriptsApi.parse(uploadFile.value)
    parsedResult.value = data
  } catch (e: any) {
    uploadError.value = e?.response?.data?.detail || e.message || '解析失败，请检查文件格式'
  } finally {
    parsing.value = false
  }
}

// ── Create project from parsed script ──
async function handleCreateProject() {
  if (!uploadFile.value || !parsedResult.value) return
  creating.value = true
  uploadError.value = ''
  try {
    // Step 1: Create a new project (store the original text as description)
    const title = uploadFile.value.name.replace(/\.(docx|doc|txt)$/i, '').slice(0, 50)
    const { data: project } = await projectsApi.create({
      title,
      genre: 'other',
      style: 'realistic',
      description: parsedResult.value?.full_text?.slice(0, 500) || '',
    })
    // Step 2: Upload script to the project
    await scriptsApi.upload(project.id, uploadFile.value, 1)
    // Step 3: Navigate to script page
    router.push(`/projects/${project.id}/script`)
  } catch (e: any) {
    uploadError.value = e?.response?.data?.detail || e.message || '创建项目失败'
  } finally {
    creating.value = false
  }
}

// ── Format text for preview ──
interface FormattedLine {
  type: 'scene' | 'dialogue' | 'action' | 'normal'
  text: string
  character?: string
}

const formattedPreview = computed<FormattedLine[]>(() => {
  if (!parsedResult.value) return []
  const lines = parsedResult.value.full_text.split('\n')
  const result: FormattedLine[] = []
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) {
      result.push({ type: 'normal', text: '' })
      continue
    }
    // Scene header: 场景X：... or 【场景】
    if (/^(场景\d*[：:]|第\d+[场景集幕场]|【场景|[Ss]cene\s*\d)/.test(trimmed)) {
      result.push({ type: 'scene', text: trimmed })
    }
    // Dialogue: 角色名：对白
    else if (/^[^\s:：]{1,10}[：:](?!\s*$)/.test(trimmed)) {
      const match = trimmed.match(/^([^\s:：]{1,10})[：:](.*)/)
      result.push({
        type: 'dialogue',
        text: match![2].trim(),
        character: match![1].trim(),
      })
    }
    // Action description
    else if (/^[（(].*[）)]$|^\(|^（/.test(trimmed) || /动作|旁白|镜头|画面/.test(trimmed)) {
      result.push({ type: 'action', text: trimmed })
    }
    // Default
    else {
      result.push({ type: 'normal', text: trimmed })
    }
  }
  return result
})

const previewLines = computed(() => {
  if (showFullPreview.value) return formattedPreview.value
  return formattedPreview.value.slice(0, 80)
})

// ── AI Generate ──
async function handleGenerate() {
  if (!aiPrompt.value.trim() || genStore.isGenerating) return
  uploadError.value = ''

  try {
    const title = aiPrompt.value.slice(0, 30)
    const { data: project } = await projectsApi.create({
      title,
      genre: genreMap[aiGenre.value] || DramaGenre.OTHER,
      style: VideoStyle.REALISTIC,
      description: aiPrompt.value,
    })

    // Start generation in global store (survives navigation)
    genStore.startGeneration(project.id, {
      user_input: aiPrompt.value,
      genre: genreMap[aiGenre.value] || DramaGenre.OTHER,
      total_episodes: aiEpisodes.value,
      duration_per_episode: 60,
    })

    // Wait for completion by watching the store
    const unwatch = watch(
      () => genStore.status,
      (newStatus) => {
        if (newStatus === 'complete' && genStore.result) {
          unwatch()
          router.push(`/projects/${project.id}/script`)
        } else if (newStatus === 'error') {
          unwatch()
          uploadError.value = genStore.error || '生成失败'
        }
      },
    )
  } catch (e: any) {
    uploadError.value = e?.response?.data?.detail || e.message || '生成失败'
  }
}

function cancelGeneration() {
  genStore.stopGeneration()
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

// Reset preview when file changes
watch(uploadFile, () => {
  parsedResult.value = null
})
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
              <div class="wb-upload-icon-area">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none" class="wb-upload-cloud">
                  <path d="M32 38h6a8 8 0 10-1.5-15.8A12 12 0 1012 30h20" stroke="#d4d4d8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M24 20v14M18 28l6-6 6 6" stroke="#d4d4d8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <p class="wb-upload-hint">支持 .docx / .doc / .txt 格式<br/>剧本字数不超过 10 万字，可拖拽至此处上传</p>
                <label class="wb-upload-btn">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2v8M5 5l3-3 3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 10v3a1 1 0 001 1h10a1 1 0 001-1v-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
                  选择文件
                  <input type="file" accept=".docx,.doc,.txt" hidden @change="handleFileSelect" />
                </label>
              </div>
            </template>
            <template v-else>
              <!-- File selected, not yet parsed -->
              <div class="wb-file-info">
                <div class="wb-file-icon-box">
                  <svg width="28" height="28" viewBox="0 0 28 28" fill="none"><rect x="5" y="2" width="18" height="24" rx="3" stroke="#E8A317" stroke-width="1.6"/><path d="M9 8h10M9 13h8M9 18h6" stroke="#E8A317" stroke-width="1.4" stroke-linecap="round"/></svg>
                </div>
                <div class="wb-file-detail">
                  <span class="wb-file-name">{{ uploadFile.name }}</span>
                  <span class="wb-file-size">{{ (uploadFile.size / 1024).toFixed(1) }} KB</span>
                </div>
                <button class="wb-file-remove" @click="clearFile" :disabled="parsing || creating">✕</button>
              </div>
              <div class="wb-upload-actions">
                <button class="wb-submit-btn" :disabled="parsing" @click="handleParse">
                  <template v-if="parsing">
                    <div class="wb-spinner" />
                    解析中...
                  </template>
                  <template v-else>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 4h4M10 4h4M2 8h8M13 8h1M2 12h2M7 12h7" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                    解析预览
                  </template>
                </button>
              </div>
            </template>
          </div>
          <div class="wb-upload-format">
            <div class="wb-format-header">角色/场景解析要求</div>
            <div class="wb-format-grid">
              <div class="wb-format-block">
                <span class="wb-format-label">角色字段</span>
                <span class="wb-format-value">角色表、角色清单、主要角色、人物、出场人物</span>
              </div>
              <div class="wb-format-block">
                <span class="wb-format-label">场景字段</span>
                <span class="wb-format-value">场景、场景表、场景清单、拍摄场景</span>
              </div>
            </div>
            <pre class="wb-format-sample">剧本：《示例短剧》
作者：DramaForge

角色清单
1. 林夏 - 女，主角，冷静坚韧。
2. 周铭 - 男，反派，控制欲强。

场景清单
1. 内景  公司会议室  日
2. 外景  城市天桥  夜

第1集：会议反击
**场景：** 内景 · 公司会议室 · 日
**出场人物：** 林夏、周铭
**林夏**（冷静）："证据在这里。"</pre>
            <p class="wb-format-note">缺少上述字段时，系统仍会保存剧本，但不会自动生成角色/场景资产。</p>
          </div>
          <p v-if="uploadError" class="wb-error">{{ uploadError }}</p>

          <!-- ═══ Parsed Preview ═══ -->
          <div v-if="parsedResult" class="wb-preview-panel">
            <!-- Preview Header -->
            <div class="wb-preview-header">
              <div class="wb-preview-title-row">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="1" width="14" height="18" rx="2" stroke="#10B981" stroke-width="1.4"/><path d="M7 6h6M7 9.5h5M7 13h3" stroke="#10B981" stroke-width="1.2" stroke-linecap="round"/></svg>
                <span class="wb-preview-title">剧本预览</span>
                <span class="wb-preview-badge">{{ parsedResult.file_type.toUpperCase() }}</span>
              </div>
              <div class="wb-preview-meta">
                <span>{{ parsedResult.filename }}</span>
                <span class="wb-meta-dot">·</span>
                <span>{{ parsedResult.char_count.toLocaleString() }} 字</span>
              </div>
            </div>

            <!-- Preview Content -->
            <div class="wb-preview-content" :class="{ expanded: showFullPreview }">
              <div v-for="(line, idx) in previewLines" :key="idx" class="wb-script-line" :class="'wb-line-' + line.type">
                <!-- Scene header -->
                <template v-if="line.type === 'scene'">
                  <span class="wb-scene-marker">🎬 场景</span>
                  <span class="wb-scene-text">{{ line.text }}</span>
                </template>
                <!-- Dialogue -->
                <template v-else-if="line.type === 'dialogue'">
                  <span class="wb-char-name">{{ line.character }}</span>
                  <span class="wb-dialogue-sep">：</span>
                  <span class="wb-dialogue-text">{{ line.text }}</span>
                </template>
                <!-- Action -->
                <template v-else-if="line.type === 'action'">
                  <span class="wb-action-text">{{ line.text }}</span>
                </template>
                <!-- Normal / Empty -->
                <template v-else>
                  <span v-if="line.text" class="wb-normal-text">{{ line.text }}</span>
                  <span v-else class="wb-empty-line">&nbsp;</span>
                </template>
              </div>
            </div>

            <!-- Expand / Collapse -->
            <div v-if="formattedPreview.length > 80" class="wb-preview-expand">
              <button class="wb-expand-btn" @click="showFullPreview = !showFullPreview">
                {{ showFullPreview ? '收起预览' : `展开全部（共 ${formattedPreview.length} 行）` }}
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" :class="{ rotated: showFullPreview }"><path d="M3.5 5L7 8.5L10.5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>

            <!-- Create Project Button -->
            <div class="wb-preview-footer">
              <button class="wb-create-btn" :disabled="creating" @click="handleCreateProject">
                <template v-if="creating">
                  <div class="wb-spinner" />
                  创建项目中...
                </template>
                <template v-else>
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2l2.3 4.6L16 7.5l-3.5 3.4L13.4 16 9 13.6 4.6 16l.9-5.1L2 7.5l4.7-.9L9 2z" fill="currentColor"/></svg>
                  确认创建项目
                </template>
              </button>
            </div>
          </div>
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
              v-if="!generating"
              class="wb-submit-btn full"
              :disabled="!aiPrompt.trim()"
              @click="handleGenerate"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M13.5 2.5l-5 5M8.5 2.5h5v5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 3H3.5a1 1 0 00-1 1v8.5a1 1 0 001 1H12a1 1 0 001-1V10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
              AI 一键生成剧本
            </button>
            <button
              v-else
              class="wb-submit-btn full wb-cancel-btn"
              @click="cancelGeneration"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="3" y="3" width="10" height="10" rx="2" fill="currentColor"/></svg>
              停止生成
            </button>
            <div v-if="generating" class="wb-stream-box">
              <div class="wb-stream-label">
                <div class="wb-spinner" />
                <span>AI 正在创作中...（{{ genStreamContent.length }} 字）</span>
                <span class="wb-stream-phase">{{ genStreamContent.length < 200 ? '构思故事框架...' : genStreamContent.length < 1000 ? '展开情节...' : genStreamContent.length < 3000 ? '细化场景对白...' : '完善角色设定...' }}</span>
              </div>
              <!-- Live preview card -->
              <div v-if="genStreamContent.length > 0" class="wb-gen-preview">
                <div v-if="genPreview.protagonist" class="wb-gen-item">
                  <span class="wb-gen-item-label">👤 主角</span>
                  <span class="wb-gen-item-value">{{ genPreview.protagonist }}</span>
                </div>
                <div v-if="genPreview.genre" class="wb-gen-item">
                  <span class="wb-gen-item-label">🎭 类型</span>
                  <span class="wb-gen-item-value">{{ genPreview.genre }}</span>
                </div>
                <div v-if="genPreview.oneLiner" class="wb-gen-item">
                  <span class="wb-gen-item-label">💡 一句话</span>
                  <span class="wb-gen-item-value">{{ genPreview.oneLiner }}</span>
                </div>
                <div class="wb-gen-stats">
                  <div class="wb-gen-stat" :class="{ active: genPreview.episodeCount > 0 }">
                    <span class="wb-gen-stat-num">{{ genPreview.episodeCount || '—' }}</span>
                    <span class="wb-gen-stat-label">集</span>
                  </div>
                  <div class="wb-gen-stat" :class="{ active: genPreview.characterCount > 0 }">
                    <span class="wb-gen-stat-num">{{ genPreview.characterCount || '—' }}</span>
                    <span class="wb-gen-stat-label">角色</span>
                  </div>
                  <div class="wb-gen-stat" :class="{ active: genPreview.sceneCount > 0 }">
                    <span class="wb-gen-stat-num">{{ genPreview.sceneCount || '—' }}</span>
                    <span class="wb-gen-stat-label">场景</span>
                  </div>
                </div>
                <div v-if="genPreview.synopsis" class="wb-gen-synopsis">
                  <div class="wb-gen-synopsis-label">📖 故事梗概</div>
                  <div class="wb-gen-synopsis-text">{{ genPreview.synopsis }}</div>
                </div>
                <!-- Progress bar -->
                <div class="wb-gen-progress-bar">
                  <div class="wb-gen-progress-fill" :style="{ width: Math.min(95, genStreamContent.length / 50) + '%' }" />
                </div>
              </div>
            </div>
            <p v-if="uploadError" class="wb-error">{{ uploadError }}</p>
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
            <!-- Default project cover -->
            <div class="wb-project-thumb">
              <span class="wb-project-badge">{{ getStepLabel(p.status) }}</span>
              <div class="wb-project-cover">
                <div class="wb-project-cover-icon" aria-hidden="true">
                  <svg width="34" height="34" viewBox="0 0 34 34" fill="none">
                    <path d="M6.5 13.5h21v12a2 2 0 0 1-2 2h-17a2 2 0 0 1-2-2v-12Z" stroke="currentColor" stroke-width="1.8" />
                    <path d="M6.5 13.5 9 6.8a2 2 0 0 1 2.5-1.2l14.8 5.4a2 2 0 0 1 1.2 2.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                    <path d="M12 13.5 18 8M20.5 13.5 26.5 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                    <path d="M11 20h12M11 24h7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                  </svg>
                </div>
                <div class="wb-project-cover-title">{{ p.title }}</div>
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
  background: #FDF5D6;
}

/* ── Top Bar ── */
.wb-topbar {
  height: 56px;
  border-bottom: 1px solid #FDF4D8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: #FDF5D6;
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
.wb-back-btn:hover { background: #FDF4D8; color: #333; }

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
  color: #2D2515;
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
  border: 1px solid #D4C898;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 16px;
}

/* ── Tabs ── */
.wb-tabs {
  display: flex;
  border-bottom: 1px solid #D4C898;
}
.wb-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 0;
  background: #FEF9E7;
  border: none;
  font-size: 14px;
  font-weight: 600;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.wb-tab.active {
  background: #FDF5D6;
  color: #2D2515;
}
.wb-tab:not(:last-child) {
  border-right: 1px solid #D4C898;
}
.wb-tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 20%;
  right: 20%;
  height: 2px;
  background: #2D2515;
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
  background: #FEF9E7;
}
.wb-upload-zone.dragging {
  border-color: #E8A317;
  background: rgba(232, 163, 23, 0.08);
}
.wb-upload-zone.has-file {
  border-style: solid;
  border-color: #E8A317;
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
  border: 1.5px solid #2D2515;
  border-radius: 24px;
  background: #FDF5D6;
  font-size: 14px;
  font-weight: 600;
  color: #2D2515;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-upload-btn:hover {
  background: #2D2515;
  color: #FFFFFF;
}
.wb-upload-format {
  margin-top: 16px;
  padding: 16px 18px;
  border: 1px solid #ead9a7;
  border-radius: 12px;
  background: #fffaf0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.wb-format-header {
  font-size: 13px;
  font-weight: 700;
  color: #2D2515;
}
.wb-format-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.wb-format-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.wb-format-label {
  font-size: 12px;
  color: #8a6d2f;
}
.wb-format-value {
  font-size: 13px;
  line-height: 1.55;
  color: #2D2515;
  overflow-wrap: anywhere;
}
.wb-format-sample {
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #2D2515;
  color: #fff6d8;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  overflow-x: auto;
}
.wb-format-note {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: #9a5b00;
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
  background: #FDF4D8;
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
  background: #2D2515;
  color: #FFFFFF;
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
  border: 1.5px solid #D4C898;
  border-radius: 20px;
  background: #FDF5D6;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-genre-tag.active, .wb-episode-tag.active {
  border-color: #E8A317;
  background: rgba(232, 163, 23, 0.08);
  color: #E8A317;
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
  border: 1.5px solid #D4C898;
  border-radius: 12px;
  font-size: 14px;
  color: #333;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
  font-family: var(--font-sans);
  line-height: 1.6;
}
.wb-textarea::placeholder { color: #ccc; }
.wb-textarea:focus { border-color: #E8A317; }

/* ── Stream Preview ── */
.wb-cancel-btn {
  background: #FEF2F2 !important;
  color: #DC2626 !important;
}
.wb-cancel-btn:hover {
  background: #FEE2E2 !important;
}
.wb-stream-box {
  margin-top: 16px;
  border: 1.5px solid #E5E7EB;
  border-radius: 12px;
  overflow: hidden;
  background: #FEF9E7;
}
.wb-stream-label {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #E8A317;
  background: rgba(232, 163, 23, 0.08);
  border-bottom: 1px solid rgba(232, 163, 23, 0.1);
}
.wb-stream-phase {
  font-weight: 400;
  color: #F5C34B;
  font-size: 11px;
  margin-left: auto;
}

/* ── Live generation preview card ── */
.wb-gen-preview {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.wb-gen-item {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.wb-gen-item-label {
  font-size: 12px;
  color: #9CA3AF;
  flex-shrink: 0;
}
.wb-gen-item-value {
  font-size: 14px;
  font-weight: 600;
  color: #1F2937;
}
.wb-gen-stats {
  display: flex;
  gap: 12px;
  padding: 8px 0;
}
.wb-gen-stat {
  display: flex;
  align-items: baseline;
  gap: 3px;
  padding: 6px 14px;
  border-radius: 10px;
  background: #F3F4F6;
  transition: all 0.3s;
}
.wb-gen-stat.active {
  background: rgba(232, 163, 23, 0.1);
}
.wb-gen-stat-num {
  font-size: 18px;
  font-weight: 700;
  color: #9CA3AF;
}
.wb-gen-stat.active .wb-gen-stat-num {
  color: #E8A317;
}
.wb-gen-stat-label {
  font-size: 11px;
  color: #9CA3AF;
}
.wb-gen-synopsis {
  background: #FDF5D6;
  border: 1px solid #F3F4F6;
  border-radius: 10px;
  padding: 12px;
}
.wb-gen-synopsis-label {
  font-size: 11px;
  font-weight: 600;
  color: #9CA3AF;
  margin-bottom: 6px;
}
.wb-gen-synopsis-text {
  font-size: 13px;
  line-height: 1.7;
  color: #4B5563;
}
.wb-gen-progress-bar {
  height: 3px;
  background: rgba(232, 163, 23, 0.1);
  border-radius: 2px;
  overflow: hidden;
}
.wb-gen-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #F5C34B, #E8A317);
  border-radius: 2px;
  transition: width 0.5s ease;
}

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
  color: #2D2515;
  margin: 0;
}
.wb-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.wb-manage-btn {
  padding: 6px 18px;
  border: 1px solid #D4C898;
  border-radius: 8px;
  background: #FDF5D6;
  font-size: 13px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-manage-btn:hover { border-color: #ccc; background: #FEF9E7; }

.wb-seed-btn {
  padding: 6px 16px;
  border: 1px solid #E8A317;
  border-radius: 8px;
  background: rgba(232, 163, 23, 0.08);
  color: #E8A317;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-seed-btn:hover { background: rgba(232, 163, 23, 0.1); }
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
  background: #E8A317;
  color: #2D2515;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-seed-btn-lg:hover { background: #C88A0C; }
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
  .wb-format-grid { grid-template-columns: 1fr; }
}

.wb-project-card {
  border: 1px solid #ececec;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  background: #FDF5D6;
}
.wb-project-card:hover {
  border-color: #ddd;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}

.wb-project-thumb {
  position: relative;
  height: 160px;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 45%),
    #171717;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.wb-project-thumb::before,
.wb-project-thumb::after {
  content: '';
  position: absolute;
  left: 18px;
  right: 18px;
  height: 1px;
  background: rgba(255,255,255,0.12);
}
.wb-project-thumb::before { top: 36px; }
.wb-project-thumb::after { bottom: 30px; }
.wb-project-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 3px 10px;
  background: #ef4444;
  color: #2D2515;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  z-index: 2;
}
.wb-project-cover {
  width: 100%;
  height: 100%;
  padding: 34px 22px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #2D2515;
  text-align: center;
}
.wb-project-cover-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fca5a5;
  background: rgba(255,255,255,0.08);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.1);
}
.wb-project-cover-title {
  max-width: 100%;
  font-size: 17px;
  line-height: 1.25;
  font-weight: 700;
  color: #f9fafb;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
  text-shadow: 0 1px 2px rgba(0,0,0,0.25);
}

.wb-project-info {
  padding: 14px 16px;
}
.wb-project-name {
  font-size: 14px;
  font-weight: 700;
  color: #2D2515;
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
  color: #E8A317;
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
  border: 3px solid #E8A317;
  border-top-color: transparent;
  border-radius: 50%;
  animation: wbspin 0.7s linear infinite;
}
@keyframes wbspin {
  to { transform: rotate(360deg); }
}

/* ══════════════════════════════════════════════════════
   Upload Icon Area
   ══════════════════════════════════════════════════════ */
.wb-upload-icon-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.wb-upload-cloud {
  opacity: 0.5;
}

/* Upload Actions */
.wb-upload-actions {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* File Icon Box */
.wb-file-icon-box {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(232, 163, 23, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ══════════════════════════════════════════════════════
   Preview Panel
   ══════════════════════════════════════════════════════ */
.wb-preview-panel {
  margin-top: 24px;
  border: 1.5px solid #e5e7eb;
  border-radius: 16px;
  overflow: hidden;
  background: #FDF5D6;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

/* Preview Header */
.wb-preview-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f3f4f6;
  background: #fafbfc;
}
.wb-preview-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.wb-preview-title {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}
.wb-preview-badge {
  font-size: 10px;
  font-weight: 700;
  color: #059669;
  background: #ECFDF5;
  padding: 3px 8px;
  border-radius: 6px;
  letter-spacing: 0.5px;
}
.wb-preview-meta {
  font-size: 13px;
  color: #9ca3af;
  padding-left: 30px;
}
.wb-meta-dot {
  margin: 0 6px;
  color: #A89870;
}

/* Preview Content */
.wb-preview-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 20px 24px;
  background: #fefefe;
  border-bottom: 1px solid #f3f4f6;
  line-height: 1.9;
  font-size: 14px;
}
.wb-preview-content.expanded {
  max-height: none;
}

/* Script Line Styles */
.wb-script-line {
  display: flex;
  align-items: baseline;
  gap: 4px;
  min-height: 1.5em;
}
.wb-script-line + .wb-script-line {
  margin-top: 2px;
}

/* Scene line */
.wb-line-scene {
  background: #FFFBEB;
  margin: 12px 0 8px;
  padding: 6px 12px;
  border-radius: 8px;
  border-left: 3px solid #F59E0B;
  font-weight: 600;
}
.wb-scene-marker {
  font-size: 12px;
  color: #D97706;
  margin-right: 8px;
  flex-shrink: 0;
  font-weight: 700;
}
.wb-scene-text {
  color: #92400E;
  font-size: 14px;
}

/* Dialogue line */
.wb-line-dialogue {
  padding: 3px 8px;
  border-radius: 6px;
  transition: background 0.15s;
}
.wb-line-dialogue:hover {
  background: rgba(232, 163, 23, 0.08);
}
.wb-char-name {
  color: #E8A317;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
  min-width: 3em;
  text-align: right;
}
.wb-dialogue-sep {
  color: #A89870;
  margin: 0 2px;
}
.wb-dialogue-text {
  color: #1f2937;
  line-height: 1.7;
}

/* Action line */
.wb-line-action {
  padding: 3px 8px;
  color: #6B7280;
  font-style: italic;
  font-size: 13px;
}
.wb-action-text {
  color: #6B7280;
}

/* Normal line */
.wb-normal-text {
  color: #374151;
}

.wb-empty-line {
  color: transparent;
}

/* Expand button */
.wb-preview-expand {
  text-align: center;
  padding: 10px;
  border-bottom: 1px solid #f3f4f6;
}
.wb-expand-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  background: #FDF5D6;
  font-size: 13px;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.15s;
}
.wb-expand-btn:hover {
  background: #f9fafb;
  color: #374151;
  border-color: #A89870;
}
.wb-expand-btn svg {
  transition: transform 0.2s;
}
.wb-expand-btn svg.rotated {
  transform: rotate(180deg);
}

/* Preview Footer */
.wb-preview-footer {
  padding: 16px 24px;
  display: flex;
  justify-content: center;
}
.wb-create-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 48px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #E8A317, #C88A0C);
  color: #2D2515;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(124,58,237,0.25);
}
.wb-create-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(124,58,237,0.35);
}
.wb-create-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
</style>
