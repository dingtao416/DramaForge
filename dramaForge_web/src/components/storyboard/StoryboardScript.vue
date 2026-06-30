<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { SegmentDetail } from '@/types/segment'
import type { ShotDetail, ShotUpdate, ShotVisualReference } from '@/types/shot'
import type { CharacterDetail } from '@/types/character'
import type { SceneDetail } from '@/types/scene'
import { firstReferenceImageUrl } from '@/utils/referenceImages'

const props = defineProps<{
  segment: SegmentDetail | null
  segmentIndex: number
  generating?: boolean
  addingShot?: boolean
  deletingShotId?: number | null
  lockedCharacterIds?: Set<number>
  characters?: CharacterDetail[]
  scenes?: SceneDetail[]
  referencesEnabled?: boolean
  referenceModelHint?: string
  savingScript?: boolean
  generatingShotIds?: Set<number>
  selectedShot?: ShotDetail | null
}>()

const emit = defineEmits<{
  editScript: []
  saveScript: [updates: Array<{ shot: ShotDetail; data: ShotUpdate }>]
  regenerate: []
  generateSegment: []
  generateShot: [shot: ShotDetail]
  selectShot: [shot: ShotDetail, index: number]
  addShot: []
  deleteShot: [shotId: number]
  updateShotReferences: [shot: ShotDetail, references: ShotVisualReference[]]
}>()

const statusConfig: Record<string, { label: string; cls: string }> = {
  pending: { label: '待生成', cls: 'status-muted' },
  generating: { label: '生成中', cls: 'status-active' },
  completed: { label: '已完成', cls: 'status-done' },
  partial: { label: '部分完成', cls: 'status-warn' },
  failed: { label: '生成失败', cls: 'status-error' },
}

const status = computed(() => {
  if (!props.segment) return null
  return statusConfig[props.segment.status] || statusConfig.pending
})

const segmentNo = computed(() => String(props.segmentIndex + 1).padStart(2, '0'))
const editingDocument = ref(false)
const scriptDraft = ref('')
const scriptTextarea = ref<HTMLTextAreaElement | null>(null)

const segmentDuration = computed(() => {
  const duration = props.segment?.duration || 0
  return duration > 0 ? `${Math.round(duration)}s` : '--'
})

const generatedShotCount = computed(() => {
  const shots = props.segment?.shots || []
  return shots.filter(shot => shot.video_url || shot.image_url).length
})

const referenceImages = computed(() => {
  if (!props.segment) return []
  const urls = [
    props.segment.thumbnail_url,
    ...props.segment.shots.map(shot => shot.image_url),
  ].filter((url): url is string => Boolean(url))

  return Array.from(new Set(urls)).slice(0, 4)
})

const scriptReferenceOptions = computed(() => {
  const options: ShotVisualReference[] = []
  const seen = new Set<string>()
  const addOption = (reference: ShotVisualReference | null) => {
    if (!reference || seen.has(reference.id)) return
    seen.add(reference.id)
    options.push(reference)
  }

  for (const shot of props.segment?.shots || []) {
    for (const reference of shotReferences(shot)) addOption(reference)
  }

  for (const character of props.characters || []) addOption(characterReference(character))
  for (const scene of props.scenes || []) addOption(sceneReference(scene))

  return options
})

const referenceById = computed(() => {
  const map = new Map<string, ShotVisualReference>()
  for (const reference of scriptReferenceOptions.value) map.set(reference.id, reference)
  return map
})

const sceneRefs = computed(() => {
  const refs = (props.segment?.shots || [])
    .map(shot => shot.scene_ref)
    .filter((ref): ref is string => Boolean(ref))
  return Array.from(new Set(refs))
})

const characterRefs = computed(() => {
  const chars = (props.segment?.shots || []).flatMap(shot => shot.characters || [])
  return Array.from(new Set(chars.map(characterLabel))).filter(Boolean)
})

function characterLabel(char: ShotDetail['characters'][number]) {
  const value = char as any
  if (typeof value === 'string') return value
  if (value?.name) return value.name
  if (value?.character_name) return value.character_name
  if (value?.char_id) {
    return props.characters?.find(item => item.id === Number(value.char_id))?.name || `角色${value.char_id}`
  }
  return ''
}

