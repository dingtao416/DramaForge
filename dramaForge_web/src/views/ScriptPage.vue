<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useScriptStore } from '@/stores/script'
import { useGenerationStore } from '@/stores/generation'
import { DramaGenreLabel, ProjectStep } from '@/types/enums'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StoryBibleEditor from '@/components/script/StoryBibleEditor.vue'
import { exportScriptToDocx } from '@/utils/exportDocx'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const scriptStore = useScriptStore()
const genStore = useGenerationStore()

const projectId = Number(route.params.id)

// Check if generation is still running for this project
const genRunning = ref(false)
const genProgressContent = ref('')
const initialLoading = ref(true)  // prevents empty state flash

async function loadScript() {
  await scriptStore.fetchScript(projectId)
}

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
          loadScript()
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
        loadScript()
      }
    }, 2000)
    return
  }

  await loadScript()
  initialLoading.value = false
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

const scriptHasEpisodes = computed(() => Boolean(scriptStore.script?.episodes?.length))

const rawScriptPayload = computed<Record<string, any>>(() => {
  const raw = scriptStore.script?.raw_content
  if (!raw) return {}

  try {
    return JSON.parse(raw)
  } catch {
    return {}
  }
})

const originalIdea = computed(() => {
  const projectDescription = projectStore.currentProject?.description?.trim()
  const scriptSeed = scriptStore.script?.one_liner?.trim() || scriptStore.script?.synopsis?.trim()
  return projectDescription || scriptSeed || '暂无原始创意'
})

const summaryStats = computed(() => {
  const script = scriptStore.script
  const project = projectStore.currentProject
  const summary = rawScriptPayload.value.script_summary || {}
  const genre = summary.story_type || script?.genre || (project?.genre ? DramaGenreLabel[project.genre] : '')

  return [
    { label: '自定义集数', value: summary.custom_episode_count ? String(summary.custom_episode_count) : script?.episodes?.length ? String(script.episodes.length) : '未设置' },
    { label: '故事类型', value: genre || '未设置' },
    { label: '目标受众', value: summary.target_audience || '未设置' },
  ]
})

const summaryBlocks = computed(() => {
  const script = scriptStore.script
  if (!script) return []
  const summary = rawScriptPayload.value.script_summary || {}

  return [
    { label: '核心梗', value: summary.core_hook || script.setting },
    { label: '一句话故事', value: summary.one_sentence_story || script.one_liner },
    { label: '人物小传', value: summary.character_biographies || script.protagonist },
    { label: '故事背景', value: script.background },
    { label: '故事概览', value: summary.story_overview || script.synopsis },
    { label: '视频风格', value: styleTags.value },
  ].filter(item => item.value && item.value.trim())
})

const downloading = ref(false)

async function handleDownload() {
  if (downloading.value || !scriptStore.script) return
  downloading.value = true
  try {
    await exportScriptToDocx(
      scriptStore.script,
      projectStore.currentProject?.title,
    )
  } catch (e) {
    console.error('导出 docx 失败', e)
  } finally {
    downloading.value = false
  }
}

const copying = ref(false)
const copySucceeded = ref(false)

async function handleCopy() {
  if (copying.value) return
  const script = scriptStore.script
  if (!script) return

  // Build full script text
  const lines: string[] = []
  const project = projectStore.currentProject
  if (project?.title) lines.push(`《${project.title}》剧本`, '')
  if (script.protagonist) lines.push(`主角：${script.protagonist}`)
  if (script.genre) lines.push(`类型：${script.genre}`)
  if (script.synopsis) lines.push(`梗概：${script.synopsis}`)
  if (script.background) lines.push(`背景：${script.background}`)
  lines.push('')

  for (const ep of (script.episodes || [])) {
    lines.push(`第${ep.number}集：${ep.title || ''}`)
    if (ep.content) {
      lines.push(ep.content)
      lines.push('')
    }
  }

  const fullText = lines.join('\n')
  copying.value = true
  copySucceeded.value = false
  try {
    await navigator.clipboard.writeText(fullText)
  } catch {
    // Fallback for older browsers or non-HTTPS
    const textarea = document.createElement('textarea')
    textarea.value = fullText
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  } finally {
    copying.value = false
  }
  copySucceeded.value = true
  window.setTimeout(() => {
    copySucceeded.value = false
  }, 1600)
}

// ── Story Bible field update ──
async function handleStoryBibleUpdate(field: string, value: string) {
  if (!scriptStore.script) return
  await scriptStore.updateStoryBible(projectId, { [field]: value })
}

