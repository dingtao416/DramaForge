<script setup lang="ts">
import { computed } from 'vue'
import type { SegmentDetail } from '@/types/segment'
import type { ShotDetail } from '@/types/shot'

const props = defineProps<{
  segment: SegmentDetail | null
  segmentIndex: number
  generating?: boolean
  addingShot?: boolean
  deletingShotId?: number | null
  lockedCharacterIds?: Set<number>
}>()

const emit = defineEmits<{
  editScript: []
  regenerate: []
  generateSegment: []
  selectShot: [shot: ShotDetail, index: number]
  addShot: []
  deleteShot: [shotId: number]
}>()

const statusConfig: Record<string, { label: string; cls: string }> = {
  pending: { label: '待生成', cls: 'status-muted' },
  generating: { label: '生成中', cls: 'status-active' },
  completed: { label: '已完成', cls: 'status-done' },
  failed: { label: '生成失败', cls: 'status-error' },
}

const status = computed(() => {
  if (!props.segment) return null
  return statusConfig[props.segment.status] || statusConfig.pending
})

const segmentNo = computed(() => String(props.segmentIndex + 1).padStart(2, '0'))

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
  if (value?.char_id) return `角色${value.char_id}`
  return ''
}

function shotPrompt(shot: ShotDetail) {
  return shot.video_prompt || shot.image_prompt || shot.background || '暂无画面提示词'
}

function shotMediaUrl(shot: ShotDetail) {
  return shot.image_url || ''
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

      <section class="script-document">
        <div class="doc-section">
          <h3>基础设定</h3>
          <p><strong>画面风格和类型：</strong>{{ segment.style || '皮影戏插画风格 2D，东方神话志怪美术，宣纸纹理背景，硬边剪影轮廓与金粉光效结合。' }}</p>
          <p v-if="sceneRefs.length"><strong>场景：</strong>{{ sceneRefs.join('、') }}</p>
          <p v-if="characterRefs.length"><strong>角色：</strong>{{ characterRefs.join('、') }}</p>
          <p><strong>声音：</strong>保留环境音、动作声和角色对白，避免过量配乐。</p>
        </div>

        <div class="doc-section">
          <h3>氛围画面</h3>
          <p>
            风格核心：戏剧化光影、强对比构图、动作清晰，画面中心始终服务当前片段的主要情绪和行动。
          </p>
          <p>
            视觉基调：以当前片段缩略图和分镜提示词为准，优先保持角色造型、场景质感、光源方向和色彩一致。
          </p>
        </div>

        <div class="doc-section">
          <h3>画面内容</h3>

          <article
            v-for="(shot, idx) in segment.shots"
            :key="shot.id"
            class="shot-row"
            @click="emit('selectShot', shot, idx)"
          >
            <div class="shot-thumb" :class="{ empty: !shotMediaUrl(shot) }">
              <img v-if="shotMediaUrl(shot)" :src="shotMediaUrl(shot)" alt="" loading="lazy" />
              <span v-else>{{ idx + 1 }}</span>
            </div>

            <div class="shot-copy">
              <div class="shot-title-line">
                <button class="shot-title" type="button" @click.stop="emit('selectShot', shot, idx)">
                  分镜 {{ idx + 1 }}
                </button>
                <span class="shot-chip">{{ shot.duration }}s</span>
                <span v-if="shot.camera_type" class="shot-chip">{{ shot.camera_type }}</span>
                <span v-if="shot.camera_movement" class="shot-chip">{{ shot.camera_movement }}</span>
                <span v-if="shot.video_url" class="shot-ready">已生成</span>
              </div>

              <p class="shot-prompt">{{ shotPrompt(shot) }}</p>

              <div v-if="shot.dialogue || shot.narration || shot.scene_ref || shot.emotion" class="shot-meta">
                <span v-if="shot.scene_ref">场景：{{ shot.scene_ref }}</span>
                <span v-if="shot.emotion">情绪：{{ shot.emotion }}</span>
                <span v-if="shot.narration">旁白：“{{ shot.narration }}”</span>
                <span v-if="shot.dialogue">台词：“{{ shot.dialogue }}”</span>
              </div>
            </div>

            <button
              class="shot-delete"
              type="button"
              :disabled="deletingShotId === shot.id"
              title="删除此分镜"
              @click.stop="emit('deleteShot', shot.id)"
            >
              <svg v-if="deletingShotId === shot.id" class="spin" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <circle cx="7" cy="7" r="5.6" stroke="currentColor" stroke-width="1.6" opacity="0.28"/>
                <path d="M7 1.4a5.6 5.6 0 014.9 2.8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M4 4l6 6M10 4l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </article>
        </div>
      </section>

      <footer class="script-actions">
        <div class="action-hint">
          <span v-if="props.lockedCharacterIds?.size">{{ props.lockedCharacterIds.size }} 个角色已锁定</span>
          <span v-else>选择左侧角色或场景作为当前片段引用</span>
        </div>

        <div class="action-buttons">
          <button class="script-btn" type="button" @click="emit('editScript')">编辑</button>
          <button class="script-btn" type="button" :disabled="addingShot" @click="emit('addShot')">
            {{ addingShot ? '添加中...' : '添加分镜' }}
          </button>
          <button
            v-if="segment.status === 'pending'"
            class="script-btn primary"
            type="button"
            :disabled="generating"
            @click="emit('generateSegment')"
          >
            {{ generating ? '生成中...' : '生成素材' }}
          </button>
          <button
            v-if="segment.status === 'completed' || segment.status === 'failed'"
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
  min-height: 100%;
  display: flex;
  flex-direction: column;
  background: #f3f4f6;
  padding: 24px 26px 22px;
  overflow-y: auto;
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
  border-radius: 2px;
  overflow: hidden;
  background: #111827;
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
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
  color: #0f172a;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0;
}

