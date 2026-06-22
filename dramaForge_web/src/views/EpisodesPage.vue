<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { episodesApi } from '@/api/episodes'
import type { EpisodeOverview } from '@/types/episode'
import { ProjectStep } from '@/types/enums'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const projectId = Number(route.params.id)

const episodes = ref<EpisodeOverview[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await episodesApi.list(projectId)
    episodes.value = data
  } finally {
    loading.value = false
  }
})

// ── Computed stats ──
const totalDuration = computed(() =>
  episodes.value.reduce((sum, ep) => sum + (ep.total_duration || 0), 0)
)
const totalCharacters = computed(() =>
  episodes.value.reduce((sum, ep) => sum + (ep.character_count || 0), 0)
)
const totalScenes = computed(() =>
  episodes.value.reduce((sum, ep) => sum + (ep.scene_count || 0), 0)
)
const totalSegments = computed(() =>
  episodes.value.reduce((sum, ep) => sum + (ep.segment_count || 0), 0)
)

const regeneratingEpId = ref<number | null>(null)

function goBackToAssets() {
  if (projectStore.currentProject) {
    projectStore.currentProject.status = ProjectStep.ASSETS
  }
  router.push(`/projects/${projectId}/assets`)
}

function handleExportEpisode(epId: number) {
  router.push(`/projects/${projectId}/episodes/${epId}/storyboard`)
}

async function handleRegenerateEpisode(epId: number) {
  if (!window.confirm('确定要 AI 重新生成本集内容吗？已有分镜和素材数据将保留。')) return
  regeneratingEpId.value = epId
  try {
    await episodesApi.regenerate(projectId, epId)
    // Refresh list
    const { data } = await episodesApi.list(projectId)
    episodes.value = data
  } catch (e: any) {
    alert(e?.response?.data?.detail || '重新生成失败')
  } finally {
    regeneratingEpId.value = null
  }
}

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function formatTotalDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  if (m >= 60) {
    const h = Math.floor(m / 60)
    const rm = m % 60
    return `${h}h ${rm}m ${s}s`
  }
  return `${m}m ${s}s`
}

// ── Thumbnail gradients (cycle through variants) ──
const thumbnailGradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)',
  'linear-gradient(135deg, #96fbc4 0%, #f9f586 100%)',
]

function getThumbnailGradient(index: number) {
  return thumbnailGradients[index % thumbnailGradients.length]
}
</script>