const advancing = ref(false)

async function goToAssets() {
  advancing.value = true
  try {
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
      const metaMatch = text.match(/^[（(]([^）)]*)[）)]/)
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
    // Supports both regular "" and smart "" quotes, full-width and half-width punctuation
    const dialogueMatch = trimmed.match(/^\*\*(.+?)\*\*\s*(?:[（(]([^）)]*)[）)])?\s*[：:]\s*["“”](.+)["“”]$/)
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
        text: simpleDialogue[2].replace(/^[""“”]|[""“”]$/g, ''),
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
const initializedScriptId = ref<number | null>(null)

watch(
  () => scriptStore.script,
  (script) => {
    if (!script || initializedScriptId.value === script.id) return
    initializedScriptId.value = script.id
    const firstEpisodeId = script.episodes?.[0]?.id
    expandedEpisodes.value = firstEpisodeId ? new Set([firstEpisodeId]) : new Set()
    allExpanded.value = script.episodes?.length === 1
  },
)

function toggleEpisode(epId: number) {
  if (expandedEpisodes.value.has(epId)) {
    expandedEpisodes.value.delete(epId)
  } else {
    expandedEpisodes.value.add(epId)
  }
  // Trigger reactivity
  expandedEpisodes.value = new Set(expandedEpisodes.value)
  const eps = scriptStore.script?.episodes || []
  allExpanded.value = eps.length > 0 && eps.every(ep => expandedEpisodes.value.has(ep.id))
}

function toggleAllEpisodes() {
  if (allExpanded.value) {
    expandedEpisodes.value.clear()
    allExpanded.value = false
  } else {
    const eps = scriptStore.script?.episodes || []
    eps.forEach(ep => expandedEpisodes.value.add(ep.id))
    allExpanded.value = true
  }
  expandedEpisodes.value = new Set(expandedEpisodes.value)
}
</script>