function shotPrompt(shot: ShotDetail) {
  return shot.video_prompt || shot.image_prompt || shot.background || '暂无画面提示词'
}

function shotMediaUrl(shot: ShotDetail) {
  return shot.image_url || ''
}

function normalizeRefName(value: string | undefined) {
  return (value || '').replace(/^@/, '').trim()
}

function shotReferences(shot: ShotDetail) {
  return shot.visual_references || []
}

function roleLabel(role: string) {
  return ({
    identity: '形象',
    environment: '场景',
    composition: '构图',
    style: '风格',
  } as Record<string, string>)[role] || role
}

function characterReference(char: CharacterDetail): ShotVisualReference | null {
  const image = firstReferenceImageUrl(char.reference_images)
  if (!image) return null
  return {
    id: `character:${char.id}:0`,
    type: 'character',
    asset_id: char.id,
    image_url: image,
    label: char.name,
    role: 'identity',
    target: char.name,
    placement: 'center_foreground',
    scope: 'whole_shot',
    instruction: `保持${char.name}的角色外观、服饰和整体轮廓。`,
  }
}

function sceneReference(scene: SceneDetail): ShotVisualReference | null {
  const image = firstReferenceImageUrl(scene.reference_images)
  if (!image) return null
  return {
    id: `scene:${scene.id}:0`,
    type: 'scene',
    asset_id: scene.id,
    image_url: image,
    label: scene.name,
    role: 'environment',
    target: scene.name,
    placement: 'background',
    scope: 'whole_shot',
    instruction: `保持${scene.name}的空间结构、环境质感和光照氛围。`,
  }
}

function suggestedReferences(shot: ShotDetail) {
  const existing = new Set(shotReferences(shot).map(ref => ref.id))
  const suggestions: ShotVisualReference[] = []

  for (const shotChar of shot.characters || []) {
    const charId = Number((shotChar as any).char_id || (shotChar as any).id)
    const charName = normalizeRefName((shotChar as any).name || (shotChar as any).character_name)
    const char = props.characters?.find(item => item.id === charId || normalizeRefName(item.name) === charName)
    const ref = char ? characterReference(char) : null
    if (ref && !existing.has(ref.id)) suggestions.push(ref)
  }

  const sceneName = normalizeRefName(shot.scene_ref)
  const scene = props.scenes?.find((item) => {
    const name = normalizeRefName(item.name)
    return name === sceneName || Boolean(sceneName && (sceneName.includes(name) || name.includes(sceneName)))
  })
  const ref = scene ? sceneReference(scene) : null
  if (ref && !existing.has(ref.id)) suggestions.push(ref)

  return suggestions
}

function addReference(shot: ShotDetail, reference: ShotVisualReference) {
  if (!props.referencesEnabled) return
  emit('updateShotReferences', shot, [...shotReferences(shot), reference])
}

function removeReference(shot: ShotDetail, referenceId: string) {
  emit('updateShotReferences', shot, shotReferences(shot).filter(ref => ref.id !== referenceId))
}

function editReference(shot: ShotDetail, reference: ShotVisualReference) {
  const instruction = window.prompt('参考图作用说明', reference.instruction)
  if (instruction === null) return
  const placement = window.prompt('出现位置', reference.placement)
  if (placement === null) return
  emit('updateShotReferences', shot, shotReferences(shot).map(ref =>
    ref.id === reference.id ? { ...ref, instruction, placement } : ref
  ))
}

function chineseNumber(value: number) {
  const labels = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
  if (value <= 10) return labels[value]
  if (value < 20) return `十${labels[value - 10]}`
  const ten = Math.floor(value / 10)
  const one = value % 10
  return `${labels[ten]}十${one ? labels[one] : ''}`
}