<template>
  <div class="episodes-page">
    <!-- ═══ Header ═══ -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="header-title">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" class="header-icon">
            <rect x="2" y="3" width="18" height="14" rx="2.5" stroke="currentColor" stroke-width="1.6"/>
            <path d="M8 3V1.5M14 3V1.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            <polygon points="10,9 10,15 14.5,12" fill="currentColor"/>
          </svg>
          剧集管理
        </h1>
        <span class="header-badge">{{ episodes.length }} 集</span>
      </div>
      <div class="header-right">
        <button class="header-btn" @click="goBackToAssets">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <rect x="1.5" y="1.5" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/>
            <circle cx="5.5" cy="5.5" r="1.5" stroke="currentColor" stroke-width="1"/>
            <path d="M1.5 11l3.5-4.5 2 2 3-3.5 3.5 4.5" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          角色 & 场景
        </button>
      </div>
    </div>

    <!-- ═══ Stats Summary ═══ -->
    <div v-if="episodes.length" class="stats-row">
      <div class="stat-card">
        <div class="stat-icon stat-icon--purple">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="1.5" y="2" width="15" height="12" rx="2" stroke="currentColor" stroke-width="1.4"/>
            <polygon points="8,7 8,12 12,9.5" fill="currentColor"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ episodes.length }}</span>
          <span class="stat-label">总集数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--blue">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="7.5" stroke="currentColor" stroke-width="1.4"/>
            <path d="M9 5v4l3 2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ formatTotalDuration(totalDuration) }}</span>
          <span class="stat-label">总时长</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--green">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="7" cy="5.5" r="3" stroke="currentColor" stroke-width="1.4"/>
            <path d="M1.5 15.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ totalCharacters }}</span>
          <span class="stat-label">角色数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--amber">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="1.5" y="1.5" width="15" height="15" rx="2" stroke="currentColor" stroke-width="1.4"/>
            <path d="M6 1.5V3M12 1.5V3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <path d="M1.5 8h15" stroke="currentColor" stroke-width="1.4"/>
            <rect x="4" y="10" width="3" height="3" rx="0.6" fill="currentColor"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ totalScenes }}</span>
          <span class="stat-label">场景数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--rose">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="1.5" y="3" width="15" height="10" rx="1.5" stroke="currentColor" stroke-width="1.4"/>
            <path d="M6 3V1.5M12 3V1.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <path d="M1.5 11h15" stroke="currentColor" stroke-width="1.4"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ totalSegments }}</span>
          <span class="stat-label">总分镜</span>
        </div>
      </div>
    </div>

    <p class="page-subtitle">点击剧集卡片进入分镜编辑器，调整每个分镜的画面与台词</p>

    <!-- ═══ Loading ═══ -->
    <div v-if="loading" class="loading-area">
      <div class="spinner" />
      <span class="loading-text">加载剧集中...</span>
    </div>

    <!-- ═══ Empty ═══ -->
    <EmptyState v-else-if="!episodes.length" title="暂无分集" description="生成剧本分集后将在这里显示" icon="📺" />

    <!-- ═══ Episode Grid ═══ -->
    <div v-else class="episode-grid">
      <div
        v-for="(ep, idx) in episodes"
        :key="ep.id"
        class="episode-card"
        @click="router.push(`/projects/${projectId}/episodes/${ep.id}/storyboard`)"
      >
        <!-- Thumbnail -->
        <div class="card-thumb" :style="{ background: getThumbnailGradient(idx) }">
          <span class="thumb-number">{{ ep.number }}</span>
          <div class="thumb-play">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <circle cx="14" cy="14" r="13" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
              <polygon points="11.5,9.5 11.5,18.5 19,14" fill="currentColor"/>
            </svg>
          </div>
          <span v-if="ep.total_duration" class="thumb-duration">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
              <circle cx="5.5" cy="5.5" r="4.5" stroke="currentColor" stroke-width="1"/>
              <path d="M5.5 3v2.5l2 1" stroke="currentColor" stroke-width="0.9" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ formatDuration(ep.total_duration) }}
          </span>
          <!-- Approved badge -->
          <span v-if="ep.is_approved" class="thumb-approved" title="已审核">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M2.5 6l2.5 2.5 4.5-5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </div>

        <!-- Info -->
        <div class="card-body">
          <div class="card-top">
            <h3 class="card-title">
              第 {{ ep.number }} 集：{{ ep.title || '无标题' }}
            </h3>
          </div>

          <!-- Stats -->
          <div class="card-stats">
            <div class="stat-pill">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="5" r="3" stroke="currentColor" stroke-width="1.2"/>
                <path d="M2 13c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="currentColor" stroke-width="1.2"/>
              </svg>
              <span class="stat-pill-label">角色</span>
              <span class="stat-pill-value">{{ ep.character_count }}</span>
            </div>
            <div class="stat-pill">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                <rect x="2" y="3" width="10" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
                <path d="M5 3V2M9 3V2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
              <span class="stat-pill-label">场景</span>
              <span class="stat-pill-value">{{ ep.scene_count }}</span>
            </div>
            <div class="stat-pill">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                <rect x="1" y="3" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
                <path d="M5 3l2-2 2 2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="stat-pill-label">分镜</span>
              <span class="stat-pill-value">{{ ep.segment_count }}</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="card-actions">
            <button
              class="action-btn action-btn--ghost"
              @click.stop="router.push(`/projects/${projectId}/episodes/${ep.id}/storyboard`)"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <polygon points="4.5,2.5 4.5,11.5 11,7" fill="currentColor"/>
              </svg>
              预览
            </button>
            <button
              class="action-btn action-btn--outline"
              @click.stop="router.push(`/projects/${projectId}/episodes/${ep.id}/storyboard`)"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M9.5 1.5l3 3-7 7H2.5v-3l7-7z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              编辑
            </button>
            <button class="action-btn action-btn--primary" @click.stop="handleExportEpisode(ep.id)">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1.5v8M4 6.5l3 3 3-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 11.5h10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
              </svg>
              导出
            </button>
            <button
              class="action-btn action-btn--ghost"
              :disabled="regeneratingEpId === ep.id"
              @click.stop="handleRegenerateEpisode(ep.id)"
              title="AI 重新生成本集内容"
            >
              <svg v-if="regeneratingEpId === ep.id" class="animate-spin" width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
                <path d="M7 1.5a5.5 5.5 0 015.1 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M1.5 10.5l3 1.5L8 2.5 4.8 1 1.5 10.5z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
                <path d="M4.8 1l.8 2.5" stroke="currentColor" stroke-width="1.2"/>
                <path d="M10.5 4.5l2-1M8.5 8.5l2 3.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
              {{ regeneratingEpId === ep.id ? '生成中...' : '分镜生成' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Bottom Bar ═══ -->
    <div v-if="episodes.length" class="bottom-bar">
      <div class="bottom-hint">
        <div class="bottom-hint-icon">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.3"/>
            <path d="M8 5v3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <circle cx="8" cy="12" r="0.7" fill="currentColor"/>
          </svg>
        </div>
        <span>点击剧集卡片进入分镜编辑器，可细调每个分镜的画面和台词</span>
      </div>
      <div class="bottom-actions">
        <button class="bottom-btn" @click="goBackToAssets">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M9 2.5L4.5 7.5 9 12.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          上一步
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════
   Episodes Page — Layout
   ═══════════════════════════════════════════════ */
.episodes-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 32px 80px;
}

/* ═══ Header ═══ */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 22px;
  font-weight: 800;
  color: #2D2515;
  letter-spacing: -0.4px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: #E8A317;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 12px;
  background: rgba(232, 163, 23, 0.08);
  color: #E8A317;
  font-size: 13px;
  font-weight: 600;
  border-radius: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 14px;
  background: #FDF5D6;
  border: 1px solid #D4C898;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  color: #555;
  cursor: pointer;
  transition: all 0.15s;
}
.header-btn:hover {
  background: #FEF9E7;
  border-color: #A89870;
  color: #333;
}

