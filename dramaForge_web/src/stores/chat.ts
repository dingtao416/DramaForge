/**
 * DramaForge — Chat Store (Pinia)
 * Manages conversations, messages, and SSE streaming state.
 * Features typewriter-effect text rendering for polished AI responses.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  sendMessageStream,
  getConversations,
  getConversation,
  deleteConversation as apiDeleteConversation,
} from '@/api/chat'
import type { AgentIntentKind, AgentIntentPayload, ChatMessage, Conversation, ConversationDetail, MediaJobPayload, SendMessageRequest } from '@/api/chat'
import { cancelJob, getJob } from '@/api/user-ai-config'
import type { MediaJob } from '@/types/user-ai-config'

/** Local UI message (extends API message with streaming state) */
export interface UIMessage {
  id: number | null          // null while streaming
  role: 'user' | 'assistant' | 'system'
  content: string
  meta_json?: Record<string, any> | null
  isStreaming?: boolean
  created_at: string
}

// ═══════════════════════════════════════════════════════════════════
// Typewriter config
// ═══════════════════════════════════════════════════════════════════
const TYPEWRITER_TICK = 35        // ms between ticks
const BURST_CHARS = 3             // chars per tick during initial burst
const NORMAL_CHARS = 1            // chars per tick during normal pace
const BURST_THRESHOLD = 20        // chars shown before switching to normal pace

