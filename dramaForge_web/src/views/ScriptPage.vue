<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useScriptStore } from '@/stores/script'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const scriptStore = useScriptStore()

const projectId = Number(route.params.id)
const rewriting = ref(false)

onMounted(() => {
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
  rewriting.value = true
  try {
    await scriptStore.rewriteNarration(projectId)
  } finally {
    rewriting.value = false
  }
}
</script>

<template>
  <LoadingOverlay :visible="scriptStore.loading" message="正在加载剧本..." />
  <LoadingOverlay :visible="rewriting" message="正在改写为旁白型..." />

  <div class="page-container" style="max-width: 860px;">
    <!-- Empty state -->
    <EmptyState
      v-if="!scriptStore.loading && !scriptStore.script"
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
          <button
            class="btn btn-outline btn-sm"
            :disabled="rewriting"
            @click="handleRewrite"
          >
            改写为旁白型剧本
          </button>
        </div>
        <div class="script-episodes">
          <details
            v-for="ep in scriptStore.script.episodes"
            :key="ep.id"
            class="script-episode"
          >
            <summary class="script-episode-summary">
              <svg class="script-episode-arrow" width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M4.5 2.5L8 6L4.5 9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="script-episode-label">第{{ ep.number }}集</span>
              <span class="script-episode-title">{{ ep.title || '无标题' }}</span>
            </summary>
            <div class="script-episode-content">
              {{ ep.content || ep.title }}
            </div>
          </details>
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
      <button class="btn btn-primary btn-sm" @click="router.push(`/projects/${projectId}/assets`)">
        下一步
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

/* ── Episode accordions ── */
.script-episodes {
  display: flex;
  flex-direction: column;
  gap: 0;
  border-top: 1px solid #eee;
}
.script-episode {
  border-bottom: 1px solid #eee;
}
.script-episode-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  user-select: none;
  list-style: none;
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
}
.script-episode-content {
  padding: 0 8px 16px 30px;
  font-size: 14px;
  color: #555;
  line-height: 2;
  white-space: pre-wrap;
}
</style>