function formatTimestamp(seconds: number) {
  const safe = Math.max(0, Math.round(seconds))
  const min = Math.floor(safe / 60)
  const sec = safe % 60
  return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

function shotStartTime(index: number) {
  const shots = props.segment?.shots || []
  return shots.slice(0, index).reduce((sum, shot) => sum + (Number(shot.duration) || 0), 0)
}

function shotTimeRange(shot: ShotDetail, index: number) {
  const start = shotStartTime(index)
  const end = start + (Number(shot.duration) || 0)
  return `${formatTimestamp(start)}-${formatTimestamp(end)}`
}

function referenceToken(reference: ShotVisualReference) {
  return `{{ref:${reference.id}}}`
}

function cleanTextValue(value: string) {
  return value
    .replace(/\{\{ref:[^}]+\}\}/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function buildShotBlock(shot: ShotDetail, index: number) {
  const references = shotReferences(shot)
  const lines = [
    `分镜${chineseNumber(index + 1)}：${shotTimeRange(shot, index)}`,
    `景别：${shot.camera_type || '未设定'}`,
    `构图：${shot.camera_angle || '未设定'}`,
    `运镜手法：${shot.camera_movement || '未设定'}`,
    `画面内容：${shotPrompt(shot)}`,
  ]

  if (references.length) lines.push(`参考图：${references.map(referenceToken).join(' ')}`)
  if (shot.scene_ref) lines.push(`场景：${shot.scene_ref}`)
  if (shot.emotion) lines.push(`情绪：${shot.emotion}`)
  if (shot.narration) lines.push(`旁白：${shot.narration}`)
  if (shot.dialogue) lines.push(`台词：${shot.dialogue}`)
  if (shot.voice_style) lines.push(`声音：${shot.voice_style}`)

  return lines.join('\n')
}

const sceneSettingText = computed(() => {
  if (!sceneRefs.value.length) return '以当前片段场景设定为准。'
  return `${sceneRefs.value.map(ref => `<location>${ref}</location>`).join('、')}。`
})

const roleSettingText = computed(() => {
  if (!characterRefs.value.length) return '以当前片段角色设定为准。'
  return characterRefs.value.map(ref => `<role>${ref}</role>`).join('、')
})

function compactSentence(value: string | undefined) {
  return (value || '')
    .replace(/\{\{ref:[^}]+\}\}/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function firstClause(value: string | undefined, maxLength = 80) {
  const text = compactSentence(value)
  if (!text) return ''
  const [head] = text.split(/[。；;.!！?？\n]/)
  const clause = head || text
  return clause.length > maxLength ? `${clause.slice(0, maxLength)}...` : clause
}

function uniqueNonEmpty(values: string[]) {
  return Array.from(new Set(values.map(value => value.trim()).filter(Boolean)))
}

const shotVisualSummaries = computed(() => {
  const shots = props.segment?.shots || []
  return uniqueNonEmpty(
    shots.map(shot => firstClause(shot.background || shot.image_prompt || shot.video_prompt))
  )
})

const shotSoundSummaries = computed(() => {
  const shots = props.segment?.shots || []
  return uniqueNonEmpty(shots.map(shot => firstClause(shot.voice_style || shot.dialogue, 72)))
})

const shotEmotionSummaries = computed(() => {
  const shots = props.segment?.shots || []
  return uniqueNonEmpty(shots.map(shot => firstClause(shot.emotion || shot.narration || shot.background, 64)))
})

const styleSettingText = computed(() => {
  const style = props.segment?.style?.trim()
  if (style) return style
  const summaries = shotVisualSummaries.value.slice(0, 2)
  if (summaries.length) return `根据当前分镜动态推断：${summaries.join('；')}。`
  return '根据剧本题材、场景资产、角色设定和分镜画面动态推断。'
})

const soundSettingText = computed(() => {
  const summaries = shotSoundSummaries.value.slice(0, 2)
  if (summaries.length) return `根据当前分镜动态推断：${summaries.join('；')}。`
  return '根据剧本对白、环境、动作节奏和场景空间动态推断。'
})

const styleCoreText = computed(() => {
  const summaries = shotEmotionSummaries.value.slice(0, 2)
  if (summaries.length) return `围绕当前片段冲突动态推断：${summaries.join('；')}。`
  return '根据剧情核心冲突、角色状态和场景目标动态推断。'
})

const visualToneText = computed(() => {
  const summaries = shotVisualSummaries.value.slice(0, 3)
  if (summaries.length) return `由分镜画面统一推断：${summaries.join('；')}。`
  return '根据场景光线、色彩、空间层次和角色关系动态推断。'
})

const textureText = computed(() => {
  const movements = uniqueNonEmpty((props.segment?.shots || []).map(shot => shot.camera_movement || ''))
  if (movements.length) return `结合当前镜头运动动态推断：${movements.slice(0, 4).join('、')}。`
  return '根据目标视频风格、镜头运动和画面细节动态推断。'
})

const baseSettingLines = computed(() => [
  '【基础设定】',
  `画面风格和类型：${styleSettingText.value}`,
  `场景：${sceneSettingText.value}`,
  `角色：${roleSettingText.value}`,
  `声音：${soundSettingText.value}`,
])

const atmosphereLines = computed(() => [
  '【氛围与画质】',
  `风格核心：${styleCoreText.value}`,
  `视觉基调：${visualToneText.value}`,
  `画面质感：${textureText.value}`,
])

const scriptDocument = computed(() => {
  if (!props.segment) return ''
  const shots = props.segment.shots.map(buildShotBlock).join('\n\n')
  return [
    baseSettingLines.value.join('\n'),
    atmosphereLines.value.join('\n'),
    '【画面内容】',
    shots || '暂无分镜内容。',
  ].join('\n\n')
})

const documentLines = computed(() => scriptDraft.value.split(/\r?\n/))

const selectedShotGenerating = computed(() => {
  const shot = props.selectedShot
  if (!shot) return false
  return Boolean(props.generatingShotIds?.has(shot.id) || shot.shot_status === 'generating')
})

watch(() => props.segment?.id, () => {
  editingDocument.value = false
  scriptDraft.value = scriptDocument.value
}, { immediate: true })

watch(scriptDocument, (value) => {
  if (!editingDocument.value) {
    scriptDraft.value = value
  }
})

function startDocumentEdit() {
  scriptDraft.value = scriptDocument.value
  editingDocument.value = true
  nextTick(() => scriptTextarea.value?.focus())
}

function cancelDocumentEdit() {
  scriptDraft.value = scriptDocument.value
  editingDocument.value = false
}

function insertReferenceToken(reference: ShotVisualReference) {
  if (!editingDocument.value) startDocumentEdit()

  nextTick(() => {
    const textarea = scriptTextarea.value
    const token = ` ${referenceToken(reference)} `
    const start = textarea?.selectionStart ?? scriptDraft.value.length
    const end = textarea?.selectionEnd ?? start
    scriptDraft.value = `${scriptDraft.value.slice(0, start)}${token}${scriptDraft.value.slice(end)}`
    nextTick(() => {
      if (!textarea) return
      const cursor = start + token.length
      textarea.focus()
      textarea.setSelectionRange(cursor, cursor)
    })
  })
}

function lineParts(line: string) {
  const parts: Array<{ type: 'text'; value: string } | { type: 'reference'; value: ShotVisualReference }> = []
  const pattern = /\{\{ref:([^}]+)\}\}/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = pattern.exec(line)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', value: line.slice(lastIndex, match.index) })
    }

    const reference = referenceById.value.get(match[1])
    if (reference) {
      parts.push({ type: 'reference', value: reference })
    } else {
      parts.push({ type: 'text', value: match[0] })
    }
    lastIndex = pattern.lastIndex
  }

  if (lastIndex < line.length) parts.push({ type: 'text', value: line.slice(lastIndex) })
  return parts.length ? parts : [{ type: 'text' as const, value: line }]
}

