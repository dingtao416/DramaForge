<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useScriptStore } from '@/stores/script'
import { useGenerationStore } from '@/stores/generation'
import { scriptsApi } from '@/api/scripts'
import { ProjectStep } from '@/types/enums'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const scriptStore = useScriptStore()
const genStore = useGenerationStore()

const projectId = Number(route.params.id)
const rewriting = ref(false)
const rewriteContent = ref('')
const exporting = ref(false)
let rewriteAbortController: AbortController | null = null

// Check if generation is still running for this project
const genRunning = ref(false)
const genProgressContent = ref('')
const initialLoading = ref(true)  // prevents empty state flash

onMounted(async () => {
  // If this project is actively being generated via the global store, show live progress
  if (genStore.projectId === projectId && genStore.isGenerating) {
    genRunning.value = true
    genProgressContent.value = genStore.streamContent
    initialLoading.value = false

    const unwatchStatus = watch(
      () => genStore.status,
      (newStatus) => {
        if (newStatus === 'complete' || newStatus === 'error') {
          genRunning.value = false
          unwatchStatus()
          scriptStore.fetchScript(projectId)
        }
      },
    )
    watch(
      () => genStore.streamContent,
      (content) => { genProgressContent.value = content },
    )
    return
  }

  // Check backend in case generation is running but SSE connection was lost
  const stillGenerating = await genStore.checkStatus(projectId)
  if (stillGenerating) {
    genRunning.value = true
    initialLoading.value = false
    // Poll until complete
    const poll = setInterval(async () => {
      const running = await genStore.checkStatus(projectId)
      if (!running) {
        clearInterval(poll)
        genRunning.value = false
        scriptStore.fetchScript(projectId)
      }
    }, 2000)
    return
  }

  initialLoading.value = false
  scriptStore.fetchScript(projectId)
})

// Style tag mapping — expand single style to descriptive labels
const styleTagsMap: Record<string, string> = {
  realistic: '真人写实, 电视风格, 暖色调',
  cinematic: '3D, CG动画, 废土末世',
  anime: '日式动漫, 赛璐珞风格, 明亮色彩',
  cartoon: '卡通, 扁平插画, 活泼配色',
  watercolor: '水彩, 手绘质感, 柔和光影',
  ink_wash: '水墨, 中国风, 古典意境',
}

const styleTags = computed(() => {
  const style = projectStore.currentProject?.style
  return style ? (styleTagsMap[style] || style) : ''
})

async function handleRewrite() {
  if (rewriting.value) return
  rewriting.value = true
  rewriteContent.value = ''

  rewriteAbortController = new AbortController()

  try {
    await scriptStore.rewriteNarrationStream(
      projectId,
      {
        onContent: (chunk: string) => {
          rewriteContent.value += chunk
        },
        onDone: (content: string) => {
          scriptStore.fetchScript(projectId)
        },
        onError: (errMsg: string) => {
          console.error('Narration rewrite failed:', errMsg)
        },
      },
      rewriteAbortController.signal,
    )
  } catch (e: any) {
    if (e.name !== 'AbortError') {
      console.error('Narration rewrite failed:', e)
    }
  } finally {
    rewriting.value = false
    rewriteAbortController = null
  }
}

const advancing = ref(false)

async function goToAssets() {
  advancing.value = true
  try {
    // Advance project status to ASSETS
    if (projectStore.currentProject) {
      projectStore.currentProject.status = ProjectStep.ASSETS
    }
    await scriptStore.approveScript(projectId)
    router.push(`/projects/${projectId}/assets`)
  } catch {
    router.push(`/projects/${projectId}/assets`)
  } finally {
    advancing.value = false
  }
}

function cancelRewrite() {
  if (rewriteAbortController) {
    rewriteAbortController.abort()
    rewriteAbortController = null
  }
}

