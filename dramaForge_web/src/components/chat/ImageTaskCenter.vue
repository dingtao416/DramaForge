<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useUserAIConfigStore } from '@/stores/user-ai-config'
import type { MediaJob, MediaJobStatus } from '@/types/user-ai-config'

const emit = defineEmits<{
  retry: [job: MediaJob]
}>()

const aiStore = useUserAIConfigStore()
const filters: Array<{ key: 'all' | MediaJobStatus; label: string }> = [
  { key: 'all', label: '全部' },
  { key: 'running', label: '生成中' },
  { key: 'succeeded', label: '已完成' },
  { key: 'failed', label: '失败' },
  { key: 'cancelled', label: '已取消' },
]

const activeFilter = defineModel<'all' | MediaJobStatus>({ default: 'all' })

const imageJobs = computed(() =>
  aiStore.jobs.filter((job) => job.capability === 'image')
)

const filteredJobs = computed(() => {
  if (activeFilter.value === 'all') return imageJobs.value
  if (activeFilter.value === 'running') {
    return imageJobs.value.filter((job) => ['created', 'queued', 'running'].includes(job.status))
  }
  return imageJobs.value.filter((job) => job.status === activeFilter.value)
})

onMounted(() => {
  void aiStore.fetchJobs()
})

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    created: '准备中',
    queued: '排队中',
    running: '生成中',
    succeeded: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return map[status] || status || '未知'
}

function friendlyError(errorText?: string | null): string {
  const text = errorText || ''
  if (!text) return '未知错误'
  if (text.includes('Concurrency limit exceeded') || text.includes('rate_limit_error') || text.includes('当前图片生成并发已满')) {
    return '当前图片生成并发已满，请稍后重试。'
  }
  if (text.includes('images-only group') || text.includes('/v1/images/generations')) {
    return '当前图片模型密钥只能用于图片接口，请关闭聊天回退后重试。'
  }
  return text
}

function imageUrl(job: MediaJob): string {
  const asset = job.result_assets_json?.[0]
  const url = asset?.url || asset?.provider_url || ''
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  const apiBase = import.meta.env.VITE_API_BASE_URL || ''
  const backendBase = apiBase.replace(/\/api\/v\d+\/?$/, '')
  return url.startsWith('/') ? `${backendBase}${url}` : url
}

function formatTime(value?: string): string {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

async function cancel(job: MediaJob): Promise<void> {
  await aiStore.cancelJob(job.id)
}
</script>

<template>
  <div class="task-center">
    <div class="task-toolbar">
      <div class="task-tabs">
        <button
          v-for="filter in filters"
          :key="filter.key"
          class="task-tab"
          :class="activeFilter === filter.key ? 'task-tab-active' : ''"
          type="button"
          @click="activeFilter = filter.key"
        >
          {{ filter.label }}
        </button>
      </div>
      <button class="task-refresh" type="button" @click="aiStore.fetchJobs()">刷新</button>
    </div>

    <div v-if="!filteredJobs.length" class="task-empty">
      <div class="task-empty-icon">IMG</div>
      <p>暂无图片任务</p>
      <span>生成中的图片会显示在这里</span>
    </div>

    <div v-else class="task-list">
      <article v-for="job in filteredJobs" :key="job.id" class="task-item">
        <div class="task-thumb">
          <img v-if="job.status === 'succeeded' && imageUrl(job)" :src="imageUrl(job)" alt="" loading="lazy" />
          <span v-else>{{ statusLabel(job.status) }}</span>
        </div>
        <div class="task-main">
          <div class="task-row">
            <strong>#{{ job.id }} · {{ statusLabel(job.status) }}</strong>
            <span>{{ formatTime(job.created_at) }}</span>
          </div>
          <p>{{ job.request_json?.prompt || '无提示词' }}</p>
          <div class="task-meta">{{ job.model_id }}</div>
          <div v-if="['created', 'queued', 'running'].includes(job.status)" class="task-progress">
            <span :style="{ width: `${Math.max(8, job.progress || 8)}%` }" />
          </div>
          <div v-if="job.status === 'failed'" class="task-error">{{ friendlyError(job.error) }}</div>
          <div class="task-actions">
            <button
              v-if="['created', 'queued', 'running'].includes(job.status)"
              type="button"
              @click="cancel(job)"
            >
              停止
            </button>
            <a v-if="job.status === 'succeeded' && imageUrl(job)" :href="imageUrl(job)" target="_blank" rel="noreferrer">查看</a>
            <a v-if="job.status === 'succeeded' && imageUrl(job)" :href="imageUrl(job)" :download="`dramaforge-image-${job.id}`">下载</a>
            <button v-if="job.status === 'failed' || job.status === 'cancelled' || job.status === 'succeeded'" type="button" @click="emit('retry', job)">
              再次生成
            </button>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.task-center {
  color: #2D2515;
}

.task-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.task-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.task-tab,
.task-refresh,
.task-actions button,
.task-actions a {
  min-height: 32px;
  padding: 0 11px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: transparent;
  color: #5F5235;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  text-decoration: none;
  cursor: pointer;
}

.task-tab-active,
.task-refresh:hover,
.task-actions button:hover,
.task-actions a:hover {
  border-color: #E8A317;
  background: #FFF3C4;
  color: #1A1508;
}

.task-list {
  display: grid;
  gap: 12px;
}

.task-item {
  display: grid;
  grid-template-columns: 108px minmax(0, 1fr);
  gap: 12px;
  padding: 12px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: #FEF9E7;
  box-shadow: 3px 3px 0 0 rgba(0, 0, 0, 0.16);
}

.task-thumb {
  aspect-ratio: 1 / 1;
  border: 2px solid #D4C898;
  background: #FFF8DF;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: #8B7A5A;
  font-size: 12px;
  font-weight: 800;
}

.task-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.task-main {
  min-width: 0;
}

.task-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.task-row strong {
  font-size: 13px;
}

.task-row span,
.task-meta {
  font-size: 11px;
  color: #8B7A5A;
}

.task-main p {
  margin: 7px 0 5px;
  font-size: 12px;
  line-height: 1.55;
  color: #4F4328;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-progress {
  height: 6px;
  margin-top: 8px;
  border: 1px solid #D4C898;
  background: rgba(255, 255, 255, 0.64);
  overflow: hidden;
}

.task-progress span {
  display: block;
  height: 100%;
  background: #E8A317;
}

.task-error {
  margin-top: 8px;
  font-size: 12px;
  color: #A33B2F;
}

.task-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.task-empty {
  min-height: 260px;
  border: 2px dashed #D4C898;
  background: #FEF9E7;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8B7A5A;
  text-align: center;
}

.task-empty-icon {
  width: 44px;
  height: 44px;
  margin-bottom: 12px;
  border: 2px solid #D4C898;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #E8A317;
  font-size: 11px;
  font-weight: 900;
}

.task-empty p {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 800;
}

.task-empty span {
  font-size: 12px;
}

@media (max-width: 560px) {
  .task-item {
    grid-template-columns: 82px minmax(0, 1fr);
  }
}
</style>
