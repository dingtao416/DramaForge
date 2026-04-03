<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStoryboardStore } from '@/stores/storyboard'
import { useAssetsStore } from '@/stores/assets'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import TopbarActions from '@/components/common/TopbarActions.vue'

const route = useRoute()
const router = useRouter()
const sbStore = useStoryboardStore()
const assetsStore = useAssetsStore()

const projectId = Number(route.params.id)
const episodeId = Number(route.params.epId)

onMounted(async () => {
  await Promise.all([
    sbStore.fetchStoryboard(projectId, episodeId),
    assetsStore.fetchAssets(projectId),
  ])
})

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const totalDuration = computed(() => sbStore.storyboard?.total_duration || 0)
const episodeTitle = computed(() => sbStore.storyboard?.episode_title || '分镜编辑器')

function goBack() {
  router.push(`/projects/${projectId}/episodes`)
}
</script>

<template>
  <LoadingOverlay :visible="sbStore.loading" message="正在加载分镜..." />

  <div class="sb-root">
    <!-- ═══ Top Bar ═══ -->
    <header class="sb-topbar">
      <div class="sb-topbar-left">
        <button class="sb-back-btn" @click="goBack">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>返回</span>
        </button>
        <div class="sb-topbar-sep" />
        <span class="sb-topbar-title">第{{ route.params.epId }}集·{{ episodeTitle }}</span>
      </div>
      <div class="sb-topbar-right">
        <TopbarActions />
        <div class="sb-topbar-sep" />
        <select class="sb-model-select">
          <option>Seedance 2.0 · Fast</option>
          <option>veo-3.1-fast</option>
          <option>veo3</option>
        </select>
        <button class="btn btn-outline btn-sm">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 1v5m0 0v5m0-5h5m-5 0H2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
          导出
        </button>
        <button class="btn btn-primary btn-sm sb-compose-btn">合成全集</button>
      </div>
    </header>

    <!-- ═══ Main Area ═══ -->
    <div class="sb-main">
      <!-- LEFT: Asset Panel -->
      <aside class="sb-left">
        <div class="sb-left-header">
          <span class="sb-left-title">资产库</span>
          <button class="sb-add-btn">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><line x1="8" y1="3" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="3" y1="8" x2="13" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
        </div>

        <div class="sb-left-body">
          <!-- Characters -->
          <div class="sb-asset-group">
            <div class="sb-asset-group-title">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="5" r="3" stroke="currentColor" stroke-width="1.2"/><path d="M2 13c0-3 2.5-5 5-5s5 2 5 5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
              角色 ({{ assetsStore.characters.length }})
            </div>
            <div class="sb-char-grid">
              <div
                v-for="char in assetsStore.characters"
                :key="char.id"
                class="sb-char-item"
              >
                <div class="sb-char-img">
                  <img
                    v-if="char.reference_images?.[0]"
                    :src="char.reference_images[0]"
                    :alt="char.name"
                  />
                  <div v-else class="sb-char-placeholder">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="4" stroke="#ccc" stroke-width="1.5"/><path d="M4 22c0-4.4 3.6-7 8-7s8 2.6 8 7" stroke="#ccc" stroke-width="1.5" stroke-linecap="round"/></svg>
                  </div>
                </div>
                <div class="sb-char-name">{{ char.name }}</div>
                <div class="sb-char-tag">基础形象</div>
              </div>
            </div>
          </div>

          <!-- Scenes -->
          <div class="sb-asset-group">
            <div class="sb-asset-group-title">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="1" y="3" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M4 3V1.5M10 3V1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
              场景 ({{ assetsStore.scenes.length }})
            </div>
            <div class="sb-scene-list">
              <div
                v-for="scene in assetsStore.scenes"
                :key="scene.id"
                class="sb-scene-item"
              >
                <div class="sb-scene-img">
                  <img
                    v-if="scene.reference_images?.[0]"
                    :src="scene.reference_images[0]"
                    :alt="scene.name"
                  />
                  <div v-else class="sb-scene-placeholder">🏠</div>
                </div>
                <div class="sb-scene-name">{{ scene.name }}</div>
              </div>
            </div>
            <!-- Empty scene placeholder -->
            <div v-if="!assetsStore.scenes.length" class="sb-scene-empty">
              暂无场景
            </div>
          </div>
        </div>
      </aside>

      <!-- CENTER: Storyboard Script -->
      <main class="sb-center">
        <template v-if="sbStore.storyboard && sbStore.storyboard.segments.length">
          <div class="sb-script-wrap">
            <!-- Segment header -->
            <div class="sb-segment-header">
              <h2 class="sb-segment-title">
                片段 {{ sbStore.currentSegmentIndex + 1 }}
              </h2>
              <span class="sb-segment-hint">
                片段时长请限制在4-15s，输入"@"可快速调整镜头时长、引用角色、场景、素材
              </span>
              <span class="sb-cost-hint">
                视频每秒消耗11积分，以实际生成为准
              </span>
            </div>

            <!-- Segment script card -->
            <div class="sb-script-card">
              <template v-if="sbStore.currentSegment">
                <div v-for="(shot, idx) in sbStore.currentSegment.shots" :key="shot.id" class="sb-shot">
                  <!-- Shot header -->
                  <div class="sb-shot-header">
                    <span class="sb-shot-label">分镜{{ idx + 1 }}</span>
                    <span class="sb-shot-meta">
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.2"/><path d="M6 3.5V6.5L8 8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
                      {{ shot.duration }}s
                    </span>
                    <span class="sb-shot-meta">时间：{{ shot.time_of_day }}</span>
                    <span class="sb-shot-meta">场景图片：{{ shot.scene_ref || '无' }}</span>
                  </div>

                  <!-- Shot content -->
                  <div class="sb-shot-body">
                    <p v-if="shot.background">{{ shot.background }}</p>
                    <p v-if="shot.dialogue">
                      <span class="sb-shot-dialogue-label">台词：</span>
                      「{{ shot.dialogue }}」
                    </p>
                    <p v-if="shot.voice_style" class="sb-shot-voice">
                      音色：{{ shot.voice_style }}
                    </p>
                  </div>
                </div>
              </template>
            </div>

            <!-- Actions -->
            <div class="sb-script-actions">
              <button class="btn btn-outline btn-sm">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M8.5 2.5l3 3M2 11l7.5-7.5 3 3L5 14H2v-3z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                编辑脚本
              </button>
              <button class="btn btn-primary btn-sm sb-regen-btn">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1.5 7a5.5 5.5 0 019.37-3.9M12.5 7a5.5 5.5 0 01-9.37 3.9" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M11 1v2.5h-2.5M3 11v-2.5h2.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                再次生成
              </button>
            </div>
          </div>
        </template>

        <!-- Empty state -->
        <div v-else-if="!sbStore.loading" class="sb-empty">
          <div class="sb-empty-icon">🎬</div>
          <p class="sb-empty-text">尚未生成分镜脚本</p>
          <button class="btn btn-primary" @click="sbStore.generateStoryboard(projectId, episodeId)">
            生成分镜脚本
          </button>
        </div>
      </main>

      <!-- RIGHT: Preview Panel -->
      <aside class="sb-right">
        <div class="sb-preview-video">
          <div v-if="sbStore.currentShot?.video_url">
            <video :src="sbStore.currentShot.video_url" controls class="sb-video" />
          </div>
          <div v-else-if="sbStore.currentShot?.image_url">
            <img :src="sbStore.currentShot.image_url" class="sb-video" />
          </div>
          <div v-else class="sb-preview-placeholder">
            暂无预览
          </div>

          <!-- Video controls overlay -->
          <div class="sb-video-controls">
            <button class="sb-play-btn">
              <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M4 2.5L13 8L4 13.5V2.5Z"/></svg>
            </button>
            <span class="sb-time">00:00</span>
            <span class="sb-time-sep">|</span>
            <span class="sb-time">00:15</span>
            <div class="sb-video-controls-right">
              <button class="sb-ctrl-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              </button>
              <button class="sb-ctrl-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 3h4v4H3V3zM9 3h4v4H9V3zM3 9h4v4H3V9zM9 9h4v4H9V9z" stroke="currentColor" stroke-width="1.2"/></svg>
              </button>
              <button class="sb-ctrl-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 14V8l5-6 5 6v6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- ═══ Bottom Timeline ═══ -->
    <div class="sb-timeline">
      <div class="sb-timeline-top">
        <button class="sb-timeline-play">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><path d="M3.5 2L11.5 7L3.5 12V2Z"/></svg>
        </button>
        <span class="sb-timeline-time">00:00 / {{ formatDuration(totalDuration) }}</span>
        <div class="sb-timeline-spacer" />
        <button class="sb-timeline-multi">多选</button>
      </div>
      <div class="sb-timeline-track">
        <div
          v-for="(seg, idx) in sbStore.storyboard?.segments || []"
          :key="seg.id"
          class="sb-timeline-seg"
          :class="{ active: idx === sbStore.currentSegmentIndex }"
          @click="sbStore.selectSegment(idx)"
        >
          <div class="sb-seg-thumb">
            <img v-if="seg.thumbnail_url" :src="seg.thumbnail_url" />
            <span v-else class="sb-seg-thumb-text">{{ idx + 1 }}</span>
            <span class="sb-seg-badge">{{ idx + 1 }}</span>
            <span class="sb-seg-dur">{{ seg.duration ? formatDuration(seg.duration) : '--:--' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══ Root Layout ═══ */
.sb-root {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

/* ═══ Top Bar ═══ */
.sb-topbar {
  height: 48px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}
.sb-topbar-left {
  display: flex;
  align-items: center;
  gap: 0;
}
.sb-back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #666;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 6px;
  transition: all 0.15s;
}
.sb-back-btn:hover { color: #333; background: #f5f5f5; }
.sb-topbar-sep {
  width: 1px;
  height: 20px;
  background: #e8e8e8;
  margin: 0 12px;
}
.sb-topbar-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}
.sb-topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.sb-model-select {
  height: 32px;
  font-size: 13px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 0 10px;
  background: #fff;
  outline: none;
  color: #333;
  cursor: pointer;
}
.sb-compose-btn {
  background: #1a1a1a !important;
  color: #fff !important;
}

/* ═══ Main 3-col ═══ */
.sb-main {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

/* ── Left Panel ── */
.sb-left {
  width: 240px;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}
.sb-left-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}
.sb-left-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}
.sb-add-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
}
.sb-add-btn:hover { background: #f5f5f5; color: #666; }

.sb-left-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.sb-asset-group {
  margin-bottom: 20px;
}
.sb-asset-group-title {
  font-size: 12px;
  color: #999;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

/* Character grid */
.sb-char-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.sb-char-item {
  text-align: center;
  cursor: pointer;
}
.sb-char-img {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
  margin-bottom: 6px;
}
.sb-char-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.sb-char-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.sb-char-name {
  font-size: 12px;
  color: #333;
  font-weight: 500;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sb-char-tag {
  font-size: 10px;
  color: #bbb;
}

/* Scene list */
.sb-scene-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.sb-scene-item {
  cursor: pointer;
}
.sb-scene-img {
  width: 100%;
  aspect-ratio: 16/10;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
  margin-bottom: 4px;
}
.sb-scene-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.sb-scene-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #ccc;
}
.sb-scene-name {
  font-size: 12px;
  color: #333;
  font-weight: 500;
}
.sb-scene-empty {
  font-size: 12px;
  color: #ccc;
  text-align: center;
  padding: 16px 0;
}

/* ── Center Panel ── */
.sb-center {
  flex: 1;
  overflow-y: auto;
  background: #fafafa;
  min-width: 0;
}
.sb-script-wrap {
  max-width: 760px;
  margin: 0 auto;
  padding: 24px 24px 32px;
}
.sb-segment-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.sb-segment-title {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a1a;
  flex-shrink: 0;
}
.sb-segment-hint {
  font-size: 12px;
  color: #bbb;
  line-height: 1.5;
}
.sb-cost-hint {
  font-size: 12px;
  color: #bbb;
  margin-left: auto;
  flex-shrink: 0;
}

/* Script card */
.sb-script-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
}
.sb-shot {
  margin-bottom: 24px;
}
.sb-shot:last-child {
  margin-bottom: 0;
}
.sb-shot-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.sb-shot-label {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}
.sb-shot-meta {
  font-size: 12px;
  color: #bbb;
  display: flex;
  align-items: center;
  gap: 3px;
}
.sb-shot-body {
  font-size: 14px;
  color: #555;
  line-height: 1.9;
  padding-left: 16px;
  border-left: 2px solid #e8e0ff;
}
.sb-shot-body p {
  margin-bottom: 6px;
}
.sb-shot-body p:last-child {
  margin-bottom: 0;
}
.sb-shot-dialogue-label {
  color: #bbb;
}
.sb-shot-voice {
  font-size: 12px;
  color: #bbb;
}

/* Script actions */
.sb-script-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
}
.sb-regen-btn {
  background: #7c3aed !important;
  color: #fff !important;
  opacity: 0.6;
}

