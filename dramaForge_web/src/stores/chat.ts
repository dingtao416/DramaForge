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
import type { ChatMessage, Conversation, ConversationDetail, SendMessageRequest } from '@/api/chat'

/** Local UI message (extends API message with streaming state) */
export interface UIMessage {
  id: number | null          // null while streaming
  role: 'user' | 'assistant' | 'system'
  content: string
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

  // AbortController + typewriter timer
  let abortController: AbortController | null = null
  let typewriterTimer: ReturnType<typeof setInterval> | null = null
  let charBuffer = ''

  // ═══════ Getters ═══════
  const currentConversation = computed(() =>
    conversations.value.find(c => c.id === currentConversationId.value) ?? null
  )
  const hasMessages = computed(() => messages.value.length > 0)

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
        created_at: m.created_at,
      }))
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
    // Getters
    currentConversation,
    hasMessages,
    // Actions
    fetchConversations,
    loadConversation,
    newConversation,
    sendMessage,
    stopStreaming,
    deleteConversation,
  }
})