export const useChatStore = defineStore('chat', () => {
  // ═══════ State ═══════
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<number | null>(null)
  const messages = ref<UIMessage[]>([])
  const isStreaming = ref(false)
  const isThinking = ref(false)          // waiting for first content chunk
  const streamingContent = ref('')       // raw SSE accumulation
  const displayContent = ref('')         // typewriter-smoothed display content
  const error = ref<string | null>(null)
  const isLoadingConversations = ref(false)
  const cancellingMediaJobIds = ref<Set<number>>(new Set())
  const mediaCancelErrors = ref<Record<number, string>>({})

  // AbortController + typewriter timer
  let abortController: AbortController | null = null
  let typewriterTimer: ReturnType<typeof setInterval> | null = null
  let charBuffer = ''
  const pollingMediaJobs = new Set<number>()

  // ═══════ Getters ═══════
  const currentConversation = computed(() =>
    conversations.value.find(c => c.id === currentConversationId.value) ?? null
  )
  const hasMessages = computed(() => messages.value.length > 0)
  const activeMediaStatuses = new Set(['created', 'queued', 'running'])

  // ═══════ Typewriter Engine ═══════

  function startTypewriter() {
    stopTypewriter(false)
    isThinking.value = true
    typewriterTimer = setInterval(() => {
      if (charBuffer.length === 0) return

      const shown = displayContent.value.length
      const charsPerTick = shown < BURST_THRESHOLD ? BURST_CHARS : NORMAL_CHARS
      const take = Math.min(charsPerTick, charBuffer.length)

      displayContent.value += charBuffer.slice(0, take)
      charBuffer = charBuffer.slice(take)

      // Update last assistant message in place
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.content = displayContent.value
      }
    }, TYPEWRITER_TICK)
  }

  function stopTypewriter(flush: boolean) {
    if (typewriterTimer) {
      clearInterval(typewriterTimer)
      typewriterTimer = null
    }
    if (flush && charBuffer.length > 0) {
      displayContent.value += charBuffer
      charBuffer = ''
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.content = displayContent.value
      }
    }
    isThinking.value = false
  }

  function normalizeMediaJob(job: MediaJob | MediaJobPayload): MediaJobPayload {
    return {
      id: job.id,
      capability: job.capability as 'image' | 'video',
      provider_id: job.provider_id,
      model_id: job.model_id,
      provider_job_id: job.provider_job_id,
      status: job.status,
      progress: job.progress,
      request_json: job.request_json || {},
      result_assets_json: job.result_assets_json || [],
      error: job.error,
    }
  }

  function friendlyMediaError(errorText?: string | null): string | null {
    const text = errorText || ''
    if (!text) return null
    if (text.includes('Concurrency limit exceeded') || text.includes('rate_limit_error') || text.includes('当前图片生成并发已满')) {
      return '当前图片生成并发已满，请稍后重试。'
    }
    if (text.includes('images-only group') || text.includes('/v1/images/generations')) {
      return '当前图片模型密钥只能用于图片接口，请关闭聊天回退后重试。'
    }
    return text
  }

  function updateLastAssistantMeta(meta: Record<string, any>): void {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.meta_json = { ...(last.meta_json || {}), ...meta }
    }
  }

  function updateMediaJobMeta(job: MediaJob | MediaJobPayload): void {
    const payload = normalizeMediaJob(job)
    payload.error = friendlyMediaError(payload.error)
    const target = [...messages.value]
      .reverse()
      .find(m => m.role === 'assistant' && m.meta_json?.media_job?.id === payload.id)
    if (target) {
      target.meta_json = { ...(target.meta_json || {}), media_job: payload }
    } else {
      updateLastAssistantMeta({ media_job: payload })
    }
  }

  async function pollMediaJob(jobId: number): Promise<void> {
    if (pollingMediaJobs.has(jobId)) return
    pollingMediaJobs.add(jobId)
    try {
      for (let attempt = -1; attempt < 120; attempt += 1) {
        // Adaptive polling: 2s for first 10 attempts, 3s for next 20, 5s thereafter
        const delay = attempt < 0 ? 0 : attempt < 10 ? 2000 : attempt < 30 ? 3000 : 5000
        if (delay) await new Promise(resolve => setTimeout(resolve, delay))
        if (cancellingMediaJobIds.value.has(jobId)) break
        const job = await getJob(jobId)
        updateMediaJobMeta(job)
        if (['succeeded', 'failed', 'cancelled'].includes(job.status)) break
      }
    } catch (e) {
      console.warn('Failed to poll media job', e)
    } finally {
      pollingMediaJobs.delete(jobId)
    }
  }

  async function refreshMediaJob(jobId: number): Promise<void> {
    try {
      const job = await getJob(jobId)
      updateMediaJobMeta(job)
      if (activeMediaStatuses.has(job.status)) {
        void pollMediaJob(job.id)
      }
    } catch {
      // Keep the saved message state if the job can no longer be fetched.
    }
  }

  async function cancelMediaJob(jobId: number): Promise<void> {
    if (cancellingMediaJobIds.value.has(jobId)) return
    const currentJob = [...messages.value]
      .reverse()
      .find(m => m.role === 'assistant' && m.meta_json?.media_job?.id === jobId)
      ?.meta_json?.media_job as MediaJobPayload | undefined
    if (currentJob && !activeMediaStatuses.has(currentJob.status)) return

    cancellingMediaJobIds.value = new Set([...cancellingMediaJobIds.value, jobId])
    const nextErrors = { ...mediaCancelErrors.value }
    delete nextErrors[jobId]
    mediaCancelErrors.value = nextErrors
    try {
      const latest = await getJob(jobId)
      updateMediaJobMeta(latest)
      if (!activeMediaStatuses.has(latest.status)) return
      const job = await cancelJob(jobId)
      updateMediaJobMeta(job)
      const cleared = { ...mediaCancelErrors.value }
      delete cleared[jobId]
      mediaCancelErrors.value = cleared
    } catch (e: any) {
      const status = e?.response?.status
      const detail = e?.response?.data?.detail
      const message = status === 404
        ? '停止失败，请确认后端已重启并加载最新代码。'
        : (detail || e?.message || '取消图片生成失败')
      error.value = message
      mediaCancelErrors.value = { ...mediaCancelErrors.value, [jobId]: message }
    } finally {
      const nextIds = new Set(cancellingMediaJobIds.value)
      nextIds.delete(jobId)
      cancellingMediaJobIds.value = nextIds
    }
  }

  async function retryImageJob(job: MediaJobPayload): Promise<void> {
    const prompt = String(job.request_json?.prompt || '').trim()
    if (!prompt) {
      error.value = '无法重试：任务缺少原始提示词'
      return
    }
    await sendMessage(prompt, {
      model: job.model_id,
      model_capability: 'image',
    })
  }

  // ═══════ Actions ═══════

  /** Fetch conversation list */
  async function fetchConversations(): Promise<void> {
    isLoadingConversations.value = true
    try {
      conversations.value = await getConversations()
    } catch (e: any) {
      console.error('Failed to fetch conversations', e)
    } finally {
      isLoadingConversations.value = false
    }
  }

  /** Load a conversation and its messages */
  async function loadConversation(conversationId: number): Promise<void> {
    try {
      const detail: ConversationDetail = await getConversation(conversationId)
      currentConversationId.value = detail.id
      messages.value = detail.messages.map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        meta_json: m.meta_json,
        created_at: m.created_at,
      }))
      // Resume polling for any in-progress media jobs
      for (const msg of messages.value) {
        const job = msg.meta_json?.media_job as MediaJobPayload | undefined
        if (job) {
          updateMediaJobMeta(job)
          void refreshMediaJob(job.id)
        }
      }
    } catch (e: any) {
      error.value = '加载对话失败'
      console.error(e)
    }
  }

  /** Start a new conversation (clear state) */
  function newConversation(): void {
    currentConversationId.value = null
    messages.value = []
    streamingContent.value = ''
    displayContent.value = ''
    charBuffer = ''
    error.value = null
  }

  /**
   * Send a message with SSE streaming + typewriter effect.
   * Raw chunks accumulate in streamingContent, typewriter smoothly
   * releases characters into displayContent → last message content.
   */
  async function sendMessage(
    content: string,
    options: {
      mode?: string
      projectId?: number
      model?: string
      model_capability?: AgentIntentKind
      temperature?: number
    } = {},
  ): Promise<void> {
    if (isStreaming.value) return
    error.value = null

    // Add user message to UI immediately
    const userMsg: UIMessage = {
      id: null,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    messages.value.push(userMsg)

    // Add placeholder assistant message (empty — thinking dots will show)
    const assistantMsg: UIMessage = {
      id: null,
      role: 'assistant',
      content: '',
      isStreaming: true,
      created_at: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)

    isStreaming.value = true
    isThinking.value = true
    streamingContent.value = ''
    displayContent.value = ''
    charBuffer = ''

    // Start the typewriter engine
    startTypewriter()

    // Create AbortController
    abortController = new AbortController()

    const request: SendMessageRequest = {
      content,
      conversation_id: currentConversationId.value ?? undefined,
      mode: options.mode,
      project_id: options.projectId,
      model: options.model,
      model_capability: options.model_capability,
      temperature: options.temperature,
    }

    try {
      await sendMessageStream(
        request,
        {
          onStart: (conversationId: number, title: string) => {
            currentConversationId.value = conversationId
            const existing = conversations.value.find(c => c.id === conversationId)
            if (!existing) {
              conversations.value.unshift({
                id: conversationId,
                title,
                mode: options.mode ?? null,
                project_id: options.projectId ?? null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                message_count: 0,
              })
            }
          },
          onContent: (chunk: string) => {
            streamingContent.value += chunk
            charBuffer += chunk
            // Thinking ends as soon as we get first content
            if (isThinking.value) {
              isThinking.value = false
            }
          },
          onAgentIntent: (intent: AgentIntentPayload) => {
            updateLastAssistantMeta({ agent_intent: intent })
          },
          onMediaJob: (job: MediaJobPayload) => {
            updateMediaJobMeta(job)
            void pollMediaJob(job.id)
          },
          onDone: (messageId: number) => {
            // Flush remaining buffer immediately
            stopTypewriter(true)
            const last = messages.value[messages.value.length - 1]
            if (last && last.role === 'assistant') {
              last.id = messageId
              last.isStreaming = false
              last.content = displayContent.value
            }
          },
          onError: (errMsg: string) => {
            stopTypewriter(true)
            error.value = errMsg
            const last = messages.value[messages.value.length - 1]
            if (last && last.role === 'assistant') {
              last.isStreaming = false
              if (!last.content) {
                last.content = '⚠️ 生成失败：' + errMsg
              }
            }
          },
        },
        abortController.signal,
      )
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        stopTypewriter(true)
        if (e.status === 402 || e.data?.code === 'INSUFFICIENT_CREDITS') {
          error.value = 'INSUFFICIENT_CREDITS'
          messages.value = messages.value.slice(0, -2)
        } else {
          error.value = e.message || '发送失败'
          const last = messages.value[messages.value.length - 1]
          if (last && last.role === 'assistant' && !last.content) {
            last.content = '⚠️ ' + (error.value || '发送失败')
            last.isStreaming = false
          }
        }
      }
    } finally {
      isStreaming.value = false
      isThinking.value = false
      streamingContent.value = ''
      stopTypewriter(false)
      abortController = null
    }
  }

  /** Stop the current streaming response */
  function stopStreaming(): void {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    stopTypewriter(true)
    isStreaming.value = false
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.isStreaming = false
    }
  }

  /** Delete a conversation */
  async function deleteConversation(conversationId: number): Promise<void> {
    try {
      await apiDeleteConversation(conversationId)
      conversations.value = conversations.value.filter(c => c.id !== conversationId)
      if (currentConversationId.value === conversationId) {
        newConversation()
      }
    } catch (e: any) {
      error.value = '删除失败'
    }
  }

  return {
    // State
    conversations,
    currentConversationId,
    messages,
    isStreaming,
    isThinking,
    streamingContent,
    displayContent,
    error,
    isLoadingConversations,
    cancellingMediaJobIds,
    mediaCancelErrors,
    // Getters
    currentConversation,
    hasMessages,
    // Actions
    fetchConversations,
    loadConversation,
    newConversation,
    sendMessage,
    stopStreaming,
    cancelMediaJob,
    retryImageJob,
    deleteConversation,
  }
})