function lineClass(line: string) {
  if (!line.trim()) return 'doc-line blank'
  if (/^【.+】$/.test(line.trim())) return 'doc-line section-title'
  if (/^分镜/.test(line.trim())) return 'doc-line shot-heading'
  if (/^(台词|旁白|声音)：/.test(line.trim())) return 'doc-line sound-line'
  return 'doc-line'
}

function shotIndexForLine(lineIndex: number) {
  let currentShotIndex = -1
  for (let index = 0; index <= lineIndex; index += 1) {
    const line = documentLines.value[index]?.trim() || ''
    if (/^分镜\s*(?:\d+|[一二三四五六七八九十]+)[：:]/.test(line)) {
      currentShotIndex += 1
    }
  }
  return currentShotIndex >= 0 ? currentShotIndex : null
}

function shotForLine(lineIndex: number) {
  const index = shotIndexForLine(lineIndex)
  if (index === null) return null
  const shot = props.segment?.shots[index]
  return shot ? { shot, index } : null
}

function selectLineShot(lineIndex: number) {
  const match = shotForLine(lineIndex)
  if (!match) return
  emit('selectShot', match.shot, match.index)
}

function isSelectedShotLine(lineIndex: number) {
  const match = shotForLine(lineIndex)
  return Boolean(match && props.selectedShot?.id === match.shot.id)
}

