<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ShotDetail } from '@/types/shot'

const props = defineProps<{
  shot: ShotDetail | null
}>()

const emit = defineEmits<{
  play: []
  download: [url: string]
}>()

const videoRef = ref<HTMLVideoElement | null>(null)
const frameRef = ref<HTMLElement | null>(null)
const audioRef = ref<HTMLAudioElement | null>(null)
const isVideoPlaying = ref(false)
const audioPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const audioCurrentTime = ref(0)
const audioDuration = ref(0)

const hasMedia = computed(() => Boolean(props.shot?.video_url || props.shot?.image_url))
const downloadUrl = computed(() => props.shot?.video_url || props.shot?.image_url || '')
const mediaStatus = computed(() => {
  if (props.shot?.video_url) return '视频已生成'
  if (props.shot?.image_url) return '素材就绪'
  return '待生成'
})

const progress = computed(() => duration.value ? (currentTime.value / duration.value) * 100 : 0)
const audioProgress = computed(() => audioDuration.value ? (audioCurrentTime.value / audioDuration.value) * 100 : 0)

function toggleVideo() {
  if (!videoRef.value) return
  if (isVideoPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
    emit('play')
  }
}

function onVideoTimeUpdate() {
  if (videoRef.value) currentTime.value = videoRef.value.currentTime
}

function onVideoLoaded() {
  if (videoRef.value) duration.value = videoRef.value.duration || props.shot?.duration || 0
}

function onVideoEnded() {
  isVideoPlaying.value = false
}

function seekVideo(e: MouseEvent) {
  if (!videoRef.value || !duration.value) return
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const ratio = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width))
  videoRef.value.currentTime = ratio * duration.value
}

function toggleAudio() {
  if (!audioRef.value) return
  if (audioPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
}

function onAudioTimeUpdate() {
  if (audioRef.value) audioCurrentTime.value = audioRef.value.currentTime
}

function onAudioLoaded() {
  if (audioRef.value) audioDuration.value = audioRef.value.duration
}

function seekAudio(e: MouseEvent) {
  if (!audioRef.value || !audioDuration.value) return
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const ratio = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width))
  audioRef.value.currentTime = ratio * audioDuration.value
}

function toggleFullscreen() {
  if (videoRef.value?.requestFullscreen) {
    videoRef.value.requestFullscreen()
    return
  }
  frameRef.value?.requestFullscreen?.()
}

function formatTime(s: number) {
  const safe = Number.isFinite(s) ? s : 0
  const m = Math.floor(safe / 60)
  const sec = Math.floor(safe % 60)
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}
</script>

<template>
  <aside class="preview-panel">
    <div class="preview-shell">
      <div ref="frameRef" class="preview-frame" :class="{ empty: !hasMedia }">
        <video
          v-if="shot?.video_url"
          ref="videoRef"
          :src="shot.video_url"
          class="preview-media"
          playsinline
          @timeupdate="onVideoTimeUpdate"
          @loadedmetadata="onVideoLoaded"
          @play="isVideoPlaying = true"
          @pause="isVideoPlaying = false"
          @ended="onVideoEnded"
        />

        <img
          v-else-if="shot?.image_url"
          :src="shot.image_url"
          class="preview-media"
          alt=""
          loading="lazy"
        />

        <div v-else class="preview-empty">
          <svg width="44" height="44" viewBox="0 0 44 44" fill="none" aria-hidden="true">
            <rect x="6" y="8" width="32" height="24" rx="5" stroke="currentColor" stroke-width="1.7"/>
            <path d="M18 16l11 6-11 6V16z" fill="currentColor"/>
          </svg>
          <span>选择分镜查看预览</span>
        </div>

        <div class="preview-top-tools">
          <span class="preview-badge">{{ mediaStatus }}</span>
          <div class="preview-icon-row">
            <button type="button" title="全屏" @click="toggleFullscreen">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M2 5V2h3M9 2h3v3M12 9v3H9M5 12H2V9" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <button type="button" title="下载" :disabled="!downloadUrl" @click="downloadUrl && emit('download', downloadUrl)">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M7 2v7M4.5 6.7L7 9.2l2.5-2.5M2.5 12h9" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        <div v-if="shot?.video_url" class="frame-play">
          <button type="button" @click="toggleVideo">
            <svg v-if="isVideoPlaying" width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M6 4v10M12 4v10" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M6.5 4.5v9l7-4.5-7-4.5z" fill="currentColor"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="preview-controls">
        <button
          class="control-play"
          type="button"
          :disabled="!shot?.video_url"
          @click="toggleVideo"
          title="播放/暂停"
        >
          <svg v-if="isVideoPlaying" width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden="true">
            <path d="M5.7 4.2v8.6M11.3 4.2v8.6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <svg v-else width="17" height="17" viewBox="0 0 17 17" fill="none" aria-hidden="true">
            <path d="M6 4.2v8.6l6.6-4.3L6 4.2z" fill="currentColor"/>
          </svg>
        </button>

        <div class="preview-progress" @click="seekVideo">
          <span :style="{ width: `${progress}%` }" />
        </div>

        <span class="time-label">{{ formatTime(currentTime) }} / {{ formatTime(duration || shot?.duration || 0) }}</span>

        <button class="icon-button" type="button" :disabled="!downloadUrl" title="下载" @click="downloadUrl && emit('download', downloadUrl)">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M8 2.5v8M5 7.5l3 3 3-3M3 13h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>

        <button class="icon-button" type="button" title="全屏" @click="toggleFullscreen">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M3 6V3h3M10 3h3v3M13 10v3h-3M6 13H3v-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <div v-if="shot?.audio_url" class="audio-strip">
        <audio
          ref="audioRef"
          :src="shot.audio_url"
          class="hidden"
          @timeupdate="onAudioTimeUpdate"
          @loadedmetadata="onAudioLoaded"
          @play="audioPlaying = true"
          @pause="audioPlaying = false"
          @ended="audioPlaying = false"
        />

        <button type="button" @click="toggleAudio">{{ audioPlaying ? '暂停配音' : '播放配音' }}</button>
        <div class="audio-progress" @click="seekAudio">
          <span :style="{ width: `${audioProgress}%` }" />
        </div>
        <span>{{ formatTime(audioCurrentTime) }}</span>
      </div>

      <details v-if="shot" class="shot-summary">
        <summary>分镜信息</summary>
        <dl>
          <div>
            <dt>镜头</dt>
            <dd>{{ shot.camera_type || '—' }}</dd>
          </div>
          <div>
            <dt>运镜</dt>
            <dd>{{ shot.camera_movement || '—' }}</dd>
          </div>
          <div>
            <dt>场景</dt>
            <dd>{{ shot.scene_ref || '—' }}</dd>
          </div>
          <div>
            <dt>时长</dt>
            <dd>{{ shot.duration }}s</dd>
          </div>
        </dl>
        <p v-if="shot.image_prompt">{{ shot.image_prompt }}</p>
      </details>
    </div>
  </aside>
