<script setup lang="ts">
import type { MediaJobPayload } from '@/api/chat'

const props = defineProps<{
  job: MediaJobPayload
  cancelling?: boolean
  cancelError?: string
}>()

const emit = defineEmits<{
  cancel: [jobId: number]
  retry: [job: MediaJobPayload]
}>()

const activeStatuses = ['created', 'queued', 'running']

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

function imageUrl(job: MediaJobPayload): string {
  const asset = job.result_assets_json?.[0]
  const url = asset?.url || asset?.provider_url || ''
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  const apiBase = import.meta.env.VITE_API_BASE_URL || ''
  const backendBase = apiBase.replace(/\/api\/v\d+\/?$/, '')
  return url.startsWith('/') ? `${backendBase}${url}` : url
}

function progressValue(job: MediaJobPayload): number {
  if (job.status === 'succeeded' || job.status === 'cancelled') return 100
  return Math.max(6, Math.min(100, Number(job.progress) || 6))
}

function onImageError(event: Event): void {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
  const fallback = img.nextElementSibling as HTMLElement | null
  if (fallback) fallback.style.display = 'flex'
}
</script>

<template>
  <section class="image-gen-card" :class="'image-gen-card--' + job.status">
    <header class="image-gen-head">
      <div>
        <div class="image-gen-title">图片生成</div>
        <div class="image-gen-meta">#{{ job.id }} · {{ statusLabel(job.status) }} · {{ job.model_id }}</div>
      </div>
      <button
        v-if="activeStatuses.includes(job.status)"
        class="image-gen-btn image-gen-btn-quiet"
        type="button"
        :disabled="cancelling"
        @click="emit('cancel', job.id)"
      >
        {{ cancelling ? '停止中...' : '停止' }}
      </button>
    </header>

    <div v-if="activeStatuses.includes(job.status)" class="image-gen-stage">
      <div class="image-gen-placeholder">
        <div class="image-gen-pulse" />
        <span>{{ statusLabel(job.status) }}</span>
      </div>
      <div class="image-gen-progress">
        <span :style="{ width: `${progressValue(job)}%` }" />
      </div>
      <p v-if="cancelError" class="image-gen-cancel-error">{{ cancelError }}</p>
    </div>

    <div v-else-if="job.status === 'succeeded' && imageUrl(job)" class="image-gen-result">
      <img
        :src="imageUrl(job)"
        :alt="'生成图片 #' + job.id"
        loading="lazy"
        class="image-gen-img"
        @error="onImageError"
      />
      <div class="image-gen-fallback" style="display:none;">图片加载失败</div>
      <div class="image-gen-actions">
        <a class="image-gen-btn" :href="imageUrl(job)" target="_blank" rel="noreferrer">查看原图</a>
        <a class="image-gen-btn" :href="imageUrl(job)" :download="`dramaforge-image-${job.id}`">下载</a>
        <button class="image-gen-btn image-gen-btn-quiet" type="button" @click="emit('retry', job)">再次生成</button>
      </div>
    </div>

    <div v-else-if="job.status === 'failed'" class="image-gen-error">
      <strong>生成失败</strong>
      <p>{{ friendlyError(job.error) }}</p>
      <button class="image-gen-btn" type="button" @click="emit('retry', job)">重试</button>
    </div>

    <div v-else-if="job.status === 'cancelled'" class="image-gen-cancelled">
      <span>这次图片生成已停止。</span>
      <button class="image-gen-btn image-gen-btn-quiet" type="button" @click="emit('retry', job)">重新生成</button>
    </div>

    <div v-else class="image-gen-stage">
      <div class="image-gen-placeholder">
        <span>{{ statusLabel(job.status) }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.image-gen-card {
  width: min(520px, 94%);
  margin-top: 12px;
  padding: 14px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: #FDF5D6;
  box-shadow: 4px 4px 0 0 rgba(0, 0, 0, 0.24);
}

.image-gen-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.image-gen-title {
  font-size: 13px;
  font-weight: 800;
  color: #1A1508;
}

.image-gen-meta {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: #6B5D40;
  word-break: break-word;
}

.image-gen-stage,
.image-gen-result,
.image-gen-error,
.image-gen-cancelled {
  margin-top: 12px;
}

.image-gen-placeholder {
  position: relative;
  aspect-ratio: 4 / 3;
  min-height: 210px;
  border: 2px dashed #D4C898;
  background:
    linear-gradient(90deg, rgba(255,255,255,0.2) 25%, rgba(232,163,23,0.16) 50%, rgba(255,255,255,0.2) 75%),
    #FFF8DF;
  background-size: 220% 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6B5D40;
  font-size: 13px;
  font-weight: 700;
  overflow: hidden;
  animation: image-gen-sheen 1.7s linear infinite;
}

.image-gen-pulse {
  width: 18px;
  height: 18px;
  margin-right: 8px;
  border: 2px solid #E8A317;
  border-top-color: transparent;
  border-radius: 50%;
  animation: image-gen-spin 0.9s linear infinite;
}

.image-gen-progress {
  height: 7px;
  margin-top: 10px;
  border: 1px solid #D4C898;
  background: rgba(255, 255, 255, 0.62);
  overflow: hidden;
}

.image-gen-progress span {
  display: block;
  height: 100%;
  background: #E8A317;
  transition: width 0.2s ease;
}

.image-gen-img {
  display: block;
  width: 100%;
  max-height: 520px;
  object-fit: contain;
  border: 2px solid #D4C898;
  background: #fff;
}

.image-gen-fallback {
  min-height: 180px;
  align-items: center;
  justify-content: center;
  border: 2px solid #D4C898;
  color: #8B7A5A;
  background: #FFF8DF;
}

.image-gen-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.image-gen-btn {
  min-height: 32px;
  padding: 0 12px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: #FFF3C4;
  color: #4F4328;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  text-decoration: none;
  cursor: pointer;
}

.image-gen-btn:hover {
  border-color: #E8A317;
  color: #1A1508;
}

.image-gen-btn:disabled {
  opacity: 0.56;
  cursor: wait;
}

.image-gen-btn-quiet {
  background: transparent;
}

.image-gen-cancel-error {
  margin: 8px 0 0;
  padding: 8px 10px;
  border: 1px solid rgba(192, 57, 43, 0.28);
  background: rgba(231, 76, 60, 0.08);
  color: #9F2F23;
  font-size: 12px;
  line-height: 1.5;
}

.image-gen-error {
  padding: 12px;
  border: 2px solid rgba(192, 57, 43, 0.25);
  background: rgba(231, 76, 60, 0.08);
  color: #9F2F23;
}

.image-gen-error strong {
  display: block;
  font-size: 13px;
}

.image-gen-error p {
  margin: 6px 0 10px;
  font-size: 12px;
  line-height: 1.6;
}

.image-gen-cancelled {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #6B5D40;
  font-size: 13px;
}

@keyframes image-gen-sheen {
  from { background-position: 100% 0; }
  to { background-position: -120% 0; }
}

@keyframes image-gen-spin {
  to { transform: rotate(360deg); }
}
</style>