function splitShotBlocks(text: string) {
  const lines = text.split(/\r?\n/)
  const blocks: string[][] = []
  let current: string[] | null = null

  for (const line of lines) {
    if (/^分镜\s*(?:\d+|[一二三四五六七八九十]+)[：:]/.test(line.trim())) {
      if (current) blocks.push(current)
      current = [line]
    } else if (current) {
      current.push(line)
    }
  }

  if (current) blocks.push(current)
  return blocks.map(block => block.join('\n'))
}

function extractField(block: string, label: string) {
  const pattern = new RegExp(`^${label}\\s*[：:]\\s*(.*)$`, 'm')
  const match = block.match(pattern)
  return match ? cleanTextValue(match[1]) : undefined
}

function fieldValueOrEmpty(block: string, label: string) {
  return extractField(block, label) ?? ''
}

function parseTimeToSeconds(value: string) {
  const [min, sec] = value.split(':').map(part => Number(part))
  if (!Number.isFinite(min) || !Number.isFinite(sec)) return null
  return min * 60 + sec
}

function extractDuration(block: string) {
  const headerMatch = block.match(/^分镜\s*(?:\d+|[一二三四五六七八九十]+)[：:]\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})/m)
  if (headerMatch) {
    const start = parseTimeToSeconds(headerMatch[1])
    const end = parseTimeToSeconds(headerMatch[2])
    if (start !== null && end !== null && end > start) return end - start
  }

  const durationMatch = block.match(/时长\s*[：:]\s*(\d+(?:\.\d+)?)\s*s?/i)
  return durationMatch ? Number(durationMatch[1]) : undefined
}

function extractReferences(block: string) {
  const references: ShotVisualReference[] = []
  const seen = new Set<string>()
  for (const match of block.matchAll(/\{\{ref:([^}]+)\}\}/g)) {
    const reference = referenceById.value.get(match[1])
    if (reference && !seen.has(reference.id)) {
      seen.add(reference.id)
      references.push(reference)
    }
  }
  return references
}

function saveDocumentEdit() {
  if (!props.segment) return
  const blocks = splitShotBlocks(scriptDraft.value)
  const updates = props.segment.shots.map((shot, index) => {
    const block = blocks[index] || ''
    const data: ShotUpdate = {}
    const duration = extractDuration(block)
    const cameraType = fieldValueOrEmpty(block, '景别')
    const cameraAngle = fieldValueOrEmpty(block, '构图')
    const cameraMovement = fieldValueOrEmpty(block, '运镜手法')
    const prompt = fieldValueOrEmpty(block, '画面内容')
    const sceneRef = fieldValueOrEmpty(block, '场景')
    const emotion = fieldValueOrEmpty(block, '情绪')
    const narration = fieldValueOrEmpty(block, '旁白')
    const dialogue = fieldValueOrEmpty(block, '台词')
    const voiceStyle = fieldValueOrEmpty(block, '声音')

    if (duration !== undefined && Number.isFinite(duration)) data.duration = duration
    data.camera_type = cameraType
    data.camera_angle = cameraAngle
    data.camera_movement = cameraMovement
    data.background = prompt
    data.image_prompt = prompt
    data.video_prompt = prompt
    data.scene_ref = sceneRef
    data.emotion = emotion
    data.narration = narration
    data.dialogue = dialogue
    data.voice_style = voiceStyle
    data.visual_references = extractReferences(block)

    return { shot, data }
  })

  editingDocument.value = false
  emit('saveScript', updates)
}
</script>