</template>

<style scoped>
.preview-panel {
  width: 500px;
  flex-shrink: 0;
  border-left: 1px solid #e2e5ea;
  background: #f3f4f6;
  min-height: 0;
  overflow: hidden;
}

.preview-shell {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 22px 22px 18px;
}

.preview-frame {
  position: relative;
  width: min(100%, 450px);
  aspect-ratio: 9 / 16;
  max-height: calc(100vh - 52px - 130px - 110px);
  margin: 0 auto;
  overflow: hidden;
  border-radius: 22px;
  background: #0b0f18;
  box-shadow: 0 14px 38px rgba(15, 23, 42, 0.18);
}

.preview-frame.empty {
  background: #141821;
}

.preview-media {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #080b10;
}

.preview-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.48);
  font-size: 13px;
}

.preview-top-tools {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  pointer-events: none;
}

.preview-badge,
.preview-icon-row {
  border-radius: 2px;
  background: rgba(20, 20, 20, 0.42);
  color: #2D2515;
  backdrop-filter: blur(8px);
}

.preview-badge {
  padding: 5px 9px;
  font-size: 11px;
  font-weight: 700;
}

.preview-icon-row {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 4px;
  pointer-events: auto;
}

.preview-icon-row button,
.frame-play button,
.control-play,
.icon-button {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.preview-icon-row button {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.82);
}

.preview-icon-row button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  color: #2D2515;
}

.preview-icon-row button:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.frame-play {
  position: absolute;
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
}

.frame-play button {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: #111827;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.22);
}

.preview-controls {
  display: grid;
  grid-template-columns: 32px minmax(70px, 1fr) auto 30px 30px;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
}

.control-play,
.icon-button {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #111827;
  border-radius: 50%;
  transition: background 0.15s ease, color 0.15s ease;
}

.control-play:hover:not(:disabled),
.icon-button:hover:not(:disabled) {
  background: #e5e7eb;
}

.control-play:disabled,
.icon-button:disabled {
  color: #b7beca;
  cursor: not-allowed;
}

.preview-progress,
.audio-progress {
  height: 3px;
  border-radius: 2px;
  background: #cbd5e1;
  overflow: hidden;
  cursor: pointer;
}

.preview-progress span,
.audio-progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #111827;
}

.time-label {
  color: #64748b;
  font-size: 11px;
  white-space: nowrap;
}

.audio-strip {
  display: grid;
  grid-template-columns: auto minmax(70px, 1fr) auto;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding: 8px 10px;
  border-radius: 2px;
  background: #FDF5D6;
}

.audio-strip button {
  border: 0;
  background: transparent;
  color: #111827;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.audio-strip span {
  color: #64748b;
  font-size: 11px;
}

.shot-summary {
  margin-top: 14px;
  padding: 11px 12px;
  border-radius: 2px;
  background: #FDF5D6;
  color: #334155;
  font-size: 12px;
}

.shot-summary summary {
  cursor: pointer;
  color: #111827;
  font-weight: 800;
}

.shot-summary dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 14px;
  margin-top: 10px;
}

.shot-summary div {
  min-width: 0;
}

.shot-summary dt {
  color: #94a3b8;
  font-size: 11px;
}

.shot-summary dd {
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shot-summary p {
  margin-top: 10px;
  color: #64748b;
  line-height: 1.65;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hidden {
  display: none;
}

@media (max-width: 1320px) {
  .preview-panel {
    width: 430px;
  }

  .preview-frame {
    width: min(100%, 380px);
  }
}
</style>