/* Empty state */
.sb-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
}
.sb-empty-icon {
  font-size: 48px;
}
.sb-empty-text {
  font-size: 15px;
  color: #999;
}

/* ── Right Panel ── */
.sb-right {
  width: 320px;
  border-left: 1px solid #e8e8e8;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #000;
}
.sb-preview-video {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
}
.sb-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.sb-preview-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 14px;
}
.sb-video-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
}
.sb-play-btn {
  color: #fff;
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
}
.sb-time {
  font-size: 12px;
  color: #fff;
  font-variant-numeric: tabular-nums;
}
.sb-time-sep {
  color: rgba(255,255,255,0.4);
  font-size: 12px;
}
.sb-video-controls-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
}
.sb-ctrl-btn {
  color: rgba(255,255,255,0.7);
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  padding: 4px;
}
.sb-ctrl-btn:hover { color: #fff; }

/* ═══ Bottom Timeline ═══ */
.sb-timeline {
  height: 130px;
  border-top: 1px solid #e8e8e8;
  flex-shrink: 0;
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
  background: #fff;
}
.sb-timeline-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.sb-timeline-play {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f5f5f5;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
}
.sb-timeline-play:hover { background: #eee; color: #333; }
.sb-timeline-time {
  font-size: 13px;
  color: #999;
  font-variant-numeric: tabular-nums;
}
.sb-timeline-spacer {
  flex: 1;
}
.sb-timeline-multi {
  height: 28px;
  padding: 0 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  border: 1px solid #e8e8e8;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}
.sb-timeline-multi:hover { background: #f9f9f9; }

/* Timeline track */
.sb-timeline-track {
  flex: 1;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.sb-timeline-seg {
  flex-shrink: 0;
  width: 110px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
}
.sb-timeline-seg:hover {
  border-color: #ddd;
}
.sb-timeline-seg.active {
  border-color: #7c3aed;
  box-shadow: 0 0 0 1px rgba(124,58,237,0.2);
}
.sb-seg-thumb {
  height: 64px;
  background: #f0f0f0;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.sb-seg-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.sb-seg-thumb-text {
  font-size: 12px;
  color: #bbb;
}
.sb-seg-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  background: #7c3aed;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
}
.sb-seg-dur {
  position: absolute;
  bottom: 4px;
  left: 4px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
}
</style>