<template>
  <div class="script-stage">
    <template v-if="segment">
      <header class="segment-head">
        <div class="segment-cover">
          <img
            v-if="segment.thumbnail_url || segment.shots?.[0]?.image_url"
            :src="segment.thumbnail_url || segment.shots?.[0]?.image_url || ''"
            alt=""
            loading="lazy"
          />
          <span v-else>{{ segmentNo }}</span>
        </div>

        <div class="segment-title-block">
          <div class="segment-title-row">
            <h2>片段 {{ segmentNo }}</h2>
            <span v-if="status" class="segment-status" :class="status.cls">
              <span v-if="segment.status === 'generating'" class="status-spinner" />
              {{ status.label }}
            </span>
          </div>
          <p>
            输入 @ 可快速调整镜头时长、引用角色、场景、素材。
            视频每秒消耗 11 积分，以实际生成为准
          </p>
        </div>

        <div class="segment-stats">
          <span>{{ segment.shots.length }} 分镜</span>
          <span>{{ segmentDuration }}</span>
          <span>{{ generatedShotCount }}/{{ segment.shots.length }} 素材</span>
        </div>
      </header>

      <div v-if="referenceImages.length" class="reference-strip" aria-label="片段参考图">
        <button
          v-for="(url, index) in referenceImages"
          :key="url"
          type="button"
          class="reference-thumb"
          :title="`参考图 ${index + 1}`"
        >
          <img :src="url" alt="" loading="lazy" />
        </button>
      </div>

      <section class="script-document" :class="{ editing: editingDocument }">
        <div class="document-toolbar">
          <div class="document-kicker">
            <span>片段分镜</span>
            <em>{{ segment.shots.length }} 分镜 · {{ segmentDuration }}</em>
          </div>

          <div v-if="scriptReferenceOptions.length" class="document-reference-tools">
            <button
              v-for="reference in scriptReferenceOptions"
              :key="reference.id"
              type="button"
              class="document-ref-button"
              :title="`插入 ${reference.label}`"
              @click="insertReferenceToken(reference)"
            >
              <img :src="reference.image_url" alt="" loading="lazy" />
              <span>{{ reference.label }}</span>
            </button>
          </div>
        </div>

        <textarea
          v-if="editingDocument"
          ref="scriptTextarea"
          v-model="scriptDraft"
          class="script-textarea"
          spellcheck="false"
          :disabled="savingScript"
        />

        <div v-else class="script-readonly" @dblclick="startDocumentEdit">
          <p
            v-for="(line, lineIndex) in documentLines"
            :key="`${lineIndex}-${line}`"
            :class="[lineClass(line), { selected: isSelectedShotLine(lineIndex), selectable: shotForLine(lineIndex) }]"
            @click="selectLineShot(lineIndex)"
          >
            <template v-for="(part, partIndex) in lineParts(line)" :key="partIndex">
              <span v-if="part.type === 'text'">{{ part.value || '\u00A0' }}</span>
              <button
                v-else
                type="button"
                class="inline-ref-chip"
                :title="part.value.instruction"
              >
                <img :src="part.value.image_url" alt="" loading="lazy" />
                <span>{{ part.value.label }}</span>
                <em>{{ roleLabel(part.value.role) }}</em>
              </button>
            </template>
          </p>
        </div>
      </section>

      <footer class="script-actions">
        <div class="action-hint">
          <span v-if="props.lockedCharacterIds?.size">{{ props.lockedCharacterIds.size }} 个角色已锁定</span>
          <span v-else>{{ referencesEnabled ? '选择左侧角色或场景作为当前片段引用' : referenceModelHint }}</span>
        </div>

        <div class="action-buttons">
          <button
            v-if="!editingDocument"
            class="script-btn"
            type="button"
            @click="startDocumentEdit"
          >
            编辑
          </button>
          <button
            v-if="!editingDocument"
            class="script-btn"
            type="button"
            :disabled="!selectedShot || selectedShotGenerating"
            @click="selectedShot && emit('generateShot', selectedShot)"
          >
            {{ selectedShotGenerating ? '分镜生成中...' : '生成当前分镜' }}
          </button>
          <button
            v-if="editingDocument"
            class="script-btn"
            type="button"
            :disabled="savingScript"
            @click="cancelDocumentEdit"
          >
            取消
          </button>
          <button
            v-if="editingDocument"
            class="script-btn primary"
            type="button"
            :disabled="savingScript"
            @click="saveDocumentEdit"
          >
            {{ savingScript ? '保存中...' : '保存脚本' }}
          </button>
          <button class="script-btn" type="button" :disabled="addingShot" @click="emit('addShot')">
            {{ addingShot ? '添加中...' : '添加分镜' }}
          </button>
          <button
            v-if="segment.status === 'pending' || segment.status === 'partial' || segment.status === 'failed'"
            class="script-btn primary"
            type="button"
            :disabled="generating"
            @click="emit('generateSegment')"
          >
            {{ generating ? '片段生成中...' : '生成片段' }}
          </button>
          <button
            v-if="segment.status === 'completed'"
            class="script-btn"
            type="button"
            @click="emit('regenerate')"
          >
            重新生成
          </button>
        </div>
      </footer>
    </template>

    <div v-else class="script-empty">
      <div class="empty-icon">
        <svg width="38" height="38" viewBox="0 0 38 38" fill="none" aria-hidden="true">
          <rect x="5" y="7" width="28" height="22" rx="4" stroke="currentColor" stroke-width="1.7"/>
          <path d="M16 14l9 5-9 5v-10z" fill="currentColor"/>
        </svg>
      </div>
      <p>选择一个片段开始编辑</p>
    </div>
  </div>