async function handleExport(format: 'docx' | 'txt') {
  exporting.value = true
  try {
    await scriptsApi.exportScript(projectId, format)
  } catch (e: any) {
    console.error('Export failed:', e)
  } finally {
    exporting.value = false
  }
}

// ── Script content formatter ──
interface FormattedLine {
  type: 'scene' | 'dialogue' | 'action' | 'music' | 'hook' | 'preview' | 'separator' | 'empty' | 'text'
  text: string
  meta?: string  // e.g. camera angle, character name
}

function formatScriptContent(raw: string): FormattedLine[] {
  if (!raw) return []
  const lines = raw.split('\n')
  const result: FormattedLine[] = []

  for (const line of lines) {
    const trimmed = line.trim()

    if (!trimmed) {
      result.push({ type: 'empty', text: '' })
      continue
    }

    // Scene description: △ ... or △（...）...
    if (/^△/.test(trimmed)) {
      const text = trimmed.replace(/^△\s*/, '')
      const metaMatch = text.match(/^（([^）]*)）/ )
      result.push({
        type: 'scene',
        text: metaMatch ? text.slice(metaMatch[0].length).trim() : text,
        meta: metaMatch ? metaMatch[1] : '',
      })
      continue
    }

    // Music cue: ♪ ...
    if (/^♪/.test(trimmed)) {
      result.push({ type: 'music', text: trimmed.replace(/^♪\s*/, '') })
      continue
    }

    // Hook: > 🎣 ...
    if (/^>\s*🎣/.test(trimmed)) {
      result.push({ type: 'hook', text: trimmed.replace(/^>\s*🎣\s*/, '') })
      continue
    }

    // Preview: > 📺 ...
    if (/^>\s*📺/.test(trimmed)) {
      result.push({ type: 'preview', text: trimmed.replace(/^>\s*📺\s*/, '') })
      continue
    }

    // Separator: ---
    if (/^---+\s*$/.test(trimmed)) {
      result.push({ type: 'separator', text: '' })
      continue
    }

    // Character dialogue: **角色名**（...）："台词"  or 角色名：台词
    const dialogueMatch = trimmed.match(/^\*\*(.+?)\*\*\s*(?:（([^）]*)）)?\s*[：:]\s*[""](.+)[""]$/)
    if (dialogueMatch) {
      result.push({
        type: 'dialogue',
        text: dialogueMatch[3],
        meta: dialogueMatch[1] + (dialogueMatch[2] ? ` · ${dialogueMatch[2]}` : ''),
      })
      continue
    }

    // Simple dialogue: 角色名：台词 (without ** markers)
    const simpleDialogue = trimmed.match(/^([^\s△♪>{：:]{1,10})[：:]\s*(.+)$/)
    if (simpleDialogue && !/^[>△♪*]/.test(trimmed)) {
      result.push({
        type: 'dialogue',
        text: simpleDialogue[2].replace(/^[""]|[""]$/g, ''),
        meta: simpleDialogue[1],
      })
      continue
    }

    // Action/parenthetical: （...）
    if (/^[（(].*[）)]$/.test(trimmed)) {
      result.push({ type: 'action', text: trimmed.replace(/^[（(]|[）)]$/g, '') })
      continue
    }

    // Default text
    result.push({ type: 'text', text: trimmed })
  }

  return result
}

// ── Episode expand/collapse ──
const expandedEpisodes = ref(new Set<number>())
const allExpanded = ref(false)

function toggleAllEpisodes() {
  if (allExpanded.value) {
    expandedEpisodes.value.clear()
    allExpanded.value = false
  } else {
    const eps = scriptStore.script?.episodes || []
    eps.forEach(ep => expandedEpisodes.value.add(ep.id))
    allExpanded.value = true
  }
}

function onEpisodeToggle(epId: number, event: Event) {
  const details = event.target as HTMLDetailsElement
  if (details.open) {
    expandedEpisodes.value.add(epId)
  } else {
    expandedEpisodes.value.delete(epId)
  }
  // Check if all are now open
  const eps = scriptStore.script?.episodes || []
  allExpanded.value = eps.length > 0 && eps.every(ep => expandedEpisodes.value.has(ep.id))
}
</script>

<template>
  <LoadingOverlay :visible="initialLoading || scriptStore.loading" message="正在加载剧本..." />
  <LoadingOverlay :visible="genRunning" :message="`AI 正在生成剧本...（${genProgressContent.length} 字）`" />
  <!-- Streaming rewrite overlay -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="rewriting" class="rewrite-overlay">
        <div class="rewrite-panel">
          <div class="rewrite-header">
            <div>
              <h3 class="rewrite-title">正在改写为旁白型...</h3>
              <p class="rewrite-subtitle">{{ rewriteContent.length }} 字已生成</p>
            </div>
            <button class="rewrite-cancel-btn" @click="cancelRewrite">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="3" y="3" width="10" height="10" rx="2" fill="currentColor"/></svg>
              停止
            </button>
          </div>
          <pre class="rewrite-content">{{ rewriteContent }}</pre>
        </div>
      </div>
    </Transition>
  </Teleport>

  <div class="page-container" style="max-width: 860px;">
    <!-- Empty state -->
    <EmptyState
      v-if="!initialLoading && !scriptStore.loading && !scriptStore.script"
      title="暂无剧本"
      description="请从首页开始创作或上传剧本"
      icon="📝"
    />

    <template v-if="scriptStore.script">
      <!-- Meta info: two rows like target -->
      <div class="script-meta">
        <div class="script-meta-row">
          <span class="script-meta-label">视频风格：</span>
          <span class="script-meta-value">{{ styleTags }}</span>
        </div>
        <div class="script-meta-row">
          <span class="script-meta-label">画面比例：</span>
          <span class="script-meta-value">{{ projectStore.currentProject?.aspect_ratio || '9:16' }}</span>
        </div>
      </div>

      <!-- Script summary card -->
      <div class="script-section">
        <h2 class="script-section-title">剧本摘要</h2>
        <div class="script-summary-card">
          <div class="script-summary-list">
            <div
              v-for="item in [
                { label: '主角', value: scriptStore.script.protagonist },
                { label: '故事类型', value: scriptStore.script.genre },
                { label: '故事梗概', value: scriptStore.script.synopsis },
                { label: '故事背景', value: scriptStore.script.background },
                { label: '故事设定', value: scriptStore.script.setting },
                { label: '一句话故事', value: scriptStore.script.one_liner },
              ]"
              :key="item.label"
              class="script-summary-item"
            >
              <div class="script-summary-label">{{ item.label }}</div>
              <div class="script-summary-value">{{ item.value || '未设置' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Script content: episodes with expand/collapse -->
      <div class="script-section">
        <div class="script-content-header">
          <h2 class="script-section-title" style="margin-bottom:0">剧本内容:</h2>
          <div class="script-content-actions">
            <button class="btn btn-ghost btn-sm" @click="toggleAllEpisodes">
              {{ allExpanded ? '收起全部' : '展开全部' }}
            </button>
            <button class="btn btn-ghost btn-sm" :disabled="exporting" @click="handleExport('txt')">
              {{ exporting ? '导出中...' : '导出 TXT' }}
            </button>
            <button class="btn btn-outline btn-sm" :disabled="exporting" @click="handleExport('docx')">
              {{ exporting ? '导出中...' : '导出 DOCX' }}
            </button>
            <button
              class="btn btn-outline btn-sm"
              :disabled="rewriting"
              @click="handleRewrite"
            >
              改写为旁白型剧本
            </button>
          </div>
        </div>
        <div class="script-episodes">
          <details
            v-for="(ep, idx) in scriptStore.script.episodes"
            :key="ep.id"
            class="script-episode"
            :open="idx === 0 || expandedEpisodes.has(ep.id)"
            @toggle="onEpisodeToggle(ep.id, $event)"
          >
            <summary class="script-episode-summary">
              <svg class="script-episode-arrow" width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M4.5 2.5L8 6L4.5 9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="script-episode-label">第{{ ep.number }}集</span>
              <span class="script-episode-title">{{ ep.title || '无标题' }}</span>
              <span class="script-episode-chars">{{ (ep.content || '').length }} 字</span>
            </summary>
            <div v-if="!ep.content" class="script-episode-empty">（暂无内容）</div>
            <div v-else class="script-episode-content">
              <template v-for="(line, li) in formatScriptContent(ep.content)" :key="li">
                <!-- Empty line -->
                <div v-if="line.type === 'empty'" class="fmt-empty" />
                <!-- Separator -->
                <div v-else-if="line.type === 'separator'" class="fmt-separator">
                  <span>✦ ✦ ✦</span>
                </div>
                <!-- Scene description -->
                <div v-else-if="line.type === 'scene'" class="fmt-scene">
                  <span v-if="line.meta" class="fmt-scene-tag">{{ line.meta }}</span>
                  <span class="fmt-scene-text">{{ line.text }}</span>
                </div>
                <!-- Dialogue -->
                <div v-else-if="line.type === 'dialogue'" class="fmt-dialogue">
                  <span class="fmt-dialogue-speaker">{{ line.meta }}</span>
                  <span class="fmt-dialogue-text">{{ line.text }}</span>
                </div>
                <!-- Action -->
                <div v-else-if="line.type === 'action'" class="fmt-action">{{ line.text }}</div>
                <!-- Music -->
                <div v-else-if="line.type === 'music'" class="fmt-music">
                  <span class="fmt-music-icon">♪</span>
                  <span>{{ line.text }}</span>
                </div>
                <!-- Hook -->
                <div v-else-if="line.type === 'hook'" class="fmt-hook">
                  <span class="fmt-hook-icon">🎣</span>
                  <span>{{ line.text }}</span>
                </div>
                <!-- Preview -->
                <div v-else-if="line.type === 'preview'" class="fmt-preview">
                  <span class="fmt-preview-icon">📺</span>
                  <span>{{ line.text }}</span>
                </div>
                <!-- Plain text -->
                <div v-else class="fmt-text">{{ line.text }}</div>
              </template>
            </div>
          </details>
          <div v-if="!scriptStore.script.episodes?.length" class="script-episode-empty">
            暂无剧集内容
          </div>
        </div>
      </div>
    </template>
  </div>

  <!-- Bottom bar -->
  <div v-if="scriptStore.script" class="bottom-action-bar">
    <div class="bar-hint">
      <div class="bar-icon">🤖</div>
      <span>剧本内容整理完毕，可以进行下一步了</span>
    </div>
    <div class="bar-actions">
      <button class="btn btn-primary btn-sm" :disabled="advancing" @click="goToAssets">
        {{ advancing ? '提交中...' : '下一步' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
/* ── Script Meta (two rows) ── */
.script-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 28px;
  padding: 0 4px;
}
.script-meta-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 14px;
}
.script-meta-label {
  color: #999;
  flex-shrink: 0;
}
.script-meta-value {
  color: #333;
  font-weight: 400;
}

/* ── Section ── */
.script-section {
  margin-bottom: 32px;
}
.script-section-title {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 16px;
}

/* ── Summary card ── */
.script-summary-card {
  background: #f7f7f9;
  border-radius: 12px;
  padding: 28px 32px;
}
.script-summary-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.script-summary-label {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 4px;
}
.script-summary-value {
  font-size: 14px;
  color: #444;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* ── Script content header ── */
.script-content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.script-content-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── Episode accordions ── */
.script-episodes {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}
.script-episode {
  border-bottom: 1px solid #F3F4F6;
}
.script-episode:last-child {
  border-bottom: none;
}
.script-episode[open] {
  background: #FAFAFA;
}
.script-episode-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  user-select: none;
  list-style: none;
  transition: background 0.15s;
}
.script-episode-summary:hover {
  background: #F9FAFB;
}
.script-episode-summary::-webkit-details-marker {
  display: none;
}
.script-episode-arrow {
  color: #bbb;
  flex-shrink: 0;
  transition: transform 0.2s;
}
details[open] > .script-episode-summary .script-episode-arrow {
  transform: rotate(90deg);
}
.script-episode-label {
  color: #7c3aed;
  font-weight: 600;
  flex-shrink: 0;
}
.script-episode-title {
  font-weight: 500;
  color: #1a1a1a;
  flex: 1;
}
.script-episode-chars {
  font-size: 11px;
  color: #9CA3AF;
  flex-shrink: 0;
  background: #F3F4F6;
  padding: 2px 8px;
  border-radius: 6px;
}
.script-episode-content {
  padding: 4px 16px 24px 32px;
}
.script-episode-empty {
  padding: 24px 16px 24px 32px;
  font-size: 13px;
  color: #9CA3AF;
}

/* ── Formatted Script Lines ── */

.fmt-empty {
  height: 12px;
}

.fmt-separator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 0;
  color: #D1D5DB;
  font-size: 12px;
  letter-spacing: 6px;
}

/* Scene description */
.fmt-scene {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 10px 0 6px 0;
  border-left: 3px solid #A78BFA;
  padding-left: 14px;
  margin: 8px 0;
}
.fmt-scene-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 6px;
  background: #EDE9FE;
  color: #7C3AED;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
  letter-spacing: 0.5px;
}
.fmt-scene-text {
  font-size: 14px;
  color: #4B5563;
  line-height: 1.8;
}

