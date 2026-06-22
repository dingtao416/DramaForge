/**
 * DramaForge — Generation Store (Pinia)
 * Manages AI script generation state globally so it survives page navigation.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { scriptsApi } from '@/api/scripts'
import type { ScriptGenerateStreamResult } from '@/api/scripts'

export const useGenerationStore = defineStore('generation', () => {
  // ═══════ State ═══════
  const projectId = ref<number | null>(null)
  const status = ref<'idle' | 'generating' | 'complete' | 'error'>('idle')
  const streamContent = ref('')
  const result = ref<ScriptGenerateStreamResult | null>(null)
  const error = ref<string | null>(null)

  let abortController: AbortController | null = null

  // ═══════ Getters ═══════
  const isGenerating = computed(() => status.value === 'generating')
  const isActive = computed(() => projectId.value !== null && status.value !== 'idle')
  const contentLength = computed(() => streamContent.value.length)

  // ═══════ Actions ═══════

  /**
   * Start AI script generation for a project.
   * The SSE stream runs independently and survives page navigation.
   */
  async function startGeneration(
    pid: number,
    data: {
      user_input: string
      genre?: string
      total_episodes?: number
      duration_per_episode?: number
    },
  ) {
    // Reset state
    projectId.value = pid
    status.value = 'generating'
    streamContent.value = ''
    result.value = null
    error.value = null

    abortController = new AbortController()

    try {
      await scriptsApi.generateStream(
        pid,
        data,
        {
          onContent: (chunk: string) => {
            streamContent.value += chunk
          },
          onDone: (res: ScriptGenerateStreamResult) => {
            result.value = res
            status.value = 'complete'
          },
          onError: (errMsg: string) => {
            error.value = errMsg
            status.value = 'error'
          },
        },
        abortController.signal,
      )
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        error.value = e.message || '生成失败'
        status.value = 'error'
      }
    } finally {
      abortController = null
    }
  }

  /** Stop the current generation */
  async function stopGeneration() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    // Tell the backend to cancel the background task
    if (projectId.value) {
      try {
        await scriptsApi.cancelGeneration(projectId.value)
      } catch {
        // Fire-and-forget — the abort above already stops the SSE stream
      }
    }
    status.value = 'idle'
  }

  /** Reset the store to idle */
  function reset() {
    stopGeneration()
    projectId.value = null
    status.value = 'idle'
    streamContent.value = ''
    result.value = null
    error.value = null
  }

  /**
   * Poll the backend for generation status.
   * Used when navigating to a project page to check if generation is ongoing.
   */
  async function checkStatus(pid: number): Promise<boolean> {
    try {
      const { data } = await (await import('@/api/client')).default.get(
        `/projects/${pid}/script/generate-status`,
      )
      if (data?.status === 'generating') {
        projectId.value = pid
        status.value = 'generating'
        if (data.content_length > 0) {
          streamContent.value = '...' // placeholder — reconnect needed for real content
        }
        return true
      }
      return false
    } catch {
      return false
    }
  }

  return {
    projectId,
    status,
    streamContent,
    result,
    error,
    isGenerating,
    isActive,
    contentLength,
    startGeneration,
    stopGeneration,
    reset,
    checkStatus,
  }
})