<template>
  <LoadingOverlay :visible="initialLoading || scriptStore.loading" message="正在加载剧本..." />
  <LoadingOverlay :visible="genRunning" :message="`AI 正在生成剧本...（${genProgressContent.length} 字）`" />

  <div class="script-page-shell">
    <EmptyState
      v-if="!initialLoading && !scriptStore.loading && !scriptHasEpisodes"
      title="暂无剧本"
      description="请从首页开始创作或上传剧本"
      icon="📝"
    />

    <article v-if="scriptStore.script && scriptHasEpisodes" class="script-document">
      <div class="script-document-actions" aria-label="剧本操作">
        <button
          class="script-action-btn"
          type="button"
          :disabled="downloading"
          @click="handleDownload"
        >
          <span class="script-action-icon">⬇</span>
          <span>{{ downloading ? '生成中...' : '下载剧本 .docx' }}</span>
        </button>
      </div>

      <details class="script-document-section" open>
        <summary class="script-document-summary">
          <span class="script-section-caret">›</span>
          <span class="script-section-heading">原始创意</span>
        </summary>
        <div class="script-section-body">
          <p class="script-long-text">{{ originalIdea }}</p>
        </div>
      </details>

      <details class="script-document-section">
        <summary class="script-document-summary">
          <span class="script-section-caret">›</span>
          <span class="script-section-heading">剧本摘要</span>
        </summary>
        <div class="script-section-body">
          <div class="script-summary-stats">
            <div v-for="item in summaryStats" :key="item.label" class="script-summary-stat">
              <div class="script-summary-label">{{ item.label }}</div>
              <div class="script-summary-value">{{ item.value }}</div>
            </div>
          </div>
          <div class="script-summary-blocks">
            <div v-for="item in summaryBlocks" :key="item.label" class="script-summary-block">
              <div class="script-summary-label">{{ item.label }}</div>
              <div class="script-summary-value">{{ item.value }}</div>
            </div>
          </div>
        </div>
      </details>

      <details class="script-document-section" open>
        <summary class="script-document-summary">
          <span class="script-section-caret">›</span>
          <span class="script-section-heading">Story Bible</span>
        </summary>
        <div class="script-section-body">
          <StoryBibleEditor
            :script="scriptStore.script"
            @update="handleStoryBibleUpdate"
          />
        </div>
      </details>

      <details class="script-document-section" open>
        <summary class="script-document-summary">
          <span class="script-section-caret">›</span>
          <span class="script-section-heading">分集剧本</span>
        </summary>

        <div class="script-section-body">
          <div class="script-episodes">
            <details
              v-for="ep in scriptStore.script.episodes"
              :key="ep.id"
              class="script-episode"
              :open="expandedEpisodes.has(ep.id)"
            >
              <summary class="script-episode-summary" @click.prevent="toggleEpisode(ep.id)">
                <span class="script-episode-arrow">›</span>
                <span class="script-episode-index">{{ ep.number }}.</span>
                <span class="script-episode-title">{{ ep.title || '无标题' }}</span>
              </summary>
              <div v-if="!ep.content" class="script-episode-empty">暂无内容</div>
              <div v-else class="script-episode-content">
                <template v-for="(line, li) in formatScriptContent(ep.content)" :key="li">
                  <div v-if="line.type === 'empty'" class="fmt-empty" />
                  <div v-else-if="line.type === 'separator'" class="fmt-separator">
                    <span>---</span>
                  </div>
                  <div v-else-if="line.type === 'scene'" class="fmt-scene">
                    <span v-if="line.meta" class="fmt-scene-tag">{{ line.meta }}</span>
                    <span class="fmt-scene-text">{{ line.text }}</span>
                  </div>
                  <div v-else-if="line.type === 'dialogue'" class="fmt-dialogue">
                    <span class="fmt-dialogue-speaker">{{ line.meta }}</span>
                    <span class="fmt-dialogue-text">{{ line.text }}</span>
                  </div>
                  <div v-else-if="line.type === 'action'" class="fmt-action">{{ line.text }}</div>
                  <div v-else-if="line.type === 'music'" class="fmt-music">
                    <span class="fmt-music-icon">♪</span>
                    <span>{{ line.text }}</span>
                  </div>
                  <div v-else-if="line.type === 'hook'" class="fmt-hook">
                    <span class="fmt-hook-icon">🎣</span>
                    <span>{{ line.text }}</span>
                  </div>
                  <div v-else-if="line.type === 'preview'" class="fmt-preview">
                    <span class="fmt-preview-icon">📺</span>
                    <span>{{ line.text }}</span>
                  </div>
                  <div v-else class="fmt-text">{{ line.text }}</div>
                </template>
              </div>
            </details>
            <div v-if="!scriptStore.script.episodes?.length" class="script-episode-empty">
              暂无剧集内容
            </div>
          </div>
        </div>
      </details>
    </article>

  </div>

  <div v-if="scriptStore.script && scriptHasEpisodes" class="bottom-action-bar script-bottom-bar">
    <div class="bar-hint script-bar-hint">
      <div class="bar-icon script-bar-icon">✓</div>
      <div class="script-bar-copy">
        <strong>剧本已就绪</strong>
        <span>确认内容后进入角色、场景资产生成</span>
      </div>
    </div>
    <div class="bar-actions">
      <button class="script-next-btn" type="button" :disabled="advancing" @click="goToAssets">
        <span>{{ advancing ? '提交中' : '下一步' }}</span>
        <span class="script-next-icon">→</span>
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
  color: #2D2515;
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
  color: #2D2515;
  margin-bottom: 4px;
}
.script-summary-value {
  font-size: 14px;
  color: #444;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* ── Episode accordions ── */
.script-episodes {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  overflow: hidden;
  background: #FDF5D6;
}
.script-episode {
  border-bottom: 1px solid #F3F4F6;
}
.script-episode:last-child {
  border-bottom: none;
}
.script-episode[open] {
  background: #FEF9E7;
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
  color: #E8A317;
  font-weight: 600;
  flex-shrink: 0;
}
.script-episode-title {
  font-weight: 500;
  color: #2D2515;
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
  color: #A89870;
  font-size: 12px;
  letter-spacing: 6px;
}

/* Scene description */
.fmt-scene {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 10px 0 6px 0;
  border-left: 3px solid #F5C34B;
  padding-left: 14px;
  margin: 8px 0;
}
.fmt-scene-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 6px;
  background: rgba(232, 163, 23, 0.1);
  color: #E8A317;
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
  color: #E8A317;
  white-space: nowrap;
  min-width: 60px;
}
.fmt-dialogue-speaker::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #F5C34B;
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