/* ═══ Stats Row ═══ */
.stats-row {
  display: flex;
  gap: 14px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: #FDF5D6;
  border: 1px solid #FDF4D8;
  border-radius: 14px;
  flex: 1;
  min-width: 150px;
  transition: all 0.2s;
}
.stat-card:hover {
  border-color: #D4C898;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-icon--purple { background: rgba(232, 163, 23, 0.08); color: #E8A317; }
.stat-icon--blue   { background: #EFF6FF; color: #3b82f6; }
.stat-icon--green  { background: #F0FDF4; color: #22c55e; }
.stat-icon--amber  { background: #FFFBEB; color: #f59e0b; }
.stat-icon--rose   { background: #FFF1F2; color: #f43f5e; }

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #2D2515;
  letter-spacing: -0.2px;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

/* ═══ Subtitle ═══ */
.page-subtitle {
  font-size: 13px;
  color: #aaa;
  margin-bottom: 24px;
}

/* ═══ Loading ═══ */
.loading-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 0;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #D4C898;
  border-top-color: #E8A317;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  color: #bbb;
}

/* ═══ Episode Grid ═══ */
.episode-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

@media (min-width: 768px) {
  .episode-grid {
    grid-template-columns: 1fr 1fr;
  }
}

/* ═══ Episode Card ═══ */
.episode-card {
  display: flex;
  background: #FDF5D6;
  border: 1px solid #FDF4D8;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s ease;
}
.episode-card:hover {
  border-color: #e0d5f5;
  box-shadow: 0 4px 20px rgba(232, 163, 23, 0.08);
  transform: translateY(-1px);
}

/* ── Thumbnail ── */
.card-thumb {
  width: 120px;
  min-height: 160px;
  flex-shrink: 0;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.thumb-number {
  position: absolute;
  top: 10px;
  left: 12px;
  font-size: 52px;
  font-weight: 900;
  color: rgba(255,255,255,0.18);
  line-height: 1;
  pointer-events: none;
  font-variant-numeric: tabular-nums;
}

.thumb-play {
  color: rgba(255,255,255,0.75);
  transition: all 0.25s;
  z-index: 1;
}
.episode-card:hover .thumb-play {
  color: rgba(255,255,255,0.95);
  transform: scale(1.1);
}

.thumb-duration {
  position: absolute;
  bottom: 10px;
  right: 10px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(6px);
  color: #2D2515;
  font-size: 11px;
  font-weight: 600;
  border-radius: 6px;
  letter-spacing: 0.2px;
}

.thumb-approved {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.9);
  color: #2D2515;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

/* ── Card Body ── */
.card-body {
  flex: 1;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #2D2515;
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Stats Pills ── */
.card-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: #f9fafb;
  border-radius: 8px;
  color: #888;
  font-size: 12px;
  transition: all 0.15s;
}
.stat-pill:hover {
  background: #f3f4f6;
  color: #555;
}

.stat-pill-label {
  font-weight: 500;
}

.stat-pill-value {
  font-weight: 700;
  color: #555;
}

/* ── Card Actions ── */
.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 32px;
  padding: 0 14px;
  border-radius: 9px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
  white-space: nowrap;
}

.action-btn--ghost {
  background: transparent;
  color: #999;
}
.action-btn--ghost:hover {
  background: #FDF4D8;
  color: #555;
}

.action-btn--outline {
  background: #FDF5D6;
  color: #555;
  border: 1px solid #D4C898;
}
.action-btn--outline:hover {
  background: #FEF9E7;
  border-color: #A89870;
  color: #333;
}

.action-btn--primary {
  background: #2D2515;
  color: #FFFFFF;
}
.action-btn--primary:hover {
  background: #333;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

/* ═══ Bottom Bar ═══ */
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: 56px;
  background: #FDF5D6;
  border-top: 1px solid #FDF4D8;
  display: flex;
  align-items: center;
  padding: 0 32px;
  z-index: 40;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.03);
}

.bottom-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #999;
}

.bottom-hint-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(232, 163, 23, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #E8A317;
  flex-shrink: 0;
}

.bottom-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.bottom-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 16px;
  background: #FDF5D6;
  border: 1px solid #D4C898;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  color: #555;
  cursor: pointer;
  transition: all 0.15s;
}
.bottom-btn:hover {
  background: #FEF9E7;
  border-color: #A89870;
  color: #333;
}
</style>
