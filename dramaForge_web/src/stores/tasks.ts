import { defineStore } from 'pinia'
import { ref } from 'vue'
import { wsManager } from '@/api/websocket'
import type { WSMessage } from '@/api/websocket'

export interface TaskInfo {
  id: string
  type: 'assets' | 'segment' | 'compose'
  status: 'running' | 'completed' | 'failed'
  progress: number
  message: string
}

export const useTasksStore = defineStore('tasks', () => {
  const activeTasks = ref<Map<string, TaskInfo>>(new Map())

  function watchTask(taskId: string, type: TaskInfo['type'], onComplete?: () => void) {
    const task: TaskInfo = {
      id: taskId,
      type,
      status: 'running',
      progress: 0,
      message: '准备中...',
    }
    activeTasks.value.set(taskId, task)

    wsManager.connect(taskId, (msg: WSMessage) => {
      const t = activeTasks.value.get(taskId)
      if (!t) return

      if (msg.type === 'progress') {
        t.progress = msg.progress ?? t.progress
        t.message = msg.message ?? t.message
      } else if (msg.type === 'completed') {
        t.status = 'completed'
        t.progress = 100
        t.message = '已完成'
        wsManager.disconnect(taskId)
        onComplete?.()
        // Remove after delay
        setTimeout(() => activeTasks.value.delete(taskId), 3000)
      } else if (msg.type === 'error') {
        t.status = 'failed'
        t.message = msg.error ?? '生成失败'
        wsManager.disconnect(taskId)
      }
    })
  }

  function cancelTask(taskId: string) {
    wsManager.disconnect(taskId)
    activeTasks.value.delete(taskId)
  }

  return {
    activeTasks,
    watchTask,
    cancelTask,
  }
})