.script-page-shell {
  min-height: calc(100vh - 56px);
  padding: 28px 0 116px;
  background:
    linear-gradient(180deg, #f6f0de 0%, #eef1f4 42%, #e8ecef 100%);
}

.script-document {
  position: relative;
  width: min(940px, calc(100vw - 96px));
  margin: 0 auto;
  padding: 42px 58px 88px;
  border: 1px solid rgba(26, 21, 8, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 18px 54px rgba(30, 35, 45, 0.12);
  color: #182235;
  font-size: 14px;
  line-height: 1.85;
  font-family: "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
}

.script-document-actions {
  position: sticky;
  top: 76px;
  z-index: 4;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  height: 0;
  margin-bottom: 8px;
  pointer-events: none;
}

.script-action-btn,
.script-inline-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 92px;
  height: 36px;
  padding: 0 14px;
  border: 1px solid rgba(24, 34, 53, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  color: #526071;
  box-shadow: 0 8px 24px rgba(31, 41, 55, 0.08);
  font-size: 13px;
  font-weight: 600;
  font-family: "PingFang SC", "Microsoft YaHei", system-ui, sans-serif !important;
  letter-spacing: 0;
  cursor: pointer;
  transition:
    background 0.16s ease,
    border-color 0.16s ease,
    color 0.16s ease,
    box-shadow 0.16s ease,
    transform 0.16s ease;
}

.script-action-btn {
  pointer-events: auto;
}

.script-action-btn:hover:not(:disabled),
.script-inline-btn:hover:not(:disabled) {
  border-color: rgba(232, 163, 23, 0.38);
  background: #fff8e2;
  color: #2d2515;
  box-shadow: 0 10px 28px rgba(184, 125, 8, 0.16);
  transform: translateY(-1px);
}

.script-action-btn:active:not(:disabled),
.script-inline-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 5px 14px rgba(31, 41, 55, 0.1);
}

.script-action-btn:focus-visible,
.script-inline-btn:focus-visible,
.script-next-btn:focus-visible,
.script-episode-summary:focus-visible,
.script-document-summary:focus-visible {
  outline: 3px solid rgba(93, 173, 226, 0.34);
  outline-offset: 3px;
}

.script-action-btn.success {
  border-color: rgba(46, 204, 113, 0.38);
  background: #edf9f2;
  color: #1f7a45;
}

.script-action-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  font-size: 14px;
  line-height: 1;
}

.script-action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.68;
  transform: none;
}

.script-document-section {
  margin-top: 34px;
}

.script-document-section:first-of-type {
  margin-top: 0;
}

.script-document-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  width: fit-content;
  min-height: 40px;
  border-radius: 10px;
  list-style: none;
  cursor: pointer;
  user-select: none;
  transition: color 0.16s ease, background 0.16s ease;
}

.script-document-summary:hover {
  color: #b87d08;
}

.script-document-summary::-webkit-details-marker {
  display: none;
}

.script-document-summary.static {
  cursor: default;
}

.script-section-caret {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: #f3f5f7;
  color: #475569;
  font-size: 18px;
  line-height: 1;
  transform: rotate(0deg);
  transition: background 0.16s ease, color 0.16s ease, transform 0.16s ease;
}

details[open] > .script-document-summary .script-section-caret,
.script-section-caret.open {
  transform: rotate(90deg);
  background: #fff2c4;
  color: #b87d08;
}

.script-section-heading {
  color: #182235;
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 0;
}

.script-section-body {
  padding: 18px 0 0 32px;
}

.script-long-text,
.script-summary-value {
  color: #253145;
  white-space: pre-wrap;
  word-break: break-word;
}

.script-summary-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 26px;
}

.script-summary-stat {
  min-height: 82px;
  padding: 14px 16px;
  border: 1px solid rgba(24, 34, 53, 0.08);
  border-radius: 8px;
  background: #f8fafc;
}

.script-summary-blocks {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.script-summary-label {
  margin-bottom: 6px;
  color: #667789;
  font-size: 13px;
  font-weight: 600;
}

.script-summary-value {
  font-size: 14px;
  line-height: 1.85;
}

.script-content-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  flex-wrap: wrap;
}

.script-episodes {
  gap: 0;
  margin-top: 22px;
  padding-left: 32px;
  border: none;
  border-radius: 0;
  overflow: visible;
  background: transparent;
}

.script-episode {
  position: relative;
  border-bottom: 1px solid rgba(24, 34, 53, 0.08);
  background: transparent;
}

.script-episode:last-child {
  border-bottom: none;
}

.script-episode[open] {
  background: transparent;
}

.script-episode-summary {
  gap: 10px;
  min-height: 52px;
  padding: 12px 10px 12px 0;
  border-radius: 10px;
  color: #182235;
  font-size: 15px;
  line-height: 1.5;
  transition: color 0.16s ease, transform 0.16s ease;
}

.script-episode-summary:hover {
  background: transparent;
  color: #b87d08;
}

