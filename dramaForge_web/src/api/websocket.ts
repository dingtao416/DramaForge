/**
 * DramaForge WebSocket 客户端
 * 连接后端 WS 端点 /api/v2/ws/tasks/{taskId}
 * 支持自动重连 + 事件分发
 */

export type WSMessageType = 'progress' | 'completed' | 'error' | 'heartbeat'

export interface WSMessage {
  type: WSMessageType
  task_id: string
  data?: Record<string, unknown>
  progress?: number
  message?: string
  error?: string
}

type WSCallback = (msg: WSMessage) => void

class WebSocketManager {
  private connections = new Map<string, WebSocket>()
  private listeners = new Map<string, Set<WSCallback>>()
  private reconnectTimers = new Map<string, ReturnType<typeof setTimeout>>()
  private maxRetries = 5
  private retryDelay = 2000

  /** 连接任务 WS */
  connect(taskId: string, onMessage?: WSCallback): void {
    if (this.connections.has(taskId)) return

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/api/v2/ws/tasks/${taskId}`

    const ws = new WebSocket(url)
    this.connections.set(taskId, ws)

    if (onMessage) {
      this.on(taskId, onMessage)
    }

    let retries = 0

    ws.onopen = () => {
      console.log(`[WS] connected: ${taskId}`)
      retries = 0
    }

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        this.emit(taskId, msg)
      } catch {
        console.warn('[WS] parse error:', event.data)
      }
    }

    ws.onclose = (e) => {
      console.log(`[WS] closed: ${taskId} (code=${e.code})`)
      this.connections.delete(taskId)

      // Auto reconnect unless normal close or max retries exceeded
      if (e.code !== 1000 && retries < this.maxRetries) {
        retries++
        const timer = setTimeout(() => {
          console.log(`[WS] reconnecting ${taskId} (attempt ${retries})`)
          this.connect(taskId)
        }, this.retryDelay * retries)
        this.reconnectTimers.set(taskId, timer)
      }
    }

    ws.onerror = (err) => {
      console.error(`[WS] error: ${taskId}`, err)
    }
  }

  /** 断开连接 */
  disconnect(taskId: string): void {
    const ws = this.connections.get(taskId)
    if (ws) {
      ws.close(1000, 'client disconnect')
      this.connections.delete(taskId)
    }
    const timer = this.reconnectTimers.get(taskId)
    if (timer) {
      clearTimeout(timer)
      this.reconnectTimers.delete(taskId)
    }
    this.listeners.delete(taskId)
  }

  /** 注册监听 */
  on(taskId: string, callback: WSCallback): void {
    if (!this.listeners.has(taskId)) {
      this.listeners.set(taskId, new Set())
    }
    this.listeners.get(taskId)!.add(callback)
  }

  /** 移除监听 */
  off(taskId: string, callback: WSCallback): void {
    this.listeners.get(taskId)?.delete(callback)
  }

  /** 分发消息 */
  private emit(taskId: string, msg: WSMessage): void {
    this.listeners.get(taskId)?.forEach((cb) => cb(msg))
  }

  /** 断开所有连接 */
  disconnectAll(): void {
    for (const taskId of this.connections.keys()) {
      this.disconnect(taskId)
    }
  }
}

export const wsManager = new WebSocketManager()