/* Dialogue */
.fmt-dialogue {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 6px 0 6px 14px;
  line-height: 1.8;
}
.fmt-dialogue-speaker {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  color: #7C3AED;
  white-space: nowrap;
  min-width: 60px;
}
.fmt-dialogue-speaker::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #A78BFA;
}
.fmt-dialogue-text {
  font-size: 15px;
  color: #1F2937;
}

/* Action / parenthetical */
.fmt-action {
  padding: 2px 0 2px 14px;
  font-size: 13px;
  color: #9CA3AF;
  font-style: italic;
}

/* Music cue */
.fmt-music {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0 4px 14px;
  font-size: 13px;
  color: #9CA3AF;
  font-style: italic;
}
.fmt-music-icon {
  font-size: 14px;
}

/* Hook */
.fmt-hook {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  margin: 8px 0;
  background: linear-gradient(135deg, #FEF3C7, #FDE68A);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #92400E;
}
.fmt-hook-icon {
  font-size: 16px;
}

/* Preview */
.fmt-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  margin: 2px 0;
  background: #F0F9FF;
  border-radius: 10px;
  font-size: 13px;
  color: #0369A1;
}
.fmt-preview-icon {
  font-size: 16px;
}

/* Plain text */
.fmt-text {
  padding: 2px 0 2px 14px;
  font-size: 14px;
  color: #4B5563;
  line-height: 1.8;
}

/* ── Rewrite Streaming Overlay ── */
.rewrite-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.rewrite-panel {
  background: #fff;
  border-radius: 20px;
  width: 90%;
  max-width: 720px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}
.rewrite-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 24px 28px 16px;
  border-bottom: 1px solid #F3F4F6;
}
.rewrite-title {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}
.rewrite-subtitle {
  font-size: 13px;
  color: #7C3AED;
  margin: 4px 0 0;
  font-weight: 600;
}
.rewrite-cancel-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 10px;
  background: #FEF2F2;
  color: #DC2626;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.rewrite-cancel-btn:hover {
  background: #FEE2E2;
}
.rewrite-content {
  padding: 16px 28px 24px;
  margin: 0;
  flex: 1;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.9;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}
</style>