.script-episode-arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: #f3f5f7;
  color: #475569;
  font-size: 16px;
  line-height: 1;
  transform: rotate(0deg);
  transition: background 0.16s ease, color 0.16s ease, transform 0.16s ease;
}

details[open] > .script-episode-summary .script-episode-arrow {
  transform: rotate(90deg);
  background: #fff2c4;
  color: #b87d08;
}

.script-episode-index {
  color: #b87d08;
  font-size: 15px;
  font-weight: 700;
}

.script-episode-title {
  min-width: 0;
  color: inherit;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.script-episode-content {
  padding: 6px 0 30px 32px;
}

.script-episode-empty {
  padding: 14px 0 22px 32px;
  color: #8a97a8;
}

.fmt-empty {
  height: 14px;
}

.fmt-separator {
  justify-content: flex-start;
  padding: 12px 0;
  color: #8a97a8;
  letter-spacing: 0;
}

.fmt-scene,
.fmt-dialogue,
.fmt-action,
.fmt-music,
.fmt-hook,
.fmt-preview,
.fmt-text {
  margin: 0;
  padding: 2px 0;
  border-left: none;
  background: transparent;
  color: #253145;
  font-size: 14px;
  line-height: 1.85;
}

.fmt-scene {
  align-items: baseline;
  gap: 9px;
}

.fmt-scene-tag {
  flex-shrink: 0;
  border-radius: 6px;
  background: #eef5fb;
  color: #426f91;
  padding: 1px 7px;
}

.fmt-dialogue-speaker {
  min-width: 60px;
  color: #182235;
}

.fmt-dialogue-speaker::before {
  display: none;
}

.fmt-dialogue-text {
  color: #253145;
}

.fmt-hook,
.fmt-preview {
  font-weight: 400;
}

.fmt-hook {
  border-radius: 8px;
  background: #fff7db;
  color: #7a4f07;
}

.fmt-preview {
  border-radius: 8px;
  background: #edf7ff;
  color: #255f88;
}

.script-bottom-bar {
  height: 68px;
  padding: 10px 34px;
  border-top: 1px solid rgba(24, 34, 53, 0.12);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 -16px 42px rgba(30, 35, 45, 0.12);
  backdrop-filter: blur(14px);
}

.script-bar-hint {
  gap: 12px;
  color: #526071;
}

.script-bar-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #edf9f2;
  color: #1f7a45;
  font-size: 16px;
  font-weight: 800;
}

.script-bar-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.script-bar-copy strong {
  color: #182235;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.25;
}

.script-bar-copy span {
  color: #667789;
  font-size: 12px;
  line-height: 1.35;
}

.script-next-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-width: 128px;
  height: 44px;
  padding: 0 18px;
  border: none;
  border-radius: 10px;
  background: #1f2937;
  color: #fff;
  box-shadow: 0 12px 28px rgba(31, 41, 55, 0.22);
  font-family: "PingFang SC", "Microsoft YaHei", system-ui, sans-serif !important;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0;
  cursor: pointer;
  transition:
    background 0.16s ease,
    box-shadow 0.16s ease,
    transform 0.16s ease;
}

.script-next-btn:hover:not(:disabled) {
  background: #111827;
  box-shadow: 0 14px 32px rgba(17, 24, 39, 0.28);
  transform: translateY(-1px);
}

.script-next-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 8px 18px rgba(17, 24, 39, 0.22);
}

.script-next-btn:disabled {
  cursor: not-allowed;
  opacity: 0.68;
  transform: none;
}

.script-next-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  line-height: 1;
}

@media (max-width: 760px) {
  .script-page-shell {
    padding: 10px 0 134px;
  }

  .script-document {
    width: calc(100vw - 24px);
    padding: 24px 18px 58px;
    border-radius: 14px;
  }

  .script-document-actions {
    position: static;
    height: auto;
    justify-content: flex-end;
    margin-bottom: 18px;
  }

  .script-summary-stats {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .script-section-body,
  .script-episodes {
    padding-left: 0;
  }

  .script-episode-content {
    padding-left: 28px;
  }

  .script-bottom-bar {
    align-items: stretch;
    height: auto;
    min-height: 96px;
    padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
    flex-direction: column;
    gap: 10px;
  }

  .script-bottom-bar .bar-actions {
    width: 100%;
    margin-left: 0;
  }

  .script-next-btn {
    width: 100%;
  }

  .script-bar-copy span {
    font-size: 11px;
  }
}
</style>
