/**
 * DramaForge Chat API
 * ====================
 * Conversation CRUD + SSE streaming message support.
 * Adapted from IAA project patterns.
 */
import apiClient, { getToken } from './client'

// ═══════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════

export interface ChatMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  meta_json?: Record<string, any> | null
  created_at: string
}

export interface Conversation {
  id: number
  title: string | null
  mode: string | null
  project_id: number | null
  created_at: string
  updated_at: string
  message_count: number
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[]
}

export interface SendMessageRequest {
  content: string
  conversation_id?: number
  mode?: string        // general / scriptwriter / director / project
  project_id?: number
  stream?: boolean
  model?: string
  temperature?: number
}

// ═══════════════════════════════════════════════════════════════════
// Non-streaming API
// ═══════════════════════════════════════════════════════════════════

/** Send a message (non-streaming) */
export async function sendMessage(data: SendMessageRequest): Promise<{
  conversation_id: number
  message: ChatMessage
}> {
  const response = await apiClient.post('/chat/message', { ...data, stream: false })
  return response.data
}

/** List conversations */
export async function getConversations(page = 1, pageSize = 20): Promise<Conversation[]> {
  const response = await apiClient.get<Conversation[]>('/chat/conversations', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

/** Get conversation detail with messages */
export async function getConversation(conversationId: number): Promise<ConversationDetail> {
  const response = await apiClient.get<ConversationDetail>(`/chat/conversations/${conversationId}`)
  return response.data
}

/** Delete a conversation */
export async function deleteConversation(conversationId: number): Promise<void> {
  await apiClient.delete(`/chat/conversations/${conversationId}`)
}

// ═══════════════════════════════════════════════════════════════════
// SSE Streaming
// ═══════════════════════════════════════════════════════════════════

/**
 * Send a message with SSE streaming.
 * Uses native fetch + ReadableStream to parse server-sent events.
 *
 * SSE event types from backend:
 *   - conversation  → {id, title}
 *   - user_message  → {id, content}
 *   - delta         → {content: "chunk..."}
 *   - done          → {message_id, finish_reason}
 *   - error         → {code, message}
 */
export async function sendMessageStream(
  data: SendMessageRequest,
  handlers: {
    onStart?: (conversationId: number, title: string) => void
    onContent?: (chunk: string) => void
    onDone?: (messageId: number) => void
    onError?: (error: string) => void
  },
  signal?: AbortSignal,
): Promise<void> {
  const token = getToken()

  const response = await fetch('/api/v2/chat/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: token ? `Bearer ${token}` : '',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ ...data, stream: true }),
    signal,
  })

  if (!response.ok) {
    let errorMsg = 'Failed to send message'
    let errorData: any = null
    try {
      errorData = await response.json()
      // Handle structured detail (e.g. 402 insufficient credits)
      if (typeof errorData?.detail === 'object') {
        errorMsg = errorData.detail.message || errorMsg
      } else {
        errorMsg = errorData?.detail || errorData?.message || errorMsg
      }
    } catch { /* ignore */ }

    // Special case: 402 Payment Required (insufficient credits)
    const err: any = new Error(errorMsg)
    err.status = response.status
    err.data = errorData?.detail || errorData
    throw err
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('Response body is not readable')

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE messages are separated by \n\n
      const messages = buffer.split('\n\n')
      buffer = messages.pop() ?? ''

      for (const message of messages) {
        let eventName = ''
        let dataStr = ''

        for (const line of message.split('\n')) {
          if (line.startsWith('event: ')) {
            eventName = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            dataStr = line.slice(6).trim()
          }
        }

        if (!dataStr || dataStr === '[DONE]') continue

        try {
          const payload = JSON.parse(dataStr)

          switch (eventName) {
            case 'conversation':
              handlers.onStart?.(payload.id, payload.title ?? '')
              break
            case 'delta':
              handlers.onContent?.(payload.content ?? '')
              break
            case 'done':
              handlers.onDone?.(payload.message_id)
              break
            case 'error':
              handlers.onError?.(payload.message ?? 'Unknown stream error')
              break
            default:
              // user_message etc. — ignore
              break
          }
        } catch (e) {
          console.warn('[SSE] Failed to parse event:', eventName, dataStr)
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
