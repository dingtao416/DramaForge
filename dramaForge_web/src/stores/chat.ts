/**
 * DramaForge — Chat Store (Pinia)
 * Manages conversations, messages, and SSE streaming state.
 * Designed for the HomePage inline chat experience.
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

export const useChatStore = defineStore('chat', () => {
  // ═══════ State ═══════
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<number | null>(null)
  const messages = ref<UIMessage[]>([])
  const isStreaming = ref(false)
  const streamingContent = ref('')       // accumulates chunks during SSE
  const error = ref<string | null>(null)
  const isLoadingConversations = ref(false)

  // AbortController for cancelling streams
  let abortController: AbortController | null = null

  // ═══════ Getters ═══════
  const currentConversation = computed(() =>
    conversations.value.find(c => c.id === currentConversationId.value) ?? null
  )
  const hasMessages = computed(() => messages.value.length > 0)

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
    error.value = null
  }

  /**
   * Send a message with SSE streaming.
   * This is the core function for the HomePage chat experience.
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

    // Add placeholder assistant message
    const assistantMsg: UIMessage = {
      id: null,
      role: 'assistant',
      content: '',
      isStreaming: true,
      created_at: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)

    isStreaming.value = true
    streamingContent.value = ''

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
            // Update or add to conversation list
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
            // Update the last (assistant) message in place
            const last = messages.value[messages.value.length - 1]
            if (last && last.role === 'assistant') {
              last.content = streamingContent.value
            }
          },
          onDone: (messageId: number) => {
            // Finalize assistant message
            const last = messages.value[messages.value.length - 1]
            if (last && last.role === 'assistant') {
              last.id = messageId
              last.isStreaming = false
            }
          },
          onError: (errMsg: string) => {
            error.value = errMsg
            // Remove streaming indicator
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
        error.value = e.message || '发送失败'
        const last = messages.value[messages.value.length - 1]
        if (last && last.role === 'assistant' && !last.content) {
          last.content = '⚠️ ' + (error.value || '发送失败')
          last.isStreaming = false
        }
      }
    } finally {
      isStreaming.value = false
      streamingContent.value = ''
      abortController = null
    }
  }

  /** Stop the current streaming response */
  function stopStreaming(): void {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
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
    streamingContent,
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