.segment-title-block p {
  margin-top: 4px;
  color: #64748b;
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
  color: #64748b;
  background: #e5e7eb;
}

.status-active {
  color: #C88A0C;
  background: rgba(232, 163, 23, 0.1);
}

.status-done {
  color: #15803d;
  background: #dcfce7;
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
  color: #64748b;
  font-size: 12px;
  white-space: nowrap;
}

.segment-stats span {
  padding: 4px 8px;
  border-radius: 2px;
  background: #FDF5D6;
  border: 1px solid #e5e7eb;
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
  border: 1px solid #d7dce4;
  border-radius: 2px;
  overflow: hidden;
  background: #FDF5D6;
  cursor: default;
}

.reference-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.script-document {
  flex: 1;
  min-height: 470px;
  padding: 24px 28px 26px;
  border-radius: 24px;
  background: #e9edf2;
  color: #243044;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.64);
}

.doc-section + .doc-section {
  margin-top: 22px;
}

.doc-section h3 {
  margin: 0 0 10px;
  color: #0f172a;
  font-size: 13px;
  font-weight: 800;
}

.doc-section p {
  color: #334155;
  font-size: 13px;
  line-height: 1.95;
}

.doc-section strong {
  color: #0f172a;
  font-weight: 800;
}

.shot-row {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr) 28px;
  gap: 14px;
  align-items: flex-start;
  padding: 13px 0;
  border-top: 1px solid rgba(148, 163, 184, 0.22);
  cursor: pointer;
}

.shot-row:first-of-type {
  border-top: 0;
}

.shot-thumb {
  width: 54px;
  height: 38px;
  border-radius: 9px;
  overflow: hidden;
  background: #d8dee8;
  color: #718096;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
}

.shot-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.shot-copy {
  min-width: 0;
}

.shot-title-line {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
  margin-bottom: 5px;
}

.shot-title {
  padding: 0;
  border: 0;
  background: transparent;
  color: #0f172a;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.shot-chip,
.shot-ready {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 7px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 700;
}

.shot-chip {
  color: #64748b;
  background: rgba(255, 255, 255, 0.72);
}

.shot-ready {
  color: #15803d;
  background: #dcfce7;
}

.shot-prompt {
  color: #334155;
  font-size: 13px;
  line-height: 1.9;
}

.shot-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 6px;
}

.shot-meta span {
  color: #475569;
  background: rgba(255, 255, 255, 0.62);
  border-radius: 7px;
  padding: 3px 7px;
  font-size: 12px;
  line-height: 1.5;
}

.shot-delete {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.58);
  color: #94a3b8;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease, background 0.15s ease;
}

.shot-row:hover .shot-delete {
  opacity: 1;
}

.shot-delete:hover:not(:disabled) {
  color: #b91c1c;
  background: #fee2e2;
}

.shot-delete:disabled {
  opacity: 1;
  cursor: not-allowed;
}

.script-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 8px 0;
}

.action-hint {
  color: #64748b;
  font-size: 12px;
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
  border: 1px solid #e5e7eb;
  border-radius: 2px;
  background: #FDF5D6;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.script-btn:hover:not(:disabled) {
  border-color: #cbd5e1;
  color: #0f172a;
  transform: translateY(-1px);
}

.script-btn.primary {
  border-color: #111827;
  background: #111827;
  color: #FFFFFF;
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
  color: #94a3b8;
  gap: 10px;
}

.empty-icon {
  color: #cbd5e1;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (hover: none) {
  .shot-delete {
    opacity: 1;
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
}
</style>
