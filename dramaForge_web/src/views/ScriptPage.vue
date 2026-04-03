<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useScriptStore } from '@/stores/script'
import { VideoStyleLabel } from '@/types/enums'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const scriptStore = useScriptStore()

const projectId = Number(route.params.id)
const approving = ref(false)
const rewriting = ref(false)

onMounted(() => {
  scriptStore.fetchScript(projectId)
})

async function handleApprove() {
  approving.value = true
  try {
    await scriptStore.approveScript(projectId)
    await projectStore.fetchProject(projectId)
    router.push(`/projects/${projectId}/assets`)
  } finally {
    approving.value = false
  }
}

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
      <!-- Meta info -->
      <div class="script-meta">
        <div class="script-meta-item">
          <span class="script-meta-label">视频风格:</span>
          <span class="script-meta-value">
            {{ projectStore.currentProject ? (VideoStyleLabel[projectStore.currentProject.style] || projectStore.currentProject.style) : '' }}
          </span>
        </div>
        <div class="script-meta-item">
          <span class="script-meta-label">画面比例:</span>
          <span class="script-meta-value">{{ projectStore.currentProject?.aspect_ratio || '9:16' }}</span>
        </div>
      </div>

      <!-- Script summary card -->
      <div class="mb-8">
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

      <!-- Episodes accordion -->
      <div class="mb-8">
        <h2 class="script-section-title">剧本内容</h2>
        <div class="space-y-3">
          <details
            v-for="ep in scriptStore.script.episodes"
            :key="ep.id"
            class="card group"
            :open="scriptStore.script.episodes.length <= 3"
          >
            <summary class="px-6 py-4 cursor-pointer text-[15px] font-semibold text-gray-800 hover:bg-gray-50 rounded-[14px] select-none list-none flex items-center gap-3 transition-colors">
              <svg width="14" height="14" viewBox="0 0 12 12" fill="none" class="text-gray-400 transition-transform group-open:rotate-90 shrink-0">
                <path d="M4.5 2.5L8 6L4.5 9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="text-primary-500 text-[13px] font-medium mr-1">第 {{ ep.number }} 集</span>
              {{ ep.title || '无标题' }}
            </summary>
            <div class="px-6 pb-5 text-[15px] text-gray-600 whitespace-pre-wrap leading-[1.9] border-t border-gray-100 pt-4 mx-3">
              {{ ep.title }}
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
      <span v-if="scriptStore.script.is_approved">剧本内容整理完毕，可以进行下一步了</span>
      <span v-else>请审核剧本内容，确认后进入资产生成</span>
    </div>
    <div class="bar-actions">
      <button class="btn btn-outline btn-sm" :disabled="rewriting" @click="handleRewrite">
        改写为旁白型
      </button>
      <button class="btn btn-primary btn-sm" :disabled="approving" @click="handleApprove">
        {{ scriptStore.script.is_approved ? '下一步 →' : '确认并下一步 →' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.script-meta {
  display: flex;
  align-items: center;
  gap: 32px;
  margin-bottom: 32px;
  padding: 0 4px;
}
.script-meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.script-meta-label {
  font-size: 14px;
  color: #999;
}
.script-meta-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}
.script-section-title {
  font-size: 17px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 16px;
}
.script-summary-card {
  background: #f9f9fb;
  border-radius: 14px;
  padding: 32px 36px;
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
  margin-bottom: 6px;
}
.script-summary-value {
  font-size: 15px;
  color: #444;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>