</template>

<style scoped>
.script-stage {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, rgba(255, 246, 219, 0.74), rgba(246, 236, 212, 0.95)),
    repeating-linear-gradient(90deg, rgba(126, 83, 26, 0.035) 0, rgba(126, 83, 26, 0.035) 1px, transparent 1px, transparent 9px);
  padding: 24px 26px 18px;
  overflow: hidden;
}

.segment-head {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  margin-bottom: 10px;
}

.segment-cover {
  width: 42px;
  height: 42px;
  border-radius: 6px;
  overflow: hidden;
  background: #2d2515;
  color: #fff7db;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 0 0 1px rgba(93, 52, 12, 0.2), 0 8px 18px rgba(69, 39, 12, 0.16);
}

.segment-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.segment-title-block {
  min-width: 0;
}

.segment-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.segment-title-row h2 {
  margin: 0;
  color: #2d2515;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0;
}

.segment-title-block p {
  margin-top: 4px;
  color: #7c6a46;
  font-size: 12px;
  line-height: 1.5;
}

.segment-status {
  height: 24px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 700;
}

.status-muted {
  color: #806a3b;
  background: rgba(119, 90, 38, 0.12);
}

.status-active {
  color: #C88A0C;
  background: rgba(232, 163, 23, 0.1);
}

.status-done {
  color: #15803d;
  background: rgba(220, 252, 231, 0.82);
}

.status-warn {
  color: #9a5b00;
  background: rgba(251, 191, 36, 0.18);
}

.status-error {
  color: #b91c1c;
  background: #fee2e2;
}

.status-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.segment-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #7c6a46;
  font-size: 12px;
  white-space: nowrap;
}

.segment-stats span {
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(255, 247, 219, 0.88);
  border: 1px solid rgba(212, 200, 152, 0.78);
}

.reference-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 2px 0 28px 56px;
}

.reference-thumb {
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1px solid rgba(169, 129, 58, 0.42);
  border-radius: 6px;
  overflow: hidden;
  background: #fff7db;
  cursor: default;
}

.reference-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.script-document {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 18px 20px 22px;
  border: 1px solid rgba(176, 132, 44, 0.28);
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 250, 231, 0.98), rgba(253, 244, 214, 0.96)),
    repeating-linear-gradient(0deg, rgba(92, 55, 16, 0.035) 0, rgba(92, 55, 16, 0.035) 1px, transparent 1px, transparent 28px);
  color: #2d2515;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 18px 36px rgba(94, 57, 16, 0.08);
}

.script-document.editing {
  border-color: rgba(200, 138, 12, 0.55);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.84), 0 0 0 3px rgba(200, 138, 12, 0.12);
}

.document-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 14px;
  margin-bottom: 14px;
  border-bottom: 1px solid rgba(168, 130, 60, 0.24);
}

.document-kicker {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 118px;
}

.document-kicker span {
  color: #2d2515;
  font-size: 13px;
  font-weight: 800;
}

.document-kicker em {
  color: #8c7247;
  font-size: 11px;
  font-style: normal;
}

.document-reference-tools {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.document-ref-button,
.inline-ref-chip {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(166, 109, 20, 0.32);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.58);
  color: #5f431d;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  vertical-align: middle;
}

.document-ref-button {
  max-width: 168px;
  height: 30px;
  padding: 3px 9px 3px 4px;
  transition: border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
}

.document-ref-button:hover {
  border-color: rgba(200, 138, 12, 0.75);
  background: #fff7db;
  transform: translateY(-1px);
}

.document-ref-button img,
.inline-ref-chip img {
  width: 22px;
  height: 22px;
  flex: 0 0 auto;
  border-radius: 4px;
  object-fit: cover;
}

.document-ref-button span,
.inline-ref-chip span {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.script-textarea {
  flex: 1;
  min-height: 0;
  width: 100%;
  resize: vertical;
  overflow-y: auto;
  border: 0;
  outline: none;
  border-radius: 6px;
  padding: 0 2px 8px;
  background: transparent;
  color: #2d2515;
  font: inherit;
  font-size: 13px;
  line-height: 2;
  white-space: pre-wrap;
}

.script-textarea::selection {
  background: rgba(232, 163, 23, 0.28);
}

.script-textarea:disabled {
  opacity: 0.68;
  cursor: wait;
}

.script-readonly {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 10px;
}

.script-readonly::-webkit-scrollbar,
.script-textarea::-webkit-scrollbar {
  width: 6px;
}

.script-readonly::-webkit-scrollbar-track,
.script-textarea::-webkit-scrollbar-track {
  background: transparent;
}

.script-readonly::-webkit-scrollbar-thumb,
.script-textarea::-webkit-scrollbar-thumb {
  background: rgba(168, 130, 60, 0.45);
  border-radius: 6px;
}

.doc-line {
  margin: 0;
  color: #3f321e;
  font-size: 13px;
  line-height: 2.05;
  overflow-wrap: anywhere;
}

.doc-line.selectable {
  cursor: pointer;
}

.doc-line.selectable:hover {
  background: rgba(232, 163, 23, 0.08);
}

.doc-line.selected {
  background: rgba(232, 163, 23, 0.14);
  box-shadow: inset 3px 0 0 #c88a0c;
}

.doc-line.blank {
  height: 14px;
  line-height: 14px;
}

.doc-line.section-title {
  margin-top: 8px;
  color: #2d2515;
  font-size: 13px;
  font-weight: 900;
  line-height: 1.8;
}

.doc-line.section-title:first-child {
  margin-top: 0;
}

.doc-line.shot-heading {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(168, 130, 60, 0.18);
  color: #7a1f12;
  font-size: 13px;
  font-weight: 900;
  line-height: 2;
}

.doc-line.sound-line {
  color: #5d4a2a;
}

.inline-ref-chip {
  height: 28px;
  max-width: 240px;
  padding: 3px 8px 3px 4px;
  margin: 0 3px;
}

.inline-ref-chip em {
  flex: 0 0 auto;
  color: #a35f0a;
  font-size: 11px;
  font-style: normal;
}

.script-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  flex-shrink: 0;
  padding: 12px 8px 0;
}

.action-hint {
  min-width: 0;
  max-width: min(520px, 48%);
  margin-right: auto;
  color: #7c6a46;
  font-size: 12px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.script-btn {
  height: 32px;
  padding: 0 18px;
  border: 1px solid rgba(168, 130, 60, 0.45);
  border-radius: 4px;
  background: #fff7db;
  color: #3f321e;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease, transform 0.15s ease;
}

.script-btn:hover:not(:disabled) {
  border-color: #c88a0c;
  color: #2d2515;
  background: #fff2bf;
  transform: translateY(-1px);
}

.script-btn.primary {
  border-color: #2d2515;
  background: #2d2515;
  color: #fff7db;
}

.script-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.script-empty {
  flex: 1;
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c7247;
  gap: 10px;
}

.empty-icon {
  color: #d1b66d;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1180px) {
  .segment-head {
    grid-template-columns: 42px minmax(0, 1fr);
  }

  .segment-stats {
    grid-column: 2;
    flex-wrap: wrap;
  }

  .script-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .document-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .document-reference-tools {
    justify-content: flex-start;
  }
}
</style>
